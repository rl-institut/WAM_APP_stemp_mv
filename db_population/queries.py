import os
import click
import logging
import pandas
import sqlahelper
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import ProgrammingError
import transaction
import datetime as dt

from demandlib import bdew
import oedialect

from django.core.wsgi import get_wsgi_application

os.environ["DJANGO_SETTINGS_MODULE"] = "wam.settings"
application = get_wsgi_application()

from wam.settings import BASE_DIR
from stemp.db_population import assumptions
from stemp.db_population import sources
from stemp.db_population.population_utils import get_meta_from_json

from db_apps import oemof_results
from stemp import constants
from stemp.models import Parameter, Scenario, Household, District
from stemp import oep_models
from stemp.scenarios import basic_setup


def __get_temperature():
    return pandas.read_csv(
        os.path.join(BASE_DIR, "stemp", "data", "temperature.txt"),
        index_col=[1],
        delimiter=";",
        parse_dates=[1],
        date_parser=(
            lambda x: dt.datetime(
                int(x[:4]), int(x[4:6]), int(x[6:8]), int(x[8:10]), 0, 0
            )
        ),
    )["2017-01-01":"2017-12-31"]


def delete_scenarios():
    session = sqlahelper.get_session()
    with transaction.manager:
        session.query(oep_models.OEPScenario).delete()


def insert_scenarios():
    basic_setup.upload_scenario_parameters()


def insert_pv_and_temp():
    session = sqlahelper.get_session()

    temperature = __get_temperature()
    temp = oep_models.OEPTimeseries(
        name="Temperature",
        meta_data=get_meta_from_json("dwd_temperature"),
        data=temperature["TT_TU"],
    )

    pv_feedin = pandas.read_csv(
        os.path.join(BASE_DIR, "stemp", "data", "pv_normalized.csv"),
        index_col=[0],
        header=[0, 1],
    )
    pv_system = "LG290G3_ABB_tlt34_az180_alb02"
    pv_feedin = pv_feedin.swaplevel(axis=1)[pv_system]["2014"]
    pv = oep_models.OEPTimeseries(
        name="PV", meta_data=get_meta_from_json("pv_feedin"), data=pv_feedin
    )
    with transaction.manager:
        session.add(temp)
        session.add(pv)


def insert_heat_demand():
    session = sqlahelper.get_session()

    temperature = __get_temperature()

    demand = pandas.DataFrame(
        index=pandas.date_range(pandas.datetime(2017, 1, 1, 0), periods=8760, freq="H")
    )

    # Single family house (efh: Einfamilienhaus)
    demand["efh"] = bdew.HeatBuilding(
        temperature.index,
        temperature=temperature["TT_TU"],
        shlp_type="EFH",
        building_class=1,
        wind_class=1,
        name="EFH",
        ww_incl=False,
    ).get_normalized_bdew_profile()
    # Multi family house (mfh: Mehrfamilienhaus)
    demand["mfh"] = bdew.HeatBuilding(
        temperature.index,
        temperature=temperature["TT_TU"],
        shlp_type="MFH",
        building_class=2,
        wind_class=0,
        name="MFH",
        ww_incl=False,
    ).get_normalized_bdew_profile()

    # Don't heat if temp >= 20°
    demand["efh"][temperature["TT_TU"] >= 20] = 0
    demand["mfh"][temperature["TT_TU"] >= 20] = 0

    # Add to OEP
    with transaction.manager:
        session.add_all(
            [
                oep_models.OEPTimeseries(
                    name=constants.HouseType.EFH.value,
                    meta_data={
                        "name": "Heat demand for EFH",
                        "source": "oemof/demandlib",
                    },
                    data=demand["efh"].values.tolist(),
                ),
                oep_models.OEPTimeseries(
                    name=constants.HouseType.MFH.value,
                    meta_data={
                        "name": "Heat demand for MFH",
                        "source": "oemof/demandlib",
                    },
                    data=demand["mfh"].values.tolist(),
                ),
            ]
        )


