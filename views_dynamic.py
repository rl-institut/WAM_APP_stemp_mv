
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from stemp import constants
from stemp.forms import HouseholdSelectForm
from stemp.models import District, Household


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


class HouseholdProfileView(TemplateView):
    template_name = 'stemp/load_profile.html'

    def get_context_data(self, household=None):
        if household is None:
            return {}
        else:
            hh = Household.objects.get(id=household)
            hc = hh.as_highchart()
            context = {
                'load_graph': hc.render('load_graph')
            }
            return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(int(
            request.GET.get('choice', 1)))
        return self.render_to_response(context)


class SwitchLoadView(TemplateView):
    template_name = 'stemp/load_switch.html'

    def get_context_data(self, switch, **kwargs):
        context = super(SwitchLoadView, self).get_context_data(**kwargs)
        if switch == 0:
            context['is_graph'] = False
            context['load'] = HouseholdSelectForm()
        else:
            context['is_graph'] = True
            dist = District.objects.get(id=1)
            hc = dist.as_highchart()
            context['load'] = hc.render('load_graph')
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(int(
            request.GET.get('choice', 0)))
        return self.render_to_response(context)
