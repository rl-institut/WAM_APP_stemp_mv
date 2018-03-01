
from collections import namedtuple
from django.forms import (
    Form, ChoiceField, IntegerField, FloatField, Select, CharField,
    MultipleChoiceField, CheckboxSelectMultiple, ModelForm, ModelChoiceField)

from stemp.widgets import DynamicSelectWidget, DynamicRadioWidget
from stemp.models import LoadProfile, Household, Simulation, District

PossibleField = namedtuple(
    'PossibleField',
    ['field_class', 'default_kwargs', 'init_function']
)
PossibleField.__new__.__defaults__ = (None,)


def init_choice_field(**data):
    labels = data.pop('choice_labels', data['choices'])
    data['choices'] = zip(data['choices'], labels)
    return ChoiceField(**data)


possible_fields = [
    PossibleField(
        ChoiceField,
        {'label': '<Kein Label gesetzt>', 'choices': []},
        init_choice_field
    ),
    PossibleField(
        IntegerField,
        {}
    ),
    PossibleField(
        FloatField,
        {}
    )
]


def get_possible_field(name):
    for field in possible_fields:
        if field.field_class.__name__ == name:
            return field
    return None


def create_field_from_config(parameter, data):
    # Get field class:
    field_key = data.pop('field', None)
    if field_key is None:
        raise KeyError(
            '"field" attribute not set in parameter "' + parameter + '".')

    field = get_possible_field(field_key)
    if field is None:
        raise TypeError(
            'Field "' + field_key +
            '" not included in allowed field types. See "possible fields".')

    # Initiate field with default kwargs and data:
    kwargs = field.default_kwargs
    kwargs.update(data)
    if field.init_function is not None:
        return field.init_function(**kwargs)
    else:
        return field.field_class(**kwargs)


class ChoiceForm(Form):
    def __init__(
            self, name, label=None, choices=None, submit_on_change=True,
            initial=None, widget=Select, *args, **kwargs
    ):
        super(ChoiceForm, self).__init__(*args, **kwargs)
        choices = [] if choices is None else choices
        label = label if label is not None else name
        attrs = {'class': 'btn btn-default'}
        if submit_on_change:
            attrs['onchange'] = 'this.form.submit();'
        self.fields[name] = ChoiceField(
            label=label,
            choices=choices,
            initial=initial,
            widget=widget(attrs=attrs)
        )


class ParameterForm(Form):
    def __init__(self, parameters, data=None, *args, **kwargs):
        super(ParameterForm, self).__init__(*args, **kwargs)
        if parameters is not None:
            for parameter, value in parameters.items():
                self.fields[parameter] = create_field_from_config(
                    parameter,
                    value
                )
        self.is_bound = data is not None
        self.data = data or {}


class EnergysystemForm(Form):
    def __init__(self, param_results, *args, **kwargs):
        super(EnergysystemForm, self).__init__(*args, **kwargs)


class LoadProfileForm(Form):
    """Tjaden, T.; Bergner, J.; Weniger, J.; Quaschning, V.:
    „Repräsentative elektrische Lastprofile für Einfamilienhäuser in
    Deutschland auf 1-sekündiger Datenbasis“, Datensatz,
    Hochschule für Technik und Wirtschaft HTW Berlin, 2015"""
    choices = LoadProfile.get_ids_and_names()
    profile = ChoiceField(
        label='Lastprofil',
        choices=choices,
        widget=DynamicSelectWidget(dynamic_url='load_profile/', initial=1)
    )


class HouseholdSelectForm(Form):
    profile = ModelChoiceField(
        queryset=Household.objects.all(),
        label='Haushalte',
        initial=0,
        widget=DynamicSelectWidget(
            dynamic_url='household_profile/',
            initial=1
        )
    )


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


class HouseholdForm(ModelForm):
    class Meta:
        model = Household
        exclude = ['district']


class DistrictForm(ModelForm):
    class Meta:
        model = District
        fields = ['name']
