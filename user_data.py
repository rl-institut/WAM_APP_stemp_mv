
from stemp.settings import SqlAlchemySession
from stemp.scenarios import import_scenario
from stemp.models import Scenario, Setup, Parameter, Simulation
from stemp.results import Results
from db_apps.oemof_results import store_results, restore_results


class UserSession(object):
    def __init__(self):
        self.scenario = None
        self.scenario_module = None
        self.parameter = {}
        self.setup = {}
        self.energysystem = None
        self.result = None
        self.district = {}

    def load_result(self, result_id):
        sa_session = SqlAlchemySession()
        param_results, results = restore_results(sa_session, result_id)
        self.result = Results(results, param_results)
        sa_session.close()

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
                scenario__name=self.scenario):

            # Check if result is outdated:
            if simulation.date < simulation.scenario.last_change:
                continue

            if simulation.parameter.data != self.parameter:
                continue

            # Simulation found:
            return simulation.result_id

        # Simulation not found:
        return None

    def store_simulation(self):
        # Store scenario, parameter and setup via Django ORM
        scenario = Scenario.objects.get_or_create(name=self.scenario)[0]
        parameter = Parameter.objects.get_or_create(data=self.parameter)[0]
        setup = Setup.objects.get_or_create(data=self.setup)[0]

        # Store oemeof results via SQLAlchemy:
        sa_session = SqlAlchemySession()
        result_id = store_results(
            sa_session,
            self.result.param_results,
            self.result.results
        )
        sa_session.close()

        # Store simulation in Django ORM:
        Simulation.objects.get_or_create(
            scenario=scenario,
            parameter=parameter,
            setup=setup,
            result_id=result_id
        )

    def import_scenario_module(self):
        if self.scenario is None:
            raise KeyError('no scenario found')
        scenario_module = import_scenario(self.scenario)
        self.scenario_module = scenario_module


