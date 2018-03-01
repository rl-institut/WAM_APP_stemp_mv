
from collections import namedtuple
from django.views.generic import TemplateView

from stemp.forms import (
    HouseholdSelectForm, HouseholdForm, DistrictSelectForm, DistrictForm,
    DistrictHouseholdsForm
)
from stemp.models import District, Household

Option = namedtuple('Option', ['value', 'name', 'image'])


class OptionSelectionView(TemplateView):
    template_name = 'includes/option_selection/option_selection.html'
    options = None
    option_url = None
    selection_url = None

    def get_context_data(self, option, **kwargs):
        context = super(OptionSelectionView, self).get_context_data(**kwargs)
        context['option_url'] = self.option_url
        context['selection_url'] = self.selection_url
        context['current_option'] = option
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            request.GET.get('current_option', ''))
        return self.render_to_response(context)

    def post(self, request):
        if 'current_option' in request.POST:
            if request.POST['current_option'] != '':
                context = self.get_context_data(option=None)
                return self.render_to_response(context)
            else:
                for i, option in enumerate(self.options):
                    if option in request.POST:
                        context = self.get_context_data(option=i)
                        return self.render_to_response(context)


class SingleHouseholdView(OptionSelectionView):
    options = ('hh_option_list', 'hh_option_questions', 'hh_option_manual')
    option_url = 'single_household_option'
    selection_url = 'single_household_selection'


class DistrictView(OptionSelectionView):
    options = ('district_list', 'district_new')
    option_url = 'district_option'
    selection_url = 'district_selection'


class OptionView(TemplateView):
    template_name = 'includes/option_selection/option.html'
    ajax_post = True
    option_name = 'current_option'
    option_url = None
    options = None

    def get_context_data(self, current_option, **kwargs):
        context = super(OptionView, self).get_context_data(
            **kwargs)
        context['option_name'] = self.option_name
        context['ajax_post'] = self.ajax_post
        context['current_option'] = current_option
        context['post_to_url'] = self.option_url
        context['options'] = self.options
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            request.GET.get(self.option_name, ''))
        return self.render_to_response(context)


class DemandStructureView(OptionView):
    option_url = ''
    option_name = 'current_structure'
    ajax_post = False
    options = [
        Option('Einzelner Haushalt', 'btn_single', '<img>'),
        Option('Quartier', 'btn_district', '<img>'),
    ]


class SingleHouseholdOptionView(OptionView):
    option_url = 'single_household/'
    options = [
        Option('Aus Liste wählen', 'hh_option_list', '<img>'),
        Option('Mittels Fragen', 'hh_option_questions', '<img>'),
        Option('Manuell erstellen', 'hh_option_manual', '<img>')
    ]


class DistrictOptionView(OptionView):
    option_url = 'district/'
    options = [
        Option('Aus Liste wählen', 'district_list', '<img>'),
        Option('Neues Quartier', 'district_new', '<img>'),
    ]


class SelectionView(TemplateView):
    template_name = 'includes/option_selection/selection.html'
    selection_url = None
    selection_forms = None
    selection_name = None

    def get_context_data(self, option, **kwargs):
        context = super(SelectionView, self).get_context_data(
            **kwargs)
        context['post_to_url'] = self.selection_url
        context['form'] = self.selection_forms[option]()
        context['value'] = 'Weiter'
        context['name'] = self.selection_name
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(
            option=int(request.GET.get('current_option', 0)))
        return self.render_to_response(context)


class SingleHouseholdSelectionView(SelectionView):
    selection_url = 'single_household/'
    selection_forms = (HouseholdSelectForm, None, HouseholdForm)
    selection_name = 'household_selected'


class DistrictSelectionView(SelectionView):
    selection_url = 'district/'
    selection_forms = (DistrictSelectForm, DistrictForm)
    selection_name = 'district_selected'


class DistrictEditingView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(DistrictEditingView, self).get_context_data()
        context['test'] = DistrictHouseholdsForm(
            {
                'district': 1,
                'households': [
                    (1, 2),
                    (2, 4)
                ]
            }
        )


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
