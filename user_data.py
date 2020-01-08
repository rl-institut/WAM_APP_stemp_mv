"""
Module holds classes to store user informations via sessions
"""
import logging

from stemp.app_settings import SCENARIO_MODULES
from stemp.constants import DemandType, DistrictStatus
from .tasks import simulate_energysystem
from stemp.models import Simulation, Household, District


class SessionSimulation(object):
    """
    Holds simulation data for one scenario

    Can start simulation of scenario and check if simulation is done and can return
    results if so.
    """
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
        int:
            Simulation ID if results were found, else None
        """
        for simulation in Simulation.objects.filter(scenario__name=self.name):

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
        """
        Checks if current scenario is simulated already and sets result ID if so.
        Otherwise it starts simulation of given scenario.
        """
        self.include_demand()

        # Check if results already exist:
        result_id = self.check_for_result()
        if result_id is not None:
            self.result_id = result_id
        else:
            self.pending = simulate_energysystem.delay(self.name, self.parameter)

    def is_pending(self):
        """
        Checks if simulation of scenario is still running

        Returns
        -------
        bool
            True, if simulation results are ready
        """
        if self.pending is None:
            return False
        if self.pending.ready():
            try:
                self.result_id = self.pending.get()
            except Exception:
                logging.exception("Simulation task failed")
                self.result_id = None
            return False
        return True

    def include_demand(self):
        """
        Adds demand type and index to parameters

        As demand type is not included in parameters at parameter page, this has to be
        done in an extra step.
        """
        self.parameter["demand"] = {
            "type": self.session.demand_type,
            "index": self.session.demand_id,
        }


class UserSession(object):
    """
    Session data for one user

    Holds all current scenarios of a user together with selected demand
    (household/district).
    """
    def __init__(self):
        self.scenarios = []
        self.demand_type = None
        self.demand_id = None
        self.current_district = {}

    def init_scenarios(self, scenario_names):
        """
        Initialize scenario sessions for each scenario

        Parameters
        ----------
        scenario_names : List[str]
            List of scenario names, which shall be added to user session
        """
        for scenario in scenario_names:
            self.scenarios.append(SessionSimulation(scenario, self))

    def reset_demand(self):
        """Resets current demand options"""
        self.demand_type = None
        self.demand_id = None
        self.current_district = {}

    def reset_scenarios(self):
        """Removes scenarios from session"""
        self.scenarios = []

    def get_demand(self):
        """Loads demand from model using demand type and index"""
        if self.demand_type == DemandType.Single:
            return Household.objects.get(pk=self.demand_id)
        elif self.demand_type == DemandType.District:
            return District.objects.get(pk=self.demand_id)

    def get_district_status(self):
        """
        Checks current status of demand options (new/changed/unchanged)

        This needed on district page in order to adapt labels.
        """
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

    def __str__(self):
        return (
            f'Scenarios: {",".join([scenario.name for scenario in self.scenarios])}, '
            f"Demand-Type: {self.demand_type}, "
            f"Demand-ID: {self.demand_id}, "
            f"District: {self.current_district}"
        )
