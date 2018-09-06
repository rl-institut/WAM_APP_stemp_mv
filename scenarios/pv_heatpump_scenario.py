
import os
import pandas
from copy import deepcopy

from oemof.solph import Flow, Transformer, Investment, Source, Bus
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS['General'].extend(['pv_feedin_tariff', 'net_costs'])
NEEDED_PARAMETERS['PV'] = ['lifetime', 'capex', 'opex_fix']
NEEDED_PARAMETERS['HP'] = ['lifetime', 'capex']


def get_timeseries():
    # FIXME: Get timeseries from open energy platform or elsewhere public
    csv_path = 'timeseries.csv'
    timeseries = pandas.read_csv(
        os.path.join(os.path.dirname(__file__), csv_path))
    return timeseries


def create_energysystem(periods=8760, **parameters):
    timeseries = get_timeseries()

    energysystem = basic_setup.add_basic_energysystem(periods)

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_pv_heatpump_technology,
        parameters,
        timeseries
    )

    return energysystem


def add_pv_heatpump_technology(label, energysystem, timeseries, parameters):
    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{label}_th")

    # Add electricity busses:
    sub_b_el = Bus(label=AdvancedLabel(
        f'b_{label}_el', type='Bus', belongs_to=label))
    b_el_net = Bus(label=AdvancedLabel('b_el_net', type='Bus'))
    energysystem.add(sub_b_el, b_el_net)

    # get investment parameters
    wacc = parameters['General']['wacc']

    capex = parameters['HP']['capex']
    lifetime = parameters['HP']['lifetime']
    epc_hp = annuity(capex, lifetime, wacc)

    capex = parameters['PV']['capex']
    lifetime = parameters['PV']['lifetime']
    opex_fix = parameters['PV']['opex_fix']
    epc_pv = annuity(capex, lifetime, wacc) + opex_fix

    # Add heat pump:
    COP = cop_heating(timeseries['temp'], type_hp='brine')
    hp = Transformer(
        label=AdvancedLabel(
            f"{label}_heat_pump", type='Transformer', belongs_to=label),
        inputs={
            sub_b_el: Flow(
                investment=Investment(ep_costs=epc_hp)
            )
        },
        outputs={sub_b_th: Flow()},
        conversion_factors={sub_b_th: COP}
    )

    # Add pv system:
    pv = Source(
        label=AdvancedLabel(f"{label}_pv", type='Source', belongs_to=label),
        outputs={
            sub_b_el: Flow(
                actual_value=timeseries['pv'],
                fixed=True,
                investment=Investment(ep_costs=epc_pv)
            )
        }
    )

    # Add transformer to feed in pv to net:
    t_pv_net = Transformer(
        label=AdvancedLabel(
            f'transformer_from_{label}_el',
            type='Transformer',
            belongs_to=label
        ),
        inputs={
            sub_b_el: Flow(
                variable_costs=-parameters['General']['pv_feedin_tariff']
            )
        },
        outputs={b_el_net: Flow()},
    )
    energysystem.add(
        hp,
        pv,
        t_pv_net
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
