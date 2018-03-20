
import pandas
from enum import Enum

from oemof.solph import (
    EnergySystem, Model, Bus, Flow, Sink, Source, Transformer,
    Investment
)
from oemof.solph.components import ExtractionTurbineCHP
# from oemof.solph.components import GenericCHP
from oemof.outputlib import processing, views

# Load django settings if run locally:
if __name__ == '__main__':
    import os
    from django.core.wsgi import get_wsgi_application

    os.environ['DJANGO_SETTINGS_MODULE'] = 'kopy.settings'
    application = get_wsgi_application()


from stemp.models import District, Household
from stemp.results import Results, VisualizationMeta


NET_COSTS = 0.27
PV_FEED_IN_TARIFF = -0.08


VISUALIZATIONS = {

}


class TechnologyOption(str, Enum):
    BHKW = 'bhkw'
    PV_WP = 'pv_wp'
    OIL = 'oil'


class CustomerOption(str, Enum):
    Single = 'single'
    Separate = 'separate'
    District = 'district'


def read_data():
    csv_path = __file__[:-3] + '.csv'
    data = pandas.read_csv(csv_path)
    return data


def create_energysystem(periods=2, **parameters):
    data = read_data()

    # Init parameters:
    technology = parameters.get('technology', TechnologyOption.OIL)
    customer_index = parameters.get('customer_index', 0)
    customer_case = parameters.get('customer_case', CustomerOption.District)

    # initialize energy system
    energysystem = EnergySystem(
        timeindex=pandas.date_range('2016-01-01', periods=periods, freq='H')
    )

    # BUSSES
    b_el_net = Bus(label="b_el_net")
    energysystem.add(b_el_net)

    if technology == TechnologyOption.BHKW:
        b_gas = Bus(label="b_gas", balanced=False)
        energysystem.add(b_gas)
    elif technology == TechnologyOption.OIL:
        b_oil = Bus(label="b_oil", balanced=False)
        energysystem.add(b_oil)

    # add excess sink to help avoid infeasible problems
    ex_el = Sink(
        label="excess_el",
        inputs={b_el_net: Flow()}
    )
    s_el = Source(
        label="shortage_el",
        outputs={b_el_net: Flow(variable_costs=1000)},
    )
    energysystem.add(ex_el, s_el)

    # Add households separately or as whole district:
    add_households(
        customer_index,
        customer_case,
        technology,
        energysystem,
        data
    )

    return energysystem


def add_households(customer_index, customer_case, technology, energysystem,
                   data):
    """
    Whole district as one, separate or single households are added to es
    """
    def add_household(customer):
        add_subgrid_and_demands(customer, energysystem)
        add_technology(customer.name, technology, energysystem, data)

    if customer_case == CustomerOption.Single:
        household = Household.objects.get(id=customer_index)
        add_household(household)
    else:
        district = District.objects.get(id=customer_index)
        if customer_case == CustomerOption.Separate:
            for household in district.household_set.all():
                add_household(household)
        elif customer_case == CustomerOption.District:
            add_household(district)
        else:
            raise ValueError('Unknown customer case "' + customer_case + '"')


def add_subgrid_and_demands(
        customer: [District, Household],
        energysystem: EnergySystem,
):
    # Add subgrid busses
    sub_b_el = Bus(label="b_{}_el".format(customer.name))
    sub_b_th = Bus(label="b_{}_th".format(customer.name))
    energysystem.add(sub_b_el, sub_b_th)

    # Connect electrical net to subgrid:
    t_el = Transformer(
        label='transformer_to_{}_el'.format(customer.name),
        inputs={
            energysystem.groups['b_el_net']: Flow(
                variable_costs=NET_COSTS
            )
        },
        outputs={sub_b_el: Flow()},
    )
    energysystem.add(t_el)

    # Add electricity demand
    demand_el = Sink(
        label="demand_{}_el".format(customer.name),
        inputs={
            sub_b_el: Flow(
                nominal_value=1,
                actual_value=customer.annual_load_demand().div(1e6),
                fixed=True
            )
        }
    )
    # Add heat demand
    demand_th = Sink(
        label="demand_{}_th".format(customer.name),
        inputs={
            sub_b_th: Flow(
                nominal_value=1,
                actual_value=customer.annual_heat_demand().div(1e6),
                fixed=True
            )
        }
    )
    energysystem.add(demand_el, demand_th)

    # Add safety excess:
    ex_el = Sink(
        label="excess_{}_el".format(customer.name),
        inputs={sub_b_el: Flow()}
    )
    ex_th = Sink(
        label="excess_{}_th".format(customer.name),
        inputs={sub_b_th: Flow()}
    )
    energysystem.add(ex_el, ex_th)


