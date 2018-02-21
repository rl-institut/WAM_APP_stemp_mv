
from django.views.generic import TemplateView

from stemp.forms import (
    HouseholdSelectForm, DistrictForm, HouseholdForm, ChoiceForm
)
from stemp.widgets import SelectWithDisabled
from stemp.models import District, Household


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


class SingleHouseholdView(TemplateView):
    template_name = 'stemp/single_household.html'

    def get_context_data(self, **kwargs):
        context = super(SingleHouseholdView, self).get_context_data(**kwargs)
        context['hh_select'] = HouseholdSelectForm()
        context['household_switch'] = ChoiceForm(
            'household_switch',
            'Wie möchtest du einen Haushalt auswählen?',
            [
                (0, {'label': 'Auswahl', 'disabled': True}),
                (1, 'Aus einer Liste wählen'),
                (2, 'Mittels Fragen'),
                (3, 'Von Hand erstellen')
            ],
            initial=0,
            submit_on_change=False,
            widget=SelectWithDisabled
        )
        context['hh_tree'] = ''
        context['hh_form'] = HouseholdForm()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
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