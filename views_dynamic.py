
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from stemp import constants
from stemp.models import Household


def get_next_household_name(request):
    name = request.GET['hh_name']
    i = 0
    while True:
        i += 1
        new_name = f'{name}_new{i:03d}'
        try:
            Household.objects.get(name=new_name)
        except ObjectDoesNotExist:
            return JsonResponse({'next': new_name})


def get_square_meters(request):
    value = float(request.GET['value'])
    sm = value * constants.QM_PER_PERSON
    return JsonResponse({'square_meters': sm})


def get_warm_water_energy(request):
    persons = float(request.GET['persons'])
    liter = float(request.GET['liter'])
    energy = liter * persons * constants.ENERGY_PER_LITER * 365
    return JsonResponse({'energy': energy})


def get_energy(request):
    choice = request.GET['choice']
    value = float(request.GET['value'])
    house_type = request.GET['house_type']
    if choice == 'square':
        sm = value
    elif choice == 'person':
        sm = value * constants.QM_PER_PERSON
    else:
        raise ValueError(f'Unknown choice "{choice}". Cannot calculate energy')
    energy = sm * constants.ENERGY_PER_QM_PER_YEAR[house_type]
    return JsonResponse({'energy': energy})


def get_roof_area(request):
    heat_option = request.GET['heat_option']
    value = int(request.GET['value'])
    if heat_option == 'person':
        sm = value * constants.QM_PER_PERSON
    elif heat_option == 'square':
        sm = value
    else:
        raise ValueError(f'Unknown heat option "{heat_option}"')
    house_type = request.GET['house_type']
    if house_type == 'EFH':
        sm /= 2
    elif house_type == 'MFH':
        sm /= 4
    else:
        raise ValueError(f'Unknown house type "{house_type}"')
    sm *= 0.4
    return JsonResponse({'roof_area': sm})
