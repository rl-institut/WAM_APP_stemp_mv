
import pandas
from random import uniform
from enum import Enum, IntEnum

TIME_INDEX = [str(i + 1) + 'h' for i in range(24)]

KELVIN = 273.15
ENERGY_PER_LITER = 0.058
QM_PER_PERSON = 44
QM_PER_PV_KW = 7
ENERGY_PER_QM_PER_YEAR = {'EFH': 90, 'MFH': 70}
LOCATION = (11.181475, 53.655119)  # Lützow (lon,lat)

DEFAULT_NUMBER_OF_PERSONS = 2
DEFAULT_LITER_PER_DAY = 44

EFH = ('EFH', 'Heat Demand EFH')
MFH = ('MFH', 'Heat Demand MFH')
HOUSE_TYPES = (
    (EFH[0], 'Einfamilienhaus'),
    (MFH[0], 'Mehrfamilienhaus')
)


class HeatType(Enum):
    radiator = 'Heizkörper'
    floor = 'Fussbodenheizung'


class DemandType(IntEnum):
    Single = 0
    District = 1

    def label(self):
        if self.value == 0:
            return 'Haushalt erstellen'
        elif self.value == 1:
            return 'Viertel erstellen'
        else:
            raise AttributeError(f'No label given for value={self.value}')

    def suffix(self):
        if self.value == 0:
            return 'single'
        elif self.value == 1:
            return 'district'
        else:
            raise AttributeError(f'No suffix given for value={self.value}')


class DistrictStatus(Enum):
    New = 'new'
    Changed = 'changed'
    Unchanged = 'unchanged'


class LoadProfile(Enum):
    Standard = pandas.Series(
        [uniform(0, 30) for i in range(24)],
        index=TIME_INDEX
    )
    HighLoad = pandas.Series(
        [uniform(0, 30) for i in range(24)],
        index=TIME_INDEX
    )

    def __init__(self, profile):
        self.profile = profile

    def __new__(cls, profile):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __eq__(self, other):
        return self.value == other

    @classmethod
    def get_profile(cls, index):
        assert isinstance(index, int)
        for member in cls.__members__.values():
            if member.value == index:
                return member.profile
        raise IndexError('Index "' + str(index) + '" not found in LoadProfile')
