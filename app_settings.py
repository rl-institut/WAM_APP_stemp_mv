
import os
import sqlalchemy
import sqlahelper
from configobj import ConfigObj
from importlib import import_module

import oedialect as _

from wam import settings
from db_apps import oemof_results
from stemp import oep_models

STORE_LP_FILE = False

ADDITIONAL_PARAMETERS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'attributes.cfg'))

LABELS = ConfigObj(os.path.join(settings.BASE_DIR, 'stemp', 'labels.cfg'))

# DB SETUP:
DB_URL = '{ENGINE}://{USER}:{PASSWORD}@{HOST}:{PORT}'


def build_db_url(db_name):
    conf = settings.config['DATABASES'][db_name]
    db_url = DB_URL + '/{NAME}' if 'NAME' in conf else DB_URL
    return db_url.format(**conf)


DB_SETUP = {
    'oemof_results': os.environ.get('STEMP_DB_RESULTS', 'DEFAULT'),
    'oep': os.environ.get('STEMP_DB_SCENARIOS', 'OEP'),
    'reiners_db': os.environ.get('STEMP_DB_INTERNAL', 'reiners_db')
}

# Add sqlalchemy for oemof_results:
engine = sqlalchemy.create_engine(build_db_url(DB_SETUP['oemof_results']))
sqlahelper.add_engine(engine, 'oemof_results')
oemof_results.Base.metadata.bind = engine

# Add OEP:
engine = sqlalchemy.create_engine(build_db_url(DB_SETUP['oep']))
sqlahelper.add_engine(engine, 'oep')
oep_models.Base.metadata.bind = engine

# Add reiner:
engine = sqlalchemy.create_engine(build_db_url(DB_SETUP['reiners_db']))
sqlahelper.add_engine(engine, 'reiners_db')


# SCENARIO SETUP:
ACTIVATED_SCENARIOS = list(filter(None, os.environ.get(
    'STEMP_ACTIVATED_SCENARIOS', "").split(',')))
SCENARIO_PATH = os.path.join('stemp', 'scenarios')


def import_scenario(scenario):
    filename = os.path.join(SCENARIO_PATH, scenario)
    splitted = filename.split(os.path.sep)
    module_name = '.'.join(splitted[1:])
    return import_module('.' + module_name, package=splitted[0])


class ScenarioModules(object):
    def __init__(self):
        self.modules = {}

    def __getitem__(self, module_name):
        if module_name in self.modules:
            return self.modules[module_name]
        else:
            module = import_scenario(module_name)
            self.modules[module_name] = module
            return module


# SCENARIO_MODULES are set in apps.StempConfig.ready:
SCENARIO_MODULES = ScenarioModules()
SCENARIO_PARAMETERS = {
    scenario: ConfigObj(
        os.path.join(
            settings.BASE_DIR,
            SCENARIO_PATH,
            f'{scenario}.cfg'
        )
    )
    for scenario in ACTIVATED_SCENARIOS
}
