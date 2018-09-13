
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


class TotalInvestmentAnalyzer(an.Analyzer):
    requires = ('results', 'param_results')
    depends_on = (an.SizeAnalyzer,)

    def analyze(self, *args):
        super(TotalInvestmentAnalyzer, self).analyze(*args)
        seq_result = self._get_dep_result(an.SizeAnalyzer)
        try:
            psc = self.psc(args)
            size = seq_result[args]
            invest = psc['investment_capex']
        except KeyError:
            return
        result = invest * size
        self.result[args] = result
        self.total += result


class CO2Analyzer(an.Analyzer):
    requires = ('results', 'param_results')
    depends_on = (an.SequenceFlowSumAnalyzer,)

    def analyze(self, *args):
        super(CO2Analyzer, self).analyze(*args)
        seq_result = self._get_dep_result(an.SequenceFlowSumAnalyzer)
        try:
            psc = self.psc(args)
            flow = seq_result[args]
            co2 = psc['co2_emissions']
        except KeyError:
            return
        result = co2 * flow
        self.result[args] = result
        self.total += result


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
            result.analysis.add_analyzer(CO2Analyzer())
            result.analysis.add_analyzer(an.FlowTypeAnalyzer())
            result.analysis.add_analyzer(an.SizeAnalyzer())
            result.analysis.add_analyzer(TotalInvestmentAnalyzer())
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
        visualization.highchart.set_data(data)
        return visualization.highchart.render()

    def rank(self, name):
        """Function to rank results by different Rankings"""
        # TODO: Write ranking function
        pass


class Strategy(object):
    name = 'Strategy'
    analyzer = None

    @staticmethod
    def _get_label(scenario, nodes):
        # TODO: Export label mappings into cfg or scenario
        if isinstance(nodes, str):
            return nodes
        if scenario == 'bhkw_scenario':
            if nodes[1] is not None and nodes[1].name.endswith('chp'):
                return 'BHKW'
        elif scenario == 'oil_scenario':
            if nodes[1] is not None and nodes[1].name.endswith('oil_heating'):
                return 'Ölkessel'
            elif nodes[0] is not None and nodes[0].name.endswith('oil_heating'):
                return 'Ölkessel'
        return nodes

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        return self._set_label(result.scenario.name, data)

    def _set_label(self, scenario, data):
        return {
            self._get_label(scenario, k): v
            for k, v in data.items()
        }

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
        return data.transpose()


class LCOEStrategy(Strategy):
    name = 'LCOE'
    analyzer = an.LCOEAnalyzer

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        filtered_data = {}
        for k, v in data.items():
            new_label = self._get_label(result.scenario.name, k)
            if v.investment > 0.0:
                filtered_data[new_label + ' (Investment)'] = v.investment
            if v.variable_costs > 0.0:
                filtered_data[
                    new_label + self._get_suffix(result.scenario.name, k)
                ] = v.variable_costs
        return filtered_data

    @staticmethod
    def _get_suffix(scenario, nodes):
        if isinstance(nodes, str):
            return nodes
        if scenario == 'bhkw_scenario':
            if nodes[1] is not None and nodes[1].name.endswith('chp'):
                return ' (Gas)'
        elif scenario == 'oil_scenario':
            if nodes[1] is not None and nodes[1].name.endswith('oil_heating'):
                return ' (Öl)'
            elif nodes[0] is not None and nodes[0].name.endswith('oil_heating'):
                return ' (OPEX)'
        return nodes


class TotalDemandStrategy(Strategy):
    name = 'Wärmeverbrauch'
    analyzer = an.SequenceFlowSumAnalyzer

    def _get_data(self, result):
        return dict(filter(
            lambda dct: (
                dct[0][1].tags is not None and
                'demand' in dct[0][1].tags
            ),
            result.analysis.get_analyzer(
                an.SequenceFlowSumAnalyzer).result.items()
        ))


class SizeStrategy(Strategy):
    name = 'Sizes'
    analyzer = an.SizeAnalyzer


class ProfileStrategy(Strategy):
    name = 'Profile'

    def _get_data(self, result):
        demand = [
            v['sequences']['flow'][:100]
            for k, v in result.analysis.results.items()
            if k[1].tags is not None and 'demand' in k[1].tags
        ][0].tolist()
        gas = None
        try:
            gas = [
                v['sequences']['flow'][:100]
                for k, v in result.analysis.results.items()
                if k[0].name == 'b_gas' or k[0].name == 'b_oil'
            ][0].tolist()
        except IndexError:
            pass
        excess = [
            v['sequences']['flow'][:100]
            for k, v in result.analysis.results.items()
            if k[1].name.startswith('excess')
        ][0].tolist()
        return {
            'Verbrauch': demand,
            'Einspeisung (Gas/Öl)': gas,
            'Wärme-Überschuss': excess
        }


class InvestmentStrategy(Strategy):
    name = 'Investment'
    analyzer = TotalInvestmentAnalyzer


class CO2Strategy(Strategy):
    name = 'CO2'
    analyzer = CO2Analyzer


Visualization = namedtuple(
    'Visualization',
    ['strategy', 'highchart']
)

VISUALIZATIONS = {
    'lcoe': Visualization(
        LCOEStrategy(),
        visualizations.HCCosts()
    ),
    'invest': Visualization(
        InvestmentStrategy(),
        visualizations.HCStemp(title='Investition')
    ),
    'size': Visualization(
        SizeStrategy(),
        visualizations.HCStemp(title='Optimierte Größen')
    ),
    'demand': Visualization(
        TotalDemandStrategy(),
        visualizations.HCStemp(title='Verbrauch')
    ),
    'co2': Visualization(
        CO2Strategy(),
        visualizations.HCStemp(title='CO2-Verbrauch')
    ),
    'profile': Visualization(
        ProfileStrategy(),
        visualizations.HCStemp(title='Profile', style='line')
    )
}
