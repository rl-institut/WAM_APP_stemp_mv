from abc import ABC

import pandas
from oemof.solph import analyzer as an

from stemp.results import analyzer


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

    @classmethod
    def _get_data(cls, result):
        data = result.analysis.get_analyzer(cls.analyzer).result
        return cls._set_label(data)

    @classmethod
    def _set_label(cls, data):
        return {
            cls._get_label(k): v
            for k, v in data.items()
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
            new_label = cls._get_label(k)
            if abs(v.investment) > 0.001:
                filtered_data[new_label + ' (Investment)'] = v.investment
            if abs(v.variable_costs) > 0.001:
                filtered_data[
                    new_label + cls._get_suffix(k)
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