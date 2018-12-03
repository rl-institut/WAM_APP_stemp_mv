from abc import ABC

import pandas
from oemof.solph import analyzer as an

from stemp.results import analyzer


class Aggregation(ABC):
    name = 'Aggregation'
    analyzer = None

    @classmethod
    def _get_data(cls, result):
        data = result.analysis.get_analyzer(cls.analyzer).result
        return cls._set_label(data, result)

    @classmethod
    def _set_label(cls, data, result):
        scenario = result.scenario.module.Scenario
        return {
            scenario.get_data_label(k): v
            for k, v in data.items()
            if not isinstance(k, str)
        }

    @classmethod
    def aggregate(cls, results):
        series = pandas.DataFrame(
            {
                result.scenario.name: cls._get_data(result)
                for result in results
            }
        )
        series.name = cls.name
        finalized = cls._finalize_data(series)
        return finalized

    @staticmethod
    def _finalize_data(data):
        return data.transpose()


class LCOEAggregation(Aggregation):
    name = 'LCOE'
    analyzer = analyzer.LCOEAutomatedDemandAnalyzer

    @classmethod
    def _get_data(cls, result):
        data = result.analysis.get_analyzer(cls.analyzer).result
        filtered_data = {}
        for k, v in data.items():
            new_label = result.scenario.module.Scenario.get_data_label(k)
            if abs(v.investment) > 0.001:
                filtered_data[new_label + ' (Investment)'] = v.investment
            if abs(v.variable_costs) > 0.001:
                filtered_data[
                    new_label + cls._get_suffix(k, result)
                    ] = v.variable_costs
        return filtered_data

    @staticmethod
    def _get_suffix(nodes, result):
        if isinstance(nodes, str):
            return nodes
        else:
            return result.scenario.module.Scenario.get_data_label(
                nodes, suffix=True)


class TotalDemandAggregation(Aggregation):
    name = 'Wärmeverbrauch'
    analyzer = an.SequenceFlowSumAnalyzer

    @classmethod
    def _get_data(cls, result):
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

    @classmethod
    def _get_data(cls, result):
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
    analyzer = analyzer.TotalInvestmentAnalyzer


class CO2Aggregation(Aggregation):
    name = 'CO2'
    analyzer = analyzer.CO2Analyzer
