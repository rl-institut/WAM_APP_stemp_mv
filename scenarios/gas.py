
from copy import deepcopy

from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


SHORT_NAME = 'Gas'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS['General'].append('gas_price')
NEEDED_PARAMETERS[SHORT_NAME] = [
    'lifetime', 'capex', 'opex', 'efficiency', 'co2_emissions'
]


def create_energysystem(**parameters):

    energysystem = basic_setup.add_basic_energysystem()

    # Create oil bus
    b_gas = Bus(label=AdvancedLabel("b_gas", type='Bus'), balanced=False)
    energysystem.add(b_gas)

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_gas_technology,
        parameters
    )

    return energysystem


def add_gas_technology(label, energysystem, timeseries, parameters):
    # Get investment parameters:
    wacc = parameters['General']['wacc'] / 100
    capex = parameters[SHORT_NAME]['capex']
    lifetime = parameters[SHORT_NAME]['lifetime']
    epc = annuity(capex, lifetime, wacc)

    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{label}_th")
    b_gas = basic_setup.find_element_in_groups(energysystem, "b_gas")
    invest = Investment(ep_costs=epc)
    invest.capex = capex
    gas_heating = Transformer(
        label=AdvancedLabel(f'{label}_gas_heating', type='Transformer'),
        inputs={
            b_gas: Flow(
                variable_costs=parameters['General']['gas_price'],
                investment=invest,
                co2_emissions=parameters[SHORT_NAME]['co2_emissions']
            )
        },
        outputs={
            sub_b_th: Flow(variable_costs=parameters[SHORT_NAME]['opex'])},
        conversion_factors={
            sub_b_th: parameters[SHORT_NAME]['efficiency'] / 100}
    )
    energysystem.add(gas_heating)


def add_dynamic_parameters(scenario, parameters):
    return
