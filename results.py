
import pandas
from collections import namedtuple
import sqlahelper

from oemof.solph import analyzer as an
from db_apps.oemof_results import restore_results

from stemp import visualizations
from stemp.scenarios.basic_setup import AdvancedLabel


class Result(object):
    def __init__(self, scenario):
        self.scenario = scenario
        self.data = None
        self.analysis = None


class ResultAnalysisVisualization(object):
    """
    Scenarios are loaded, analyzed and visualized within this class

    Implements the Facade Pattern.
    """
    def __init__(self, scenarios):
        self.results = [Result(scenario) for scenario in scenarios]
        self.init_scenarios()
        self.analyze()

    def init_scenarios(self):
        sa_session = sqlahelper.get_session()
        for result in self.results:
            result.data = restore_results(
                sa_session,
                result.scenario.result_id,
                restore_none_type=True,
                advanced_label=AdvancedLabel
            )
        sa_session.close()

    def analyze(self):
        for result in self.results:
            result.analysis = an.Analysis(result.data[1], result.data[0])
            result.analysis.add_analyzer(an.SequenceFlowSumAnalyzer())
            result.analysis.add_analyzer(an.FlowTypeAnalyzer())
            result.analysis.add_analyzer(an.InvestAnalyzer())
            result.analysis.add_analyzer(an.VariableCostAnalyzer())
            result.analysis.add_analyzer(an.NodeBalanceAnalyzer())
            result.analysis.analyze()

            # Find all demands:
            demands = []
            for nodes in result.data[0]:
                try:
                    if nodes[1].tags is not None and 'demand' in nodes[1].tags:
                        demands.append(nodes[1])
                except AttributeError:
                    pass

            result.analysis.add_analyzer(an.LCOEAnalyzer(demands))
            result.analysis.analyze()

    def __prepare_result_data(self, visualization):
        return visualization.strategy.algorithm(self.results)

    def visualize(self, name):
        visualization = VISUALIZATIONS[name]
        data = self.__prepare_result_data(visualization)
        return visualization.highchart(data).render()

    def rank(self, name):
        """Function to rank results by different Rankings"""
        # TODO: Write ranking function
        pass


class Strategy(object):
    name = 'Strategy'
    analyzer = None

    def _get_data(self, result):
        return result.analysis.get_analyzer(self.analyzer).result

    def algorithm(self, results):
        series = pandas.DataFrame(
            {
                result.scenario.name: self._get_data(result)
                for result in results
            }
        )
        series.name = self.name
        finalized = self._finalize_data(series)
        return finalized

    @staticmethod
    def _finalize_data(data):
        return data


class TotalStrategy(Strategy):
    def _get_data(self, result):
        return result.analysis.get_analyzer(self.analyzer).total


class LCOEStrategy(Strategy):
    name = 'LCOE'
    analyzer = an.LCOEAnalyzer

    @staticmethod
    def _finalize_data(data):
        return data.transpose()


class InvestmentStrategy(Strategy):
    name = 'Investment'
    analyzer = an.InvestAnalyzer

    @staticmethod
    def _finalize_data(data):
        return data.transpose()


Visualization = namedtuple(
    'Visualization',
    ['strategy', 'highchart']
)

VISUALIZATIONS = {
    'lcoe': Visualization(
        LCOEStrategy(),
        visualizations.HCCosts
    ),
    'invest': Visualization(
        InvestmentStrategy(),
        visualizations.HCCosts
    )
}
