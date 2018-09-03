
from copy import deepcopy
import sqlahelper
import transaction

from oemof.solph import Flow, Bus, Investment, Transformer
from oemof.solph.components import ExtractionTurbineCHP
from oemof.tools.economics import annuity

from stemp.oep_models import OEPScenario
from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


SCENARIO = 'bhkw_scenario'
SHORT_NAME = 'BHKW'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS[SHORT_NAME] = [
    'capex', 'lifetime', 'conversion_factor_el', 'conversion_factor_th',
    'full_condensation_factor_el'
]
NEEDED_PARAMETERS['General'].append('bhkw_feedin_tariff')


def upload_scenario_parameters():
    session = sqlahelper.get_session()
    if session.query(OEPScenario).filter_by(scenario=SCENARIO).first() is None:
        parameters = [
            {
                'scenario': SCENARIO,
                'component': 'General',
                'parameter_type': 'costs',
                'parameter': 'net_costs',
                'value_type': 'float',
                'value': '0.27',
                'unit': '€'
            },
            {
                'scenario': SCENARIO,
                'component': 'General',
                'parameter_type': 'costs',
                'parameter': 'wacc',
                'value_type': 'float',
                'value': '0.05',
                'unit': '%'
            },
            {
                'scenario': SCENARIO,
                'component': 'General',
                'parameter_type': 'costs',
                'parameter': 'bhkw_feedin_tariff',
                'value_type': 'float',
                'value': '-0.08',
                'unit': '€'
            },
            {
                'scenario': SCENARIO,
                'component': SHORT_NAME,
                'parameter_type': 'costs',
                'parameter': 'capex',
                'value_type': 'float',
                'value': '1200',
                'unit': '€'
            },
            {
                'scenario': SCENARIO,
                'component': SHORT_NAME,
                'parameter_type': 'costs',
                'parameter': 'lifetime',
                'value_type': 'integer',
                'value': '20',
                'unit': 'Jahre'
            },
            {
                'scenario': SCENARIO,
                'component': SHORT_NAME,
                'parameter_type': 'technologies',
                'parameter': 'conversion_factor_el',
                'value_type': 'float',
                'value': '0.5',
                'unit': '%'
            },
            {
                'scenario': SCENARIO,
                'component': SHORT_NAME,
                'parameter_type': 'technologies',
                'parameter': 'conversion_factor_th',
                'value_type': 'float',
                'value': '0.3',
                'unit': '%'
            },
            {
                'scenario': SCENARIO,
                'component': SHORT_NAME,
                'parameter_type': 'technologies',
                'parameter': 'full_condensation_factor_el',
                'value_type': 'float',
                'value': '0.5',
                'unit': '%'
            }
        ]
        scenarios = [OEPScenario(**param) for param in parameters]
        session.add_all(scenarios)
        transaction.commit()


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
    b_net_el = Bus(label=AdvancedLabel('b_net_el', type='Bus'))

    # Add transformer to feed in bhkw_el to net:
    t_bhkw_net = Transformer(
        label=AdvancedLabel(
            f'transformer_from_{label}_el',
            type='Transformer',
            belongs_to=label
        ),
        inputs={
            b_bhkw_el: Flow(
                variable_costs=parameters['General']['bhkw_feedin_tariff']
            )
        },
        outputs={b_net_el: Flow()},
    )
    energysystem.add(b_bhkw_el, b_net_el, t_bhkw_net)

    capex = parameters[SHORT_NAME]['capex']
    lifetime = parameters[SHORT_NAME]['lifetime']
    wacc = parameters['General']['wacc']
    epc = annuity(capex, lifetime, wacc)

    chp = ExtractionTurbineCHP(
        label=AdvancedLabel(
            f'{label}_chp', type='Transformer', belongs_to=label),
        inputs={b_gas: Flow(
            investment=Investment(ep_costs=epc))},
        outputs={b_bhkw_el: Flow(), sub_b_th: Flow()},
        conversion_factors={
            b_bhkw_el: parameters[SHORT_NAME]['conversion_factor_el'],
            sub_b_th: parameters[SHORT_NAME]['conversion_factor_th']
        },
        conversion_factor_full_condensation={
            b_bhkw_el: parameters[SHORT_NAME]['full_condensation_factor_el']}
    )
    energysystem.add(chp)
