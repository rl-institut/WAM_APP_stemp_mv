
import pandas
from random import uniform
from enum import Enum

TIME_INDEX = [str(i + 1) + 'h' for i in range(24)]


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
