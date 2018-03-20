
import os
import pandas
from importlib import import_module
import logging
from configobj import ConfigObj
from collections import namedtuple

from oemof.solph import Model, Source
from oemof.solph.plumbing import sequence, _Sequence
from oemof import outputlib
from oemof.tools import helpers

from kopy.settings import BASE_DIR


SCENARIO_PATH = 'stemp.scenarios'
import_module(SCENARIO_PATH)
EXCLUDED_PATHS = ('__init__.py',)
CREATE_ENERGYSYSTEM_FCT = 'create_energysystem'
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


ScenarioInput = namedtuple(
    'ScenarioInput',
    ['value', 'label', 'description']
)


def get_scenario_input_values(scenario_data):
    # Get default descriptions:
    attr_cfg_path = os.path.join(BASE_DIR, 'stemp/attributes.cfg')
    description = ConfigObj(attr_cfg_path)

    # TODO: Use ChainMap?
    # Check if it could be improved with ChainMap
    # (to combine default- and scenario-dict)

    # Prepare scenario input by combining default and scenario descriptions:
    scenario_input = {}
    for component, attributes in scenario_data.items():
        scenario_input[component] = []
        com_description = description.get(component, description['DEFAULT'])
        for attribute, value in attributes.items():
            attr_description = com_description.get(
                attribute,
                description['DEFAULT'].get(attribute)
            )
            if attr_description is not None:
                scenario_input[component].append(
                    ScenarioInput(
                        value,
                        attr_description.get('label', attribute),
                        attr_description.get('description', '')
                    )
                )
            else:
                scenario_input[component].append(
                    ScenarioInput(value, attribute, '')
                )
    return scenario_input


def import_scenario(filename):
    splitted = filename.split(os.path.sep)
    module_name = '.'.join(splitted[1:])
    return import_module('.' + module_name, package=splitted[0])


def create_energysystem(scenario_module, **parameters):
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


def adapt_parameters_to_energysystem(es, parameters):
    def adapt_source_parameters(source, outputs):
        for output in outputs:
            bus_name = output.pop('bus')
            try:
                bus = es.groups[bus_name]
            except KeyError:
                raise KeyError(
                    'Could not find bus "' + str(bus_name) +
                    '" in energysystem'
                )
            try:
                flow = source.outputs[bus]
            except KeyError:
                raise KeyError(
                    'Could not find flow "' + str(bus) + '" in source "' +
                    str(source) + '"'
                )
            for key, value in output.items():
                attr = getattr(flow, key)
                if isinstance(attr, _Sequence):
                    value = sequence(value)
                flow.__setattr__(key, value)

    for component in parameters['entities']:
        try:
            name = component['name']
        except KeyError:
            raise KeyError(
                'No name given for component with data:\n' +
                str(component)
            )
        try:
            entity = es.groups[name]
        except KeyError:
            raise KeyError('Could not find component "' + name +
                           '" in energysystem')

        if isinstance(entity, Source):
            adapt_source_parameters(entity, component['outputs'])


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
