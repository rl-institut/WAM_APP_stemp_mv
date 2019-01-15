
import sqlahelper

from stemp.app_settings import SCENARIO_MODULES
from stemp.constants import DemandType, DistrictStatus
from .tasks import simulate_energysystem
from stemp.models import Scenario, Parameter, Simulation, Household, District
from db_apps.oemof_results import store_results


class SessionSimulation(object):
    def __init__(self, name, session):
        self.session = session
        self.name = name
        self.module = SCENARIO_MODULES[name]
        self.energysystem = None
        self.parameter = {}
        self.changed_parameters = None
        self.result_id = None
        self.pending = None

    def check_for_result(self):
        """
        Checks if result for given scenario and parameters is already simulated

        Following checks are made:
            * Find scenario name
            * Check if scenario file has been changed recently
            * Check if params match

        Returns
        -------
        int: Simulation ID if results were found, else None
        """
        for simulation in Simulation.objects.filter(
                scenario__name=self.name):

            # Check if result is outdated:
            if simulation.date < simulation.scenario.last_change:
                continue

            if simulation.parameter.data != self.parameter:
                continue

            # Simulation found:
            return simulation.result_id

        # Simulation not found:
        return None

    def load_or_simulate(self):
        self.include_demand()
        
        # Check if results already exist:
        result_id = self.check_for_result()
        if result_id is not None:
            self.result_id = result_id
        else:
            self.pending = (
                simulate_energysystem.delay(self.name, self.parameter)
            )

    def is_pending(self):
        if self.pending is None:
            return False
        if self.pending.ready():
            self.result_id = self.pending.get()
            return False
        return True

    def store_results(self, results, param_results):
        # Store scenario, parameter and setup via Django ORM
        scenario = Scenario.objects.get_or_create(name=self.name)[0]
        parameter = Parameter.objects.get_or_create(data=self.parameter)[0]

        # Store oemeof results via SQLAlchemy:
        sa_session = sqlahelper.get_session()
        result_id = store_results(
            sa_session,
            param_results,
            results
        )
        sa_session.close()

        # Store simulation in Django ORM:
        Simulation.objects.get_or_create(
            scenario=scenario,
            parameter=parameter,
            result_id=result_id
        )
        return result_id

    def include_demand(self):
        self.parameter['demand'] = {
            'type': self.session.demand_type,
            'index': self.session.demand_id
        }


class UserSession(object):
    def __init__(self):
        self.scenarios = []
        self.demand_type = None
        self.demand_id = None
        self.current_district = {}

    def init_scenarios(self, scenario_names):
        for scenario in scenario_names:
            self.scenarios.append(SessionSimulation(scenario, self))

    def reset_demand(self):
        self.demand_type = None
        self.demand_id = None
        self.current_district = {}

    def reset_scenarios(self):
        self.scenarios = []

    def get_demand(self):
        if self.demand_type == DemandType.Single:
            return Household.objects.get(pk=self.demand_id)
        elif self.demand_type == DemandType.District:
            return District.objects.get(pk=self.demand_id)

    def get_district_status(self):
        if self.demand_id is None:
            return DistrictStatus.New
        district = District.objects.get(pk=self.demand_id)
        if self.current_district == {
            str(dh.household.id): dh.amount
            for dh in district.districthouseholds_set.all()
        }:
            return DistrictStatus.Unchanged
        else:
            return DistrictStatus.Changed
