
from django.urls import path
from django.views.generic.base import TemplateView
from stemp.views import (
    SelectView, ResultView, ParameterView, DemandSingleView,
    DemandDistrictView, TechnologyView,
    DemandSelectionView
)
from stemp.views_dynamic import HouseholdProfileView, get_next_household_name

app_name = 'stemp'

urlpatterns = [
    path('', SelectView.as_view(), name='index'),
    path(
        'home/',
        TemplateView.as_view(template_name='stemp/homepage.html'),
        name='home'
    ),
    path('select/', SelectView.as_view(), name='select'),
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
        'demand/district/',
        DemandDistrictView.as_view(),
        name='demand_district'
    ),
    path('technology/', TechnologyView.as_view(), name='technology'),
    path('parameter/', ParameterView.as_view(), name='parameter'),
    path('result/', ResultView.as_view(), name='result'),
    path(
        'demand/household_profile/',
        HouseholdProfileView.as_view(),
    ),
    path(
        'ajax/get_next_household_name/',
        get_next_household_name,
        name='household_name'
    ),
]
