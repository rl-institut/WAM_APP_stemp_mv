
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
    os.path.join(settings.BASE_DIR, 'stemp', 'scenarios', 'attributes.cfg'))

LABELS = ConfigObj(os.path.join(settings.BASE_DIR, 'stemp', 'labels.cfg'))
ENERGY_TIPS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'texts', 'energy_tips.cfg'))

stemp_config = settings.config['STEMP']

# DB SETUP:
DB_URL = '{ENGINE}://{USER}:{PASSWORD}@{HOST}:{PORT}'


def add_engine(engine_name):
    db_name = stemp_config.get(engine_name, DB_DEFAULT_SETUP[engine_name])
    conf = settings.config['DATABASES'][db_name]
    db_url = DB_URL + '/{NAME}' if 'NAME' in conf else DB_URL
    engine = sqlalchemy.create_engine(db_url.format(**conf))
    sqlahelper.add_engine(engine, engine_name)


DB_DEFAULT_SETUP = {
    'DB_RESULTS': 'DEFAULT',
    'DB_SCENARIOS': 'OEP',
    'DB_INTERNAL': 'reiners_db'
}

for setup in DB_DEFAULT_SETUP:
    add_engine(setup)

# Add sqlalchemy for oemof_results:
oemof_results.Base.metadata.bind = sqlahelper.get_engine('DB_RESULTS')

# Add OEP:
oep_models.Base.metadata.bind = sqlahelper.get_engine('DB_SCENARIOS')

# SCENARIO SETUP:
ACTIVATED_SCENARIOS = stemp_config.get('ACTIVATED_SCENARIOS', [])
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
