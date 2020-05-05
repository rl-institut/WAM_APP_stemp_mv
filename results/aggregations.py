"""Aggregation module is used to compare multiple oemof analysis"""

from abc import ABC
import pandas
from collections import OrderedDict, defaultdict

from oemof.solph import analyzer as an

from stemp.results import analyzer as stemp_an
from stemp.app_settings import SCENARIO_PARAMETERS


class Aggregation(ABC):
    """Baseclass to group and label multiple oemof analyses into one dataframe"""

    name = "Aggregation"
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

    @staticmethod
    def _get_result_label(result):
        scenario_name = SCENARIO_PARAMETERS[result.scenario.Scenario.name.lower()]
        return f"{scenario_name['LABELS']['name']}<br><small>Szenario #{result.result_id}</small>"

    def aggregate(self, results):
        aggregated_data = OrderedDict(
            (self._get_result_label(result), self._get_data(result))
            for result in results
        )
        df = pandas.DataFrame(aggregated_data)
        df.name = self.name
        finalized = self._finalize_data(df)
        return finalized

    def _finalize_data(self, data):
        return data.transpose()


class LCOEAggregation(Aggregation):
    """
    Advanced aggregation to aggregate LCOE results

    Results are distinguished between investment and variable costs.
    Additionally, variable costs are named depending on current scenario.
    """
    name = "LCOE"
    analyzer = stemp_an.LCOEAutomatedDemandAnalyzer

    def _get_data(self, result):
        data = result.analysis.get_analyzer(self.analyzer).result
        filtered_data = defaultdict(float)
        for k, v in data.items():
            if abs(v.investment) > 0.001:
                filtered_data["Investitionskosten"] += v.investment
            if abs(v.variable_costs) > 0.001:
                filtered_data[
                    result.scenario.Scenario.get_data_label(k)
                ] += v.variable_costs
        return filtered_data


class TechnologieComparison(Aggregation):
    """
    Aggregates and compares different scenarios

    Comparison is done for analyzers in "analyzer" attribute.
    Additionally, pros and cons are shown for each scenario.
    """
    name = "Technologievergleich"
    analyzer = OrderedDict(
        [
            ("Wärmekosten", stemp_an.LCOEAutomatedDemandAnalyzer),
            ("Investitionskosten", stemp_an.TotalInvestmentAnalyzer),
            ("CO2 Emissionen", stemp_an.CO2Analyzer),
            ("Brennstoffkosten", stemp_an.FossilCostsAnalyzer),
        ]
    )

    def aggregate(self, results):
        df = pandas.DataFrame()
        for result in results:
            series = pandas.Series(name=self._get_result_label(result))

            # Add data from analyzers:
            for category, analyzer in self.analyzer.items():
                series[category] = result.analysis.get_analyzer(analyzer).total

            # Add primary energy:
            pe = result.scenario.Scenario.calculate_primary_factor_and_energy(
                result.analysis.param_results,
                result.analysis.get_analyzer(an.NodeBalanceAnalyzer),
            )
            series["Primärenergiefaktor"] = pe.factor
            series["Primärenergie"] = pe.energy

            # Add pros and cons:
            labels = SCENARIO_PARAMETERS[result.scenario.Scenario.name.lower()][
                "LABELS"
            ]
            pros = labels.get("pros", [])
            cons = labels.get("cons", [])
            series["Vorteile"] = "<br>".join(
                map(
                    lambda x: f'<i class ="icon ion-thumbsup icon--small"> {x} </i>',
                    pros,
                )
            )
            series["Nachteile"] = "<br>".join(
                map(
                    lambda x: f'<i class ="icon ion-thumbsdown icon--small"> {x} </i>',
                    cons,
                )
            )

            df = df.append(series)

        # Order columns:
        df = df[
            [
                "Wärmekosten",
                "Investitionskosten",
                "Brennstoffkosten",
                "CO2 Emissionen",
                "Primärenergiefaktor",
                "Primärenergie",
                "Vorteile",
                "Nachteile",
            ]
        ]

        return df.transpose()
