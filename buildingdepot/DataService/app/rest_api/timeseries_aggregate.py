"""
DataService.rest_api.timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the class for the domain service for time-series data. It
handles all the logic for inserting a data value and reading from the underlying
data stores.

@copyright: (c) 2024 SynergyLabs
@license: CMU License. See License file for details.
"""

import influxdb
import sys
import time
import yaml
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, namedtuple
from flask import request, jsonify
from flask.views import MethodView

from . import responses
from .helper import timestamp_to_time_string, check_oauth, get_email, form_query, check_if_super
from .time_utils import parse_time_input, get_request_timezone, convert_times_to_timezone
from ..models.ds_models import Sensor, AggregateTimeSeriesAccessLog
from .. import r, influx, oauth, exchange

sys.path.append("/srv/buildingdepot")
from ..api_0_0.resources.utils import (
    batch_permission_check,
    permissions_val,
)

# Named tuple for access control check results
AccessControlResult = namedtuple('AccessControlResult', ['allowed', 'error_msg', 'policy_id', 'min_sensors', 'bypass_bd_acl', 'policy_info', 'rate_limit'])

# Named tuple for rate limit configuration
RateLimitConfig = namedtuple('RateLimitConfig', ['max_requests', 'window_days'])


def load_access_control_policies():
    """Load access control policies from YAML file"""
    policy_file = os.path.join(os.path.dirname(__file__), "access_control_policies.yaml")
    with open(policy_file, 'r') as f:
        return yaml.safe_load(f)