def add_technology(label, technology, energysystem, data):
    # Get subgrid busses:
    sub_b_el = energysystem.groups["b_{}_el".format(label)]
    sub_b_th = energysystem.groups["b_{}_th".format(label)]

    if technology == TechnologyOption.BHKW:
        chp = ExtractionTurbineCHP(
            label='{}_chp'.format(label),
            inputs={energysystem.groups['b_gas']: Flow(nominal_value=10e10)},
            outputs={sub_b_el: Flow(), sub_b_th: Flow()},
            conversion_factors={sub_b_el: 0.3, sub_b_th: 0.5},
            conversion_factor_full_condensation={sub_b_el: 0.5}
        )
        energysystem.add(chp)
    elif technology == TechnologyOption.PV_WP:
        # Add heat pump:
        COP = cop_heating(data['temp'], type_hp='brine')
        hp = Transformer(
            label="{}_heat_pump".format(label),
            inputs={sub_b_el: Flow(
                investment=Investment(ep_costs=3)
            )},
            outputs={sub_b_th: Flow(variable_costs=10)},
            conversion_factors={sub_b_th: COP}
        )

        # Add pv system:
        pv = Source(
            label="{}_pv".format(label),
            outputs={
                sub_b_el: Flow(
                    actual_value=data['pv'],
                    # nominal_value=200,
                    variable_costs=2,
                    fixed=True,
                    investment=Investment(ep_costs=0.1)
                )
            }
        )

        # Add transformer to feed in pv to net:
        t_pv_net = Transformer(
            label='transformer_from_{}_el'.format(label),
            inputs={
                sub_b_el: Flow(
                    variable_costs=PV_FEED_IN_TARIFF
                )
            },
            outputs={energysystem.groups['b_el_net']: Flow()},
        )
        energysystem.add(
            hp,
            pv,
            t_pv_net
        )
    elif technology == TechnologyOption.OIL:
        oil_heating = Transformer(
            label='{}_oil_heating'.format(label),
            inputs={energysystem.groups['b_oil']: Flow(nominal_value=10e10)},
            outputs={sub_b_th: Flow()},
            conversion_factors={sub_b_th: 0.3},
        )
        energysystem.add(oil_heating)
    else:
        raise ValueError(
            'Technology "' + str(technology) + '" unknown. ' +
            'Cannot build household subgrids correctly.'
        )


def optimize(energysystem, write_lp=False):
    om = Model(es=energysystem)
    om.solve(solver='cbc', solve_kwargs={'tee': False})
    if write_lp:
        om.write(
            'heat_scenario.lp',
            io_options={'symbolic_solver_labels': True}
        )
    return (
        processing.results(om),
        processing.param_results(om, exclude_none=True, keys_as_str=True)
    )


def calc_hp_heating_supply_temp(temp, heating_system, **kwargs):
    """
    Generates an hourly supply temperature profile depending on the ambient
    temperature.
    For ambient temperatures below t_heat_period the supply temperature
    increases linearly to t_sup_max with decreasing ambient temperature.
    Parameters
    temp -- pandas Series with ambient temperature
    heating_system -- string specifying the heating system (floor heating or
        radiator)
    """
    # outdoor temp upto which is heated:
    t_heat_period = kwargs.get('t_heat_period', 20)
    # design outdoor temp:
    t_amb_min = kwargs.get('t_amb_min', -14)

    # minimum and maximum supply temperature of heating system
    if heating_system == 'floor heating':
        t_sup_max = kwargs.get('t_sup_max', 35)
        t_sup_min = kwargs.get('t_sup_min', 20)
    elif heating_system == 'radiator':
        t_sup_max = kwargs.get('t_sup_max', 55)
        t_sup_min = kwargs.get('t_sup_min', 20)
    else:
        t_sup_max = kwargs.get('t_sup_max', 55)
        t_sup_min = kwargs.get('t_sup_min', 20)

    # calculate parameters for linear correlation for supply temp and
    # ambient temp
    slope = (t_sup_min - t_sup_max) / (t_heat_period - t_amb_min)
    y_intercept = t_sup_max - slope * t_amb_min

    # calculate supply temperature
    t_sup_heating = slope * temp + y_intercept
    t_sup_heating[t_sup_heating < t_sup_min] = t_sup_min
    t_sup_heating[t_sup_heating > t_sup_max] = t_sup_max

    return t_sup_heating


def cop_heating(temp, type_hp, **kwargs):
    """
    Returns the COP of a heat pump for heating.
    Parameters
    temp -- pandas Series with ambient or brine temperature
    type_hp -- string specifying the heat pump type (air or brine)
    """
    # share of heat pumps in new buildings
    share_hp_new_building = kwargs.get('share_hp_new_building', 0.5)
    # share of floor heating in old buildings
    share_fh_old_building = kwargs.get('share_fbh_old_building', 0.25)
    cop_max = kwargs.get('cop_max', 7)
    if type_hp == 'air':
        eta_g = kwargs.get('eta_g', 0.3)  # COP/COP_max
    elif type_hp == 'brine':
        eta_g = kwargs.get('eta_g', 0.4)  # COP/COP_max
    else:
        eta_g = kwargs.get('eta_g', 0.4)  # COP/COP_max
    # get supply temperatures
    t_sup_fh = calc_hp_heating_supply_temp(temp, 'floor heating')
    t_sup_radiator = calc_hp_heating_supply_temp(temp, 'radiator')
    # share of floor heating systems and radiators
    share_fh = (
        share_hp_new_building + (1 - share_hp_new_building) *
        share_fh_old_building
    )
    share_rad = (1 - share_hp_new_building) * (1.0 - share_fh_old_building)

    # calculate COP for floor heating and radiators
    cop_hp_heating_fh = eta_g * ((273.15 + t_sup_fh) / (t_sup_fh - temp))
    cop_hp_heating_fh[cop_hp_heating_fh > cop_max] = cop_max
    cop_hp_heating_rad = (
        eta_g * (273.15 + t_sup_radiator) / (t_sup_radiator - temp)
    )
    cop_hp_heating_rad[cop_hp_heating_rad > cop_max] = cop_max
    cop_hp_heating = (
        share_fh * cop_hp_heating_fh + share_rad * cop_hp_heating_rad
    )

    return cop_hp_heating 


if __name__ == '__main__':
    params = {
        'customer_index': '1',
        'customer_case': CustomerOption.Single,
        'technology': TechnologyOption.OIL
    }
    es = create_energysystem(periods=24, **params)
    results = optimize(es, write_lp=False)

    import matplotlib.pyplot as plt
    node_results = [
        views.node(results, node)
        for node in views.filter_nodes(results, exclude_busses=True)
    ]
    data = pandas.concat([nr['sequences'] for nr in node_results], axis=1)
    data.plot()
    plt.show()
