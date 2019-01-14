
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
DEFAULT_LITER_PER_DAY_WITHOUT_SHOWER = 22


class WarmwaterConsumption(Enum):
    Low = 0
    Medium = 1
    High = 2

    def in_liters(self):
        return {
            WarmwaterConsumption.Low: 43,
            WarmwaterConsumption.Medium: 66,
            WarmwaterConsumption.High: 109,
        }.get(self)


EFH = ('EFH', 'Heat Demand EFH')
MFH = ('MFH', 'Heat Demand MFH')
HOUSE_TYPES = (
    (EFH[0], 'Einfamilienhaus'),
    (MFH[0], 'Mehrfamilienhaus')
)


class HouseType(Enum):
    EFH = 'Einfamilienhaus'
    MFH = 'Mehrfamilienhaus'


class HeatType(Enum):
    radiator = 'Heizkörper'
    floor = 'Fussbodenheizung'


class DemandType(IntEnum):
    Single = 0
    District = 1

    def label(self):
        return {
            DemandType.Single: 'Haushalt erstellen',
            DemandType.District: 'Viertel erstellen'
        }.get(self)

    def suffix(self):
        return {
            DemandType.Single: 'single',
            DemandType.District: 'district'
        }.get(self)


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


def get_roof_square_meters(household_square_meters, house_type):
    sm = household_square_meters
    if house_type == HouseType.EFH:
        sm /= 2
    elif house_type == HouseType.MFH:
        sm /= 4
    else:
        raise KeyError(
            f'Could not calculate roof area from household type '
            f'"{house_type}"'
        )
    sm *= 0.4
    return sm