class AggregateTimeSeriesService(MethodView):
    def _check_recency(self, max_recency, start_time, end_time):
        """Check if query time range meets policy recency requirements"""
        if max_recency is None:
            return True  # Unrestricted
        
        current_time = time.time()
        # Check if start_time is within max_recency seconds from now
        time_limit = current_time - max_recency
        print(f"time_limit: {time_limit}, start_time: {start_time}, end_time: {end_time}, current_time: {current_time}, max_recency: {max_recency}, float(start_time): {float(start_time)}, float(end_time): {float(end_time)}, result: {float(start_time) >= time_limit and float(end_time) <= current_time}")
        # return float(start_time) >= time_limit and float(end_time) <= current_time
        return float(start_time) >= time_limit

    def _check_time_resolution(self, min_time_resolution, query_resolution_seconds):
        """Check if query resolution meets policy requirements"""
        if min_time_resolution is None:
            return True  # Unrestricted
        
        # query_resolution_seconds is already in seconds
        return query_resolution_seconds >= min_time_resolution

    def _check_matching_tags(self, policy_tags, query_tag_dict, user_email):
        """Check if query tags match policy tag requirements
        
        Args:
            policy_tags (dict): Dictionary of tag requirements. Values can be:
                - A single string value (e.g., "building_a")
                - An array of allowed values (e.g., ["building_a", "building_b"])
                - Special value "<user_email>" to match against user's email
            query_tag_dict (dict): Dictionary of tag key-value pairs from the query
            user_email (str): User's email address for <user_email> substitution
        
        Returns:
            bool: True if all policy tag requirements are met, False otherwise
        """
        # Check each policy tag requirement
        for tag_name, tag_value in policy_tags.items():
            if tag_name not in query_tag_dict:
                return False
            
            query_value = query_tag_dict[tag_name]
            
            # Handle array of allowed values
            if isinstance(tag_value, list):
                # Check if query value matches any of the allowed values
                matched = False
                for allowed_value in tag_value:
                    if allowed_value == "<user_email>":
                        if query_value == user_email:
                            matched = True
                            break
                    elif query_value == allowed_value:
                        matched = True
                        break
                if not matched:
                    return False
            else:
                # Handle single value (original behavior)
                if tag_value == "<user_email>":
                    if query_value != user_email:
                        return False
                else:
                    if query_value != tag_value:
                        return False
        
        return True

    def _check_access_control(self, tags_dict, start_time, end_time, time_aggregation_window, user_email):
        """Check if the query meets access control policy requirements
        
        Args:
            tags_dict (dict): Dictionary of tag key-value pairs
            start_time: Query start time
            end_time: Query end time
            time_aggregation_window: Time aggregation window in seconds
            user_email (str): User's email address
        
        Returns:
            AccessControlResult: Named tuple with fields:
                - allowed (bool): Whether access is allowed
                - error_msg (str or None): Error message if access denied
                - policy_id (str or None): Policy ID that matched
                - bypass_bd_acl (bool): Whether to bypass BD ACL
                - policy_info (list): List of all policies checked with criteria results
        """
        try:
            policies = load_access_control_policies()
        except Exception as e:
            print(f"Error loading access control policies: {str(e)}")
            return AccessControlResult(
                allowed=False,
                error_msg="Error loading access control policies",
                policy_id=None,
                min_sensors=None,
                bypass_bd_acl=False,
                policy_info=[],
                rate_limit=None
            )
        
        policy_info = []
        matching_policy_id = None
        matching_bypass_bd_acl = False
        matching_rate_limit = None
        
        # Walk through ALL policies and check each criterion
        for policy in policies:
            policy_id = policy.get("policy_id")
            required_tags = policy.get("required_tags", {})
            min_sensors = policy.get("min_sensors", None)
            optional_tags = policy.get("optional_tags", [])
            time_restrictions = policy.get("time_restrictions", [])
            bypass_bd_acl = policy.get("bypass_bd_acl", False)
            rate_limit_config = policy.get("rate_limit", None)
            
            # Check that all required_tags match
            required_tags_met = self._check_matching_tags(required_tags, tags_dict, user_email)
            
            # Check that only required_tags and optional_tags are present in query
            allowed_tag_keys = set(required_tags.keys()) | set(optional_tags)
            query_tag_keys = set(tags_dict.keys())
            optional_tags_met = query_tag_keys.issubset(allowed_tag_keys)
            
            # Check time_restrictions - check each restriction individually
            time_restriction_met = False
            for restriction in time_restrictions:
                max_recency = restriction.get("max_recency")
                min_time_resolution = restriction.get("min_time_resolution")
                
                recency_met = self._check_recency(max_recency, start_time, end_time)
                time_resolution_met = self._check_time_resolution(min_time_resolution, time_aggregation_window)
                
                if recency_met and time_resolution_met:
                    time_restriction_met = True
            
            # If no time_restrictions defined, treat as unrestricted
            if not time_restrictions:
                time_restriction_met = True
            
            # Determine if all criteria passed for this policy
            all_criteria_met = required_tags_met and optional_tags_met and time_restriction_met
            
            # Record this policy's check results
            policy_check_result = {
                "policy_id": policy_id,
                "required_tags": {
                    "expected": required_tags,
                    "actual": tags_dict,
                    "met": required_tags_met
                },
                "optional_tags": {
                    "expected": optional_tags,
                    "actual": tags_dict,
                    "met": optional_tags_met
                },
                "time_restrictions": {
                    "expected": time_restrictions,
                    "actual": {
                        "start_time": start_time,
                        "end_time": end_time,
                        "time_aggregation_window": time_aggregation_window
                    },
                    "met": time_restriction_met
                },
            }
            policy_info.append(policy_check_result)
            
            # Track the first matching policy
            if all_criteria_met and matching_policy_id is None:
                matching_policy_id = policy_id
                matching_bypass_bd_acl = bypass_bd_acl
                matching_min_sensors = min_sensors
                # Parse rate limit configuration
                if rate_limit_config:
                    matching_rate_limit = RateLimitConfig(
                        max_requests=rate_limit_config.get("max_requests"),
                        window_days=rate_limit_config.get("window_days", 1)
                    )
        
        # Determine final result
        if matching_policy_id is not None:
            return AccessControlResult(
                allowed=True,
                error_msg=None,
                policy_id=matching_policy_id,
                min_sensors=matching_min_sensors,
                bypass_bd_acl=matching_bypass_bd_acl,
                policy_info=policy_info,
                rate_limit=matching_rate_limit
            )
        
        # No policy allowed access
        return AccessControlResult(
            allowed=False,
            error_msg=f"Access denied: Query does not match any policy requirements",
            policy_id=None,
            min_sensors=None,
            bypass_bd_acl=False,
            policy_info=policy_info,
            rate_limit=None
        )

    def _check_rate_limit(self, user_email, policy_id, rate_limit):
        """Check if the user has exceeded their rate limit for this policy.
        
        Args:
            user_email (str): User's email address
            policy_id (str): Policy ID being used
            rate_limit (RateLimitConfig): Rate limit configuration
        
        Returns:
            tuple: (allowed: bool, request_count: int, error_msg: str or None)
        """
        if rate_limit is None or rate_limit.max_requests is None:
            return (True, 0, None)  # No rate limit configured
        
        try:
            # Calculate the start of the time window
            window_start = datetime.utcnow() - timedelta(days=rate_limit.window_days)
            
            # Count requests in the time window
            request_count = AggregateTimeSeriesAccessLog.objects(
                user_email=user_email,
                policy_id=policy_id,
                timestamp__gte=window_start
            ).count()
            
            if request_count >= rate_limit.max_requests:
                return (
                    False,
                    request_count,
                    f"Rate limit exceeded: {request_count}/{rate_limit.max_requests} requests in the past {rate_limit.window_days} day(s) for policy '{policy_id}'"
                )
            
            return (True, request_count, None)
        except Exception as e:
            print(f"Error checking rate limit: {str(e)}")
            # On error, allow the request but log the issue
            return (True, -1, None)

    def _log_request(self, user_email, policy_id, query_params=None):
        """Log a successful request for rate limiting purposes.
        
        Args:
            user_email (str): User's email address
            policy_id (str): Policy ID that was matched
            query_params (dict): Query parameters for auditing (tags, time range, aggregation, etc.)
        """
        try:
            log_entry = AggregateTimeSeriesAccessLog(
                user_email=user_email,
                policy_id=policy_id,
                timestamp=datetime.utcnow(),
                request_params=query_params or {}
            )
            log_entry.save()
        except Exception as e:
            print(f"Error logging request: {str(e)}")
            # Don't fail the request if logging fails

    def _apply_threshold_filter(self, sensor_names, threshold_field, threshold_direction, threshold_value, threshold_mode, start_time, end_time):
        """Apply a single threshold filter to the sensor list based on their data values.
        
        Args:
            sensor_names (list): List of sensor names to filter.
            threshold_field (str): Field name to apply the threshold on.
            threshold_direction (str): "above" or "below".
            threshold_value (float): Threshold value.
            threshold_mode (str): "any" (at least one value meets threshold) or "all" (all values must meet threshold).
            start_time: Query start time.
            end_time: Query end time.
        
        Returns:
            tuple: (filtered_sensor_names, error_dict) where error_dict is None on success, or a dict with error info on failure.
        """
        # Validate threshold_field - reject "*" queries
        if threshold_field == "*":
            return (None, {"success": False, "error": "Wildcard queries ('*') are not supported for threshold_field"})
        
        # Validate required parameters
        if not sensor_names:
            return (None, {"success": False, "error": "Invalid threshold filter: sensor_names list is empty"})
        
        if not threshold_field:
            return (None, {"success": False, "error": "Invalid threshold filter: threshold_field is required"})
        
        if threshold_value is None:
            return (None, {"success": False, "error": "Invalid threshold filter: threshold_value is required"})

        try:
            threshold_value = float(threshold_value)
        except (ValueError, TypeError):
            return (None, {"success": False, "error": f"Invalid threshold filter: threshold_value '{threshold_value}' is not a valid number"})

        direction = (threshold_direction or "above").lower()
        if direction not in ("above", "below"):
            return (None, {"success": False, "error": f"Invalid threshold filter: threshold_direction must be 'above' or 'below', got '{threshold_direction}'"})

        mode = (threshold_mode or "any").lower()
        if mode not in ("any", "all"):
            return (None, {"success": False, "error": f"Invalid threshold filter: threshold_mode must be 'any' or 'all', got '{threshold_mode}'"})

        # Query each sensor to check if it meets threshold criterion
        filtered_sensors = []
        where_clause = (
            " where (time>'"
            + timestamp_to_time_string(float(start_time))
            + "' and time<'"
            + timestamp_to_time_string(float(end_time))
            + "')"
        )

        # Escape special regex characters in field name and build field query
        escaped_field = (
            threshold_field.replace("(", "\\(")
            .replace(")", "\\)")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        field_query = "/(" + escaped_field + ")-*/"

        for sensor_name in sensor_names:
            query = (
                "select "
                + field_query
                + ' from "'
                + sensor_name
                + '"'
                + where_clause
            )

            try:
                data = influx.query(query)
                sensor_passes = False

                if "series" in data.raw and data.raw["series"]:
                    for series in data.raw["series"]:
                        if "values" in series and series["values"]:
                            columns = series.get("columns", [])
                            field_idx = None

                            # Find column index for the field
                            for idx, col in enumerate(columns):
                                if idx == 0:
                                    continue  # skip time column
                                if col == threshold_field:
                                    field_idx = idx
                                    break
                                elif col.endswith("_" + threshold_field) or col == threshold_field:
                                    field_idx = idx
                                    break
                                elif threshold_field in col:
                                    field_idx = idx
                                    break

                            # If we found a specific field column
                            if field_idx is not None:
                                if mode == "any":
                                    # At least one value must meet threshold
                                    for row in series["values"]:
                                        if row and field_idx < len(row) and row[field_idx] is not None:
                                            try:
                                                value = float(row[field_idx])
                                                if direction == "above" and value >= threshold_value:
                                                    sensor_passes = True
                                                    break
                                                elif direction == "below" and value <= threshold_value:
                                                    sensor_passes = True
                                                    break
                                            except (ValueError, TypeError):
                                                continue
                                else:  # mode == "all"
                                    # All values must meet threshold
                                    has_values = False
                                    sensor_passes = True
                                    for row in series["values"]:
                                        if row and field_idx < len(row) and row[field_idx] is not None:
                                            has_values = True
                                            try:
                                                value = float(row[field_idx])
                                                if direction == "above" and value < threshold_value:
                                                    sensor_passes = False
                                                    break
                                                elif direction == "below" and value > threshold_value:
                                                    sensor_passes = False
                                                    break
                                            except (ValueError, TypeError):
                                                # Skip invalid values in "all" mode (treat as passing)
                                                continue
                                    # If no values found, sensor fails (can't say all values meet threshold)
                                    if not has_values:
                                        sensor_passes = False

                        if (mode == "any" and sensor_passes) or (mode == "all" and not sensor_passes):
                            break

            except Exception as e:
                print(f"Error querying sensor {sensor_name} for threshold filter: {str(e)}")
                sensor_passes = False

            if sensor_passes:
                filtered_sensors.append(sensor_name)

        return (filtered_sensors, None)

    @check_oauth
    def get(self):
        """
        Reads the data of multiple sensors selected by tags over the interval specified.
        Access is controlled by policies defined in access_control_policies.json.
        
        Args as JSON:
            "tags": <tags to filter sensors>
            "start_time": <unix timestamp of start time>
            "end_time": <unix timestamp of end time>
            "fields": <fields to retrieve, separated by semicolons>
            "aggregation": <aggregation function: "raw", "mean", "median", "max", "min", or "count">
            "time_aggregation_window": <optional time window for aggregation, e.g. "1m", "5m", "1h"> (defaults to "1h")
            "dry_run": <optional boolean to dry run the query>
            "threshold_field": <optional field name to filter on>
            "threshold_direction": <optional direction: "above" or "below">
            "threshold_value": <optional numeric threshold value>
            "threshold_mode": <optional mode: "any" (at least one value meets threshold) or "all" (all values must meet threshold), defaults to "any">
        """
        try:
            data = request.args
            tags_str = data.get("tags", "")
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []
            start_time_raw = data.get("start_time")
            end_time_raw = data.get("end_time")
            fields = data.get("fields", "*")
            aggregation = data.get("aggregation", "mean")
            dry_run = data.get("dry_run", False)
            if isinstance(dry_run, str):
                if dry_run.lower() == "true":
                    dry_run = True
                else:
                    dry_run = False
            # Default to 3600 seconds (1 hour), accept as integer/float
            time_aggregation_window = data.get("time_aggregation_window", 3600)
            try:
                time_aggregation_window = float(time_aggregation_window)
            except (ValueError, TypeError):
                time_aggregation_window = 3600  # Default to 1 hour if invalid
            
            # Parse simple threshold parameters
            threshold_field = data.get("threshold_field")
            threshold_direction = data.get("threshold_direction")
            threshold_value = data.get("threshold_value")
            threshold_mode = data.get("threshold_mode", "any")  # Default to "any"
        except:
             return jsonify(responses.missing_parameters)

        if not all([tags, start_time_raw]):
            return jsonify(responses.missing_parameters)
        
        # Parse start_time (required)
        start_time, start_time_error = parse_time_input(start_time_raw)
        if start_time_error:
            return jsonify({
                "success": False,
                "error": f"Invalid start_time: {start_time_error}"
            })
        
        # Parse end_time (optional, defaults to current time)
        if end_time_raw is None:
            end_time = time.time()
        else:
            end_time, end_time_error = parse_time_input(end_time_raw)
            if end_time_error:
                return jsonify({
                    "success": False,
                    "error": f"Invalid end_time: {end_time_error}"
                })
        
        # Detect timezone from user's input for response formatting
        response_tz = get_request_timezone(start_time_raw) or get_request_timezone(end_time_raw)

        # Parse tags into a simple key-value dictionary
        tags_dict = {}
        for tag in tags:
            if tag and ':' in tag:
                key, value = tag.split(':', 1)
                tags_dict[key] = value
        
        # Check access control policies
        user_email = get_email()
        access_result = self._check_access_control(
            tags_dict, start_time, end_time, time_aggregation_window, user_email
        )
        if not access_result.allowed:
            return jsonify({
                "success": False,
                "error": access_result.error_msg or "Access denied",
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info
            })

        # Check rate limit
        rate_allowed, request_count, rate_error = self._check_rate_limit(
            user_email, access_result.policy_id, access_result.rate_limit
        )
        if not rate_allowed:
            return jsonify({
                "success": False,
                "error": rate_error,
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info,
                "rate_limit_info": {
                    "requests_used": request_count,
                    "max_requests": access_result.rate_limit.max_requests if access_result.rate_limit else None,
                    "window_days": access_result.rate_limit.window_days if access_result.rate_limit else None
                }
            })

        # Form query to find sensors
        args = {}
        form_query("tags", tags, args, "$and")
        sensors = Sensor._get_collection().find(args)
        
        # Collect all sensor names (measurements) for the InfluxDB query
        sensor_names = [sensor['name'] for sensor in sensors]
        print("sensor_names before permission check:", sensor_names)

        # check if zero sensors found
        if len(sensor_names) == 0:
            if "owner" in tags_dict:
                # try the search query without owner tag to give better error message
                args_no_owner = {}
                tags_no_owner = {k: v for k, v in tags_dict.items() if k != "owner"}
                form_query("tags", [f"{k}:{v}" for k, v in tags_no_owner.items()], args_no_owner, "$and")
                sensors_no_owner = Sensor._get_collection().find(args_no_owner)
                if len(list(sensors_no_owner)) > 0:
                    error_msg = f"Owner '{tags_dict["owner"]}' does not own any sensors with the specified tags"
                else:
                    error_msg = "No sensors found with the specified tags"
            else:
                error_msg = "No sensors found with the specified tags"
            return jsonify({
                "success": False,
                "error": error_msg,
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info
            })
        
        # Check permissions for each sensor
        if access_result.bypass_bd_acl != True:
            permissions = batch_permission_check(sensor_names, user_email)
            # Filter sensors to only include those with read permission (matching authenticate_acl logic)
            # For "r" permission, allow permissions with value <= 4: "r/w/p" (2), "r/w" (3), "r" (4)
            sensor_names = [
                name for name in sensor_names 
                if permissions.get(name) and permissions.get(name) != "u/d" and 
                permissions_val.get(permissions.get(name), 999) <= permissions_val.get("r", 4)
            ]
            print("sensor_names after permission check:", sensor_names)

        # Check min_sensors requirement
        if access_result.min_sensors is not None and len(sensor_names) < access_result.min_sensors:
            return jsonify({
                "success": False,
                "error": "Query requires at least " + str(access_result.min_sensors) + " sensors in result, but fewer were matched",
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info
            })
            
        if dry_run==True:
            # Build rate limit info for dry run response (doesn't consume a request)
            dry_run_rate_limit_info = None
            if access_result.rate_limit:
                dry_run_rate_limit_info = {
                    "requests_used": request_count,  # Don't include this request since it's a dry run
                    "max_requests": access_result.rate_limit.max_requests,
                    "window_days": access_result.rate_limit.window_days
                }
            return jsonify({
                "success": True,
                "error": None,
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info,
                "rate_limit_info": dry_run_rate_limit_info,
                "sensor_count": len(sensor_names),
            })

        # Apply threshold filter
        if threshold_field and threshold_value is not None:
            filtered_sensors, error = self._apply_threshold_filter(
                sensor_names,
                threshold_field,
                threshold_direction,
                threshold_value,
                threshold_mode,
                start_time,
                end_time,
            )
            if error is not None:
                return jsonify(error)
            sensor_names = filtered_sensors
            print("sensor_names after threshold filter:", sensor_names)
        
            # Check min_sensors AGAIN after filtering
            # The sensors might have been filtered too low, so we check threshold again
            if access_result.min_sensors is not None and len(sensor_names) < access_result.min_sensors:
                return jsonify({
                    "success": False,
                    "error": "Query requires at least " + str(access_result.min_sensors) + " sensors in result, but fewer were matched",
                    "policy_matched": access_result.policy_id,
                    "policy_info": access_result.policy_info
                })
        
        if not sensor_names:
            return jsonify({
                "success": False,
                "error": "No sensors found", 
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info
            })

        # If fields is empty, return no fields (just time array)
        if fields == "":
            return jsonify({
                "success": True,
                "data": {"time": []},
                "aggregation": aggregation,
                "policy_matched": access_result.policy_id,
                "policy_info": access_result.policy_info
            })
        
        # Field handling logic matching TimeSeriesService
        current_fields = fields
        if current_fields != "*":
            current_fields = "/(" + "|".join(current_fields.split(";")) + ")-*/"
        
        # Build base WHERE clause
        where_clause = (
            " where (time>'"
            + timestamp_to_time_string(float(start_time))
            + "' and time<'"
            + timestamp_to_time_string(float(end_time))
            + "')"
        )
        
        # Build FROM clause with all sensor measurements
        # InfluxDB allows querying multiple measurements separated by commas
        from_clause = ", ".join(['"' + name + '"' for name in sensor_names])
        
        # Build query based on aggregation and time_aggregation_window
        # When querying multiple measurements, InfluxDB aggregates across all of them
        # time_aggregation_window is in seconds
        time_window_str = str(int(time_aggregation_window)) + "s"
        if aggregation == "raw":
            # For "raw" aggregation with time window, use mean as default aggregation
            query = (
                "select mean("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        elif aggregation == "mean":
            query = (
                "select mean("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        elif aggregation == "median":
            query = (
                "select median("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        elif aggregation == "max":
            query = (
                "select max("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        elif aggregation == "min":
            query = (
                "select min("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        elif aggregation == "count":
            # For count, we use COUNT(*) to detect if a sensor has data in a time window
            # We'll count how many sensors have data in each window
            query = (
                "select count("
                + current_fields
                + ") from "
                + from_clause
                + where_clause
                + " GROUP BY time("
                + time_window_str
                + ")"
            )
        else:
            return jsonify(responses.missing_parameters)
        print("aggregate query to influx:", query)

        try:
            data = influx.query(query)
            # print("influx data:", data.raw)
            # InfluxDB may return multiple series (one per measurement) even with aggregation
            # We need to merge them to get a single aggregated result across all sensors
            if 'series' in data.raw and data.raw['series']:
                # Handle count aggregation differently - count sensors per time window
                if aggregation == "count":
                    # For count, we count how many sensors have data in each time window
                    time_to_sensor_count = defaultdict(int)
                    
                    for series in data.raw['series']:
                        if 'values' in series:
                            for row in series['values']:
                                if row:  # Ensure row is not empty
                                    time_val = row[0]  # First column is time
                                    # Check if there's any data (count > 0)
                                    has_data = False
                                    for val in row[1:]:  # Check all field values
                                        if val is not None and val != 0:
                                            has_data = True
                                            break
                                    if has_data:
                                        time_to_sensor_count[time_val] += 1
                    
                    # Build response with count data
                    formatted_data = {"time": [], "count": []}
                    for time_val in sorted(time_to_sensor_count.keys()):
                        formatted_data["time"].append(time_val)
                        formatted_data["count"].append(time_to_sensor_count[time_val])
                    
                    response_data = {
                        "data": formatted_data,
                        "aggregation": aggregation
                    }
                else:
                    # If we have multiple series, merge them by time
                    # Group values by time and aggregate across all sensors
                    time_to_values = defaultdict(list)
                    columns = None
                    
                    for series in data.raw['series']:
                        if 'columns' in series:
                            if columns is None:
                                columns = series['columns']
                            if 'values' in series:
                                for row in series['values']:
                                    if row:  # Ensure row is not empty
                                        time_val = row[0]  # First column is time
                                        # Store all field values for this time point
                                        time_to_values[time_val].append(row[1:])  # All values except time
                    
                    # Aggregate values for each time point
                    aggregated_values = []
                    for time_val in sorted(time_to_values.keys()):
                        values_list = time_to_values[time_val]
                        if values_list:
                            # Aggregate across all sensors for this time point
                            aggregated_row = [time_val]
                            # For each field, aggregate across all sensors
                            num_fields = len(values_list[0])
                            for field_idx in range(num_fields):
                                field_values = [v[field_idx] for v in values_list if field_idx < len(v) and v[field_idx] is not None]
                                if field_values:
                                    if aggregation == "mean":
                                        aggregated_value = sum(field_values) / len(field_values)
                                    elif aggregation == "median":
                                        # Simple median calculation
                                        sorted_vals = sorted(field_values)
                                        n = len(sorted_vals)
                                        if n % 2 == 0:
                                            aggregated_value = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
                                        else:
                                            aggregated_value = sorted_vals[n//2]
                                    else:  # raw or default to mean
                                        aggregated_value = sum(field_values) / len(field_values)
                                    aggregated_row.append(aggregated_value)
                                else:
                                    aggregated_row.append(None)
                            aggregated_values.append(aggregated_row)
                    
                    # Transform to nested JSON structure
                    # Format: {"data": {"time": [...], "field1": [...], ...}, "aggregation": "mean"}
                    if columns and len(columns) > 0:
                        # Initialize data structure with time array and field arrays
                        formatted_data = {"time": []}
                        # Get field column names (skip first column which is time)
                        # Strip aggregation prefixes (mean_, median_, etc.) from column names
                        field_columns = []
                        for col in columns[1:] if len(columns) > 1 else []:
                            # Remove aggregation function prefix (e.g., "mean_", "median_")
                            cleaned_col = col
                            if aggregation == "mean" and col.startswith("mean_"):
                                cleaned_col = col[5:]  # Remove "mean_" prefix
                            elif aggregation == "median" and col.startswith("median_"):
                                cleaned_col = col[7:]  # Remove "median_" prefix
                            elif aggregation == "max" and col.startswith("max_"):
                                cleaned_col = col[4:]  # Remove "max_" prefix
                            elif aggregation == "min" and col.startswith("min_"):
                                cleaned_col = col[4:]  # Remove "min_" prefix
                            field_columns.append(cleaned_col)
                        
                        for field_col in field_columns:
                            formatted_data[field_col] = []
                        
                        # Populate arrays from aggregated_values
                        for row in aggregated_values:
                            if row and len(row) > 0:
                                formatted_data["time"].append(row[0])  # Time value
                                # Add field values
                                for idx, field_col in enumerate(field_columns):
                                    field_value = row[idx + 1] if idx + 1 < len(row) else None
                                    formatted_data[field_col].append(field_value)
                        
                        response_data = {
                            "data": formatted_data,
                            "aggregation": aggregation
                        }
                    else:
                        response_data = {
                            "data": {"time": []},
                            "aggregation": aggregation
                        }
            else:
                response_data = {
                    "data": {"time": []},
                    "aggregation": aggregation
                }
        except influxdb.exceptions.InfluxDBClientError as e:
            # Log the error for debugging
            print(f"Error querying sensors: {str(e)}")
            return jsonify({"success": False, "error": str(e), "policy_matched": access_result.policy_id, "policy_info": access_result.policy_info})
        
        # Convert response times to the user's requested timezone
        if response_tz and "data" in response_data and "time" in response_data["data"]:
            response_data["data"]["time"] = convert_times_to_timezone(
                response_data["data"]["time"], response_tz
            )

        # Log successful request for rate limiting
        query_params = {
            "tags": tags_dict,
            "start_time": start_time,
            "end_time": end_time,
            "fields": fields,
            "aggregation": aggregation,
            "time_aggregation_window": time_aggregation_window,
            "threshold_field": threshold_field,
            "threshold_direction": threshold_direction,
            "threshold_value": threshold_value,
            "threshold_mode": threshold_mode,
            "sensors_matched": len(sensor_names)
        }
        self._log_request(user_email, access_result.policy_id, query_params)
        
        # Build rate limit info for response
        rate_limit_info = None
        if access_result.rate_limit:
            rate_limit_info = {
                "requests_used": request_count + 1,  # Include this request
                "max_requests": access_result.rate_limit.max_requests,
                "window_days": access_result.rate_limit.window_days
            }
        
        return jsonify({
            "success": True,
            "data": response_data,
            "policy_matched": access_result.policy_id,
            "policy_info": access_result.policy_info,
            "rate_limit_info": rate_limit_info
        })


class AccessLogService(MethodView):
    """Admin-only API to read the aggregate time series access log."""
    
    @check_oauth
    def get(self):
        """
        Retrieves access log entries. Admin only.
        
        Query parameters:
            user_email: (optional) Filter by user email
            policy_id: (optional) Filter by policy ID
            start_time: (optional) Filter logs after this Unix timestamp
            end_time: (optional) Filter logs before this Unix timestamp
            limit: (optional) Maximum number of entries to return (default: 100, max: 1000)
            offset: (optional) Number of entries to skip for pagination (default: 0)
        """
        # Check admin permissions
        current_user_email = get_email()
        if not check_if_super(current_user_email):
            return jsonify({
                "success": False,
                "error": "Access denied: Admin privileges required"
            }), 403
        
        try:
            data = request.args
            user_email_filter = data.get("user_email")
            policy_id_filter = data.get("policy_id")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            limit = min(int(data.get("limit", 100)), 1000)  # Cap at 1000
            offset = int(data.get("offset", 0))
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Invalid query parameters"
            })
        
        # Build query filters
        query_filters = {}
        if user_email_filter:
            query_filters["user_email"] = user_email_filter
        if policy_id_filter:
            query_filters["policy_id"] = policy_id_filter
        if start_time:
            try:
                query_filters["timestamp__gte"] = datetime.utcfromtimestamp(float(start_time))
            except (ValueError, TypeError):
                pass
        if end_time:
            try:
                query_filters["timestamp__lte"] = datetime.utcfromtimestamp(float(end_time))
            except (ValueError, TypeError):
                pass
        
        try:
            # Get total count for pagination info
            total_count = AggregateTimeSeriesAccessLog.objects(**query_filters).count()
            
            # Query with pagination, ordered by most recent first
            logs = AggregateTimeSeriesAccessLog.objects(**query_filters).order_by("-timestamp").skip(offset).limit(limit)
            
            # Format results
            results = []
            for log in logs:
                results.append({
                    "user_email": log.user_email,
                    "policy_id": log.policy_id,
                    "timestamp": log.timestamp.isoformat() + "Z" if log.timestamp else None,
                    "request_params": log.request_params
                })
            
            return jsonify({
                "success": True,
                "data": results,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(results) < total_count
                }
            })
        except Exception as e:
            print(f"Error reading access log: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error reading access log"
            })
