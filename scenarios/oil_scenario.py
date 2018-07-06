
from copy import deepcopy
import sqlahelper
import transaction

from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.oep_models import OEPScenario
from stemp.scenarios import basic_setup


SCENARIO = 'oil_scenario'
SHORT_NAME = 'Oil'
NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS[SHORT_NAME] = [
    'oil_lifetime', 'oil_capex', 'oil_efficiency'
]


def upload_scenario_parameters():
    session = sqlahelper.get_session()
    if session.query(OEPScenario).filter_by(scenario=SCENARIO).first() is None:
        parameters = [
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
                'parameter': 'net_costs',
                'value_type': 'float',
                'value': '0.27',
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
                'parameter': 'efficiency',
                'value_type': 'float',
                'value': '0.6',
                'unit': '%'
            }
        ]
        scenarios = [OEPScenario(**param) for param in parameters]
        session.add_all(scenarios)
        transaction.commit()


def create_energysystem(periods=2, **parameters):

    energysystem = basic_setup.add_basic_energysystem(periods)

    # Create oil bus
    b_oil = Bus(label="b_oil", balanced=False)
    energysystem.add(b_oil)

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_oil_technology,
        parameters
    )

    return energysystem


def add_oil_technology(label, energysystem, timeseries, parameters):
    # Get investment parameters:
    wacc = parameters['General']['wacc']
    capex = parameters[SHORT_NAME]['oil_capex']
    lifetime = parameters[SHORT_NAME]['oil_lifetime']
    epc = annuity(capex, lifetime, wacc)

    # Get subgrid busses:
    sub_b_th = energysystem.groups["b_{}_th".format(label)]
    oil_heating = Transformer(
        label='{}_oil_heating'.format(label),
        inputs={energysystem.groups['b_oil']: Flow(
            investment=Investment(ep_costs=epc))},
        outputs={sub_b_th: Flow()},
        conversion_factors={sub_b_th: parameters[SHORT_NAME]['oil_efficiency']}
    )
    energysystem.add(oil_heating)
