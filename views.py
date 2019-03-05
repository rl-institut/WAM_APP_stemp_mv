
import os
import pandas

from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.urls import reverse

from wam.settings import SESSION_DATA, BASE_DIR
from utils.widgets import Wizard, CSVWidget, OrbitWidget

from user_sessions.utils import check_session_method
from stemp import app_settings
from stemp.constants import DemandType
from stemp.models import Household
from stemp.oep_models import OEPScenario
from stemp import models, forms
from stemp.results import results
from stemp.visualizations import highcharts, dataframe
from stemp.results import aggregations as agg
from stemp.user_data import UserSession
from stemp.widgets import HouseholdSummary, TechnologySummary, ParameterSummary


class IndexView(TemplateView):
    template_name = 'stemp/index.html'


class DemandSelectionView(TemplateView):
    template_name = 'stemp/demand_selection.html'


class DemandSingleView(TemplateView):
    template_name = 'stemp/demand_single.html'
    only_house_type = None
    is_district_hh = False

    def get_context_data(self):
        context = super(DemandSingleView, self).get_context_data()
        context['household_form'] = forms.HouseholdForm(self.only_house_type)
        context['list_form'] = forms.HouseholdSelectForm(self.only_house_type)
        context['is_district_hh'] = self.is_district_hh
        context['wizard'] = Wizard([None] * 4, current=0)
        context['demand_label'] = (
            DemandType.District.label() if self.is_district_hh
            else DemandType.Single.label()
        )
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request, UserSession)
        session = SESSION_DATA.get_session(request)
        session.demand_type = (
            DemandType.District if self.is_district_hh else DemandType.Single)

        context = self.get_context_data()
        return self.render_to_response(context)

    @check_session_method
    def post(self, request, session):
        hh_id = None
        form = request.POST['form']
        if form == 'house':
            hh_form = forms.HouseholdForm(None, request.POST)
            if hh_form.is_valid():
                hh = hh_form.save()
                hh_id = hh.id
            else:
                context = self.get_context_data()
                context['household_form'] = hh_form
                return self.render_to_response(context)
        elif form == 'list':
            hh = forms.HouseholdSelectForm(None, request.POST)
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
        context['wizard'] = Wizard([None] * 4, current=0)
        context['demand_label'] = session.demand_type.label()
        return context

    def get(self, request, *args, **kwargs):
        # Start session (if no session yet):
        SESSION_DATA.start_session(request, UserSession)
        session = SESSION_DATA.get_session(request)
        if self.new_district:
            session.reset_demand()
        session.demand_type = DemandType.District

        context = self.get_context_data(session)
        return self.render_to_response(context)

    @staticmethod
    def __update_district(request, session):
        session.current_district = {
            hh: count
            for hh, count in request.POST.items()
            if hh not in (
                'csrfmiddlewaretoken',
                'trash',
                'add_efh',
                'add_mfh',
                'demand_submit',
                'district_name',
                'district_status'
            )
        }

    def __change_district_list(self, request, session):
        self.__update_district(request, session)
        if 'trash' in request.POST:
            trash = request.POST['trash']
            del session.current_district[trash]
            context = self.get_context_data(session)
            return self.render_to_response(context)
        elif 'add_efh' in request.POST:
            return redirect('stemp:demand_district_household_efh')
        elif 'add_mfh' in request.POST:
            return redirect('stemp:demand_district_household_mfh')

    @check_session_method
    def post(self, request, session):
        if any(key in request.POST for key in ('add_efh', 'add_mfh', 'trash')):
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
                self.__update_district(request, session)
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

    def get_context_data(self, session, **kwargs):
        context = super(TechnologyView, self).get_context_data(**kwargs)
        choices = tuple(
            (sc, params['LABELS']['name'])
            for sc, params in app_settings.SCENARIO_PARAMETERS.items()
        )
        initial = [choice[0] for choice in choices]
        technology_information = {
            sc: params['LABELS'].copy()
            for sc, params in app_settings.SCENARIO_PARAMETERS.items()
        }

        demand = session.get_demand()

        # Make BHKW/BIO-BHKW uncheckable if bhkw-size is out of bounds:
        if 'bhkw' in app_settings.ACTIVATED_SCENARIOS:
            scenario = (
                app_settings.SCENARIO_MODULES['bhkw'].Scenario)
            if not scenario.is_available(demand):
                name = (
                    app_settings.SCENARIO_PARAMETERS['bhkw']['LABELS']['name'])
                technology_information['bhkw']['warning'] = (
                    f"{name} ist nicht in nötiger Größe verfügbar"
                )
                technology_information['bhkw']['grey_out'] = True
                technology_information['bhkw']['disabled'] = True
                initial.remove('bhkw')
        if 'bio_bhkw' in app_settings.ACTIVATED_SCENARIOS:
            scenario = (
                app_settings.SCENARIO_MODULES['bio_bhkw'].Scenario)
            if not scenario.is_available(demand):
                name = (
                    app_settings.SCENARIO_PARAMETERS['bio_bhkw']['LABELS'][
                        'name'
                    ]
                )
                technology_information['bio_bhkw']['warning'] = (
                    f"{name} ist nicht in nötiger Größe verfügbar"
                )
                technology_information['bio_bhkw']['grey_out'] = True
                technology_information['bio_bhkw']['disabled'] = True
                initial.remove('bio_bhkw')
            else:
                # Add warning for bio-bhkw
                technology_information['bio_bhkw']['warning'] = (
                    app_settings.SCENARIO_PARAMETERS[
                        'bio_bhkw']['LABELS']['warning']
                )

        # Add warning if radiator is chosen in combination with heatpump:
        if 'pv_heatpump' in app_settings.ACTIVATED_SCENARIOS:
            if demand.contains_radiator():
                technology_information['pv_heatpump']['warning'] = (
                    app_settings.SCENARIO_PARAMETERS[
                        'pv_heatpump']['LABELS']['warning']
                )

        context['technology'] = forms.TechnologyForm(
            'technology',
            'Technology',
            choices=choices,
            initial=initial,
            information=technology_information
        )
        context['demand_type'] = session.demand_type.suffix()
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = demand.name
        context['wizard'] = Wizard(
            urls=[
                (reverse('stemp:demand_selection'), 'Zurück zu Schritt 1'),
                None,
                None,
                None,
            ],
            current=1,
            screen_reader_for_current=(
                'Sie sind auf der Seite Technologie-Auswahl')
        )
        return context

    @check_session_method
    def get(self, request, *args, **kwargs):
        session = kwargs['session']
        session.reset_scenarios()
        context = self.get_context_data(session)
        return self.render_to_response(context)

    @check_session_method
    def post(self, request, session):
        scenarios = request.POST.getlist('technology')
        session.init_scenarios(scenarios)
        return redirect('stemp:parameter')


