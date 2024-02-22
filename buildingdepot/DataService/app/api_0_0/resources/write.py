from flask_restful import Resource, reqparse
from time import time

from .utils import success, validate_sensor, permission
from .. import auth, g
from ..errors import not_allowed
from ... import r, influx


def timeseries_validator(ts):
    if isinstance(ts, dict):
        ts = [ts]
    if not isinstance(ts, list):
        raise ValueError("Timeseries field must be dict or list")
    return ts


class Write(Resource):
    decorators = [auth.login_required]

    @validate_sensor
    def get(self, sensor_name):
        if permission(g.user, sensor_name) == "undefined":
            return not_allowed(
                "You do not have read permission to sensor {}".format(sensor_name)
            )
        parser = reqparse.RequestParser()
        parser.add_argument("start", type=int, default=0, location="args")
        parser.add_argument("end", type=int, location="args")
        args = parser.parse_args()

        query = "select value from {} where time > {}s".format(
            sensor_name, args["start"]
        )
        if args["end"] is not None:
            query += " and time < {}s".format(args["end"])
        points = influx.query(query)[0]["points"]
        return {"timeseries": [{point[0]: point[2]} for point in points]}

    @validate_sensor
    def post(self, sensor_name):
        # permission_s = time()
        if permission(g.user, sensor_name) != "r/w":
            return not_allowed(
                "You do not have write permission to sensor {}".format(sensor_name)
            )
        # permission_e = time()
        parser = reqparse.RequestParser()
        parser.add_argument(
            "timeseries", type=timeseries_validator, required=True, location="json"
        )
        args = parser.parse_args()

        points = [
            [int(list(pair.keys())[0]), list(pair.values())[0]]
            for pair in args["timeseries"]
        ]
        max_point = max(points)

        # sub_s = time()
        emails = r.smembers("subscribers:{}".format(sensor_name))
        pipe = r.pipeline()

        for email in emails:
            pipe.set(
                "latest_point:{}:{}".format(sensor_name, email),
                "{}-{}".format(max_point[0], max_point[1]),
            )
        pipe.execute()
        # sub_e = time()

        data = [{"name": sensor_name, "columns": ["time", "value"], "points": points}]
        print("I am here")
        print(data)
        # series_s = time()
        try:
            influx.write_points(data)
        except Exception as e:
            print(("wrong ", e))
        # series_e = time()
        print("I am ther")
        # all_e = time()
        # print 'permission: ', permission_e - permission_s
        # print 'sub: ', sub_e - sub_s
        # print 'series: ', series_e - series_s
        # print 'all: ', all_e-all_s
        return success()
