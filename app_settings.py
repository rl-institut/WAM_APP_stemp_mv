
"""
App-specific settings

These settings are initialized when `wam.settings` are called,
before app itself gets started.
"""

import os
import sqlalchemy
import sqlahelper
from configobj import ConfigObj
from importlib import import_module

import oedialect as _

from wam import settings
from db_apps import oemof_results
from stemp import oep_models

ADDITIONAL_PARAMETERS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'scenarios', 'attributes.cfg'))

LABELS = ConfigObj(os.path.join(settings.BASE_DIR, 'stemp', 'labels.cfg'))
ENERGY_TIPS = ConfigObj(
    os.path.join(settings.BASE_DIR, 'stemp', 'texts', 'energy_tips.cfg'))

stemp_config = settings.config['STEMP']

STORE_LP_FILE = stemp_config.get('STORE_LP_FILE', 'False') == 'True'
DEFAULT_PERIODS = int(stemp_config.get('DEFAULT_PERIODS', 8760))

# DB SETUP:
DB_URL = '{ENGINE}://{USER}:{PASSWORD}@{HOST}:{PORT}'


def add_engine(db_connection):
    """
    Creates and adds DB connection from configuration file by given name

    First, it is checked which db configuration should be used (default, or specified in
    config file). Second, engine is created by DB parameters for given DB connection
    and added to slqahelper with connection name.

    Parameters
    ----------
    db_connection (str):
        Database connection to set up
    """
    db_name = stemp_config.get(db_connection, DB_DEFAULT_SETUP[db_connection])
    conf = settings.config['DATABASES'][db_name]
    db_url = DB_URL + '/{NAME}' if 'NAME' in conf else DB_URL
    engine = sqlalchemy.create_engine(db_url.format(**conf))
    sqlahelper.add_engine(engine, db_connection)


DB_DEFAULT_SETUP = {
    'DB_RESULTS': 'DEFAULT',
    'DB_SCENARIOS': 'OEP',
}

if 'READTHEDOCS' not in os.environ:
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
    """
    Scenario with given name is imported from scenario module

    Parameters
    ----------
    scenario (str):
        Name of scenario module

    Returns
    -------
    module:
        Imported scenario module
    """
    filename = os.path.join(SCENARIO_PATH, scenario)
    splitted = filename.split(os.path.sep)
    module_name = '.'.join(splitted[1:])
    return import_module('.' + module_name, package=splitted[0])


class ScenarioModules(object):
    """
    Class to import scenario modules once needed

    Scenarios cannot be imported within app_settings as not all resources are yet ready.
    Therefore, scenario modules are imported once when accessed later.
    """
    def __init__(self):
        self.modules = {}

    def __getitem__(self, module_name):
        if module_name in self.modules:
            return self.modules[module_name]
        else:
            module = import_scenario(module_name)
            self.modules[module_name] = module
            return module


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
