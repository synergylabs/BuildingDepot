"""
DataService.rest_api.responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the constants i.e.  the responses that will be returned
to the user under certain failure and success conditions are
defined here in this file

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

success_true = {"success": "True"}
success_false = {"success": "False"}
missing_data = {"success": "False", "error": "Missing data"}
missing_parameters = {"success": "False", "error": "Missing parameters"}
resolution_high = {"success": "False", "error": "Too many points for this resolution"}
broker_connection_failure = {"success": "False", "error": "Failed to connect broker"}
queue_creation_failure = {"success": "False", "error": "Failed to create queue"}
queue_deletion_failure = {"success": "False", "error": "Failed to delete queue"}
application_does_not_exist = {"success": "False", "error": "Application does not exist"}
