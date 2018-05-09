
from collections import namedtuple
from oemof.solph import analyzer as an
from stemp.settings import SqlAlchemySession
from utils.highcharts import Highchart
from db_apps.oemof_results import restore_results

Visualization = namedtuple('Visualization', ['analyzer', 'style', 'kwargs'])
VISUALIZATIONS = {
    'invest': Visualization(
        an.InvestAnalyzer,
        'column',
        {
            'title': 'Investment',
            'x_title': 'Technologie',
            'y_title': 'Investemnt [€]',
            'stacked': True
        }
    )
}


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
        sa_session = SqlAlchemySession()
        for result in self.results:
            result.data = restore_results(
                sa_session, result.scenario.result_id)
        sa_session.close()

    def analyze(self):
        for result in self.results:
            result.analysis = an.Analysis(*result.data)
            result.analysis.add_analyzer(an.SequenceFlowSumAnalyzer())
            result.analysis.add_analyzer(an.FlowTypeAnalyzer())
            result.analysis.add_analyzer(an.InvestAnalyzer())
            result.analysis.add_analyzer(an.VariableCostAnalyzer())
            result.analysis.add_analyzer(an.NodeBalanceAnalyzer())
            result.analysis.analyze()
            # TODO: How to set demand outputs?
            # result.analysis.add_analyzer(analyzer.LCOEAnalyzer())

    def __get_result_dict(self, analyzer):
        return {
            result.scenario: result.analysis.get_analyzer(analyzer).result
            for result in self.results
        }

    def visualize(self, name):
        visualization = VISUALIZATIONS[name]
        data = self.__get_result_dict(visualization.analyzer)
        return Highchart(data, visualization.style, **visualization.kwargs)
