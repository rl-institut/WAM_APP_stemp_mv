from __future__ import absolute_import, unicode_literals
import sqlahelper

from wam.celery import app

from stemp.scenarios.simulation import get_simulation_function
from stemp.scenarios.simulation import create_energysystem
from stemp.app_settings import SCENARIO_MODULES

from stemp.models import Scenario, Parameter, Simulation
from db_apps import oemof_results


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)


@app.task
def simulate_energysystem(scenario_module, parameters):
    module = SCENARIO_MODULES[scenario_module]
    energysystem = create_energysystem(
        module,
        **parameters
    )
    simulation_fct = get_simulation_function(module)
    result, param_result = simulation_fct(energysystem)
    result_id = store_results(
        scenario_module, parameters, result, param_result)
    return result_id


def store_results(name, parameters, results, param_results):
    # Store scenario, parameter and setup via Django ORM
    scenario = Scenario.objects.get_or_create(name=name)[0]
    parameter = Parameter.objects.get_or_create(data=parameters)[0]

    # Store oemeof results via SQLAlchemy:
    sa_session = sqlahelper.get_session()
    result_id = oemof_results.store_results(
        sa_session,
        param_results,
        results
    )
    sa_session.close()

    # Store simulation in Django ORM:
    Simulation.objects.get_or_create(
        scenario=scenario,
        parameter=parameter,
        result_id=result_id
    )
    return result_id