class ParameterView(TemplateView):
    template_name = 'stemp/parameter.html'

    @staticmethod
    def get_scenario_parameters(session):
        scenarios = session.scenarios
        if not scenarios:
            raise KeyError('No scenarios found')

        # Get data from OEP:
        parameters = []
        for scenario in scenarios:
            scenario_parameters = OEPScenario.get_scenario_parameters(
                scenario.name, session.demand_type)
            # Load additional dynamic parameters from module:
            scenario_parameters = (
                scenario.module.Scenario.add_dynamic_parameters(
                    scenario, scenario_parameters)
            )
            parameters.append(
                (
                    scenario.name,
                    scenario_parameters
                )
            )
        return parameters

    def get_context_data(self, session, parameter_form=None, **kwargs):
        context = {}
        if parameter_form is None:
            context['parameter_form'] = forms.ParameterForm(
                self.get_scenario_parameters(session))
        else:
            context['parameter_form'] = parameter_form
        context['demand_label'] = session.demand_type.label()
        context['demand_name'] = session.get_demand().name
        context['wizard'] = Wizard(
            urls=[
                (reverse('stemp:demand_selection'), 'Zurück zu Schritt 1'),
                (reverse('stemp:technology'), 'Zurück zu Schritt 2'),
                None,
                None
            ],
            current=2,
            screen_reader_for_current=(
                'Hier können Parameter optional angepasst werden')
        )
        return context

    @check_session_method
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs['session'])
        return self.render_to_response(context)

    @check_session_method
    def post(self, request, session):
        parameters = self.get_scenario_parameters(session)
        parameter_form = forms.ParameterForm(parameters, request.POST)
        if not parameter_form.is_valid():
            context = self.get_context_data(session, parameter_form)
            return self.render_to_response(context)

        for scenario in session.scenarios:
            scenario.parameter.update(
                parameter_form.prepared_data(scenario.name))

        session.changed_parameters = (
            forms.ParameterForm.get_changed_parameters(
                parameters, request.POST
            )
        )
        return redirect('stemp:summary')


