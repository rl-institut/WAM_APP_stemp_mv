
from django.conf.urls import url
from stemp.views import (
    SelectView, ResultView, ParameterView, ComparisonView, DemandView,
    TechnologyView
)
from stemp.views_dynamic import (
    DemandStructureView, SingleHouseholdView, SingleHouseholdOptionView,
    SingleHouseholdSelectionView, HouseholdProfileView, DistrictView
)

urlpatterns = [
    url(r'^select/$', SelectView.as_view(), name='select'),
    url(r'^demand/$', DemandView.as_view(), name='demand'),
    url(r'^technology/$', TechnologyView.as_view(), name='technology'),
    url(r'^parameter/$', ParameterView.as_view(), name='parameter'),
    url(r'^result/$', ResultView.as_view(), name='result'),
    url(r'^comparison/$', ComparisonView.as_view(), name='comparison'),
    url(
        r'^demand/structure/$',
        DemandStructureView.as_view(),
    ),
    url(
        r'^demand/district/$',
        DistrictView.as_view(),
    ),
    url(
        r'^demand/single_household/$',
        SingleHouseholdView.as_view(),
    ),
    url(
        r'^demand/single_household_option/$',
        SingleHouseholdOptionView.as_view(),
    ),
    url(
        r'^demand/single_household_selection/$',
        SingleHouseholdSelectionView.as_view(),
    ),
    url(
        r'^demand/household_profile/$',
        HouseholdProfileView.as_view(),
    ),
]
