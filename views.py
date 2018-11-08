
import pandas
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from wam.settings import SESSION_DATA
from stemp import app_settings
from stemp.user_data import DemandType
from stemp.oep_models import OEPScenario
from stemp import results, models, forms, visualizations


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
            labels = app_settings.LABELS['demand_single']['District']
        else:
            labels = app_settings.LABELS['demand_single']['Single']
        return labels

    def get_context_data(self):
        context = super(DemandSingleView, self).get_context_data()
        context['household_form'] = forms.HouseholdForm()
        context['list_form'] = forms.HouseholdSelectForm()
        context['labels'] = self.get_labels()
        context['is_district_hh'] = self.is_district_hh
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request)
        session = SESSION_DATA.get_session(request)
        session.demand_type = (
            DemandType.District if self.is_district_hh else DemandType.Single)

        context = self.get_context_data()
        return self.render_to_response(context)

    @check_session
    def post(self, request, session):
        hh_id = None
        form = request.POST['form']
        if form == 'house':
            hh_form = forms.HouseholdForm(request.POST)
            if hh_form.is_valid():
                hh = hh_form.save()
                hh_id = hh.id
            else:
                context = self.get_context_data()
                context['household_form'] = hh_form
                return self.render_to_response(context)
        elif form == 'list':
            hh = forms.HouseholdSelectForm(request.POST)
            if hh.is_valid():
                hh_id = hh.cleaned_data['profile'].id
        else:
            raise ValueError(f'Unknown value "{form}" detected')

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
        context['labels'] = app_settings.LABELS['demand_district']
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
        if 'add_household' in request.POST or 'trash' in request.POST:
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
            (sc, params['LABELS']['name'])
            for sc, params in app_settings.SCENARIO_PARAMETERS.items()
        )
        technology_information = {
            sc: {
                'image': params['LABELS']['image'],
                'description': params['LABELS']['description']
            }
            for sc, params in app_settings.SCENARIO_PARAMETERS.items()
            if 'description' in params['LABELS']
        }

        # Add warning if radiator is chosen in combination with heatpump:
        demand = session.get_demand()
        if demand.contains_radiator():
            technology_information['pv_heatpump']['warning'] = (
                app_settings.SCENARIO_PARAMETERS[
                    'pv_heatpump']['LABELS']['warning']
            )

        context['technology'] = forms.TechnologyForm(
            'technology',
            'Technology',
            choices=choices,
            information=technology_information
        )
        context['demand_type'] = session.demand_type.suffix()
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = demand.name
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
                parameters = OEPScenario.get_scenario_parameters(
                    scenario.name, session.demand_type)
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
        for scenario in scenarios:
            scenario_parameters = OEPScenario.get_scenario_parameters(
                scenario.name, session.demand_type)
            # Load additional dynamic parameters from module:
            scenario.module.add_dynamic_parameters(
                scenario, scenario_parameters)
            parameters.append(
                (
                    scenario.name,
                    scenario_parameters
                )
            )
        return forms.ParameterForm(parameters, data)

    def get_context_data(self, session, **kwargs):
        context = super(ParameterView, self).get_context_data(**kwargs)
        context['parameter_form'] = self.get_scenario_parameters(session)
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = session.get_demand().name
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
            visualization.visualize(vis)
            for vis in app_settings.ACTIVATED_VISUALIZATIONS
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


class HighchartTestView(TemplateView):
    template_name = 'stemp/highchart_test.html'

    def get_context_data(self, **kwargs):
        context = {'visualizations': []}

        context['visualizations'].append(
            visualizations.HCCosts(
                pandas.DataFrame(
                    {
                        'Investitionskosten': [5.2, 5, 3.2, 2.8],
                        'Wartungskosten': [1, 1, .9, 1],
                        'Brennstoffkosten': [5.4, 4.9, 3.8, 3.1]
                    },
                    index=[
                        'BHKW',
                        'PV + Wärmepumpe',
                        'Ölheizung',
                        'Gasheizung'
                    ]
                )
            ).render(
                "container-costs",
                {'style': 'min-width: 310px; height: 400px; margin: 0 auto'}
            )
        )

        emissions = visualizations.HCEmissions(
            pandas.Series(
                [140, 140, 280, 220],
                index=['BHKW', 'PV + Wärmepumpe', 'Ölheizung', 'Gasheizung'],
                name='CO2-Emissionen'
            )
        )
        emissions.dict['series'][0].update(
            {
                'dataLabels': {
                    'enabled': True,
                    'color': '#FFFFFF',
                    'format': '{point.y:.1f}',
                    'style': {
                        'fontSize': '13px',
                        'fontFamily': 'Verdana, sans-serif'
                    }
                }
            }
        )
        context['visualizations'].append(
            emissions.render(
                "container-emissions",
                {'style': 'min-width: 310px; height: 400px; margin: 0 auto'}
            )
        )

        context['visualizations'].append(
            visualizations.HCScatter(
                pandas.DataFrame(
                    {
                        'BHKW': [11.6, 140],
                        'PV + Wärmepumpe': [10.9, 140],
                        'Ölheizung': [7.9, 280],
                        'Gasheizung': [6.9, 220]
                    },
                    index=['Kosten (cent/kWh)', 'CO2-Emissionen (g/kWh)']
                )
            ).render(
                "container-scatter",
                {'style': 'min-width: 310px; height: 400px; margin: 0 auto'}
            )
        )

        return context
