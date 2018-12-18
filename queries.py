
import os
import logging
import pandas
import sqlahelper
import json
from geoalchemy2 import func
import transaction

from demandlib import bdew
import oedialect

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'wam.settings'
application = get_wsgi_application()

from stemp import constants
from stemp.models import Simulation

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

    temperature = get_coastdat_data(
        session,
        year=2014,
        datatype='T_2M',
        location=constants.LOCATION
    )
    temp_meta_file = os.path.join(
        os.path.dirname(__file__), 'metadata', 'coastdat_temp.json')
    with open(temp_meta_file) as json_data:
        meta = json.load(json_data)
    temp = oep_models.OEPTimeseries(
        name='Temperature',
        meta_data=meta,
        data=temperature
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
    transaction.commit()


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
            name='Heat Demand EFH',
            meta_data={
                'name': 'Heat demand for EFH',
                'source': 'oemof/demandlib'
            },
            data=demand['efh'].values.tolist()
        ),
        oep_models.OEPTimeseries(
            name='Heat Demand MFH',
            meta_data={
                'name': 'Heat demand for MFH',
                'source': 'oemof/demandlib'
            },
            data=demand['mfh'].values.tolist()
        ),
    ])
    transaction.commit()


def insert_dhw_timeseries():
    hot_water_file = os.path.join(
        os.path.dirname(__file__), 'data', 'Warmwasser_76_liter_DHW.txt')
    hot_water_profile = pandas.read_csv(
        hot_water_file, header=None, escapechar='\\')

    meta = {
        'name': 'Hot Water for 76l/person/day',
        'source': 'DHWCalc'
    }
    hot_water = oep_models.OEPTimeseries(
        name='Hot Water',
        meta_data=meta,
        data=hot_water_profile[0].values.tolist()
    )

    hot_water_energy_profile = hot_water_profile * constants.ENERGY_PER_LITER
    meta = {
        'name': 'Annual energy for hot water supply for 76l/person/day',
        'source': 'DHWCalc',
        'energy_factor': constants.ENERGY_PER_LITER
    }
    hot_water_energy = oep_models.OEPTimeseries(
        name='Hot Water Energy',
        meta_data=meta,
        data=hot_water_energy_profile[0].values.tolist()
    )

    session = sqlahelper.get_session()
    session.add(hot_water)
    session.add(hot_water_energy)
    transaction.commit()


def create_questions_and_households():
    # Start django application
    from django.core.wsgi import get_wsgi_application

    os.environ['DJANGO_SETTINGS_MODULE'] = 'wam.settings'
    _ = get_wsgi_application()
    from stemp.models import Question, QuestionHousehold, Household

    for num_person in range(1, 11):
        for house_type in ('EFH', 'MFH'):
            question = Question(
                number_of_persons=num_person, house_type=house_type)
            energy_per_year = (
                    num_person * constants.QM_PER_PERSON *
                    constants.ENERGY_PER_QM_PER_YEAR[house_type]
            )
            person_str = (
                f'{num_person} Personen' if num_person > 1 else '1 Person')
            name = house_type + ', ' + person_str
            household = Household(name=name, heat_demand=energy_per_year)
            question.save()
            household.save()
            question_household = QuestionHousehold(
                question_id=question.id,
                household_id=household.id,
                default=True
            )
            question_household.save()


def delete_oep_tables():
    try:
        oep_models.Base.metadata.drop_all()
    except oedialect.engine.ConnectionException:
        pass


def create_oep_tables():
    oep_models.Base.metadata.create_all()


def delete_stored_simulations():
    Simulation.objects.all().delete()
    session = sqlahelper.get_session()
    session.query(oemof_results.OemofInputResult).delete()
    session.query(oemof_results.OemofScalar).delete()
    session.query(oemof_results.OemofSequence).delete()
    session.query(oemof_results.OemofData).delete()
    transaction.commit()
