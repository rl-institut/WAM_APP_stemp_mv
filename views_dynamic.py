
from django.views.generic import TemplateView

from stemp.forms import (
    HouseholdSelectForm, HouseholdForm
)
from stemp.models import District, Household


class DemandStructureView(TemplateView):
    template_name = 'stemp/demand/demand_structure.html'

    def get_context_data(self, current_structure, **kwargs):
        context = super(DemandStructureView, self).get_context_data(**kwargs)
        context['current_structure'] = current_structure
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            request.GET.get('current_structure', ""))
        return self.render_to_response(context)


class SingleHouseholdView(TemplateView):
    template_name = 'stemp/demand/single_household.html'

    def get_context_data(self, option, **kwargs):
        context = super(SingleHouseholdView, self).get_context_data(**kwargs)
        context['current_option'] = option
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            request.GET.get('current_option', ""))
        return self.render_to_response(context)

    def post(self, request):
        if "current_option" in request.POST:
            if request.POST["current_option"] != "":
                context = self.get_context_data(option=None)
                return self.render_to_response(context)
            else:
                if "hh_option_list" in request.POST:
                    context = self.get_context_data(option=0)
                    return self.render_to_response(context)
                elif "hh_option_questions" in request.POST:
                    context = self.get_context_data(option=1)
                    return self.render_to_response(context)
                elif "hh_option_manual" in request.POST:
                    context = self.get_context_data(option=2)
                    return self.render_to_response(context)


class SingleHouseholdOptionView(TemplateView):
    template_name = 'stemp/demand/single_household_option.html'

    def get_context_data(self, current_option, **kwargs):
        context = super(SingleHouseholdOptionView, self).get_context_data(
            **kwargs)
        context['current_option'] = current_option
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            request.GET.get('current_option', ""))
        return self.render_to_response(context)


class SingleHouseholdSelectionView(TemplateView):
    template_name = 'stemp/demand/single_household_selection.html'

    def get_context_data(self, option, **kwargs):
        context = super(SingleHouseholdSelectionView, self).get_context_data(
            **kwargs)
        hh_forms = (HouseholdSelectForm, None, HouseholdForm)
        context['hh_form'] = hh_forms[option]()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            option=int(request.GET.get('current_option', 0)))
        return self.render_to_response(context)


class DistrictView(TemplateView):
    template_name = 'stemp/district.html'


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
