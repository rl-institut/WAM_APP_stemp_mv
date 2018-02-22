
from django.conf.urls import url
from django.views.generic.base import TemplateView
from stemp.views import (
    SelectView, ResultView, ParameterView, ComparisonView, DemandView,
    TechnologyView
)
from stemp.views_dynamic import SingleHouseholdView, HouseholdProfileView

urlpatterns = [
    url(r'^home/$', TemplateView.as_view(template_name='stemp/homepage.html'), name='home'),
    url(r'^select/$', SelectView.as_view(), name='select'),
    url(r'^demand/$', DemandView.as_view(), name='demand'),
    url(r'^technology/$', TechnologyView.as_view(), name='technology'),
    url(r'^parameter/$', ParameterView.as_view(), name='parameter'),
    url(r'^result/$', ResultView.as_view(), name='result'),
    url(r'^comparison/$', ComparisonView.as_view(), name='comparison'),
    url(
        r'^demand/single_household/$',
        SingleHouseholdView.as_view(),
    ),
    url(
        r'^demand/household_profile/$',
        HouseholdProfileView.as_view(),
    ),
]
