import os
from collections import defaultdict, OrderedDict, ChainMap
from configobj import ConfigObj
from kopy.settings import BASE_DIR
from stemp.settings import PARAMETER_CONFIG
from db_apps.oep import OEPTable


class OEPScenario(OEPTable):
    schema = 'sandbox'
    table = 'kopernikus_simulation_parameter'
    structure = {
        "query": {
            "columns": [
                {
                    "name": "id",
                    "data_type": "bigserial",
                    "is_nullable": "NO"
                },
                {
                    "name": "scenario",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },
                {
                    "name": "component",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },
                {
                    "name": "parameter_type",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },
                {
                    "name": "parameter",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },
                {
                    "name": "value_type",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                },
                {
                    "name": "value",
                    "data_type": "varchar",
                    "character_maximum_length": "50"
                }
            ],
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id"
                }
            ]
        }
    }

    @classmethod
    def get_scenario_parameters(cls, scenario_name):
        where = 'scenario=' + scenario_name
        scenario = super(OEPScenario, cls).select(where)
        if not scenario:
            return None

        # Get default descriptions:
        attr_cfg_path = os.path.join(BASE_DIR, PARAMETER_CONFIG)
        description = ConfigObj(attr_cfg_path)

        parameters = defaultdict(OrderedDict)
        for item in scenario:
            comp = item['component']
            parameter = item['parameter']
            param_dict = ChainMap(
                {
                    'value': item['value'],
                    'value_type': item['value_type'],
                    'parameter_type': item['parameter_type']
                },
                description.get(comp, {}).get(parameter, {})
            )
            parameters[comp][parameter] = param_dict

        # Default factory has to be unset in order to support iterating over
        # dict in django template:
        parameters.default_factory = None
        return parameters
