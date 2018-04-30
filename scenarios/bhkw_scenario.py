
from oemof.solph import Flow, Bus, Investment
from oemof.solph.components import ExtractionTurbineCHP
from oemof.tools.economics import annuity

from stemp.oep_models import OEPScenario
from stemp.scenarios import basic_setup


SCENARIO = 'bhkw_scenario'
SHORT_NAME = 'BHKW'
NEEDED_PARAMETERS = basic_setup.NEEDED_PARAMETERS
NEEDED_PARAMETERS[SHORT_NAME] = [
    'invest', 'conversion_factor_el', 'conversion_factor_th',
    'full_condensation_factor_el'
]


def upload_scenario_parameters():
    if len(OEPScenario.select(where='scenario=' + SCENARIO)) == 0:
        parameters = {
            'query': [
                {
                    'scenario': SCENARIO,
                    'component': 'General',
                    'parameter_type': 'cost',
                    'parameter': 'net_costs',
                    'value_type': 'float',
                    'value': '0.27'
                },
                {
                    'scenario': SCENARIO,
                    'component': 'General',
                    'parameter_type': 'cost',
                    'parameter': 'wacc',
                    'value_type': 'float',
                    'value': '0.05'
                },
                {
                    'scenario': SCENARIO,
                    'component': SHORT_NAME,
                    'parameter_type': 'cost',
                    'parameter': 'invest',
                    'value_type': 'float',
                    'value': '1200'
                },
                {
                    'scenario': SCENARIO,
                    'component': SHORT_NAME,
                    'parameter_type': 'cost',
                    'parameter': 'lifetime',
                    'value_type': 'integer',
                    'value': '20'
                },
                {
                    'scenario': SCENARIO,
                    'component': SHORT_NAME,
                    'parameter_type': 'tech',
                    'parameter': 'conversion_factor_el',
                    'value_type': 'float',
                    'value': '0.5'
                },
                {
                    'scenario': SCENARIO,
                    'component': SHORT_NAME,
                    'parameter_type': 'tech',
                    'parameter': 'conversion_factor_th',
                    'value_type': 'float',
                    'value': '0.3'
                },
                {
                    'scenario': SCENARIO,
                    'component': SHORT_NAME,
                    'parameter_type': 'tech',
                    'parameter': 'full_condensation_factor_el',
                    'value_type': 'float',
                    'value': '0.5'
                }
            ]
        }
        OEPScenario.insert(parameters)


def create_energysystem(periods=2, **parameters):
    energysystem = basic_setup.add_basic_energysystem(periods)

    # Create oil bus
    b_gas = Bus(label="b_gas", balanced=False)
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
    sub_b_el = energysystem.groups["b_{}_el".format(label)]
    sub_b_th = energysystem.groups["b_{}_th".format(label)]

    capex = parameters[SHORT_NAME]['invest']
    lifetime = parameters[SHORT_NAME]['lifetime']
    wacc = parameters['General']['wacc']
    epc = annuity(capex, lifetime, wacc)

    chp = ExtractionTurbineCHP(
        label='{}_chp'.format(label),
        inputs={energysystem.groups['b_gas']: Flow(
            investment=Investment(ep_costs=epc))},
        outputs={sub_b_el: Flow(), sub_b_th: Flow()},
        conversion_factors={
            sub_b_el: parameters[SHORT_NAME]['conversion_factor_el'],
            sub_b_th: parameters[SHORT_NAME]['conversion_factor_th']
        },
        conversion_factor_full_condensation={
            sub_b_el: parameters[SHORT_NAME]['full_condensation_factor_el']}
    )
    energysystem.add(chp)
