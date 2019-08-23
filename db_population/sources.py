from meta.models import Category, Source
from stemp.db_population.population_utils import get_meta_from_json


def insert_sources():
    c_timeseries = Category(
        name="Zeitreihen", description="Quellen der verwendeten Zeitreihen"
    )
    c_timeseries.save()

    Source(
        meta_data=get_meta_from_json("pv_feedin"),
        app_name="stemp",
        category=c_timeseries,
    ).save()

    Source(
        meta_data=get_meta_from_json("dwd_temperature"),
        app_name="stemp",
        category=c_timeseries,
    ).save()
