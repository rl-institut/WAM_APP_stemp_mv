
from django.urls import path, register_converter
import cursive_re

from wam.admin import wam_admin_site
from meta import models
from meta.views import AppListView, AssumptionsView
from stemp import views
from stemp import views_dynamic
from stemp import views_admin


def get_list_regex():
    number = cursive_re.one_or_more(
        cursive_re.any_of(cursive_re.in_range('0', '9')))
    regex = cursive_re.alternative(
        number +
        cursive_re.zero_or_more(cursive_re.text(',') + number)
    )
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
    path('', views.IndexView.as_view(), name='index'),
    path('sources/', AppListView.as_view(
        model=models.Source, app_name='stemp'), name='sources'),
    path('assumptions/', AssumptionsView.as_view(
        app_name='stemp'), name='assumptions'),
    path(
        'demand_selection/',
        views.DemandSelectionView.as_view(),
        name='demand_selection'
    ),
    path(
        'demand/single/',
        views.DemandSingleView.as_view(),
        name='demand_single'
    ),
    path(
        'demand/district/household/',
        views.DemandSingleView.as_view(is_district_hh=True),
        name='demand_district_household'
    ),
    path(
        'demand/district/empty',
        views.DemandDistrictView.as_view(),
        name='demand_district_empty',
    ),
    path(
        'demand/district/',
        views.DemandDistrictView.as_view(new_district=False),
        name='demand_district',
    ),
    path('technology/', views.TechnologyView.as_view(), name='technology'),
    path('parameter/', views.ParameterView.as_view(), name='parameter'),
    path('summary/', views.SummaryView.as_view(), name='summary'),
    path('result/', views.ResultView.as_view(), name='result'),
    path('pending/', views.PendingView.as_view(), name='pending'),
    path(
        'result/<list:results>',
        views.ResultView.as_view(),
        name='result_list'
    ),
    path(
        'energy_links/',
        views.EnergyLinksView.as_view(),
        name='energy_links'
    ),
    path(
        'ajax/get_next_household_name/',
        views_dynamic.get_next_household_name,
        name='household_name'
    ),
    path(
        'ajax/get_heat_demand/',
        views_dynamic.get_heat_demand,
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
    path(
        'ajax/check_pending/',
        views_dynamic.check_pending,
    ),
    path(
        'ajax/get_household_summary/',
        views_dynamic.get_household_summary,
    ),
]

admin_url_patterns = [
    path(
        'stemp/manage',
        wam_admin_site.admin_view(views_admin.ManageView.as_view()),
        name='manage_stemp'
    ),
]
