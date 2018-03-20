
import pandas

from oemof.solph import (
    EnergySystem, Bus, Flow, Sink, Transformer,
    Investment
)

# Load django settings if run locally:
if __name__ == '__main__':
    import os
    from django.core.wsgi import get_wsgi_application

    os.environ['DJANGO_SETTINGS_MODULE'] = 'kopy.settings'
    application = get_wsgi_application()


def read_data():
    demand = [100] * 8760
    demand[0] = 0.0
    data = pandas.DataFrame(
        {
            'demand_el': demand
        }
    )
    return data


def create_energysystem(periods=8760, **parameters):
    data = read_data()

    # initialize energy system
    energysystem = EnergySystem(
        timeindex=pandas.date_range('2016-01-01', periods=periods, freq='H')
    )

    # BUSSES
    b_el = Bus(label="b_el")
    b_diesel = Bus(label='b_diesel', balanced=False)
    energysystem.add(b_el, b_diesel)

    # TEST DIESEL:
    dg = Transformer(
        label='diesel',
        inputs={
            b_diesel: Flow(
                variable_costs=2,
                investment=Investment(ep_costs=0.5)
            )
        },
        outputs={
            b_el: Flow(
                conversion_factors={b_el: 5},
                variable_costs=1
            )
        },
    )

    demand = Sink(
        label="demand_el",
        inputs={
            b_el: Flow(
                nominal_value=1,
                actual_value=data['demand_el'],
                fixed=True
            )
        }
    )
    energysystem.add(dg, demand)
    return energysystem
