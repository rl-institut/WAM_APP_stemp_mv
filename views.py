
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django. forms import MultipleChoiceField

from wam.settings import SESSION_DATA
from stemp.app_settings import LABELS
from stemp.user_data import DemandType
from stemp.oep_models import OEPScenario
from stemp import results
from stemp import models
from stemp import forms
from stemp.widgets import TechnologyWidget


def check_session(func):
    def func_wrapper(self, request, *args, **kwargs):
        try:
            session = SESSION_DATA.get_session(request)
        except KeyError:
            return render(request, 'stemp/session_not_found.html')
        return func(self, request, session=session, *args, **kwargs)
    return func_wrapper


class IndexView(TemplateView):
    template_name = 'stemp/index.html'


class DemandSelectionView(TemplateView):
    template_name = 'stemp/demand_selection.html'


class DemandSingleView(TemplateView):
    template_name = 'stemp/demand_single.html'
    is_district_hh = False

    def __init__(self, **kwargs):
        super(DemandSingleView, self).__init__(**kwargs)

    def get_labels(self):
        if self.is_district_hh:
            labels = LABELS['demand_single']['District']
        else:
            labels = LABELS['demand_single']['Single']
        return labels

    def get_context_data(self, hh_proposal=None):
        context = super(DemandSingleView, self).get_context_data()
        context['specific_form'] = forms.HouseholdQuestionsForm()
        context['list_form'] = forms.HouseholdSelectForm()
        context['new_form'] = hh_proposal
        context['labels'] = self.get_labels()
        context['is_district_hh'] = self.is_district_hh
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        request.session.modified = True
        session = SESSION_DATA.get_session(request)
        session.demand_type = (
            DemandType.District if self.is_district_hh else DemandType.Single)

        context = self.get_context_data()
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        hh_id = None
        if 'questions' in request.POST:
            hh_questions = forms.HouseholdQuestionsForm(request.POST)
            if hh_questions.is_valid():
                proposal_form = hh_questions.hh_proposal()
                context = self.get_context_data(proposal_form)
                return self.render_to_response(context)
        elif 'new' in request.POST:
            hh_id = models.Household.objects.get(name=request.POST['name']).id
        elif 'new_save' in request.POST:
            hh_form = forms.HouseholdForm(request.POST)
            if hh_form.is_valid():
                hh = hh_form.save()
                question = models.Question.objects.get(
                    pk=request.POST['question_id'])
                qh = models.QuestionHousehold(question=question, household=hh)
                qh.save()
                hh_id = hh.id
        elif 'list' in request.POST:
            hh = forms.HouseholdSelectForm(request.POST)
            if hh.is_valid():
                hh_id = hh.cleaned_data['profile'].id

        if self.is_district_hh:
            session.current_district[str(hh_id)] = 1
            return redirect('stemp:demand_district')
        else:
            session.demand_id = hh_id
            return redirect('stemp:technology')


class DemandDistrictView(TemplateView):
    template_name = 'stemp/demand_district.html'
    new_district = True

    def get_context_data(self, session):
        context = super(DemandDistrictView, self).get_context_data()
        if session.demand_id is not None:
            context['demand_name'] = models.District.objects.get(
                pk=session.demand_id).name
        context['district_status'] = session.get_district_status().value
        context['district_load_form'] = forms.DistrictSelectForm()
        context['district_form'] = forms.DistrictListForm(
            session.current_district)
        context['labels'] = LABELS['demand_district']
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        session = SESSION_DATA.get_session(request)
        if self.new_district:
            session.reset_demand()
        session.demand_type = DemandType.District

        context = self.get_context_data(session)
        return self.render_to_response(context)

    def __change_district_list(self, request, session):
        session.current_district = {
            hh: count
            for hh, count in request.POST.items()
            if hh not in (
                'csrfmiddlewaretoken',
                'trash',
                'add_household',
                'demand_submit',
                'district_name',
                'district_status'
            )
        }
        if 'trash' in request.POST:
            trash = request.POST['trash']
            del session.current_district[trash]
            context = self.get_context_data(session)
            return self.render_to_response(context)
        elif 'add_household' in request.POST:
            return redirect('stemp:demand_district_household')

    @check_session
    def post(self, request, session):
        if 'add_household' in request.POST:
            return self.__change_district_list(request, session)
        elif 'load_district' in request.POST:
            session.demand_id = request.POST['district']
            district = models.District.objects.get(pk=request.POST['district'])
            session.current_district = {
                str(dh.household.id): dh.amount
                for dh in district.districthouseholds_set.all()
            }
            context = self.get_context_data(session)
            return self.render_to_response(context)
        else:
            if request.POST['district_status'] in ('new', 'changed'):
                if request.POST['district_name'] == '':
                    # Save changes to district:
                    district = models.District.objects.get(
                        pk=session.demand_id)
                    district.districthouseholds_set.all().delete()
                    district.add_households(session.current_district)
                else:
                    # Save district as new district:
                    district = models.District(
                        name=request.POST['district_name'])
                    district.save()
                    district.add_households(session.current_district)
                    session.demand_id = district.id

            return redirect('stemp:technology')


