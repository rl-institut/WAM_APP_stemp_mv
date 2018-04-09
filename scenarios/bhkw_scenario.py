
from oemof.solph import Flow, Bus
from oemof.solph.components import ExtractionTurbineCHP

# Load django settings if run locally:
if __name__ == '__main__':
    import os
    from django.core.wsgi import get_wsgi_application

    os.environ['DJANGO_SETTINGS_MODULE'] = 'kopy.settings'
    application = get_wsgi_application()


from stemp.models import OEPScenario
from stemp.scenarios import basic_setup


SCENARIO = 'bhkw_scenario'
NEEDED_PARAMETERS = {
    'General': (
        'net_costs',
    )
}


def upload_scenario_parameters():
    if len(OEPScenario.select(where='scenario=' + SCENARIO)) == 0:
        parameters = {
            'query': [
                {
                    'scenario': SCENARIO,
                    'component': 'General',
                    'parameter_type': 'various',
                    'parameter': 'net_connection',
                    'value_type': 'boolean',
                    'value': 'True'
                },
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
                    'parameter': 'pv_feedin_tariff',
                    'value_type': 'float',
                    'value': '-0.08'
                },
                {
                    'scenario': SCENARIO,
                    'component': 'BHKW',
                    'parameter_type': 'cost',
                    'parameter': 'invest',
                    'value_type': 'float',
                    'value': '1200'
                },
                {
                    'scenario': SCENARIO,
                    'component': 'BHKW',
                    'parameter_type': 'tech',
                    'parameter': 'efficiency',
                    'value_type': 'float',
                    'value': '0.6'
                }
            ]
        }
        OEPScenario.insert(parameters)


upload_scenario_parameters()


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

    chp = ExtractionTurbineCHP(
        label='{}_chp'.format(label),
        inputs={energysystem.groups['b_gas']: Flow(nominal_value=10e10)},
        outputs={sub_b_el: Flow(), sub_b_th: Flow()},
        conversion_factors={sub_b_el: 0.3, sub_b_th: 0.5},
        conversion_factor_full_condensation={sub_b_el: 0.5}
    )
    energysystem.add(chp)
