from abc import ABC

import pandas
from oemof.solph import analyzer as an

from stemp.results import analyzer as stemp_an


class Aggregation(ABC):
    name = 'Aggregation'
    analyzer = None

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        return self._set_label(data, result)

    @staticmethod
    def _set_label(data, result):
        scenario = result.scenario.Scenario
        return {
            scenario.get_data_label(k): v
            for k, v in data.items()
            if not isinstance(k, str)
        }

    def aggregate(self, results):
        aggregated_data = {
            result.scenario.Scenario.name: self._get_data(result)
            for result in results
        }
        df = pandas.DataFrame(aggregated_data)
        df.name = self.name
        finalized = self._finalize_data(df)
        return finalized

    def _finalize_data(self, data):
        return data.transpose()


class LCOEAggregation(Aggregation):
    name = 'LCOE'
    analyzer = stemp_an.LCOEAutomatedDemandAnalyzer

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        filtered_data = {}
        for k, v in data.items():
            new_label = result.scenario.Scenario.get_data_label(k)
            if abs(v.investment) > 0.001:
                filtered_data[new_label + ' (Investment)'] = v.investment
            if abs(v.variable_costs) > 0.001:
                filtered_data[
                    new_label + self._get_suffix(k, result)
                    ] = v.variable_costs
        return filtered_data

    @staticmethod
    def _get_suffix(nodes, result):
        if isinstance(nodes, str):
            return nodes
        else:
            return result.scenario.Scenario.get_data_label(
                nodes, suffix=True)


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


class Ranking(Aggregation):
    def __init__(self, ascending=True, precision=0):
        self.ascending = ascending
        self.precision = precision

    def _finalize_data(self, data):
        data = data.sum(axis=1)
        data.sort_values(ascending=self.ascending, inplace=True)
        data = data.round(decimals=self.precision)
        return data.to_frame(self.name)


class InvestmentRanking(Ranking):
    name = 'Investment'
    analyzer = stemp_an.TotalInvestmentAnalyzer


class CO2Ranking(Ranking):
    name = 'CO2'
    analyzer = stemp_an.CO2Analyzer


class TechnologieComparison(Aggregation):
    name = 'Technologievergleich'
    analyzer = {
        'invest': stemp_an.TotalInvestmentAnalyzer,
        'co2': stemp_an.CO2Analyzer,
        'fuel': stemp_an.FossilCostsAnalyzer
    }

    def aggregate(self, results):
        df = pandas.DataFrame()
        for result in results:
            series = pandas.Series(name=result.scenario.Scenario.name)

            # Add data from analyzers:
            for category, analyzer in self.analyzer.items():
                series[category] = int(
                    result.analysis.get_analyzer(analyzer).total)

            # Add primary energy:
            pe = result.scenario.Scenario.calculate_primary_factor_and_energy(
                result.analysis.param_results,
                result.analysis.get_analyzer(an.NodeBalanceAnalyzer)
            )

            df = df.append(series)
        return df.transpose()
