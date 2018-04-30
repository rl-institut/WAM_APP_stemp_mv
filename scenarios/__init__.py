
import os
import pandas
from importlib import import_module
import logging
from configobj import ConfigObj

from oemof.solph import Model
from oemof import outputlib
from oemof.tools import helpers

try:
    from kopy.settings import BASE_DIR
except KeyError:
    logging.warning(
        'Could not find kopy settings. '
        'Maybe you have to start django application first.'
    )


SCENARIO_PATH = 'stemp.scenarios'
import_module(SCENARIO_PATH)
EXCLUDED_PATHS = ('__init__.py',)
CREATE_ENERGYSYSTEM_FCT = 'create_energysystem'
NEEDED_PARAMETERS = 'NEEDED_PARAMETERS'
SIMULATE_FCT = 'simulate'


def get_scenarios():
    def scenarios_in_path(current_folder):
        path = os.path.join(BASE_DIR, current_folder)
        nonlocal scenarios
        scenarios += [
            os.path.join(current_folder, filename.split('.')[0])
            for filename in os.listdir(path)
            if filename not in EXCLUDED_PATHS and filename.endswith('.py')
        ]
        subfolders = [
            os.path.join(current_folder, subfolder)
            for subfolder in os.listdir(path)
            if os.path.isdir(os.path.join(path, subfolder))
        ]
        for subfolder in subfolders:
            scenarios_in_path(subfolder)

    scenarios = []
    scenarios_in_path(SCENARIO_PATH)
    return scenarios


def get_scenario_config(scenario):
    if scenario is None:
        return None
    config_path = os.path.join(BASE_DIR, scenario + '.cfg')
    return ConfigObj(config_path)


def import_scenario(filename):
    splitted = filename.split(os.path.sep)
    module_name = '.'.join(splitted[1:])
    return import_module('.' + module_name, package=splitted[0])


def create_energysystem(scenario_module, **parameters):
    # Check if all needed parameters are given:
    needed = getattr(
        scenario_module,
        NEEDED_PARAMETERS
    )
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
    create = getattr(
        scenario_module,
        CREATE_ENERGYSYSTEM_FCT
    )
    return create(**parameters)


def get_param_results(energysystem):
    om = Model(energysystem)
    return outputlib.processing.param_results(om, keys_as_str=True)


def get_simulation_function(scenario_module):
    simulate_fct = getattr(
        scenario_module,
        SIMULATE_FCT,
        default_simulate_fct
    )
    return simulate_fct


def default_simulate_fct(
        energysystem, solver='cbc', debug=False, tee_switch=True,
        keep=True):
    # create Optimization model based on energy_system
    logging.info("Create optimization problem")
    om = Model(energysystem=energysystem)

    # if debug is true an lp-file will be written
    if debug:
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), 'storage_invest.lp')
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

    return (
        outputlib.processing.results(om),
        outputlib.processing.param_results(
            om, exclude_none=True, keys_as_str=True)
    )


def get_results(energysystem):
    """Shows how to extract single time series from DataFrame.

    Parameters
    ----------
    energysystem : solph.EnergySystem

    Returns
    -------
    dict : Some results.
    """
    logging.info('Check the results')

    myresults = outputlib.DataFramePlot(energy_system=energysystem)
    print(list(myresults))

    # Create output csv:
    output_meta = (
        ('load', 'b_el', 'from_bus', 'demand_el'),
        ('dg', 'b_el', 'to_bus', 'pp_oil'),
        ('pv', 'b_el', 'to_bus', 'pv'),
        ('excess', 'b_el', 'from_bus', 'excess'),
        ('batt discharge', 'b_el', 'to_bus', 'storage'),
        ('batt charge', 'b_el', 'from_bus', 'storage'),
        ('batt capacity', 'b_el', 'other', 'storage'),
    )
    data = pandas.DataFrame()
    for column, bus, direction, component in output_meta:
        data[column] = myresults.loc[(bus, direction, component)].iloc[:, 0]
    data.to_csv('output.csv')

    grouped = myresults.groupby(level=[0, 1, 2]).sum()
    rdict = {r + (k,): v
             for r, kv in grouped.iterrows()
             for k, v in kv.to_dict().items()}

    rdict['objective'] = energysystem.results.objective

    return rdict