class TechnologyView(TemplateView):
    template_name = 'stemp/technology.html'

    def __init__(self, **kwargs):
        super(TechnologyView, self).__init__(**kwargs)

    def get_context_data(self, session, **kwargs):
        context = super(TechnologyView, self).get_context_data(**kwargs)
        choices = (
            ('bhkw_scenario', 'BHKW'),
            ('pv_heatpump_scenario', 'PV + Wärmepumpe'),
            ('oil_scenario', 'Ölheizung')
        )
        context['technology'] = forms.ChoiceForm(
            'technology',
            'Technology',
            choices=choices,
            field=MultipleChoiceField,
            widget=TechnologyWidget,
            submit_on_change=False
        )
        context['demand_type'] = str(session.demand_type.value)
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = session.get_demand_name()
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs['session'])
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        scenarios = request.POST.getlist('technology')
        session.init_scenarios(scenarios)
        if 'continue' in request.POST:
            for scenario in session.scenarios:
                # Load default parameters:
                parameters = OEPScenario.get_scenario_parameters(scenario.name)
                parameter_form = forms.ParameterForm(
                    [(scenario.name, parameters)])
                scenario.parameter.update(parameter_form.prepared_data())
                scenario.load_or_simulate()
            return redirect('stemp:result')
        else:
            return redirect('stemp:parameter')


class ParameterView(TemplateView):
    template_name = 'stemp/parameter.html'

    def __init__(self, **kwargs):
        super(ParameterView, self).__init__(**kwargs)

    @staticmethod
    def get_scenario_parameters(session, data=None):
        scenarios = session.scenarios
        if not scenarios:
            raise KeyError('No scenarios found')

        # Get data from OEP:
        parameters = []
        # TODO: Hard-coded to avoid OEP-Error 500
        parameters = [
            (
                'oil',
                {
                    'General': {
                        'WACC': {
                            'label': 'WACC',
                            'parameter_type': 'costs',
                            'value_type': 'float',
                            'value': 7.1,
                            'unit': '%',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 20
                        },
                        'Ölpreis': {
                            'label': 'Ölpreis',
                            'parameter_type': 'costs',
                            'value_type': 'float',
                            'value': 1.3,
                            'unit': '€/liter',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 10
                        }
                    },
                    'Ölheizung': {
                        'Effizienz': {
                            'label': 'Effizienz',
                            'parameter_type': 'technologies',
                            'value_type': 'float',
                            'value': 0.7,
                            'unit': 'kW_e/kW_th',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 1
                        },
                        'Investment': {
                            'label': 'Investmentkosten',
                            'parameter_type': 'costs',
                            'value_type': 'integer',
                            'value': 200,
                            'unit': '€/kW',
                            'min': 0,
                            'max': 1000
                        }
                    }
                }
            ),
            (
                'bhkw',
                {
                    'General': {
                        'WACC': {
                            'label': 'WACC',
                            'parameter_type': 'costs',
                            'value_type': 'float',
                            'value': 7.1,
                            'unit': '%',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 20
                        }
                    },
                    'BHKW': {
                        'WärmeEffizienz': {
                            'label': 'Wärme-Effizienz',
                            'parameter_type': 'technologies',
                            'value_type': 'float',
                            'value': 0.3,
                            'unit': 'kW_e/kW_th',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 1
                        },
                        'StromEffizienz': {
                            'label': 'Strom-Effizienz',
                            'parameter_type': 'technologies',
                            'value_type': 'float',
                            'value': 0.6,
                            'unit': 'kW_e/kW_th',
                            'step_size': 0.1,
                            'min': 0,
                            'max': 1
                        },
                        'Investment': {
                            'label': 'Investment',
                            'parameter_type': 'costs',
                            'value_type': 'integer',
                            'value': 200,
                            'unit': '€/kW',
                            'min': 0,
                            'max': 1000
                        }
                    }
                }
            )
        ]
        for scenario in scenarios:
            parameters.append(
                (
                    scenario.name,
                    OEPScenario.get_scenario_parameters(scenario.name)
                )
            )
        return forms.ParameterForm(parameters, data)

    def get_context_data(self, session, **kwargs):
        context = super(ParameterView, self).get_context_data(**kwargs)
        context['parameter_form'] = self.get_scenario_parameters(session)
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = session.get_demand_name()
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs['session'])
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        parameter_form = self.get_scenario_parameters(session, request.POST)
        if not parameter_form.is_valid():
            raise ValueError('Invalid scenario parameters')
        for scenario in session.scenarios:
            scenario.parameter.update(
                parameter_form.prepared_data(scenario.name))
            scenario.load_or_simulate()
        return redirect('stemp:result')


class ResultView(TemplateView):
    template_name = 'stemp/result.html'

    def __init__(self, **kwargs):
        super(ResultView, self).__init__(**kwargs)

    def get_context_data(self, session, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)
        context['save'] = forms.SaveSimulationForm()
        visualization = results.ResultAnalysisVisualization(session.scenarios)
        context['visualizations'] = [
            visualization.visualize('invest'),
            visualization.visualize('invest_detail')
        ]
        return context

    @check_session
    def get(self, request, *args, **kwargs):
        session = kwargs['session']
        context = self.get_context_data(session)
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
