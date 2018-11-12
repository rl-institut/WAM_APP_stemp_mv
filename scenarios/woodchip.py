
from copy import deepcopy

from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


SHORT_NAME = 'Woodchip'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS['General'].append('woodchip_price')
NEEDED_PARAMETERS[SHORT_NAME] = [
    'lifetime', 'capex', 'opex', 'efficiency', 'co2_emissions'
]


def create_energysystem(**parameters):

    energysystem = basic_setup.add_basic_energysystem()

    # Create woodchip bus
    b_woodchip = Bus(
        label=AdvancedLabel("b_woodchip", type='Bus'), balanced=False)
    energysystem.add(b_woodchip)

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_woodchip_technology,
        parameters
    )

    return energysystem


def add_woodchip_technology(demand, energysystem, timeseries, parameters):
    # Get investment parameters:
    wacc = parameters['General']['wacc'] / 100
    capex = parameters[SHORT_NAME]['capex']
    lifetime = parameters[SHORT_NAME]['lifetime']
    epc = annuity(capex, lifetime, wacc)

    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{demand.name}_th")
    b_woodchip = basic_setup.find_element_in_groups(energysystem, "b_woodchip")
    invest = Investment(ep_costs=epc)
    invest.capex = capex
    woodchip_heating = Transformer(
        label=AdvancedLabel(
            f'{demand.name}_woodchip_heating',
            type='Transformer'
        ),
        inputs={
            b_woodchip: Flow(
                variable_costs=parameters['General']['woodchip_price'],
                investment=invest,
                co2_emissions=parameters[SHORT_NAME]['co2_emissions']
            )
        },
        outputs={
            sub_b_th: Flow(variable_costs=parameters[SHORT_NAME]['opex'])},
        conversion_factors={
            sub_b_th: parameters[SHORT_NAME]['efficiency'] / 100}
    )
    energysystem.add(woodchip_heating)


def add_dynamic_parameters(scenario, parameters):
    return
