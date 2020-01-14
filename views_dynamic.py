"""Functions to handle dynamic AJAX-requests"""

from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from stemp import constants
from user_sessions.utils import check_session
from stemp.models import Household
from stemp.widgets import HouseholdSummary


@check_session
def check_pending(request, session):
    """
    Returns true if all results are ready
    """
    ready = all([not scenario.is_pending() for scenario in session.scenarios])
    return JsonResponse({"ready": ready})


def get_next_household_name(request):
    """
    Dynamic household naming

    If household name is already present in DB, a counting number prefix is added
    """
    name = request.GET["hh_name"]
    i = 0
    while True:
        i += 1
        new_name = f"{name}_new{i:03d}"
        try:
            Household.objects.get(name=new_name)
        except ObjectDoesNotExist:
            return JsonResponse({"next": new_name})


def get_square_meters(request):
    """Calculates square meters related to number of persons"""
    persons = float(request.GET["persons"])
    sm = round(persons * constants.QM_PER_PERSON)
    return JsonResponse({"square_meters": sm})


def get_warm_water_energy(request):
    """Calculates warm water consumption related to number of persons"""
    persons = float(request.GET["persons"])
    warmwater_consumption = constants.WarmwaterConsumption(
        int(request.GET["warmwater_consumption"])
    )
    liter = warmwater_consumption.in_liters()
    energy = round(liter * persons * constants.ENERGY_PER_LITER * 365)
    return JsonResponse({"energy": energy, "daily_warm_water": liter})


def get_heat_demand(request):
    """Calculates heat demand related to square meters and household type"""
    sm = float(request.GET["sm"])
    house_type = request.GET["house_type"]
    heat_demand = round(sm * constants.ENERGY_PER_QM_PER_YEAR[house_type])
    return JsonResponse({"heat_demand": heat_demand})


def get_roof_area(request):
    """Calculates roof area related to square meters and household type"""
    sm = int(request.GET["sm"])
    house_type = constants.HouseType[request.GET["house_type"]]
    sm = round(constants.get_roof_square_meters(sm, house_type))
    return JsonResponse({"roof_area": sm})


def get_household_summary(request):
    """Provides household summary widget for given household ID"""
    hh_id = int(request.GET["hh_id"])
    return HttpResponse(
        HouseholdSummary(Household.objects.get(pk=hh_id), use_header=False)
    )
