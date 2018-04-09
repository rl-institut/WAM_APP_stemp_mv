
from collections import namedtuple, OrderedDict
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from kopy.settings import SESSION_DATA
from stemp.bookkeeping import simulate_energysystem
from stemp.models import OEPScenario
from stemp.scenarios import create_energysystem

from .forms import (
    SaveSimulationForm, ComparisonForm, ChoiceForm, HouseholdForm,
    HouseholdSelectForm, DistrictListForm, HouseholdQuestionsForm,
    ParameterForm
)
from stemp.results import Comparison
from stemp.scenarios import get_scenario_config

Option = namedtuple('Option', ['label', 'value', 'image'])
demand_options = OrderedDict(
    [
        (
            'structure',
            [
                Option('Einzelhaushalt', 'single', '<img>'),
                Option('Quartier', 'district', '<img>')
            ]
        ),
        (
            'selection',
            [
                Option('Aus einer Liste wählen', 'list', '<img>'),
                Option('Per Fragen', 'questions', '<img>'),
            ]
        )
    ]
)


def check_session(func):
    def func_wrapper(self, request, *args, **kwargs):
        try:
            session = SESSION_DATA.get_session(request)
        except KeyError:
            return render(request, 'stemp/session_not_found.html')
        return func(self, request, session=session, *args, **kwargs)
    return func_wrapper


class SelectView(TemplateView):
    template_name = 'stemp/select.html'


class DemandSelectionView(TemplateView):
    template_name = 'stemp/demand_selection.html'


class DemandView(TemplateView):
    template_name = 'stemp/demand.html'

    def __init__(self, **kwargs):
        super(DemandView, self).__init__(**kwargs)

    @staticmethod
    def __build_hh_selection(context, structure, selection, hh_form=None):
        if selection is None or selection in ('add_household', 'back'):
            context['options']['selection'] = demand_options['selection']
        elif selection == 'list':
            context['options']['selection'] = [demand_options['selection'][0]]
            context['selection_form'] = HouseholdSelectForm()
            context['demand_submit_value'] = structure + '_list'
        elif selection == 'questions':
            context['options']['selection'] = [demand_options['selection'][1]]
            context['selection_form'] = HouseholdQuestionsForm()
            context['demand_submit_value'] = structure + '_questions'
        elif selection == 'new':
            context['options']['selection'] = [demand_options['selection'][1]]
            context['selection_form'] = hh_form
            context['demand_submit_value'] = structure + '_new'
        else:
            raise ValueError(
                'Unknown demand selection "' + str(selection) +
                '" for structure "' + structure + "'")

    def __get_single_context(self, context, data):
        context['options']['structure'] = [demand_options['structure'][0]]
        selection = data.get('selection')
        self.__build_hh_selection(
            context, 'single', selection, data.get('hh_proposal'))

    def __get_district_context(self, session, context, data):
        context['options']['structure'] = [demand_options['structure'][1]]
        selection = data.get('selection')
        if selection is None:
            context['selection_form'] = DistrictListForm(session.district)
            context['demand_submit_value'] = 'district_done'
            return
        self.__build_hh_selection(
            context, 'district', selection, data.get('hh_proposal'))
        return

    def get_context_data(self, session, data):
        context = super(DemandView, self).get_context_data()
        context['options'] = OrderedDict()

        structure = data.get('structure')
        if structure is None or structure == 'back':
            # First choose between single and district:
            context['options']['structure'] = demand_options['structure']
        elif structure == 'single':
            self.__get_single_context(context, data)
        elif structure == 'district':
            self.__get_district_context(session, context, data)
        else:
            raise ValueError(
                'Unknown demand structure "' + str(structure) + '"')
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        session = SESSION_DATA.get_session(request)

        data = request.GET
        context = self.get_context_data(session, data)
        return self.render_to_response(context)

    def __change_district_list(self, request, session):
        session.district = {
            hh: count
            for hh, count in request.POST.items()
            if hh not in (
                'csrfmiddlewaretoken',
                'trash',
                'add_household',
                'demand_submit'
            )
        }
        if 'trash' in request.POST:
            trash = request.POST['trash']
            del session.district[trash]
            data = {'structure': 'district'}
            context = self.get_context_data(session, data)
            return self.render_to_response(context)
        elif 'add_household' in request.POST:
            data = {
                'structure': 'district',
                'selection': 'add_household',
            }
            context = self.get_context_data(session, data)
            return self.render_to_response(context)

    @check_session
    def post(self, request, session, selection):
        if 'done' not in request.POST:
            return self.__change_district_list(request, session)
        submit = request.POST.get('demand_submit')
        if submit is None:
            raise ValueError('Invalid demand post!')
        if submit in ('single_questions', 'district_questions'):
            hh_questions = HouseholdQuestionsForm(request.POST)
            if hh_questions.is_valid():  # TODO: If not valid...
                data = {
                    'structure': request.POST['demand_submit'].split('_')[0],
                    'selection': 'new',
                    'hh_proposal': hh_questions.hh_proposal()
                }
                context = self.get_context_data(session, data)
                return self.render_to_response(context)
        if submit in ('single_new', 'district_new'):
            hh_form = HouseholdForm(request.POST)
            if hh_form.is_valid():  # TODO: If not valid...
                hh = hh_form.save()
                if submit.split('_')[0] == 'single':
                    session.parameter = {
                        'customer_index': hh.id,
                        'customer_case': 'single'
                    }
                    return redirect('stemp:technology')
                elif submit.split('_')[0] == 'district':
                    session.district[str(hh.id)] = 1
                    data = {'structure': 'district'}
                    context = self.get_context_data(session, data)
                    return self.render_to_response(context)
                else:
                    raise ValueError('Unknown submit key "' + submit)
        if submit in ('single_list', 'district_list'):
            hh = HouseholdSelectForm(request.POST)
            if hh.is_valid():  # TODO: If not valid...
                hh_id = hh.cleaned_data['profile'].id
            if submit.split('_')[0] == 'single':
                session.parameter = {
                    'customer_index': hh_id,
                    'customer_case': 'single'
                }
                return redirect('stemp:technology')
            elif submit.split('_')[0] == 'district':
                session.district[str(hh_id)] = 1
                data = {'structure': 'district'}
                context = self.get_context_data(session, data)
                return self.render_to_response(context)
            else:
                raise ValueError('Unknown submit key "' + submit)
        else:
            # TODO: Correct parameter input of district:
            session.parameter = session.district
            return redirect('stemp:technology')


