
from collections import defaultdict, OrderedDict, namedtuple
from itertools import chain

from django.forms import (
    Form, ChoiceField, IntegerField, Select, CharField, FloatField,
    BooleanField, MultipleChoiceField, CheckboxSelectMultiple, ModelForm,
    ModelChoiceField, NumberInput, HiddenInput
)
from crispy_forms.helper import FormHelper

from utils.highcharts import Highchart
from stemp import constants
from stemp.fields import HouseholdField, SubmitField
from stemp.widgets import (
    DynamicRadioWidget, SliderInput, DistrictSubmitWidget,
    TechnologyWidget)
from stemp.models import (Household, Simulation, District)


ValueUnit = namedtuple('ValueUnit', ['value', 'unit'])


class ChoiceForm(Form):
    def __init__(
            self, name, label=None, choices=None, submit_on_change=True,
            initial=None, field=ChoiceField, widget=Select, *args, **kwargs
    ):
        super(ChoiceForm, self).__init__(*args, **kwargs)
        choices = [] if choices is None else choices
        label = label if label is not None else name
        attrs = {'class': 'btn btn-default'}
        if submit_on_change:
            attrs['onchange'] = 'this.form.submit();'
        self.fields[name] = field(
            label=label,
            choices=choices,
            initial=initial,
            widget=widget(attrs=attrs),
        )


class TechnologyForm(Form):
    def __init__(
            self, name, label=None, choices=None,
            initial=None, information=None, *args, **kwargs
    ):
        super(TechnologyForm, self).__init__(*args, **kwargs)
        choices = [] if choices is None else choices
        label = label if label is not None else name
        attrs = {'class': 'btn btn-default'}
        information = {} if information is None else information
        self.fields[name] = MultipleChoiceField(
            label=label,
            choices=choices,
            initial=initial,
            widget=TechnologyWidget(attrs=attrs, information=information),
        )


