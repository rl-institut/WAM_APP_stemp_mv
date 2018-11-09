
from django.urls import path
from stemp.views import (
    IndexView, ResultView, ParameterView, DemandSingleView,
    DemandDistrictView, TechnologyView,
    DemandSelectionView
)
from stemp import views_dynamic

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
    path('result/', ResultView.as_view(), name='result'),
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
