
from os import path
from collections import namedtuple, OrderedDict
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from kopy.settings import SESSION_DATA, SqlAlchemySession
from kopy.bookkeeping import simulate_energysystem
from db_apps.oemof_results import store_results
from stemp.models import OEPScenario
from stemp.results import Results
from scenarios import create_energysystem

from .forms import (
    SaveSimulationForm, ComparisonForm, ChoiceForm, HouseholdForm,
    HouseholdSelectForm
)
from stemp.results import Comparison
from scenarios import get_scenario_config, get_scenario_input_values

BASIC_SCENARIO = path.join('scenarios', 'heat_scenario')

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
                Option('Manuell erstellen', 'new', '<img>')
            ]
        )
    ]
)


def check_session(func):
    def func_wrapper(self, request, *args):
        try:
            session = SESSION_DATA.get_session(request)
        except KeyError:
            return render(request, 'stemp/session_not_found.html')
        return func(self, request, session=session, *args)
    return func_wrapper


class SelectView(TemplateView):
    template_name = 'stemp/select.html'

    def __init__(self, **kwargs):
        super(SelectView, self).__init__(**kwargs)


class DemandView(TemplateView):
    template_name = 'stemp/demand.html'

    def __init__(self, **kwargs):
        super(DemandView, self).__init__(**kwargs)

    @staticmethod
    def __get_single_context(context, data):
        context['options']['structure'] = [demand_options['structure'][0]]
        selection = data.get('selection')
        if selection is None or selection == 'back':
            context['options']['selection'] = demand_options['selection']
        elif selection == 'list':
            context['options']['selection'] = [demand_options['selection'][0]]
            context['selection_form'] = HouseholdSelectForm()
        elif selection == 'questions':
            context['options']['selection'] = [demand_options['selection'][1]]
        elif selection == 'new':
            context['options']['selection'] = [demand_options['selection'][2]]
            context['selection_form'] = HouseholdForm()
        else:
            raise ValueError(
                'Unknown demand selection "' + str(selection) +
                '" for structure "single"')

    @staticmethod
    def __get_district_context(context, data):
        context['options']['structure'] = [demand_options['structure'][1]]

    def get_context_data(self, data, **kwargs):
        context = super(DemandView, self).get_context_data(**kwargs)
        context['options'] = OrderedDict()

        structure = data.get('structure')
        if structure is None or structure == 'back':
            # First choose between single and district:
            context['options']['structure'] = demand_options['structure']
        elif structure == 'single':
            self.__get_single_context(context, data)
        elif structure == 'district':
            self.__get_district_context(context, data)
        else:
            raise ValueError(
                'Unknown demand structure "' + str(structure) + '"')
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)

        # Set scenario in session
        SESSION_DATA.get_session(request).scenario = BASIC_SCENARIO

        data = request.GET
        context = self.get_context_data(data)
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        customer_dict = {}
        customer_dict['customer_index'] = 1  # FIXME: Hardcoded
        customer_dict['customer_case'] = 'district'
        # if int(request.POST['single_district_switch']) == 2:
        #     customer_dict['customer_index'] = 1  # FIXME: Hardcoded
        #     customer_dict['customer_case'] = 'district'
        # else:
        #     customer_dict['customer_index'] = request.POST['profile']
        #     customer_dict['customer_case'] = 'single'

        session.parameter = customer_dict
        return redirect('stemp:technology')


class TechnologyView(TemplateView):
    template_name = 'stemp/technology.html'

    def __init__(self, **kwargs):
        super(TechnologyView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(TechnologyView, self).get_context_data(**kwargs)
        choices = (
            ('bhkw', 'BHKW'),
            ('pv_wp', 'PV + Wärmepumpe'),
            ('oil', 'Ölheizung')
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
        technology = request.POST['technology']
        session.parameter['technology'] = technology
        if 'continue' in request.POST:
            # Load default parameters:
            oep_scenario = OEPScenario.select_scenario('heat_scenario')
            if oep_scenario is not None:
                session.parameter['input_parameters'] = oep_scenario['data']

            # Check if results already exist:
            result_id = session.check_for_result()
            if result_id is not None:
                session.load_result(result_id)
            else:
                session.import_scenario_module()
                energysystem = create_energysystem(
                    session.scenario_module,
                    **session.parameter
                )
                session.energysystem = energysystem
                result, param_result = simulate_energysystem(request)

                sa_session = SqlAlchemySession()
                store_results(sa_session, param_result, result)
                sa_session.close()

                session.result = Results(result, param_result)
                session.store_simulation()
            return redirect('stemp:result')
        else:
            return redirect('stemp:parameter')


class ParameterView(TemplateView):
    template_name = 'stemp/parameter.html'

    def __init__(self, **kwargs):
        super(ParameterView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(ParameterView, self).get_context_data(**kwargs)

        # Get data from OEP:
        oep_scenario = OEPScenario.select_scenario('heat_scenario')
        if oep_scenario is not None:
            context['scenario_input'] = get_scenario_input_values(
                oep_scenario['data'])

        return context

    @check_session
    def get(self, request, *args, **kwargs):
        scenario = kwargs['session'].scenario
        if scenario is None:
            raise KeyError('No scenario found')
        context = self.get_context_data(scenario=scenario)

        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        session.import_scenario_module()
        energysystem = create_energysystem(
            session.scenario_module,
            **session.parameter
        )
        session.energysystem = energysystem
        result, param_result = simulate_energysystem(request)
        session.result = Results(result, param_result)
        session.store_simulation()
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