class ParameterForm(Form):
    delimiter = '-'

    @staticmethod
    def __init_field(parameter_data, scenario):
        attributes = ('label', 'description', 'parameter_type', 'unit')
        attrs = {
            attr_name: parameter_data[attr_name]
            for attr_name in attributes
            if attr_name in parameter_data
        }
        if parameter_data['value_type'] == 'boolean':
            field = BooleanField(initial=bool(parameter_data['value']))
        elif parameter_data['value_type'] == 'float':
            if all(map(lambda x: x in parameter_data, ('min', 'max'))):
                step_size = parameter_data.get('step_size', "0.1")
                min_value = float(parameter_data['min'])
                min_value = (
                    int(min_value)
                    if int(min_value) == min_value else min_value
                )
                field = FloatField(
                    widget=SliderInput(
                        step_size=step_size,
                        attrs=attrs
                    ),
                    initial=float(parameter_data['value']),
                    min_value=min_value,
                    max_value=float(parameter_data['max'])
                )
            else:
                field = FloatField(initial=parameter_data['value'])
        elif parameter_data['value_type'] == 'integer':
            if all(map(lambda x: x in parameter_data, ('min', 'max'))):
                field = IntegerField(
                    widget=SliderInput(attrs=attrs),
                    initial=int(parameter_data['value']),
                    min_value=int(parameter_data['min']),
                    max_value=int(parameter_data['max'])
                )
            else:
                field = IntegerField(initial=int(parameter_data['value']))
        elif parameter_data['value_type'] == 'hidden':
            field = CharField(
                widget=HiddenInput,
                initial=parameter_data['value']
            )
        else:
            raise TypeError(
                'Unknown value type "' + parameter_data['value_type'] +
                '" - cannot convert into FormField'
            )
        field.scenarios = [scenario]
        return field

    def __init__(self, parameters, data=None, *args, **kwargs):
        super(ParameterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.template = 'forms/parameter_form.html'

        field_order = OrderedDict()
        for scenario, scenario_data in parameters:
            for component, component_data in scenario_data.items():
                if component not in field_order:
                    field_order[component] = []
                for parameter, parameter_data in component_data.items():
                    field_name = self.delimiter.join((component, parameter))
                    if field_name in self.fields:
                        self.fields[field_name].scenarios.append(scenario)
                        continue
                    field = self.__init_field(parameter_data, scenario)
                    field.type = parameter_data.get('parameter_type')
                    if field.type == 'costs':
                        field_order[component].insert(0, field_name)
                    else:
                        field_order[component].append(field_name)
                    field.group = component
                    self.fields[field_name] = field

        self.order_fields(chain(*field_order.values()))

        self.is_bound = data is not None
        self.data = data or {}

    def prepared_data(self, scenario=None):
        def belongs_to_scenario():
            if (
                    scenario is not None and
                    scenario not in self.fields[field_name].scenarios
            ):
                return False
            return True

        data = defaultdict(dict)
        if not self.is_bound:
            for field_name, field in self.fields.items():
                if not belongs_to_scenario():
                    continue
                component, parameter = field_name.split(self.delimiter)
                data[component][parameter] = field.initial
            return data
        for field_name, value in self.cleaned_data.items():
            if not belongs_to_scenario():
                continue
            component, parameter = field_name.split(self.delimiter)
            data[component][parameter] = value
        return data

    @staticmethod
    def get_changed_parameters(parameters, data):
        """Compare original parameters with user entries and return diffs"""

        # Transform parameters and data into comparable shapes
        # original-shape (to get unit as well):
        # Dict['category', DICT['parameter', ('value', 'unit')]]
        # posted-shape:
        # Dict['category', DICT['parameter', 'value']]

        # parameters-shape:
        # List[
        #     Tuple[
        #         'scenario', Dict[
        #             'category', Dict[
        #                 'parameter', Dict['attribute', 'value']
        #             ]
        #         ]
        #     ]
        # ]
        original = defaultdict(dict)
        for (_, scenario_params) in parameters:
            for category, category_params in scenario_params.items():
                for parameter, attributes in category_params.items():
                    original[category][parameter] = ValueUnit(
                        attributes['value'],
                        attributes['unit']
                    )

        # posted-shape:
        # Dict['category-parameter', 'value']
        posted = defaultdict(dict)
        skip = ['csrfmiddlewaretoken', 'scenario']
        for cat_param, value in data.items():
            if cat_param not in skip:
                category, parameter = cat_param.split('-')
                posted[category][parameter] = value

        # Compare and return changed parameters by category
        changed = defaultdict(dict)
        for category, category_params in original.items():
            for parameter, (value, unit) in category_params.items():
                if value != posted[category][parameter]:
                    val = posted[category][parameter]
                    changed[category][parameter] = ValueUnit(val, unit)
        changed.default_factory = None
        return changed


class HouseholdForm(ModelForm):
    number_of_persons = IntegerField(
        widget=NumberInput(
            attrs={
                'class': "input input-group-field input--s",
                'id': 'number_of_persons'
            }
        ),
        label='Anzahl Personen im Haushalt',
        initial=constants.DEFAULT_NUMBER_OF_PERSONS,
    )
    heat_demand_hand = IntegerField(
        widget=NumberInput(
            attrs={
                'class': "input input-group-field input--s",
                'id': 'heat_hand'
            }
        ),
        label='Manuell eingeben'
    )
    roof_area_hand = IntegerField(
        widget=NumberInput(
            attrs={
                'class': "input-group-field input input--m",
                'id': 'roof_hand'
            }
        ),
        label='Manuell eingeben'
    )

    class Meta:
        model = Household
        fields = '__all__'
        widgets = {
            'heat_demand': HiddenInput(),
            'roof_area': HiddenInput(),
            'square_meters': HiddenInput(),
            'warm_water_per_day': NumberInput(
                attrs={
                    'class': "input-group-field input input--m",
                    'readonly': True
                }
            )
        }
        error_messages = {
            'name': {
                'required': (
                    'Bitte geben Sie einen Namen für den neuen Haushalt an.')
            }
        }

    class Media:
        js = ('stemp/js/household.js',)

    def __init__(self, only_house_type=None, *args, **kwargs):
        kwargs['initial'] = {
            'square_meters': (
                constants.DEFAULT_NUMBER_OF_PERSONS * constants.QM_PER_PERSON
            ),
            'warm_water_per_day': (
                constants.WarmwaterConsumption.Medium.in_liters()
            ),
            'heat_demand_hand': (
                constants.DEFAULT_NUMBER_OF_PERSONS * constants.QM_PER_PERSON *
                constants.ENERGY_PER_QM_PER_YEAR[constants.HouseType.EFH.name]
            ),
            'roof_area_hand': round(constants.get_roof_square_meters(
                constants.DEFAULT_NUMBER_OF_PERSONS * constants.QM_PER_PERSON,
                constants.HouseType.EFH
            ))
        }
        super(HouseholdForm, self).__init__(*args, **kwargs)
        if only_house_type is not None:
            self.fields['house_type'] = CharField(
                label='Haustyp',
                widget=HiddenInput(
                    attrs={
                        'id': 'id_house_type',
                        'value': only_house_type.name
                    }
                )
            )
            self.house_type_fix = only_house_type
        self.helper = FormHelper()
        self.helper.template = 'forms/household_form.html'
        self.hotwater_hc = self.create_hotwater_chart()

    @staticmethod
    def create_hotwater_chart():
        water = [
            ['Baden / Duschen / Körperpflege', 44.28],
            ['Toilette', 33.21],
            ['Wäsche waschen', 14.76],
            ['Kleingewerbeanteil', 11.07],
            ['Geschirrspülen', 7.38],
            ['Raumreinigung / Auto / Garten', 7.38],
            ['Essen / Trinken', 4.92]
        ]
        water_hc = Highchart()
        water_hc.set_options(
            'title', {'text': 'Trinkwasserverbrauch pro Person'})
        water_hc.set_options(
            'subtitle',
            {
                'text': (
                    'Durchschnittswerte bezogen ' +
                    'auf die Wasserabgabe an Haushalte'
                )
            }
        )
        water_hc.set_options(
            'colors',
            [
                'LightCoral',
                'DeepSkyBlue',
                'IndianRed',
                'DodgerBlue',
                'Salmon',
                'SkyBlue',
                'SteelBlue'
            ]
        )
        water_hc.set_options(
            'plotOptions',
            {
                'pie': {
                    'dataLabels': {
                        'format': '{point.name}: {y} l',
                    }
                }
            }
        )
        water_hc.add_data_set(water, series_type='pie')
        return water_hc


class HouseholdSelectForm(Form):
    profile = ModelChoiceField(
        queryset=Household.objects.all(),
        label='Haushalt auswählen',
        initial=0,
    )

    class Media:
        js = ('stemp/js/household_select.js',)

    def __init__(self, only_house_type=None, *args, **kwargs):
        super(HouseholdSelectForm, self).__init__(*args, **kwargs)
        if only_house_type is not None:
            self.fields['profile'].queryset = Household.objects.filter(
                house_type=only_house_type.name).all()
        self.helper = FormHelper(self)
        self.helper.template = 'forms/household_list_form.html'


class DistrictSelectForm(Form):
    district = ModelChoiceField(
        queryset=District.objects.all(),
        label='Quartier',
        initial=0,
        widget=Select()
    )


class DynamicChoiceForm(Form):
    def __init__(self, name, label, choices, dynamic_url, initial=0, **kwargs):
        super(DynamicChoiceForm, self).__init__()
        self.fields[name] = ChoiceField(
            label=label,
            choices=choices,
            initial=initial,
            widget=DynamicRadioWidget(
                dynamic_url=dynamic_url, initial=initial, **kwargs)
        )


class DistrictHouseholdsForm(Form):
    def __init__(self, district_dict=None):
        super(DistrictHouseholdsForm, self).__init__()
        if district_dict is None:
            return
        district_id = district_dict['district']
        self.name = District.objects.get(pk=district_id).name
        households = district_dict['households']
        for i, (household_id, amount) in enumerate(households):
            self.fields['hh_' + str(i)] = IntegerField(
                initial=amount,
                label=Household.objects.get(pk=household_id).name,
                min_value=0
            )


class SaveSimulationForm(Form):
    simulation_name = CharField(
        label='Simulation speichern unter',
        max_length=255
    )


class ComparisonForm(Form):
    def __init__(self, initial=0):
        super(ComparisonForm, self).__init__()
        choices = [(sim.id, sim.name) for sim in Simulation.objects.all()]
        self.fields['comparison'] = MultipleChoiceField(
            label='Vergleiche Szenarios',
            choices=choices,
            initial=initial,
            widget=CheckboxSelectMultiple
        )


class DistrictListForm(Form):
    def __init__(self, hh_dict):
        super(DistrictListForm, self).__init__()
        if hh_dict is not None:
            for hh_id, count in hh_dict.items():
                household = Household.objects.get(pk=hh_id)
                hh_field = HouseholdField(household, count)
                hh_field.group = household.house_type
                self.fields[hh_id] = hh_field
        self.fields['add_efh'] = SubmitField(
            widget=DistrictSubmitWidget,
            label="",
            initial='Einzelhaus hinzufügen'
        )
        self.fields['add_efh'].group = 'EFH'
        self.fields['add_mfh'] = SubmitField(
            widget=DistrictSubmitWidget,
            label="",
            initial='Mehrfamilienhaus hinzufügen'
        )
        self.fields['add_mfh'].group = 'MFH'

    def efh(self):
        return [
            self[field_name]
            for field_name, field in self.fields.items()
            if field.group == 'EFH'
        ]

    def mfh(self):
        return [
            self[field_name]
            for field_name, field in self.fields.items()
            if field.group == 'MFH'
        ]


class DistrictForm(ModelForm):
    class Meta:
        model = District
        fields = ['name']
