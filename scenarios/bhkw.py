
from copy import deepcopy

from oemof.solph import Flow, Bus, Investment, Transformer
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


SHORT_NAME = 'BHKW'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS[SHORT_NAME] = [
    'capex', 'lifetime', 'conversion_factor_el', 'conversion_factor_th',
    'co2_emissions', 'minimal_load'
]
NEEDED_PARAMETERS['General'].extend(
    ['gas_price', 'gas_rate', 'bhkw_feedin_tariff'])

BHKW_SIZE_PEAK_FACTOR = 3.33


def create_energysystem(**parameters):
    energysystem = basic_setup.add_basic_energysystem()

    # Create oil bus
    b_gas = Bus(label=AdvancedLabel("b_gas", type='Bus'), balanced=False)
    energysystem.add(b_gas)

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_bhkw_technology,
        parameters
    )

    return energysystem


def add_bhkw_technology(demand, energysystem, timeseries, parameters):
    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{demand.name}_th")
    b_gas = basic_setup.find_element_in_groups(
        energysystem, "b_gas")

    # Add bus from bhkw to net:
    b_bhkw_el = Bus(label=AdvancedLabel('b_bhkw_el', type='Bus'))
    b_net_el = Bus(label=AdvancedLabel('b_net_el', type='Bus'), balanced=False)

    # Add transformer to feed in bhkw_el to net:
    t_bhkw_net = Transformer(
        label=AdvancedLabel(
            f'transformer_from_{demand.name}_el',
            type='Transformer',
            belongs_to=demand.name
        ),
        inputs={
            b_bhkw_el: Flow(
                variable_costs=-parameters['General']['bhkw_feedin_tariff']
            )
        },
        outputs={b_net_el: Flow()},
    )
    energysystem.add(b_bhkw_el, b_net_el, t_bhkw_net)

    capex = parameters[SHORT_NAME]['capex']
    lifetime = parameters[SHORT_NAME]['lifetime']
    wacc = parameters['General']['wacc'] / 100
    epc = annuity(capex, lifetime, wacc)
    invest = Investment(ep_costs=epc)
    invest.capex = capex
    avg_gas_price = basic_setup.average_cost_per_year(
        parameters['General']['gas_price'],
        lifetime,
        parameters['General']['gas_rate']
    )

    bhkw = Transformer(
        label=AdvancedLabel(
            f'{demand.name}_chp', type='Transformer', belongs_to=demand.name),
        inputs={
            b_gas: Flow(
                variable_costs=avg_gas_price,
                investment=invest,
                min=(
                        parameters[SHORT_NAME]['minimal_load'] /
                        parameters[SHORT_NAME]['conversion_factor_th']
                ),
                co2_emissions=parameters[SHORT_NAME]['co2_emissions']
            )
        },
        outputs={
            b_bhkw_el: Flow(
                co2_emissions=-217.0  # FIXME: MAKE IT A PARAMETER
            ),
            sub_b_th: Flow()
        },
        conversion_factors={
            b_bhkw_el: parameters[SHORT_NAME]['conversion_factor_el'] / 100,
            sub_b_th: parameters[SHORT_NAME]['conversion_factor_th'] / 100
        }
    )
    energysystem.add(bhkw)

    # Additional gas for peak load
    capex = parameters['Gas']['capex']
    lifetime = parameters['Gas']['lifetime']
    epc = annuity(capex, lifetime, wacc)
    invest = Investment(ep_costs=epc)
    invest.capex = capex
    gas_heating = Transformer(
        label=AdvancedLabel(f'{demand.name}_gas_heating', type='Transformer'),
        inputs={
            b_gas: Flow(
                variable_costs=avg_gas_price,
                investment=invest,
                co2_emissions=parameters['Gas']['co2_emissions']
            )
        },
        outputs={
            sub_b_th: Flow(variable_costs=parameters['Gas']['opex'])
        },
        conversion_factors={
            sub_b_th: parameters['Gas']['efficiency'] / 100
        }
    )
    energysystem.add(gas_heating)


def add_dynamic_parameters(scenario, parameters):
    demand = basic_setup.get_demand(
        scenario.session.demand_type,
        scenario.session.demand_id
    )
    max_heat_demand = max(demand.annual_heat_demand())

    # Estimate bhkw size:
    bhkw_size = max_heat_demand * BHKW_SIZE_PEAK_FACTOR

    # Get capex:
    if bhkw_size < 1:
        capex = 9.585 * 1e3
    elif 1 <= bhkw_size < 10:
        capex = 9.585 * bhkw_size ** -0.542 * 1e3
    elif 10 <= bhkw_size < 100:
        capex = 5.438 * bhkw_size ** -0.351 * 1e3
    elif 100 <= bhkw_size < 1000:
        capex = 4.907 * bhkw_size ** -0.352 * 1e3
    elif 1000 <= bhkw_size < 19000:
        capex = 460.89 * bhkw_size ** -0.015
    else:
        raise IndexError(f'No BHKW-capex found for size {bhkw_size}kW')

    # Get eff:
    if bhkw_size < 1:
        raise IndexError(f'No BHKW-efficiency found for size {bhkw_size}kW')
    elif 1 <= bhkw_size < 10:
        eff = 21.794 * bhkw_size ** 0.108
    elif 10 <= bhkw_size < 100:
        eff = 22.56 * bhkw_size ** 0.1032
    elif 100 <= bhkw_size < 1000:
        eff = 25.416 * bhkw_size ** 0.0732
    elif 1000 <= bhkw_size < 19000:
        eff = 29.627 * bhkw_size ** 0.0498
    else:
        eff = 29.627

    parameters[SHORT_NAME]['capex'] = (
        parameters[SHORT_NAME]['capex'].new_child({'value': str(capex)}))
    parameters[SHORT_NAME]['conversion_factor_el'] = (
        parameters[SHORT_NAME]['conversion_factor_el'].new_child(
            {'value': str(int(eff))}
        )
    )
