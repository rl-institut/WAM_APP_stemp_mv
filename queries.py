
import os
import logging
import pandas
import sqlahelper
from geoalchemy2 import func
import transaction
import matplotlib.pyplot as plt

from demandlib import bdew

import stemp.app_settings
from db_apps import coastdat
from stemp.oep_models import OEPScenario, OEPTimeseries
from stemp.scenarios import bhkw_scenario, oil_scenario, pv_heatpump_scenario

logging.getLogger().setLevel(logging.INFO)

KELVIN = 273.15
ENERGY_PER_LITER = 0.058
LUETZOW_LON_LAT = (11.181475, 53.655119)


def delete_oep_scenario(scenario):
    # Does not work!
    OEPScenario.delete({'scenario': scenario})


def insert_scenarios():
    bhkw_scenario.upload_scenario_parameters()
    oil_scenario.upload_scenario_parameters()
    pv_heatpump_scenario.upload_scenario_parameters()


def insert_heat_demand():
    # Get temperature from coastdat dataset:
    session = sqlahelper.get_session()
    query = coastdat.get_timeseries_join(session)
    query = query.filter(coastdat.Year.year == 2014)
    query = query.filter(coastdat.Datatype.name == 'T_2M')
    ts = query.order_by(
        func.ST_Distance(
            coastdat.Spatial.geom,
            func.Geometry(
                func.ST_GeographyFromText(
                    'POINT({} {})'.format(*LUETZOW_LON_LAT)
                )
            )
        )
    ).limit(1).first()
    temperature = pandas.Series(ts.tsarray) - KELVIN

    demand = pandas.DataFrame(
        index=pandas.date_range(
            pandas.datetime(2018, 1, 1, 0),
            periods=8760,
            freq='H'
        )
    )

    # Single family house (efh: Einfamilienhaus)
    demand['efh'] = bdew.HeatBuilding(
        demand.index, temperature=temperature,
        shlp_type='EFH',
        building_class=1, wind_class=1,
        name='EFH').get_normalized_bdew_profile()

    # Multi family house (mfh: Mehrfamilienhaus)
    demand['mfh'] = bdew.HeatBuilding(
        demand.index, temperature=temperature,
        shlp_type='MFH',
        building_class=2, wind_class=0,
        name='MFH').get_normalized_bdew_profile()
    demand.plot()
    plt.show()


def insert_dhw_timeseries():
    hot_water_file = os.path.join(
        os.path.dirname(__file__), 'data', 'Warmwasser_76_liter_DHW.txt')
    hot_water_profile = pandas.read_csv(
        hot_water_file, header=None, escapechar='\\')

    meta = {
        'name': 'Hot Water for 76l/person/day',
        'source': 'DHWCalc'
    }
    hot_water = OEPTimeseries(
        name='Hot Water',
        meta=meta,
        data=hot_water_profile[0].values.tolist()
    )

    hot_water_energy_profile = hot_water_profile * ENERGY_PER_LITER
    meta = {
        'name': 'Annual energy for hot water supply for 76l/person/day',
        'source': 'DHWCalc',
        'energy_factor': ENERGY_PER_LITER
    }
    hot_water_energy = OEPTimeseries(
        name='Hot Water Energy',
        meta=meta,
        data=hot_water_energy_profile[0].values.tolist()
    )

    session = sqlahelper.get_session()
    session.add(hot_water)
    session.add(hot_water_energy)
    transaction.commit()


if __name__ == '__main__':
    insert_heat_demand()
    # insert_scenarios()
    # insert_dhw_timeseries()
