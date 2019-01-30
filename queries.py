
import os
import logging
import pandas
import sqlahelper
import json
from geoalchemy2 import func
import transaction
import datetime as dt

from demandlib import bdew
import oedialect

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'wam.settings'
application = get_wsgi_application()

from stemp import constants
from stemp.models import Parameter, Scenario, Household, District

from db_apps import coastdat, oemof_results
from stemp import oep_models
from stemp.scenarios import basic_setup

logging.getLogger().setLevel(logging.INFO)


def delete_scenarios():
    session = sqlahelper.get_session()
    session.query(oep_models.OEPScenario).delete()


def insert_scenarios():
    basic_setup.upload_scenario_parameters()


def get_coastdat_data(session, year, datatype, location):
    # Get temperature from coastdat dataset:
    query = coastdat.get_timeseries_join(session)
    query = query.filter(coastdat.Year.year == year)
    query = query.filter(coastdat.Datatype.name == datatype)
    ts = query.order_by(
        func.ST_Distance(
            coastdat.Spatial.geom,
            func.Geometry(
                func.ST_GeographyFromText(
                    'POINT({} {})'.format(*location)
                )
            )
        )
    ).limit(1).first()
    data = pandas.Series(ts.tsarray) - constants.KELVIN
    return data


def insert_pv_and_temp():
    session = sqlahelper.get_session()

    temperature = pandas.read_csv(
        os.path.join(os.path.dirname(__file__), 'data', 'temperature.txt'),
        index_col=[1],
        delimiter=';',
        parse_dates=[1],
        date_parser=lambda x: dt.datetime(int(x[:4]), int(x[4:6]), int(x[6:8]),
                                          int(x[8:10]), 0, 0)
    )['2017-01-01':'2017-12-31']
    temp_meta_file = os.path.join(
        os.path.dirname(__file__), 'metadata', 'dwd_temperature.json')
    with open(temp_meta_file) as json_data:
        meta = json.load(json_data)
    temp = oep_models.OEPTimeseries(
        name='Temperature',
        meta_data=meta,
        data=temperature['TT_TU']
    )
    session.add(temp)

    pv_feedin = pandas.read_csv(
        os.path.join(os.path.dirname(__file__), 'data', 'pv_normalized.csv'),
        index_col=[0],
        header=[0, 1]
    )
    pv_system = 'LG290G3_ABB_tlt34_az180_alb02'
    pv_feedin = pv_feedin.swaplevel(axis=1)[pv_system]['2014']
    pv_meta_file = os.path.join(
        os.path.dirname(__file__), 'metadata', 'pv_feedin.json')
    with open(pv_meta_file) as json_data:
        meta = json.load(json_data)
    pv = oep_models.OEPTimeseries(
        name='PV',
        meta_data=meta,
        data=pv_feedin
    )
    session.add(pv)
    with transaction.manager as tm:
        tm.commit()


def insert_heat_demand():
    session = sqlahelper.get_session()
    temperature = get_coastdat_data(
        session, year=2014, datatype='T_2M', location=constants.LOCATION)

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

    # Add to OEP
    session.add_all([
        oep_models.OEPTimeseries(
            name=constants.HouseType.EFH.value,
            meta_data={
                'name': 'Heat demand for EFH',
                'source': 'oemof/demandlib'
            },
            data=demand['efh'].values.tolist()
        ),
        oep_models.OEPTimeseries(
            name=constants.HouseType.MFH.value,
            meta_data={
                'name': 'Heat demand for MFH',
                'source': 'oemof/demandlib'
            },
            data=demand['mfh'].values.tolist()
        ),
    ])
    with transaction.manager as tm:
        tm.commit()


def insert_dhw_timeseries():
    NUM_PERSONS = 10

    session = sqlahelper.get_session()

    for consumption in constants.WarmwaterConsumption:
        for p in range(NUM_PERSONS):
            hot_water_file = os.path.join(
                os.path.dirname(__file__),
                'data',
                'hot_water',
                f'Warmwasser_{consumption.in_liters()}l_{p + 1}_DHW.txt'
            )
            hot_water_profile = pandas.read_csv(
                hot_water_file, header=None, escapechar='\\')
            hot_water_energy_profile = (
                hot_water_profile * constants.ENERGY_PER_LITER)
            hot_water = oep_models.OEPHotWater(
                liter=consumption.in_liters() * (p + 1),
                data=hot_water_energy_profile[0].values.tolist()
            )
            session.add(hot_water)
    with transaction.manager as tm:
        tm.commit()


def insert_default_households():
    for house_type in constants.HouseType:
        for num_persons in range(1, 11):
            square_meters = num_persons * constants.QM_PER_PERSON
            household = Household(
                name=f'{house_type.value}_{num_persons}',
                number_of_persons=num_persons,
                house_type=house_type.name,
                square_meters=square_meters,
                heat_demand=(
                    square_meters *
                    constants.ENERGY_PER_QM_PER_YEAR[house_type.name]
                ),
                heat_type=constants.HeatType.radiator.name,
                warm_water_per_day=(
                    constants.WarmwaterConsumption.Medium.in_liters()),
                roof_area=constants.get_roof_square_meters(
                    square_meters, house_type)
            )
            household.save()


def delete_households():
    Household.objects.all().delete()
    District.objects.all().delete()


def delete_oep_tables():
    try:
        oep_models.Base.metadata.drop_all()
    except oedialect.engine.ConnectionException:
        pass


def create_oep_tables():
    oep_models.Base.metadata.create_all()


def delete_stored_simulations():
    Parameter.objects.all().delete()
    Scenario.objects.all().delete()
    session = sqlahelper.get_session()
    session.query(oemof_results.OemofInputResult).delete()
    session.query(oemof_results.OemofScalar).delete()
    session.query(oemof_results.OemofSequence).delete()
    session.query(oemof_results.OemofData).delete()
    with transaction.manager as tm:
        tm.commit()
