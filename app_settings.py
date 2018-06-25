
from os import path
from wam import settings
import sqlalchemy
from sqlalchemy import orm
import sqlahelper
from configobj import ConfigObj

# Add sqlalchemy:
db_url = '{engine}://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format(
    engine=settings.config['DEFAULT']['ENGINE'].split('.')[-1],
    **settings.config['DEFAULT']
)
engine = sqlalchemy.create_engine(db_url)
sqlahelper.add_engine(engine)
SqlAlchemySession = orm.sessionmaker(bind=engine)
from db_apps.oemof_results import Base
Base.metadata.bind = engine
Base.metadata.create_all()

SCENARIO_PATH = path.join('stemp', 'scenarios')

PARAMETER_CONFIG = 'stemp/attributes.cfg'

LABELS = ConfigObj(path.join(settings.BASE_DIR, 'stemp', 'labels.cfg'))
