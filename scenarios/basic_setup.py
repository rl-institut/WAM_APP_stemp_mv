
import sqlahelper
import transaction
import pandas
import logging
from collections import namedtuple
from abc import ABC, abstractmethod

from oemof.solph import (
    EnergySystem, Bus, Flow, Sink
)

from stemp import app_settings
from stemp import constants
from stemp.oep_models import OEPScenario
from stemp.models import District, Household


AdvancedLabel = namedtuple(
    'AdvancedLabel', ('name', 'type', 'tags'))
AdvancedLabel.__new__.__defaults__ = (None,)

pe = namedtuple('PrimaryEnergy', ('energy', 'factor'))


def upload_scenario_parameters():
    session = sqlahelper.get_session()
    for sc_parameters in app_settings.SCENARIO_PARAMETERS.values():
        for sc_setup in sc_parameters['SETUPS']:
            if session.query(OEPScenario).filter_by(
                    scenario=sc_setup).first() is None:
                scenarios = [
                    OEPScenario(
                        scenario=sc_setup,
                        component=com,
                        parameter=parameter_name,
                        **parameter_data
                    )
                    for com, parameters in sc_parameters[
                        'SETUPS'][sc_setup].items()
                    for parameter_name, parameter_data in parameters.items()
                ]
                with transaction.manager:
                    session.add_all(scenarios)
                logging.info(f'Scenario upload: {sc_setup} done.')


class BaseScenario(ABC):
    needed_parameters = {
        'General': ['wacc'],
        'demand': ['index', 'type']
    }

    def __init__(self, **parameters):
        self.energysystem = None
        self.sub_b_th = None
        self.demand_th = None
        self.create_energysystem(**parameters)

    def create_energysystem(self, **parameters):
        # initialize energy system
        self.energysystem = EnergySystem(
            timeindex=pandas.date_range(
                '2016-01-01', periods=app_settings.DEFAULT_PERIODS, freq='H'),
        )

    def add_subgrid_and_demands(self, customer):
        # Add subgrid busses
        self.sub_b_th = Bus(
            label=AdvancedLabel(
                f"b_demand_th",
                type='Bus',
            )
        )
        self.energysystem.add(self.sub_b_th)

        # Add heat demand
        self.demand_th = Sink(
            label=AdvancedLabel(
                f"demand_th",
                type='Sink',
                tags=('demand', )
            ),
            inputs={
                self.sub_b_th: Flow(
                    nominal_value=1,
                    actual_value=customer.annual_total_demand(),
                    fixed=True
                )
            }
        )

        # Add safety excess:
        ex_th = Sink(
            label=AdvancedLabel(
                f"excess_th",
                type='Sink',
            ),
            inputs={self.sub_b_th: Flow()}
        )
        self.energysystem.add(self.demand_th, ex_th)

    def add_households(self, parameters, timeseries=None):
        """
        Whole district as one, separate or single households are added to es
        """
        demand = self.get_demand(
            parameters['demand']['type'],
            parameters['demand']['index']
        )
        self.add_subgrid_and_demands(demand)
        self.add_technology(demand, timeseries, parameters)

    @classmethod
    def add_dynamic_parameters(cls, scenario, parameters):
        return parameters

    @abstractmethod
    def add_technology(self, demand, timeseries, parameters):
        pass

    @staticmethod
    def average_cost_per_year(start, years, rate):
        cost = 0.0
        for year in range(years):
            cost += (start * (1 + rate / 100.0) ** (year - 1))
        return cost / years

    @staticmethod
    def get_demand(demand_type, demand_id):
        if demand_type == constants.DemandType.Single:
            return Household.objects.get(id=demand_id)
        elif demand_type == constants.DemandType.District:
            return District.objects.get(id=demand_id)
        else:
            raise ValueError('Unknown customer case "' + demand_type + '"')

    @classmethod
    @abstractmethod
    def get_data_label(cls, nodes):
        return '-'.join(map(str, nodes))

    @classmethod
    @abstractmethod
    def calculate_primary_factor_and_energy(cls, param_results, results):
        return pe(None, None)


class PrimaryInputScenario(BaseScenario):
    """
    Scenario where one primary source provides demand
    """

    @abstractmethod
    def add_technology(self, demand, timeseries, parameters):
        pass

    @classmethod
    def calculate_primary_factor_and_energy(cls, param_results, node_results):
        # Find primary source & demand:
        primary_source_node = next(filter(
            lambda x: x.tags is not None and 'primary_source' in x.tags,
            node_results.result
        ))
        demand_node = next(filter(
            lambda x: x.tags is not None and 'demand' in x.tags,
            node_results.result
        ))

        # Get primary factor:
        pf_primary = param_results[
            (primary_source_node, None)]['scalars']['pf']
        pf_net = param_results[
            (primary_source_node, None)]['scalars']['pf_net']
        pf = pf_primary + 0.1 * pf_net
        # Get demand:
        demand = sum(node_results.result[demand_node]['input'].values())

        return pe(energy=demand * pf, factor=pf)
