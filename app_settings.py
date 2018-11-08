
import os
import sqlalchemy
import sqlahelper
from configobj import ConfigObj
from importlib import import_module

import oedialect as _

from wam import settings
from db_apps import oemof_results
from stemp import oep_models

ACTIVATED_VISUALIZATIONS = list(filter(None, os.environ.get(
    'ACTIVATED_VISUALIZATIONS', "").split(',')))
STORE_LP_FILE = True

ACTIVATED_SCENARIOS = list(filter(None, os.environ.get(
    'ACTIVATED_SCENARIOS', "").split(',')))
SCENARIO_PATH = os.path.join('stemp', 'scenarios')
SCENARIO_PARAMETERS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'scenarios', 'parameters.cfg'))

ADDITIONAL_PARAMETERS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'attributes.cfg'))

LABELS = ConfigObj(os.path.join(settings.BASE_DIR, 'stemp', 'labels.cfg'))

# DB SETUP:
DB_URL = '{ENGINE}://{USER}:{PASSWORD}@{HOST}:{PORT}'


def build_db_url(db_name):
    conf = settings.config['DATABASES'][db_name]
    db_url = DB_URL + '/{NAME}' if 'NAME' in conf else DB_URL
    return db_url.format(**conf)


# Add sqlalchemy for oemof_results:
engine = sqlalchemy.create_engine(build_db_url('DEFAULT'))
sqlahelper.add_engine(engine, 'oemof_results')
oemof_results.Base.metadata.bind = engine

# Add OEP:
engine = sqlalchemy.create_engine(build_db_url('DEFAULT'))
sqlahelper.add_engine(engine, 'oep')
oep_models.Base.metadata.bind = engine

# Add reiner:
engine = sqlalchemy.create_engine(build_db_url('reiners_db'))
sqlahelper.add_engine(engine, 'reiners_db')


# SCENARIO SETUP:
def import_scenario(scenario):
    filename = os.path.join(SCENARIO_PATH, scenario)
    splitted = filename.split(os.path.sep)
    module_name = '.'.join(splitted[1:])
    return import_module('.' + module_name, package=splitted[0])


SCENARIO_MODULES = {
    scenario: import_scenario(scenario)
    for scenario in ACTIVATED_SCENARIOS
}

