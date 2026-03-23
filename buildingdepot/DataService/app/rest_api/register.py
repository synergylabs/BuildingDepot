from . import app_subscription
from . import apps
from . import timeseries
from . import timeseries_aggregate
from . import views


def register_view(app_obj):
    timeseries_view = timeseries.TimeSeriesService.as_view("timeseries_api")
    app_obj.add_url_rule(
        "/api/sensor/<name>/timeseries", view_func=timeseries_view, methods=["GET"]
    )
    app_obj.add_url_rule(
        "/api/sensor/timeseries", view_func=timeseries_view, methods=["POST"]
    )
    
    aggregate_timeseries_view = timeseries_aggregate.AggregateTimeSeriesService.as_view("aggregate_timeseries_api")
    app_obj.add_url_rule(
        "/api/sensor/bulk", view_func=aggregate_timeseries_view, methods=["GET"] # deprecated old name
    )
    app_obj.add_url_rule(
        "/api/sensor/aggregate", view_func=aggregate_timeseries_view, methods=["GET"]
    )
    
    access_log_view = timeseries_aggregate.AccessLogService.as_view("access_log_api")
    app_obj.add_url_rule(
        "/api/admin/aggregate_timeseries_access_log", view_func=access_log_view, methods=["GET"]
    )

    app_view = apps.AppService.as_view("app_api")
    app_obj.add_url_rule(
        "/api/apps", view_func=app_view, methods=["GET", "POST", "DELETE"]
    )

    appsub_view = app_subscription.AppSubscriptionService.as_view("appsub_api")
    app_obj.add_url_rule(
        "/api/apps/subscription", view_func=appsub_view, methods=["POST", "DELETE"]
    )
