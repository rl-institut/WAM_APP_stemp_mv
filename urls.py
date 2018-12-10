
from django.urls import path, register_converter
import cursive_re

from wam.admin import wam_admin_site
from stemp.views import (
    IndexView, ResultView, ParameterView, DemandSingleView,
    DemandDistrictView, TechnologyView,
    DemandSelectionView
)
from stemp import views_dynamic
from stemp import views_admin


def get_list_regex():
    number = cursive_re.one_or_more(
        cursive_re.any_of(cursive_re.in_range('0', '9')))
    regex = number + cursive_re.zero_or_more(cursive_re.text(',') + number)
    return str(regex)


class ListConverter:
    regex = get_list_regex()

    @staticmethod
    def to_python(value):
        return [int(v) for v in value.split(',')]

    @staticmethod
    def to_url(value):
        return ','.join(map(str, value))


register_converter(ListConverter, 'list')


app_name = 'stemp'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path(
        'demand_selection/',
        DemandSelectionView.as_view(),
        name='demand_selection'
    ),
    path('demand/single/', DemandSingleView.as_view(), name='demand_single'),
    path(
        'demand/district/household/',
        DemandSingleView.as_view(is_district_hh=True),
        name='demand_district_household'
    ),
    path(
        'demand/district/empty',
        DemandDistrictView.as_view(),
        name='demand_district_empty',
    ),
    path(
        'demand/district/',
        DemandDistrictView.as_view(new_district=False),
        name='demand_district',
    ),
    path('technology/', TechnologyView.as_view(), name='technology'),
    path('parameter/', ParameterView.as_view(), name='parameter'),
    path('result/<list:results>', ResultView.as_view(), name='result'),
    path(
        'ajax/get_next_household_name/',
        views_dynamic.get_next_household_name,
        name='household_name'
    ),
    path(
        'ajax/get_energy/',
        views_dynamic.get_energy,
    ),
    path(
        'ajax/get_square_meters/',
        views_dynamic.get_square_meters,
    ),
    path(
        'ajax/get_warm_water_energy/',
        views_dynamic.get_warm_water_energy,
    ),
    path(
        'ajax/get_roof_area/',
        views_dynamic.get_roof_area,
    ),
]

admin_url_patterns = [
    path(
        'stemp/manage',
        wam_admin_site.admin_view(views_admin.ManageView.as_view()),
        name='manage'
    ),
]