class TechnologyView(TemplateView):
    template_name = 'stemp/technology.html'

    def __init__(self, **kwargs):
        super(TechnologyView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(TechnologyView, self).get_context_data(**kwargs)
        choices = (
            ('bhkw_scenario', 'BHKW'),
            ('pv_heatpump_scenario', 'PV + Wärmepumpe'),
            ('oil_scenario', 'Ölheizung')
        )
        context['technology'] = ChoiceForm(
            'technology',
            'Technology',
            choices=choices,
            submit_on_change=False
        )
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        scenario = request.POST['technology']
        session.scenario = scenario
        session.import_scenario_module()
        if 'continue' in request.POST:
            # Load default parameters:
            oep_scenario = OEPScenario.get_scenario_parameters(scenario)
            parameter_form = ParameterForm(oep_scenario)
            session.parameter.update(parameter_form.prepared_data())

            # Check if results already exist:
            result_id = session.check_for_result()
            if result_id is not None:
                session.load_result(result_id)
            else:
                energysystem = create_energysystem(
                    session.scenario_module,
                    **session.parameter
                )
                session.energysystem = energysystem
                simulate_energysystem(session)
            return redirect('stemp:result')
        else:
            return redirect('stemp:parameter')


class ParameterView(TemplateView):
    template_name = 'stemp/parameter.html'

    def __init__(self, **kwargs):
        super(ParameterView, self).__init__(**kwargs)

    @staticmethod
    def get_scenario_parameters(session, data=None):
        scenario = session.scenario
        if scenario is None:
            raise KeyError('No scenario found')

        # Get data from OEP:
        oep_scenario = OEPScenario.get_scenario_parameters(scenario)
        if oep_scenario is not None:
            return ParameterForm(oep_scenario, data)
        else:
            return {}

    @check_session
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['parameter_form'] = self.get_scenario_parameters(
            kwargs['session'])
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        parameter_form = self.get_scenario_parameters(session, request.POST)
        if not parameter_form.is_valid():
            raise ValueError('Invalid scenario parameters')
        session.parameter.update(parameter_form.prepared_data())
        session.import_scenario_module()
        energysystem = create_energysystem(
            session.scenario_module,
            **session.parameter,
        )
        session.energysystem = energysystem
        simulate_energysystem(session)
        return redirect('stemp:result')


class ResultView(TemplateView):
    template_name = 'stemp/result.html'

    def __init__(self, **kwargs):
        super(ResultView, self).__init__(**kwargs)

    def get_context_data(self, result, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)
        context['save'] = SaveSimulationForm()
        context['visualizations'] = result.get_visualizations()
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        session = kwargs['session']
        result_config = get_scenario_config(session.scenario).get('results')
        session.result.create_visualization_data(result_config)
        context = self.get_context_data(session.result)
        return self.render_to_response(context)

    @check_session
    def post(self, request, *args, **kwargs):
        if 'save' in request.POST:
            simulation_name = request.POST['simulation_name']
            try:
                session = SESSION_DATA.get_session(request)
            except KeyError:
                return render(request, 'stemp/session_not_found.html')
            session.store_simulation(simulation_name)
            return self.render_to_response({})


class ComparisonView(TemplateView):
    template_name = 'stemp/comparison.html'

    def __init__(self, **kwargs):
        super(ComparisonView, self).__init__(**kwargs)

    def get_context_data(self, sim_ids=None, **kwargs):
        context = super(ComparisonView, self).get_context_data(**kwargs)
        if sim_ids is None:
            context['comparison'] = ComparisonForm()
        else:
            comparison = Comparison(sim_ids)
            context['visualizations'] = comparison.get_visualizations()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request):
        sim_ids = request.POST.getlist('comparison')
        context = self.get_context_data(sim_ids)
        return self.render_to_response(context)
