.. DataService API Documentation


Timeseries
##########

The Sensor collection manages Sensors for Locations associated with the DataService.
Sensor access is restricted to :ref:`Users <CentralS-Users>` or :ref:`Admins <DataS-Admins>` with
Permissions for the Sensor and to the `Admin` who owns the Sensor.

.. _DataS List Sensors:

Post Timeseries Datapoints
**************************

This stores datapoints in the timeseries of the specified Sensorpoint.

The first datapoint that is posted to the uuid defines the datatype for all further timeseries datapoints e.g. if the first datapoint posted to a certain uuid is a int then all further datapoints have to be ints.


.. http:post:: /api/sensor/timeseries

   Within a singe POST request data can be posted to multiple sensor points. The format for each sensor point in the list should be as follows.

   :json string sensor_id: UUID of the sensor to which data has to be posted
   :json list samples: A list of the data points that have to be added to the time-series of the sensor point given by sensor_id. Each item in the list has to be of the following format:
        {
            "time": A unix timestamp of a sampling,

            "value": A sensor value
        }
   :returns:
      * **success** `(string)` -- Returns 'True' if data is posted succesfully otherwise 'False'
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

.. compound::

   **Example request**:

   .. sourcecode:: http

      POST /api/sensor/timeseries HTTP/1.1
      Accept: application/json; charset=utf-8

      [
        {
          "sensor_id":"a5d6277e-4b51-4056-b9fd-0a6505b4f5a6",
          "samples":[
                  {
                    "value":24.56,
                    "time":1225865462
                  },
                  {
                    "value":23.12,
                    "time":1225865500
                  }
                 ]
        },
        {
          "sensor_id":"cee06227-72e5-49d2-94f1-20c501ca2afa",
          "samples":[
                  {
                    "value":24.56,
                    "time":1225865462
                  },
                  {
                    "value":23.12,
                    "time":1225865500
                  }
                 ]
        }
      ]

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success": "True"
      }

Read Timeseries Datapoints
**************************

This retreives a list of datapoints for the timeseries of the specified Sensorpoint

.. http:get:: /sensor/<sensor-uuid>/timeseries?start_time=<start_timestamp>&end_time=<end_timestamp>&resolution=<resolution_units>

   :param string sensor-uuid: UUID associated with Sensor (compulsory)
   :param integer start_time: The starting point of time from which the timeseries data of this sensor point is desired. Has to be a UNIX timestamp. (compulsory)
   :param integer end_time: The ending point of time till which the timeseries data of this sensor point is desired. Has to be a UNIX timestamp.(compulsory)
   :param string resolution: The resolution of the data required. If not specified will retrieve all the datapoints over the specified interval. Has to be specified in the format time units as an integer + unit identifier e.g. 10s,1m,1h etc. (optional)
   :returns:
      * **success** `(string)` -- Returns 'True' if data is retrieved succesfully otherwise 'False'
      * **data** `(struct)` -- Contains the series
          * **series** `(list)` -- Contains the timeseries data, uuid of the sensor and the column names for the timeseries data
          * **columns** `(list)` -- Contains the names of the columns of the data that is present in the timeseries
          * **name** `(string)` -- uuid of the sensor whose data is being retrieved
          * **values** `(list)` -- Contains the list of timeseries data that has been requested in the order represented by the columns.
   :status 200: Success
   :status 401: Unauthorized Credentials (See :ref:`HTTP 401 <HTTP 401>`)

Note: Both interval and resolution are specified with the time value appended by the type of the value e.g. 10s for 10 seconds or 10m for 10 minutes.

.. compound::

   **Example request**:

   .. sourcecode:: http

      GET /sensor/<sensor-uuid>/timeseries?start_time=1445535722&end_time=1445789516&resolution=10s HTTP/1.1
      Accept: application/json; charset=utf-8

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "success":"True",
        "data": {
          "series": [
            {
              "columns": [
                "time",
                "inserted_at",
                "value"
              ],
              "name": "35b137b2-c7c6-4608-8489-1c3f0ee7e2d5",
              "values": [
                [
                  "2015-10-22T17:41:44.762495917Z",
                  1445535722.0,
                  22.11
                ],
                [
                  "2015-10-22T17:43:19.48927063Z",
                  1445535818.0,
                  22.23
                ],
                          [
                  "2015-10-22T22:44:53.066248715Z",
                  1445553913.0,
                  24.56
                ]
              ]
            }
          ]
        }
      }
