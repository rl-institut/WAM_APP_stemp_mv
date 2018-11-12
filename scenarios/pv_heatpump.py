
import pandas
import sqlahelper
from copy import deepcopy

from oemof.solph import Flow, Transformer, Investment, Source, Bus
from oemof.tools.economics import annuity

from stemp.oep_models import OEPTimeseries
from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


NEEDED_PARAMETERS = deepcopy(basic_setup.NEEDED_PARAMETERS)
NEEDED_PARAMETERS['General'].extend(['pv_feedin_tariff', 'net_costs'])
NEEDED_PARAMETERS['PV'] = ['lifetime', 'capex', 'opex_fix']
NEEDED_PARAMETERS['HP'] = ['lifetime', 'capex']


def get_timeseries():
    session = sqlahelper.get_session()
    temp = session.query(OEPTimeseries).filter_by(
        name='Temperature').first().data
    pv = session.query(OEPTimeseries).filter_by(
        name='PV').first().data
    timeseries = pandas.DataFrame({'temp': temp, 'pv': pv})
    return timeseries


def create_energysystem(**parameters):
    timeseries = get_timeseries()

    energysystem = basic_setup.add_basic_energysystem()

    # Add households separately or as whole district:
    basic_setup.add_households(
        energysystem,
        add_pv_heatpump_technology,
        parameters,
        timeseries
    )

    return energysystem


def add_pv_heatpump_technology(demand, energysystem, timeseries, parameters):
    # Get subgrid busses:
    sub_b_th = basic_setup.find_element_in_groups(
        energysystem, f"b_{demand.name}_th")

    # Add electricity busses:
    sub_b_el = Bus(label=AdvancedLabel(
        f'b_{demand.name}_el', type='Bus', belongs_to=demand.name))
    b_el_net = Bus(label=AdvancedLabel('b_el_net', type='Bus'), balanced=False)
    energysystem.add(sub_b_el, b_el_net)

    # get investment parameters
    wacc = parameters['General']['wacc'] / 100

    # Add heat pump:
    capex = parameters['HP']['capex']
    lifetime = parameters['HP']['lifetime']
    epc = annuity(capex, lifetime, wacc)
    hp_invest = Investment(ep_costs=epc)
    hp_invest.capex = capex
    COP = cop_heating(timeseries['temp'], type_hp='air')

    hp = Transformer(
        label=AdvancedLabel(
            f"{demand.name}_heat_pump",
            type='Transformer',
            belongs_to=demand.name
        ),
        inputs={
            sub_b_el: Flow(
                investment=hp_invest,
                co2_emissions=parameters['HP']['co2_emissions']
            )
        },
        outputs={sub_b_th: Flow()},
        conversion_factors={sub_b_th: COP}
    )

    # Add pv system:
    capex = parameters['PV']['capex']
    lifetime = parameters['PV']['lifetime']
    opex_fix = parameters['PV']['opex_fix']
    epc = annuity(capex, lifetime, wacc) + opex_fix
    pv_invest = Investment(ep_costs=epc, maximum=demand.max_pv_size)
    pv_invest.capex = capex
    pv = Source(
        label=AdvancedLabel(
            f"{demand.name}_pv",
            type='Source',
            belongs_to=demand.name
        ),
        outputs={
            sub_b_el: Flow(
                actual_value=timeseries['pv'],
                fixed=True,
                investment=pv_invest,
                co2_emissions=parameters['PV']['co2_emissions']
            )
        }
    )

    # Add transformer to get electricty from net for heat pump:
    t_net_el = Transformer(
        label=AdvancedLabel(
            f'transformer_net_to_{demand.name}_el',
            type='Transformer',
            belongs_to=demand.name
        ),
        inputs={
            b_el_net: Flow(
                variable_costs=parameters['General']['net_costs']
            )
        },
        outputs={sub_b_el: Flow()},
    )

    # Add transformer to feed in pv to net:
    t_pv_net = Transformer(
        label=AdvancedLabel(
            f'transformer_from_{demand.name}_el',
            type='Transformer',
            belongs_to=demand.name
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
        t_pv_net,
        t_net_el
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

    cop_hp_heating.clip(lower=0.0, inplace=True)

    return cop_hp_heating


def cop_ww(temp, ww_profile_sfh, ww_profile_mfh, **kwargs):
    """
    Returns the COP of a heat pump for warm water
    Parameters
    temp -- pandas Series with temperature profile (ambient or brine temp.)
    ww_profile_sfh -- pandas Dataframe with warm water profile for
        single family houses
    ww_profile_mfh -- pandas Dataframe with warm water profile for
        multi family houses
    """

    t_ww_sfh = kwargs.get('t_ww_sfh', 50)  # warm water temp. in SFH
    t_ww_mfh = kwargs.get('t_ww_mfh', 60)  # warm water temp. in MFH
    cop_max = kwargs.get('cop_max', 7)
    type_hp = kwargs.get('type_hp', 'air')
    if type_hp == 'air':
        eta_g = kwargs.get('eta_g', 0.3)  # COP/COP_max
    elif type_hp == 'brine':
        eta_g = kwargs.get('eta_g', 0.4)  # COP/COP_max
    else:
        # TODO Raise Warning
        eta_g = kwargs.get('eta_g', 0.4)  # COP/COP_max

    # calculate the share of the warm water demand of sfh and mfh for each hour
    share_sfh = ww_profile_sfh.values / (ww_profile_sfh.values +
        ww_profile_mfh.values)

    # calculates mixed WW supply temperature for single and multi family houses
    t_sup_ww = share_sfh * t_ww_sfh + (1 - share_sfh) * t_ww_mfh

    # calculate COP
    cop = eta_g * ((t_sup_ww + 273.15) / (t_sup_ww - temp))
    cop[cop > cop_max] = cop_max

    return cop


def add_dynamic_parameters(scenario, parameters):
    return
