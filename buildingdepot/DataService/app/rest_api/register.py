from . import views
from . import timeseries
from . import apps
from . import app_subscription


def register_view(app_obj):
    timeseries_view = timeseries.TimeSeriesService.as_view('timeseries_api')
    app_obj.add_url_rule('/api/sensor/<name>/timeseries',
                         view_func=timeseries_view,
                         methods=['GET'])
    app_obj.add_url_rule('/api/sensor/timeseries',
                         view_func=timeseries_view,
                         methods=['POST'])

    app_view = apps.AppService.as_view('app_api')
    app_obj.add_url_rule('/api/apps',
                         view_func=app_view,
                         methods=['GET', 'POST', 'DELETE'])

    appsub_view = app_subscription.AppSubscriptionService.as_view('appsub_api')
    app_obj.add_url_rule('/api/apps/subscription',
                         view_func=appsub_view,
                         methods=['POST', 'DELETE'])
