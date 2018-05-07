
from pathos.helpers import mp
from stemp.results import Results
from stemp.scenarios import get_simulation_function


def simulate_energysystem(session):
    energysystem = session.energysystem
    simulation_fct = get_simulation_function(session.scenario_module)
    result, param_result = multiprocess_energysystem(
        energysystem, simulation_fct)

    session.result = Results(result, param_result)
    session.store_simulation()


# TODO: Create user-dependent pool in settings
def multiprocess_energysystem(energysystem, simulate_fct):
    queue = mp.Queue()
    p = mp.Process(
        target=queue_energysytem,
        args=(queue, energysystem, simulate_fct)
    )
    p.start()
    results = queue.get()
    p.join()
    return results


def queue_energysytem(queue, energysystem, simulate_fct):
    """
    All function in fcts are succesively run on energysystem
    """
    results = simulate_fct(energysystem)
    queue.put(results)
