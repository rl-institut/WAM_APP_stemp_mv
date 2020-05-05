"""
Functions to be used by celery in order to run them in parallel.

Simulations are run in parallel and results are stored in database.
Only result-ID is returned to django via celery.
"""

import sqlahelper

from wam.celery import app

from stemp.scenarios.simulation import get_simulation_function
from stemp.scenarios.simulation import create_energysystem
from stemp.app_settings import SCENARIO_MODULES

from stemp.models import Scenario, Parameter, Simulation
from db_apps import oemof_results


@app.task
def simulate_energysystem(scenario_module, parameters):
    """
    This functions combines creating and simulating the energysystem and storing results

    Parameters
    ----------
    scenario_module : str
        Name of scenario module (module is needed to get Scenario class)
    parameters : dict
        Parameters which shall be used to create energysystem via Scenario class

    Returns
    -------
    int
        Result ID, which points to stored results in database
    """
    module = SCENARIO_MODULES[scenario_module]
    energysystem = create_energysystem(module, **parameters)
    simulation_fct = get_simulation_function(module)
    result, param_result = simulation_fct(energysystem)
    result_id = store_results(scenario_module, parameters, result, param_result)
    return result_id


def store_results(name, parameters, results, param_results):
    """
    Results from oemof simulation are stored in database

    Scenario and parameters are stored via django ORM.
    Oemof results are stored via oemof_db package using SQLAlchemy.
    Result-ID of oemof results is stored in Simulation model together with scenario and
    parameters.

    Parameters
    ----------
    name : str
        Name of scenario
    parameters : dict
        Parameters for current scenario
    results : dict
        Oemof results of the simulation
    param_results : dict
        Oemof input parameters of the simulation

    Returns
    -------
    int
        Result-ID of stored simulation
    """
    # Store scenario, parameter and setup via Django ORM
    scenario = Scenario.objects.get_or_create(name=name)[0]
    parameter = Parameter.objects.get_or_create(data=parameters)[0]

    # Store oemeof results via SQLAlchemy:
    sa_session = sqlahelper.get_session()
    result_id = oemof_results.store_results(sa_session, param_results, results)
    sa_session.close()

    # Store simulation in Django ORM:
    Simulation.objects.get_or_create(
        scenario=scenario, parameter=parameter, result_id=result_id
    )
    return result_id