class SummaryView(TemplateView):
    template_name = 'stemp/summary.html'

    def get_context_data(self, session, **kwargs):
        context = super(SummaryView, self).get_context_data(**kwargs)
        context['wizard'] = Wizard(
            urls=[
                (reverse('stemp:demand_selection'), 'Zurück zu Schritt 1'),
                (reverse('stemp:technology'), 'Zurück zu Schritt 2'),
                (reverse('stemp:parameter'), 'Zurück zu Schritt 3'),
                None
            ],
            current=3,
            screen_reader_for_current=(
                'Sie sind auf der Seite Zusammenfassung des Haushalts')
        )
        context['demand_label'] = session.demand_type.label()
        demand = session.get_demand()
        context['demand_name'] = demand.name
        context['is_district'] = session.demand_type == DemandType.District
        if isinstance(demand, Household):
            context['demands'] = [HouseholdSummary(demand)]
        else:
            context['demands'] = [
                HouseholdSummary(dh.household, count=dh.amount)
                for dh in demand.districthouseholds_set.all()
            ]
        context['technologies'] = [
            TechnologySummary(app_settings.SCENARIO_PARAMETERS[scenario.name])
            for scenario in session.scenarios
        ]
        context['parameters'] = ParameterSummary(session.changed_parameters)
        return context

    @check_session_method
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs['session'])
        return self.render_to_response(context)

    @check_session_method
    def post(self, request, session):
        if 'done' in request.POST:
            for scenario in session.scenarios:
                scenario.load_or_simulate()
            return redirect('stemp:result')
        else:
            return redirect('stemp:parameter')


class ResultView(TemplateView):
    template_name = 'stemp/result.html'

    def get_context_data(self, result_ids, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)

        aggregations = {
            'lcoe': agg.LCOEAggregation(),
            'tech': agg.TechnologieComparison()
        }
        aggregated_results = results.ResultAggregations(
            result_ids,
            aggregations
        )
        context['visualizations'] = [
            highcharts.LCOEHighchart(aggregated_results.aggregate('lcoe')),
            dataframe.ComparisonDataframe(aggregated_results.aggregate('tech'))
        ]
        return context

    def get(self, request, *args, **kwargs):
        result_ids = kwargs.get('results')

        if result_ids is not None:
            context = self.get_context_data(result_ids)
            # Render list of given results:
            return self.render_to_response(context)

        try:
            session = SESSION_DATA.get_session(request)
        except KeyError:
            # Render empty results:
            return self.render_to_response({})

        pending = any(
            [
                scenario.is_pending()
                for scenario in session.scenarios
            ]
        )
        if pending:
            # Render pending simulation:
            return redirect('stemp:pending')

        result_ids = [
            sc.result_id
            for sc in session.scenarios
            if sc.result_id is not None
        ]
        if len(result_ids) == 0:
            return self.render_to_response({})
        # Render stored results from session:
        return redirect('stemp:result_list', results=result_ids)

    @check_session_method
    def post(self, request):
        if 'save' in request.POST:
            simulation_name = request.POST['simulation_name']
            try:
                session = SESSION_DATA.get_session(request)
            except KeyError:
                return render(request, 'stemp/session_not_found.html')
            session.store_simulation(simulation_name)
            return self.render_to_response({})


class PendingView(TemplateView):
    template_name = 'stemp/pending.html'

    def get_context_data(self, **kwargs):
        filename = os.path.join(
            BASE_DIR, 'stemp', 'texts', 'energiespartipps.csv')
        data = pandas.read_csv(
            filename, index_col=0, sep=';')
        return {
            'tipps': OrbitWidget(
                'Energiespartipps',
                [
                    OrbitWidget.OrbitItem(d[0], d[1]['Beschreibung'])
                    for d in data.iterrows()
                ],
                orbit_class='orbit orbit--white'
            )
        }


class AdressesView(TemplateView):
    template_name = 'stemp/addresses.html'

    def get_context_data(self, **kwargs):
        return {
            'contacts': CSVWidget(
                'stemp/texts/ansprechpartner.csv',
                'Ansprechpartner',
                csv_kwargs={
                    'index_col': 0,
                    'sep': ';',
                    'encoding': 'latin_1',
                },
                links=['Link']
            ),
            'funding': CSVWidget(
                'stemp/texts/förderprogramme.csv',
                'Förderprogramme',
                csv_kwargs={
                    'index_col': 0,
                    'sep': ';',
                    'encoding': 'latin_1',
                },
                links=['Link']
            ),
        }


class TipsView(TemplateView):
    template_name = 'stemp/tips.html'

    def get_context_data(self, **kwargs):
        filename = os.path.join(
            BASE_DIR, 'stemp', 'texts', 'energiespartipps.csv')
        data = pandas.read_csv(
            filename, index_col=0, sep=';')
        return {
            'tipps': OrbitWidget(
                'Energiespartipps',
                [
                    OrbitWidget.OrbitItem(d[0], d[1]['Beschreibung'])
                    for d in data.iterrows()
                ]
            )
        }
