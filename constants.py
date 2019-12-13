"""
Collection of stemp-related constants and enumerations
"""

from collections import namedtuple
from enum import Enum, IntEnum

TIME_INDEX = [str(i + 1) + "h" for i in range(24)]

KELVIN = 273.15
ENERGY_PER_LITER = 0.058
QM_PER_PERSON = 44
QM_PER_PV_KW = 7
ENERGY_PER_QM_PER_YEAR = {"EFH": 90, "MFH": 70}
LOCATION = (11.181475, 53.655119)  # Lützow (lon,lat)

DEFAULT_NUMBER_OF_PERSONS = 2
DEFAULT_LITER_PER_DAY_WITHOUT_SHOWER = 22

BHKW_FULL_LOAD_HOURS = 5000
BHKW_OPTIMISATION_STEP = 10

ResultColor = namedtuple("ResultColor", ["quality", "percentage", "style"])
RESULT_COLORS = (
    ResultColor("good", 0.2, "background-color: #0A6164; color: #fefefe;"),
    ResultColor("neutral", 0.6, "background-color: #E6E1BD;"),
    ResultColor("bad", 0.2, "background-color: #DA4225; color: #fefefe;"),
)
assert sum([r.percentage for r in RESULT_COLORS]) == 1


class WarmwaterConsumption(Enum):
    """
    Enumeration for Warmwater consumption levels
    """

    Low = 0
    Medium = 1
    High = 2

    def in_liters(self):
        """
        Warmwater level in liters

        Returns
        -------
        int:
            Warmwater consumption in liters
        """
        return {
            WarmwaterConsumption.Low: 43,
            WarmwaterConsumption.Medium: 66,
            WarmwaterConsumption.High: 109,
        }.get(self)

    @staticmethod
    def from_liters(liters):
        """
        Returns warmwater consumption level for given liters

        Parameters
        ----------
        liters (int):
            warmwater consumption in liters

        Returns
        -------
        WarmwaterConsumption:
            Warmwater consumption level
        """
        return {
            43: WarmwaterConsumption.Low,
            66: WarmwaterConsumption.Medium,
            109: WarmwaterConsumption.High,
        }.get(liters)


class HouseType(Enum):
    """
    House type enumeration
    """

    EFH = "Einfamilienhaus"
    MFH = "Mehrfamilienhaus"


class HeatType(Enum):
    """
    Heat type enumeration
    """

    radiator = "Heizkörper"
    floor = "Fussbodenheizung"


class DemandType(IntEnum):
    """
    Enumeration to differentiate between single household and district
    """

    Single = 0
    District = 1

    def label(self):
        """
        Label for given demand type

        Returns
        -------
        str:
            Label of current demand type
        """
        return {
            DemandType.Single: "Haushalt erstellen",
            DemandType.District: "Viertel erstellen",
        }.get(self)

    def suffix(self):
        """
        Suffix for current demand type

        This is needed in order to load scenario parameters which are dependent on
        demand type.

        Returns
        -------
        str:
            Demand type suffix
        """
        return {DemandType.Single: "single", DemandType.District: "district"}.get(self)


class DistrictStatus(Enum):
    """
    District status enumeration
    """

    New = "new"
    Changed = "changed"
    Unchanged = "unchanged"


def get_roof_square_meters(household_square_meters, house_type):
    """
    Calculates potential roof square meters available for PV

    Parameters
    ----------
    household_square_meters (int):
        Square meters of current household
    house_type (HouseType):
        Single household or district

    Returns
    -------
    float:
        Roof square meters available for PV
    """
    sm = household_square_meters
    if house_type == HouseType.EFH:
        sm /= 2
    elif house_type == HouseType.MFH:
        sm /= 4
    else:
        raise KeyError(
            f"Could not calculate roof area from household type " f'"{house_type}"'
        )
    sm *= 0.4
    return sm
