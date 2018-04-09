
from django.urls import path
from django.views.generic.base import TemplateView
from stemp.views import (
    SelectView, ResultView, ParameterView, ComparisonView, DemandView,
    TechnologyView, DemandSelectionView
)
from stemp.views_dynamic import HouseholdProfileView

app_name = 'stemp'

urlpatterns = [
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
    path('demand/<str:selection>/', DemandView.as_view(), name='demand'),
    path('technology/', TechnologyView.as_view(), name='technology'),
    path('parameter/', ParameterView.as_view(), name='parameter'),
    path('result/', ResultView.as_view(), name='result'),
    path('comparison/', ComparisonView.as_view(), name='comparison'),
    path(
        'demand/household_profile/',
        HouseholdProfileView.as_view(),
    ),
]
