
from pathos.helpers import mp
from kopy.settings import SESSION_DATA
from stemp.scenarios import get_simulation_function

# mp.set_start_method('fork')


def simulate_energysystem(request):
    energysystem = SESSION_DATA.get_session(request).energysystem
    simulation_fct = get_simulation_function(
        SESSION_DATA.get_session(request).scenario_module)
    return multiprocess_energysystem(
        energysystem, simulation_fct)


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
