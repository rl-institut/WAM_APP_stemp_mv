
from django.views.generic import TemplateView

from stemp.forms import (
    HouseholdSelectForm, DistrictHouseholdsForm
)
from stemp.models import District, Household


class DistrictEditingView(TemplateView):
    template_name = 'stemp/demand_editing.html'

    def get_context_data(self, district_id, **kwargs):
        context = super(DistrictEditingView, self).get_context_data()
        context['district'] = DistrictHouseholdsForm(
            {
                'district': district_id,
                'households': [
                    (1, 2),
                    (2, 4)
                ]
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        district_id = request.GET.get('district', 1)
        context = self.get_context_data(district_id, **kwargs)
        return self.render_to_response(context)

    def post(self, request):
        district_id = request.POST.get('district', 1)
        context = self.get_context_data(district_id)
        return self.render_to_response(context)


class HouseholdProfileView(TemplateView):
    template_name = 'stemp/load_profile.html'

    def get_context_data(self, household=None):
        if household is None:
            return {}
        else:
            hh = Household.objects.get(id=household)
            hc = hh.as_highchart()
            context = {
                'load_graph': hc.render('load_graph')
            }
            return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(int(
            request.GET.get('choice', 1)))
        return self.render_to_response(context)


class SwitchLoadView(TemplateView):
    template_name = 'stemp/load_switch.html'

    def get_context_data(self, switch, **kwargs):
        context = super(SwitchLoadView, self).get_context_data(**kwargs)
        if switch == 0:
            context['is_graph'] = False
            context['load'] = HouseholdSelectForm()
        else:
            context['is_graph'] = True
            dist = District.objects.get(id=1)
            hc = dist.as_highchart()
            context['load'] = hc.render('load_graph')
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(int(
            request.GET.get('choice', 0)))
        return self.render_to_response(context)
