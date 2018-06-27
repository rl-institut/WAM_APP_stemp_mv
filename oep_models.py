
from collections import defaultdict, OrderedDict, ChainMap
from configobj import ConfigObj
from stemp.app_settings import ADDITIONAL_PARAMETERS
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
                    "character_maximum_length": 50
                },
                {
                    "name": "component",
                    "data_type": "varchar",
                    "character_maximum_length": 50
                },
                {
                    "name": "unit",
                    "data_type": "varchar",
                    "character_maximum_length": 50
                },
                {
                    "name": "parameter_type",
                    "data_type": "varchar",
                    "character_maximum_length": 50
                },
                {
                    "name": "parameter",
                    "data_type": "varchar",
                    "character_maximum_length": 50
                },
                {
                    "name": "value_type",
                    "data_type": "varchar",
                    "character_maximum_length": 50
                },
                {
                    "name": "value",
                    "data_type": "varchar",
                    "character_maximum_length": 50
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

        # Get secondary attributes:
        description = ConfigObj(ADDITIONAL_PARAMETERS)

        parameters = defaultdict(OrderedDict)
        for item in scenario:
            item.pop('id')
            item.pop('scenario')
            comp = item.pop('component')
            parameter = item.pop('parameter')
            param_dict = ChainMap(
                item,
                description.get(
                    comp, {}).get(parameter, description.get(parameter, {}))
            )
            parameters[comp][parameter] = param_dict

        # Default factory has to be unset in order to support iterating over
        # dict in django template:
        parameters.default_factory = None
        return parameters
