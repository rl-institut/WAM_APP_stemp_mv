
from os import path
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from kopy.settings import SESSION_DATA
from kopy.bookkeeping import simulate_energysystem
from scenarios import create_energysystem

from .forms import (
    SaveSimulationForm, ComparisonForm, ChoiceForm
)
from stemp.results import Comparison
from scenarios import get_scenario_config, get_scenario_input_values

BASIC_SCENARIO = path.join('scenarios', 'heat_scenario')


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

    @staticmethod
    def post(request):
        if 'new' in request.POST:
            # Start session (if no session yet):
            SESSION_DATA.start_session(request)

            # Set scenario in session
            SESSION_DATA.get_session(request).scenario = BASIC_SCENARIO

            return redirect('stemp:demand')
        else:
            return redirect('stemp:comparison')


class DemandView(TemplateView):
    template_name = 'stemp/demand.html'

    def __init__(self, **kwargs):
        super(DemandView, self).__init__(**kwargs)

    def get_context_data(self, structure, **kwargs):
        context = super(DemandView, self).get_context_data(**kwargs)
        context['current_structure'] = structure
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request.GET.get("structure", None))
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        if "current_structure" in request.POST:
            if request.POST["current_structure"] != "":
                context = self.get_context_data(structure=None)
                return self.render_to_response(context)
            else:
                if "btn_single" in request.POST:
                    context = self.get_context_data(structure=0)
                    return self.render_to_response(context)
                elif "btn_district" in request.POST:
                    context = self.get_context_data(structure=1)
                    return self.render_to_response(context)
        else:
            customer_dict = {}
            if int(request.POST['single_district_switch']) == 2:
                customer_dict['customer_index'] = 1  # FIXME: Hardcoded
                customer_dict['customer_case'] = 'district'
            else:
                customer_dict['customer_index'] = request.POST['profile']
                customer_dict['customer_case'] = 'single'

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
            session.import_scenario_module()
            energysystem = create_energysystem(
                session.scenario_module,
                **session.parameter
            )
            session.energysystem = energysystem
            simulate_energysystem(request)
            return redirect('stemp:result')
        else:
            return redirect('stemp:parameter')


class ParameterView(TemplateView):
    template_name = 'stemp/parameter.html'

    def __init__(self, **kwargs):
        super(ParameterView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(ParameterView, self).get_context_data(**kwargs)
        context['scenario_input'] = get_scenario_input_values('heat_scenario')
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
        simulate_energysystem(request)
        return redirect('stemp:result')


class ResultView(TemplateView):
    template_name = 'stemp/result.html'

    def __init__(self, **kwargs):
        super(ResultView, self).__init__(**kwargs)

    def get_context_data(self, result, result_config, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)

        context['save'] = SaveSimulationForm()

        result.create_visualization_data(result_config)
        context['visualizations'] = result.get_visualizations()
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        scenario = kwargs['session'].scenario
        result_config = get_scenario_config(scenario).get('results')
        result = kwargs['session'].result

        context = self.get_context_data(result, result_config)
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
