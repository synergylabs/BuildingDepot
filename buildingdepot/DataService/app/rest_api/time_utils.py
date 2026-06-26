"""
DataService.rest_api.time_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shared helper functions for parsing and timezone-converting time values used
across time-series APIs.
"""

from datetime import datetime, timezone


def parse_time_input(time_str):
    """Parse a time input as either a Unix timestamp or ISO 8601 string.

    Args:
        time_str: Either a Unix timestamp (int/float/string) or ISO 8601 string

    Returns:
        tuple: (unix_timestamp: float, error_message: str or None)
               On success, returns (timestamp, None)
               On failure, returns (None, error_message)
    """
    if time_str is None:
        return (None, "Time value is required")

    # First, try to parse as a Unix timestamp (int or float)
    try:
        timestamp = float(time_str)
        return (timestamp, None)
    except (ValueError, TypeError):
        pass

    # If not a valid Unix timestamp, try ISO 8601
    time_str = str(time_str).strip()

    try:
        dt = datetime.fromisoformat(time_str)
        return (dt.timestamp(), None)
    except ValueError as e:
        return (
            None,
            f"Invalid time format: '{time_str}'. Expected Unix timestamp or ISO 8601 format. Error: {str(e)}",
        )


def get_request_timezone(time_str):
    """Extract timezone info from a time input string.

    Returns the timezone if the input is an ISO 8601 string with timezone info,
    otherwise returns None (indicating UTC).
    """
    if time_str is None:
        return None

    # If it's a unix timestamp (numeric), no timezone info
    try:
        float(time_str)
        return None
    except (ValueError, TypeError):
        pass

    # Try parsing as ISO 8601
    try:
        dt = datetime.fromisoformat(str(time_str).strip())
        return dt.tzinfo
    except ValueError:
        return None


def convert_times_to_timezone(time_values, target_tz):
    """Convert a list of UTC time strings (from InfluxDB) to the target timezone.

    Args:
        time_values: list of ISO 8601 time strings from InfluxDB (UTC)
        target_tz: target timezone (datetime.tzinfo), or None for no conversion

    Returns:
        list of ISO 8601 strings in target timezone
    """
    if target_tz is None:
        return time_values

    converted = []
    for time_val in time_values:
        try:
            # Replace 'Z' with '+00:00' for fromisoformat() compatibility (Python < 3.11)
            dt = datetime.fromisoformat(str(time_val).replace("Z", "+00:00"))
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_local = dt.astimezone(target_tz)
            converted.append(dt_local.isoformat())
        except (ValueError, AttributeError, TypeError):
            converted.append(time_val)
    return converted
