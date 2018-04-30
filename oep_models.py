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
        return scenario
