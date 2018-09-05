
import pandas
from random import uniform
from enum import Enum, IntEnum

TIME_INDEX = [str(i + 1) + 'h' for i in range(24)]


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
            return 'efh'
        elif self.value == 1:
            return 'mfh'
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
