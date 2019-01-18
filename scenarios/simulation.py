
import os
import logging
from configobj import ConfigObj

from oemof.solph import Model
from oemof import outputlib
from oemof.tools import helpers

try:
    from wam.settings import BASE_DIR
    from stemp.app_settings import STORE_LP_FILE
except KeyError:
    logging.warning(
        'Could not find wam settings. '
        'Maybe you have to start django application first.'
    )

EXCLUDED_PATHS = ('__init__.py',)
CREATE_ENERGYSYSTEM_FCT = 'create_energysystem'
NEEDED_PARAMETERS = 'NEEDED_PARAMETERS'
SIMULATE_FCT = 'simulate'


class SimulationError(Exception):
    pass


def get_scenario_config(scenario):
    if scenario is None:
        return None
    config_path = os.path.join(BASE_DIR, scenario + '.cfg')
    return ConfigObj(config_path)


def create_energysystem(scenario_module, **parameters):
    # Check if all needed parameters are given:
    needed = scenario_module.Scenario.needed_parameters
    missing_components = [key for key in needed if key not in parameters]
    if len(missing_components) > 0:
        raise KeyError(
            'Missing components in parameters for scenario "' +
            scenario_module.__file__ + '": ' +
            ', '.join(missing_components)
        )
    for com in needed:
        missing_keys = [
            key for key in needed[com] if key not in parameters[com]]
        if len(missing_keys) > 0:
            raise KeyError(
                'Missing parameters for component "' +
                com + '" in scenario "' + scenario_module.__file__ + '": ' +
                ', '.join(missing_keys)
            )

    # Create energysystem:
    scenario = scenario_module.Scenario(**parameters)
    return scenario.energysystem


def get_param_results(energysystem):
    om = Model(energysystem)
    return outputlib.processing.convert_keys_to_strings(
        outputlib.processing.param_results(om))


def get_simulation_function(scenario_module):
    simulate_fct = getattr(
        scenario_module,
        SIMULATE_FCT,
        default_simulate_fct
    )
    return simulate_fct


def default_simulate_fct(
        energysystem, solver='cbc', tee_switch=True, keep=True):
    # create Optimization model based on energy_system
    logging.info("Create optimization problem")
    om = Model(energysystem=energysystem)

    # if debug is true an lp-file will be written
    if STORE_LP_FILE:
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), 'kopernikus.lp')
        logging.info('Store lp-file in {0}.'.format(filename))
        om.write(filename, io_options={'symbolic_solver_labels': True})

    # SOLVE:
    # solve with specific optimization options (passed to pyomo)
    logging.info("Solve optimization problem")
    om.solve(
        solver=solver,
        solve_kwargs={'tee': tee_switch, 'keepfiles': keep},
        cmdline_options={
            # 'MaxNodes': 1000,
            'mipgap': 0.005  # Only for Gurobi
        }
    )

    results = outputlib.processing.results(om)
    param_results = outputlib.processing.parameter_as_dict(
            om, exclude_none=True)
    return map(
        outputlib.processing.convert_keys_to_strings,
        (results, param_results)
    )
