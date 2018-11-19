
from collections import defaultdict, OrderedDict, ChainMap
from stemp import app_settings
from sqlalchemy import Column, VARCHAR, BIGINT, JSON
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from sqlalchemy.ext.declarative import declarative_base
import sqlahelper


SCHEMA = 'sandbox'

Base = declarative_base()


class OEPScenario(Base):
    __tablename__ = 'kopernikus_simulation_parameter'
    __table_args__ = {'schema': SCHEMA}

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
        scenario_parameters = session.query(cls).filter_by(
            scenario=f'{scenario_name}_{demand_type.suffix()}').all()
        if not scenario_parameters:
            scenario_parameters = session.query(cls).filter_by(
                scenario=f'{scenario_name}').all()
        if not scenario_parameters:
            raise KeyError(f'Scenario "{scenario_name}" not found in OEP')

        # Get secondary attributes:
        description = app_settings.ADDITIONAL_PARAMETERS

        parameters = defaultdict(OrderedDict)
        for scenario_parameter in scenario_parameters:
            item = scenario_parameter.__dict__
            item.pop('_sa_instance_state')
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


class OEPTimeseries(Base):
    __tablename__ = 'kopernikus_timeseries'
    __table_args__ = {'schema': SCHEMA}

    id = Column(BIGINT, primary_key=True)
    name = Column(VARCHAR(50))
    meta_data = Column(JSON)
    data = Column(ARRAY(FLOAT))
