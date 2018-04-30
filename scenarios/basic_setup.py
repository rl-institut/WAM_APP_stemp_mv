
import pandas
import logging
from enum import Enum
from django.core.exceptions import AppRegistryNotReady

from oemof.solph import (
    EnergySystem, Bus, Flow, Sink, Transformer, Source
)

try:
    from stemp.models import District, Household
except AppRegistryNotReady:
    logging.warning(
        'Could not find django models. '
        'Maybe you have to start django application first.'
    )


NEEDED_PARAMETERS = {
    'General': [
        'net_costs', 'wacc'
    ]
}


class CustomerOption(str, Enum):
    Single = 'single'
    District = 'district'


def add_basic_energysystem(periods):
    # initialize energy system
    energysystem = EnergySystem(
        timeindex=pandas.date_range('2016-01-01', periods=periods, freq='H')
    )

    # BUSSES
    b_el_net = Bus(label="b_el_net")
    energysystem.add(b_el_net)

    # add excess sink to help avoid infeasible problems
    ex_el = Sink(
        label="excess_el",
        inputs={b_el_net: Flow()}
    )
    s_el = Source(
        label="shortage_el",
        outputs={b_el_net: Flow(variable_costs=1000)},
    )
    energysystem.add(ex_el, s_el)
    return energysystem


def add_subgrid_and_demands(
        customer,
        energysystem: EnergySystem,
        parameters: dict
):
    # Add subgrid busses
    sub_b_el = Bus(label="b_{}_el".format(customer.name))
    sub_b_th = Bus(label="b_{}_th".format(customer.name))
    energysystem.add(sub_b_el, sub_b_th)

    # Connect electrical net to subgrid:
    t_el = Transformer(
        label='transformer_to_{}_el'.format(customer.name),
        inputs={
            energysystem.groups['b_el_net']: Flow(
                variable_costs=parameters['General']['net_costs']
            )
        },
        outputs={sub_b_el: Flow()},
    )
    energysystem.add(t_el)

    # Add electricity demand
    demand_el = Sink(
        label="demand_{}_el".format(customer.name),
        inputs={
            sub_b_el: Flow(
                nominal_value=1,
                actual_value=customer.annual_load_demand().div(1e6),
                fixed=True
            )
        }
    )
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
    energysystem.add(demand_el, demand_th)

    # Add safety excess:
    ex_el = Sink(
        label="excess_{}_el".format(customer.name),
        inputs={sub_b_el: Flow()}
    )
    ex_th = Sink(
        label="excess_{}_th".format(customer.name),
        inputs={sub_b_th: Flow()}
    )
    energysystem.add(ex_el, ex_th)


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
    customer_index = parameters.get('customer_index', 0)
    customer_case = parameters.get('customer_case', CustomerOption.District)

    if customer_case == CustomerOption.Single:
        household = Household.objects.get(id=customer_index)
        add_household(household)
    else:
        district = District.objects.get(id=customer_index)
        if customer_case == CustomerOption.Separate:
            for household in district.household_set.all():
                add_household(household)
        elif customer_case == CustomerOption.District:
            add_household(district)
        else:
            raise ValueError('Unknown customer case "' + customer_case + '"')
