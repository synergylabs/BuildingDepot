from flask_restful import Resource, reqparse
from ...models.ds_models import Sensor
from ... import r
from .utils import validate_email, success, permission
from .. import auth, g
from ..errors import not_allowed


def subscribed_sensors_validator(sensors):
    if isinstance(sensors, str):
        sensors = [sensors]
    if not isinstance(sensors, list):
        raise ValueError('Sensors field must be string or list')
    for sensor_name in sensors:
        if Sensor.objects(name=sensor_name).first() is None:
            raise ValueError('Sensor {} does not exist'.format(sensor_name))
    return sensors


class Subscription(Resource):
    decorators = [auth.login_required]

    @validate_email
    def get(self, email):
        return {'subscribed_sensors': list(r.smembers('subscribed_sensors:{}'.format(email)))}

    def process(self, email, handler_name):
        parser = reqparse.RequestParser()
        parser.add_argument('sensors', type=subscribed_sensors_validator, required=True, location='json')
        args = parser.parse_args()

        sensors = args['sensors']
        for sensor_name in sensors:
            if permission(g.user, sensor_name) == 'undefined':
                return not_allowed('You do not have read permission to sensor {}'.format(sensor_name))

        pipe = r.pipeline()
        for sensor_name in sensors:
            fn = getattr(pipe, handler_name)
            fn('subscribers:{}'.format(sensor_name), email)
            fn('subscribed_sensors:{}'.format(email), sensor_name)
        pipe.execute()
        return success()

    @validate_email
    def post(self, email):
        return self.process(email, 'sadd')

    @validate_email
    def delete(self, email):
        return self.process(email, 'srem')


class SubscriptionChanges(Resource):
    decorators = [auth.login_required]

    @validate_email
    def get(self, email):
        subscribed_sensors = r.smembers('subscribed_sensors:{}'.format(email))
        res = []
        for sensor_name in subscribed_sensors:
            point = r.get('latest_point:{}:{}'.format(sensor_name, email))
            if point is not None:
                time, value = point.split('-')
                res.append({'sensor': sensor_name, 'latest_point': {time: value}})
        return {'changes': res}


class SubscriptionClearAllChanges(Resource):
    decorators = [auth.login_required]

    @validate_email
    def post(self, email):
        subscribed_sensors = r.smembers('subscribed_sensors:{}'.format(email))
        pipe = r.pipeline()
        for sensor_name in subscribed_sensors:
            pipe.delete('latest_point:{}:{}'.format(sensor_name, email))
        pipe.execute()
        return success()


class SubscriptionClearChange(Resource):
    decorators = [auth.login_required]

    @validate_email
    def post(self, email, sensor_name):
        r.delete('latest_point:{}:{}'.format(sensor_name, email))
        return success()