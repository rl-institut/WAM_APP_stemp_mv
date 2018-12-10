import sqlahelper
from typing import Dict, List

from oemof.solph import analyzer as an
from db_apps.oemof_results import restore_results

from stemp.app_settings import SCENARIO_MODULES
from stemp.scenarios import basic_setup
from stemp.models import Simulation
from stemp.results.aggregations import Aggregation


class SimulationResultNotFound(Exception):
    pass


class Result(object):
    def __init__(self, result_id):
        self.result_id = result_id
        self.scenario = self.__init_scenario(result_id)
        self.data = None
        self.analysis: an.Analysis = None

    @staticmethod
    def __init_scenario(result_id):
        try:
            sim = Simulation.objects.get(result_id=result_id)
        except Simulation.DoesNotExist:
            raise SimulationResultNotFound(
                f'Simulation result #{result_id} not found')
        return SCENARIO_MODULES[sim.scenario.name]


class ResultAggregations(object):
    """
    Scenarios are loaded, analyzed and aggregated within this class
    """
    def __init__(
            self,
            result_ids: List[int],
            aggregations: Dict[str, Aggregation]
    ):
        self.results = [Result(result_id) for result_id in result_ids]
        self.aggregations = aggregations
        self.init_scenarios()
        self.analyze()

    def init_scenarios(self):
        sa_session = sqlahelper.get_session()
        for result in self.results:
            result.data = restore_results(
                sa_session,
                result.result_id,
                restore_none_type=True,
                advanced_label=basic_setup.AdvancedLabel
            )
        sa_session.close()

    def analyze(self):
        for result in self.results:
            result.analysis = an.Analysis(result.data[1], result.data[0])
            for aggregation in self.aggregations.values():
                if isinstance(aggregation.analyzer, dict):
                    for analyzer in aggregation.analyzer.values():
                        result.analysis.add_analyzer(analyzer())
                else:
                    result.analysis.add_analyzer(
                        aggregation.analyzer())
            result.analysis.analyze()

    def aggregate(self, name):
        return self.aggregations[name].aggregate(self.results)