def insert_dhw_timeseries():
    NUM_PERSONS = 30

    session = sqlahelper.get_session()

    for consumption in constants.WarmwaterConsumption:
        for p in range(NUM_PERSONS):
            hot_water_file = os.path.join(
                BASE_DIR,
                "stemp",
                "data",
                "hot_water",
                f"Warmwasser_{consumption.in_liters()}l_{p + 1}_DHW.txt",
            )
            hot_water_profile = pandas.read_csv(
                hot_water_file, header=None, escapechar="\\"
            )
            hot_water_energy_profile = hot_water_profile * constants.ENERGY_PER_LITER
            hot_water = oep_models.OEPHotWater(
                liter=consumption.in_liters() * (p + 1),
                data=hot_water_energy_profile[0].values.tolist(),
            )
            with transaction.manager:
                session.add(hot_water)


def insert_default_households():
    for house_type in constants.HouseType:
        for num_persons in range(1, 11):
            square_meters = num_persons * constants.QM_PER_PERSON
            household = Household(
                name=f"{house_type.value}_{num_persons}",
                number_of_persons=num_persons,
                house_type=house_type.name,
                square_meters=square_meters,
                heat_demand=(
                    square_meters * constants.ENERGY_PER_QM_PER_YEAR[house_type.name]
                ),
                heat_type=constants.HeatType.radiator.name,
                warm_water_per_day=(constants.WarmwaterConsumption.Medium.in_liters()),
                roof_area=constants.get_roof_square_meters(square_meters, house_type),
            )
            household.save()


def insert_assumptions():
    assumptions.insert_assumptions()


def insert_sources():
    sources.insert_sources()


def delete_households():
    Household.objects.all().delete()
    District.objects.all().delete()


def delete_oep_tables():
    try:
        oep_models.Base.metadata.drop_all()
    except oedialect.engine.ConnectionException:
        pass


def create_oep_tables():
    try:
        oep_models.Base.metadata.bind.execute(CreateSchema(oep_models.SCHEMA))
    except ProgrammingError:
        pass
    oep_models.Base.metadata.create_all()


def create_oemof_results_tables():
    oemof_results.Base.metadata.create_all()


def delete_stored_simulations():
    Parameter.objects.all().delete()
    Scenario.objects.all().delete()
    session = sqlahelper.get_session()
    with transaction.manager:
        session.query(oemof_results.OemofInputResult).delete()
        session.query(oemof_results.OemofScalar).delete()
        session.query(oemof_results.OemofSequence).delete()
        session.query(oemof_results.OemofData).delete()


def create_all():
    create_oep_tables()
    create_oemof_results_tables()
    insert_heat_demand()
    insert_default_households()
    insert_dhw_timeseries()
    insert_pv_and_temp()
    insert_scenarios()
    insert_sources()
    insert_assumptions()


@click.command()
@click.argument("commands", nargs=-1)
def execute(commands):
    if not isinstance(commands, tuple):
        commands = [commands]
    for command in commands:
        if command == "all":
            create_all()
        elif command == "reset_all":
            delete_households()
            delete_oep_tables()
            delete_stored_simulations()
            create_all()
        elif command == "heat":
            insert_heat_demand()
        elif command == "sources":
            insert_sources()
        elif command == "assumptions":
            insert_assumptions()
        elif command == "households":
            insert_default_households()
        elif command == "dhw":
            insert_dhw_timeseries()
        elif command == "pv_temp":
            insert_pv_and_temp()
        elif command == "scenarios":
            insert_scenarios()
        elif command == "oep_tables":
            create_oep_tables()
        elif command == "oemof_results_tables":
            create_oemof_results_tables()
        elif command == "delete_households":
            delete_households()
        elif command == "delete_oep_tables":
            delete_oep_tables()
        elif command == "delete_scenarios":
            delete_scenarios()
        elif command == "delete_simulations":
            delete_stored_simulations()
        else:
            raise KeyError(f'Unkown command "{command}"')


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    execute()
