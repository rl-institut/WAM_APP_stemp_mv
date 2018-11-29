
import pandas
from collections import namedtuple
from abc import ABC
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


class LCOEAutomatedDemandAnalyzer(an.LCOEAnalyzer):
    def __init__(self):
        super(LCOEAutomatedDemandAnalyzer, self).__init__([])

    def init_analyzer(self):
        # Find all demands:
        for nodes in self.analysis.param_results:
            try:
                if nodes[1].tags is not None and 'demand' in nodes[1].tags:
                    self.load_sinks.append(nodes[1])
            except AttributeError:
                pass
        super(LCOEAutomatedDemandAnalyzer, self).init_analyzer()


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
            result.analysis.add_analyzer(LCOEAutomatedDemandAnalyzer())
            result.analysis.analyze()

    def __prepare_result_data(self, visualization):
        return visualization.strategy.aggregate(self.results)

    def visualize(self, name):
        visualization = VISUALIZATIONS[name]
        data = self.__prepare_result_data(visualization)
        visualization.highchart.set_data(data)
        return visualization.highchart

    def rank(self, name):
        """Function to rank results by different Rankings"""
        # TODO: Write ranking function
        pass


class Aggregation(ABC):
    name = 'Aggregation'
    analyzer = None

    @staticmethod
    def _get_label(nodes):
        # TODO: Export label mappings into cfg or scenario
        if isinstance(nodes, str):
            return nodes
        if nodes[1] is not None and nodes[1].name.endswith('chp'):
            return 'BHKW'
        elif nodes[0].name.endswith('chp'):
            return 'BHKW (Stromgutschrift)'
        elif (
                nodes[0].name.startswith('b_bhkw_el') and
                nodes[1] is not None and
                nodes[1].name.startswith('transformer_from')
        ):
            return 'BHKW (Stromgutschrift)'
        elif (
                nodes[1] is not None and
                nodes[1].name.startswith('transformer_from')
        ):
            return 'PV (Stromgutschrift)'
        elif nodes[1] is not None and nodes[1].name.endswith('oil_heating'):
            return 'Ölkessel'
        elif (
                nodes[0] is not None and
                nodes[0].name.endswith('oil_heating')
        ):
            return 'Ölkessel'
        elif nodes[1] is not None and nodes[1].name.endswith('gas_heating'):
            return 'Gasheizung'
        elif (
                nodes[0] is not None and
                nodes[0].name.endswith('gas_heating')
        ):
            return 'Gasheizung'
        elif nodes[1] is not None and nodes[1].name.endswith('heat_pump'):
            return 'Wärmepumpe'
        elif nodes[0] is not None and nodes[0].name.endswith('pv'):
            return 'PV'
        elif nodes[0] is not None and nodes[0].name.endswith('net'):
            return 'Stromkosten'
        return '-'.join(map(str, nodes))

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        return self._set_label(data)

    def _set_label(self, data):
        return {
            self._get_label(k): v
            for k, v in data.items()
        }

    def aggregate(self, results):
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


class LCOEAggregation(Aggregation):
    name = 'LCOE'
    analyzer = LCOEAutomatedDemandAnalyzer

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        filtered_data = {}
        for k, v in data.items():
            new_label = self._get_label(k)
            if abs(v.investment) > 0.001:
                filtered_data[new_label + ' (Investment)'] = v.investment
            if abs(v.variable_costs) > 0.001:
                filtered_data[
                    new_label + self._get_suffix(k)
                ] = v.variable_costs
        return filtered_data

    @staticmethod
    def _get_suffix(nodes):
        if isinstance(nodes, str):
            return nodes
        if nodes[1] is not None and nodes[1].name.endswith('chp'):
            return ' (Gas)'
        elif nodes[1] is not None and nodes[1].name.endswith('oil_heating'):
            return ' (Öl)'
        elif (
                nodes[0] is not None and
                nodes[0].name.endswith('oil_heating')
        ):
            return ' (OPEX)'
        elif nodes[1] is not None and nodes[1].name.endswith('gas_heating'):
            return ' (Gas)'
        elif (
                nodes[0] is not None and
                nodes[0].name.endswith('gas_heating')
        ):
            return ' (OPEX)'
        return ''


class TotalDemandAggregation(Aggregation):
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


class SizeAggregation(Aggregation):
    name = 'Sizes'
    analyzer = an.SizeAnalyzer


class ProfileAggregation(Aggregation):
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


class InvestmentAggregation(Aggregation):
    name = 'Investment'
    analyzer = TotalInvestmentAnalyzer


class CO2Aggregation(Aggregation):
    name = 'CO2'
    analyzer = CO2Analyzer


Visualization = namedtuple(
    'Visualization',
    ['strategy', 'highchart']
)

VISUALIZATIONS = {
    'lcoe': Visualization(
        LCOEAggregation(),
        visualizations.HCCosts(
            title='Wärmekosten',
            subtitle='Euro pro Kilowattstunde'
        )
    ),
    'invest': Visualization(
        InvestmentAggregation(),
        visualizations.HCCosts(
            title='Investition',
            subtitle='Euro'
        )
    ),
    'size': Visualization(
        SizeAggregation(),
        visualizations.HCStemp(
            title='Installierte Leistungen',
            subtitle='kW',
            stacked=True
        )
    ),
    'demand': Visualization(
        TotalDemandAggregation(),
        visualizations.HCStemp(title='Verbrauch', stacked=True)
    ),
    'co2': Visualization(
        CO2Aggregation(),
        visualizations.HCStemp(
            title='CO2-Verbrauch',
            subtitle='g/kWh',
            stacked=True
        )
    ),
    'profile': Visualization(
        ProfileAggregation(),
        visualizations.HCStemp(title='Profile', style='line')
    )
}
