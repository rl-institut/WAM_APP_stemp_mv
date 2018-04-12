
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from kopy.settings import SESSION_DATA
from stemp.tasks import add
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


class DemandSingleView(TemplateView):
    template_name = 'stemp/demand_single.html'
    is_district_hh = False

    def __init__(self, **kwargs):
        super(DemandSingleView, self).__init__(**kwargs)

    def get_context_data(self, hh_proposal=None):
        context = super(DemandSingleView, self).get_context_data()
        context['specific_form'] = HouseholdQuestionsForm()
        context['list_form'] = HouseholdSelectForm()
        context['new_form'] = hh_proposal
        return context

    def get(self, request, *args, **kwargs):
        # Test celery:
        result = add.delay(4, 4)
        print(result.ready())
        print(result.get(timeout=1))

        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        request.session.modified = True

        context = self.get_context_data()
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        hh_id = None
        if 'questions' in request.POST:
            hh_questions = HouseholdQuestionsForm(request.POST)
            if hh_questions.is_valid():
                proposal_form = hh_questions.hh_proposal()
                context = self.get_context_data(proposal_form)
                return self.render_to_response(context)
        elif 'new' in request.POST:
            hh_form = HouseholdForm(request.POST)
            if hh_form.is_valid():
                hh = hh_form.save()
                hh_id = hh.id
        elif 'list' in request.POST:
            hh = HouseholdSelectForm(request.POST)
            if hh.is_valid():
                hh_id = hh.cleaned_data['profile'].id

        if self.is_district_hh:
            session.district[str(hh_id)] = 1
            return redirect('stemp:demand_district')
        else:
            session.parameter = {
                'customer_index': hh_id,
                'customer_case': 'single'
            }
            return redirect('stemp:technology')


class DemandDistrictView(TemplateView):
    template_name = 'stemp/demand_district.html'

    def get_context_data(self, session):
        context = super(DemandDistrictView, self).get_context_data()
        context['district_form'] = DistrictListForm(session.district)
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        session = SESSION_DATA.get_session(request)

        context = self.get_context_data(session)
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
            context = self.get_context_data(session)
            return self.render_to_response(context)
        elif 'add_household' in request.POST:
            return redirect('stemp:demand_district_household')

    @check_session
    def post(self, request, session):
        if 'done' in request.POST:
            session.parameter = session.district
            return redirect('stemp:technology')
        else:
            return self.__change_district_list(request, session)


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
    def post(self, request):
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
