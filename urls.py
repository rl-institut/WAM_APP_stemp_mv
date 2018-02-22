
from django.conf.urls import url
from django.views.generic.base import TemplateView
from stemp.views import (
    SelectView, ResultView, HouseholdView, ParameterView,
    ComparisonView, SwitchLoadView, DemandView, TechnologyView
)

urlpatterns = [
    url(r'^home/$', TemplateView.as_view(template_name='stemp/homepage.html'), name='home'),
    url(r'^select/$', SelectView.as_view(), name='select'),
    url(r'^demand/$', DemandView.as_view(), name='demand'),
    url(r'^demand/switch_load/$', SwitchLoadView.as_view()),
    url(r'^demand/households/$', HouseholdView.as_view()),
    url(r'^technology/$', TechnologyView.as_view(), name='technology'),
    url(r'^parameter/$', ParameterView.as_view(), name='parameter'),
    url(r'^result/$', ResultView.as_view(), name='result'),
    url(r'^comparison/$', ComparisonView.as_view(), name='comparison'),
]
