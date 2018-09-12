
import sqlahelper
import transaction
import pandas
import logging
from collections import namedtuple
from django.core.exceptions import AppRegistryNotReady

from oemof.solph import (
    EnergySystem, Bus, Flow, Sink
)

from stemp.app_settings import SCENARIO_PARAMETERS
from stemp.constants import DemandType
from stemp.oep_models import OEPScenario
try:
    from stemp.models import District, Household
except AppRegistryNotReady:
    logging.warning(
        'Could not find django models. '
        'Maybe you have to start django application first.'
    )


NEEDED_PARAMETERS = {
    'General': ['wacc'],
    'demand': ['index', 'type']
}

AdvancedLabel = namedtuple(
    'AdvancedLabel', ('name', 'type', 'belongs_to', 'tags'))
AdvancedLabel.__new__.__defaults__ = (None, None)


def upload_scenario_parameters():
    session = sqlahelper.get_session()
    for sc in SCENARIO_PARAMETERS:
        if session.query(OEPScenario).filter_by(
                scenario=sc).first() is None:
            scenarios = [
                OEPScenario(
                    scenario=sc,
                    component=component,
                    parameter=parameter_name,
                    **parameter_data
                )
                for component, parameters in SCENARIO_PARAMETERS[sc].items()
                for parameter_name, parameter_data in parameters.items()
            ]
            session.add_all(scenarios)
            transaction.commit()


def find_element_in_groups(energysystem, label):
    try:
        return next(v for k, v in energysystem.groups.items() if label in k)
    except StopIteration:
        raise KeyError(f'Could not find element containing {label} in label')


def add_basic_energysystem(periods, **kwargs):
    # initialize energy system
    energysystem = EnergySystem(
        timeindex=pandas.date_range('2016-01-01', periods=periods, freq='H'),
        ** kwargs
    )
    return energysystem


def add_subgrid_and_demands(
        customer,
        energysystem: EnergySystem,
        parameters: dict
):
    # Add subgrid busses
    sub_b_th = Bus(
        label=AdvancedLabel(
            f"b_{customer.name}_th",
            type='Bus',
            belongs_to=customer.name,
        )
    )
    energysystem.add(sub_b_th)

    # Add heat demand
    demand_th = Sink(
        label=AdvancedLabel(
            f"demand_{customer.name}_th",
            type='Sink',
            belongs_to=customer.name,
            tags=('demand', )
        ),
        inputs={
            sub_b_th: Flow(
                nominal_value=1,
                actual_value=customer.annual_heat_demand(),
                fixed=True
            )
        }
    )
    energysystem.add(demand_th)

    # Add safety excess:
    ex_th = Sink(
        label=AdvancedLabel(
            f"excess_{customer.name}_th",
            type='Sink',
            belongs_to=customer.name
        ),
        inputs={sub_b_th: Flow()}
    )
    energysystem.add(ex_th)


def get_demand(demand_type, demand_id):
    if demand_type == DemandType.Single:
        return Household.objects.get(id=demand_id)
    elif demand_type == DemandType.District:
        return District.objects.get(id=demand_id)
    else:
        raise ValueError('Unknown customer case "' + demand_type + '"')


def add_households(
        energysystem, technology_fct, parameters, timeseries=None
):
    """
    Whole district as one, separate or single households are added to es
    """
    demand = get_demand(
        parameters['demand']['type'],
        parameters['demand']['index']
    )
    add_subgrid_and_demands(demand, energysystem, parameters)
    technology_fct(demand.name, energysystem, timeseries, parameters)
