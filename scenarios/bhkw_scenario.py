
from copy import deepcopy

from oemof.solph import Flow, Bus, Investment, Transformer
from oemof.solph.components import ExtractionTurbineCHP
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


SHORT_NAME = 'BHKW'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS[SHORT_NAME] = [
    'capex', 'lifetime', 'conversion_factor_el', 'conversion_factor_th',
    'full_condensation_factor_el', 'co2_emissions'
]
NEEDED_PARAMETERS['General'].extend(['gas_price', 'bhkw_feedin_tariff'])

BHKW_SIZE_PEAK_FACTOR = 3.33


def create_energysystem(periods=8760, **parameters):
    energysystem = basic_setup.add_basic_energysystem(periods)

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


def add_bhkw_technology(label, energysystem, timeseries, parameters):
    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{label}_th")
    b_gas = basic_setup.find_element_in_groups(
        energysystem, "b_gas")

    # Add bus from bhkw to net:
    b_bhkw_el = Bus(label=AdvancedLabel('b_bhkw_el', type='Bus'))
    b_net_el = Bus(label=AdvancedLabel('b_net_el', type='Bus'), balanced=False)

    # Add transformer to feed in bhkw_el to net:
    t_bhkw_net = Transformer(
        label=AdvancedLabel(
            f'transformer_from_{label}_el',
            type='Transformer',
            belongs_to=label
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
    wacc = parameters['General']['wacc']
    epc = annuity(capex, lifetime, wacc)
    invest = Investment(ep_costs=epc)
    invest.capex = capex

    chp = ExtractionTurbineCHP(
        label=AdvancedLabel(
            f'{label}_chp', type='Transformer', belongs_to=label),
        inputs={
            b_gas: Flow(
                variable_costs=parameters['General']['gas_price'],
                investment=invest
            )
        },
        outputs={b_bhkw_el: Flow(), sub_b_th: Flow()},
        conversion_factors={
            b_bhkw_el: parameters[SHORT_NAME]['conversion_factor_el'],
            sub_b_th: parameters[SHORT_NAME]['conversion_factor_th']
        },
        conversion_factor_full_condensation={
            b_bhkw_el: parameters[SHORT_NAME]['full_condensation_factor_el']}
    )
    chp.co2_emissions = parameters[SHORT_NAME]['co2_emissions']
    energysystem.add(chp)


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
        capex = 460.89 * bhkw_size ** -0.015 * 1e3
    else:
        raise IndexError(f'No BHKW-capex found for size {bhkw_size}kW')

    # Get eff:
    if bhkw_size < 1:
        raise IndexError(f'No BHKW-efficiency found for size {bhkw_size}kW')
    elif 1 <= bhkw_size < 10:
        eff = 21.794 * bhkw_size ** 0.108 / 100
    elif 10 <= bhkw_size < 100:
        eff = 22.56 * bhkw_size ** 0.1032 / 100
    elif 100 <= bhkw_size < 1000:
        eff = 25.416 * bhkw_size ** 0.0732 / 100
    elif 1000 <= bhkw_size < 19000:
        eff = 29.627 * bhkw_size ** 0.0498 / 100
    else:
        eff = 29.627 / 100

    parameters[SHORT_NAME]['capex'] = (
        parameters[SHORT_NAME]['capex'].new_child({'value': str(capex)}))
    parameters[SHORT_NAME]['conversion_factor_el'] = (
        parameters[SHORT_NAME]['conversion_factor_el'].new_child(
            {'value': str(eff)}
        )
    )
