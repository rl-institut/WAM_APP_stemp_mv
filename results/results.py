import sqlahelper
from typing import List

from oemof.solph import analyzer as an
from db_apps.oemof_results import restore_results

from stemp.scenarios import basic_setup
from stemp.results.visualizations import Visualization


class Result(object):
    def __init__(self, scenario):
        self.scenario = scenario
        self.data = None
        self.analysis = None


class ResultAggregations(object):
    """
    Scenarios are loaded, analyzed and aggregated within this class
    """
    def __init__(self, scenarios, visualizations: List[Visualization]):
        self.results = [Result(scenario) for scenario in scenarios]
        self.visualizations = visualizations
        self.init_scenarios()
        self.analyze()

    def init_scenarios(self):
        sa_session = sqlahelper.get_session()
        for result in self.results:
            result.data = restore_results(
                sa_session,
                result.scenario.result_id,
                restore_none_type=True,
                advanced_label=basic_setup.AdvancedLabel
            )
        sa_session.close()

    def analyze(self):
        for result in self.results:
            result.analysis = an.Analysis(result.data[1], result.data[0])
            for visualization in self.visualizations:
                result.analysis.add_analyzer(
                    visualization.aggregation.analyzer())
            result.analysis.analyze()

    def visualize(self, name):
        visualization = next(
            vis for vis in self.visualizations if vis.name == name)
        aggregated_data = visualization.aggregation.aggregate(self.results)
        visualization.template.set_data(aggregated_data)
        return visualization.template
