
from os import path
from stemp.settings import SqlAlchemySession, SCENARIO_PATH
from stemp.scenarios import import_scenario, create_energysystem
from stemp.bookkeeping import simulate_energysystem
from stemp.models import Scenario, Parameter, Simulation
from db_apps.oemof_results import store_results


class SessionSimulation(object):
    def __init__(self, name, session):
        self.session = session
        self.name = name
        self.module = None
        self.energysystem = None
        self.parameter = {}
        self.result_id = None
        self.import_scenario_module()

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
            energysystem = create_energysystem(
                self.module,
                **self.parameter
            )
            self.energysystem = energysystem
            self.result_id = simulate_energysystem(self)

    def store_results(self, results, param_results):
        # Store scenario, parameter and setup via Django ORM
        scenario = Scenario.objects.get_or_create(name=self.name)[0]
        parameter = Parameter.objects.get_or_create(data=self.parameter)[0]

        # Store oemeof results via SQLAlchemy:
        sa_session = SqlAlchemySession()
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

    def import_scenario_module(self):
        self.module = import_scenario(
            path.join(SCENARIO_PATH, self.name))

    def include_demand(self):
        self.parameter['demand'] = self.session.demand


class UserSession(object):
    def __init__(self):
        self.scenarios = []
        self.demand = {}

    def init_scenarios(self, scenario_names):
        for scenario in scenario_names:
            self.scenarios.append(SessionSimulation(scenario, self))
