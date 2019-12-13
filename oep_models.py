import os
from collections import defaultdict, OrderedDict, ChainMap
import sqlahelper
import transaction
from sqlalchemy import Column, VARCHAR, BIGINT, JSON, INT
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from sqlalchemy.ext.declarative import declarative_base

from stemp import app_settings


SCHEMA = "sandbox"

Base = declarative_base()


class OEPScenario(Base):
    __tablename__ = "kopernikus_simulation_parameter"
    __table_args__ = {"schema": SCHEMA}

    id = Column(BIGINT, primary_key=True)
    scenario = Column(VARCHAR(50))
    component = Column(VARCHAR(50))
    unit = Column(VARCHAR(50))
    parameter_type = Column(VARCHAR(50))
    parameter = Column(VARCHAR(50))
    value_type = Column(VARCHAR(50))
    value = Column(VARCHAR(50))

    @classmethod
    def get_scenario_parameters(cls, scenario_name, demand_type):
        session = sqlahelper.get_session()
        with transaction.manager:
            scenario_parameters = (
                session.query(cls)
                .filter_by(scenario=f"{scenario_name}_{demand_type.suffix()}")
                .all()
            )
            if not scenario_parameters:
                scenario_parameters = (
                    session.query(cls).filter_by(scenario=f"{scenario_name}").all()
                )
            if not scenario_parameters:
                raise KeyError(f'Scenario "{scenario_name}" not found in OEP')

            # Get secondary attributes:
            description = app_settings.ADDITIONAL_PARAMETERS
            parameters = defaultdict(OrderedDict)

            for scenario_parameter in scenario_parameters:
                item = scenario_parameter.__dict__.copy()
                item.pop("_sa_instance_state")
                item.pop("id")
                item.pop("scenario")
                comp = item.pop("component")
                parameter = item.pop("parameter")
                param_dict = ChainMap(
                    item,
                    description.get(comp, {}).get(
                        parameter, description.get(parameter, {})
                    ),
                )
                parameters[comp][parameter] = param_dict

        # Default factory has to be unset in order to support iterating over
        # dict in django template:
        parameters.default_factory = None
        return parameters


class OEPTimeseries(Base):
    __tablename__ = "kopernikus_timeseries"
    __table_args__ = {"schema": SCHEMA}

    id = Column(BIGINT, primary_key=True)
    name = Column(VARCHAR(50))
    meta_data = Column(JSON)
    data = Column(ARRAY(FLOAT))


temp_meta_file = os.path.join(
    os.path.dirname(__file__), "metadata", "coastdat_temp.json"
)
with open(temp_meta_file) as meta_file:
    dhw_meta = meta_file.read()


class OEPHotWater(Base):
    __tablename__ = "kopernikus_warmwasser"
    __table_args__ = {"schema": SCHEMA, "comment": dhw_meta}

    id = Column(BIGINT, primary_key=True)
    liter = Column(INT)
    data = Column(ARRAY(FLOAT))
