
import pandas
import logging
from django.core.exceptions import AppRegistryNotReady

from oemof.solph import (
    EnergySystem, Bus, Flow, Sink
)

from stemp.constants import DemandType
try:
    from stemp.models import District, Household
except AppRegistryNotReady:
    logging.warning(
        'Could not find django models. '
        'Maybe you have to start django application first.'
    )


NEEDED_PARAMETERS = {
    'General': ['net_costs', 'wacc'],
    'demand': ['index', 'type']
}


def add_basic_energysystem(periods):
    # initialize energy system
    energysystem = EnergySystem(
        timeindex=pandas.date_range('2016-01-01', periods=periods, freq='H')
    )
    return energysystem


def add_subgrid_and_demands(
        customer,
        energysystem: EnergySystem,
        parameters: dict
):
    # Add subgrid busses
    sub_b_th = Bus(label="b_{}_th".format(customer.name))
    energysystem.add(sub_b_th)

    # Add heat demand
    demand_th = Sink(
        label="demand_{}_th".format(customer.name),
        inputs={
            sub_b_th: Flow(
                nominal_value=1,
                actual_value=customer.annual_heat_demand().div(1e6),
                fixed=True
            )
        }
    )
    energysystem.add(demand_th)

    # Add safety excess:
    ex_th = Sink(
        label="excess_{}_th".format(customer.name),
        inputs={sub_b_th: Flow()}
    )
    energysystem.add(ex_th)


def add_households(
        energysystem, technology_fct, parameters, timeseries=None
):
    """
    Whole district as one, separate or single households are added to es
    """
    def add_household(customer):
        add_subgrid_and_demands(customer, energysystem, parameters)
        technology_fct(customer.name, energysystem, timeseries, parameters)

    # Init parameters:
    customer_index = parameters['demand']['index']
    customer_case = parameters['demand']['type']

    if customer_case == DemandType.Single:
        household = Household.objects.get(id=customer_index)
        add_household(household)
    elif customer_case == DemandType.District:
        district = District.objects.get(id=customer_index)
        add_household(district)
    else:
        raise ValueError('Unknown customer case "' + customer_case + '"')
