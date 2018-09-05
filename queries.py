
import os
import logging
import pandas
import sqlahelper
from geoalchemy2 import func
import transaction

from demandlib import bdew

import stemp.app_settings
from db_apps import coastdat
from stemp import oep_models
from stemp.scenarios import basic_setup

logging.getLogger().setLevel(logging.INFO)

KELVIN = 273.15
ENERGY_PER_LITER = 0.058
QM_PER_PERSON = 44.40
ENERGY_PER_QM_PER_YEAR = {'EFH': 90, 'MFH': 70}
LUETZOW_LON_LAT = (11.181475, 53.655119)


def delete_oep_scenario(scenario):
    session = sqlahelper.get_session()
    session.query(oep_models.OEPScenario).filter_by(scenario=scenario).delete()


def insert_scenarios():
    basic_setup.upload_scenario_parameters()


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

    # Add to OEP
    session.add_all([
        oep_models.OEPTimeseries(
            name='Heat Demand EFH',
            meta={
                'name': 'Heat demand for EFH',
                'source': 'oemof/demandlib'
            },
            data=demand['efh'].values.tolist()
        ),
        oep_models.OEPTimeseries(
            name='Heat Demand MFH',
            meta={
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
        meta=meta,
        data=hot_water_profile[0].values.tolist()
    )

    hot_water_energy_profile = hot_water_profile * ENERGY_PER_LITER
    meta = {
        'name': 'Annual energy for hot water supply for 76l/person/day',
        'source': 'DHWCalc',
        'energy_factor': ENERGY_PER_LITER
    }
    hot_water_energy = oep_models.OEPTimeseries(
        name='Hot Water Energy',
        meta=meta,
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
    application = get_wsgi_application()
    from stemp.models import Question, QuestionHousehold, Household

    for num_person in range(1, 11):
        for house_type in ('EFH', 'MFH'):
            question = Question(
                number_of_persons=num_person, house_type=house_type)
            energy_per_year = (
                    num_person * QM_PER_PERSON *
                    ENERGY_PER_QM_PER_YEAR[house_type]
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


def read_data():
    session = sqlahelper.get_session()
    hd = session.query(oep_models.OEPTimeseries).filter_by(name='Heat Demand EFH').first()
    print(hd.__dict__)


def create_oep_tables():

    oep_models.Base.metadata.create_all()


if __name__ == '__main__':
    # create_oep_tables()
    # delete_oep_scenario('bhkw_scenario')
    # insert_heat_demand()
    insert_scenarios()
    # insert_dhw_timeseries()
