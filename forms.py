
from collections import defaultdict, OrderedDict
from itertools import chain
from django.forms import (
    Form, ChoiceField, IntegerField, Select, CharField, FloatField,
    BooleanField, MultipleChoiceField, CheckboxSelectMultiple, ModelForm,
    ModelChoiceField
)

from stemp.fields import HouseholdField, SubmitField
from stemp.widgets import (
    DynamicSelectWidget, DynamicRadioWidget, SliderInput, DistrictSubmitWidget)
from stemp.models import (
    LoadProfile, Household, Simulation, District, Question)
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


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
            widget=widget(attrs=attrs)
        )


class ParameterForm(Form):
    delimiter = '-'

    @staticmethod
    def __init_field(parameter_data, scenario):
        attributes = ('label', 'parameter_type', 'unit')
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
        else:
            raise TypeError(
                'Unknown value type "' + parameter_data['value_type'] +
                '" - cannot convert into FormField'
            )
        field.scenarios = [scenario]
        return field

    def __init__(self, parameters, data=None, *args, **kwargs):
        super(ParameterForm, self).__init__(*args, **kwargs)

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


class HouseholdQuestionsForm(Form):
    number_of_persons = IntegerField(
        widget=SliderInput(
            attrs={
                'class': 'input input--s',
                'id': 'hh_question_count'
            }
        ),
        label='Anzahl Personen im Haushalt',
        initial=2,
        max_value=10,
        min_value=1,
    )
    house_type = ChoiceField(
        label='Haushaltstyp',
        choices=Question.HOUSE_TYPES,
    )

    def hh_proposal(self):
        if self.data is not None:
            question = Question.objects.get(**self.cleaned_data)
            qh = question.question_household.filter(default=True)
            if len(qh) == 0:
                raise ObjectDoesNotExist(
                    'No household connected to current question with data:\n' +
                    str(self.cleaned_data)
                )
            elif len(qh) > 1:
                raise MultipleObjectsReturned(
                    'Multiple default households connected to current '
                    'question with data:\n' + str(self.cleaned_data)
                )
            return HouseholdForm(
                question_id=question.id, instance=qh.first().household)


class HouseholdSelectForm(Form):
    profile = ModelChoiceField(
        queryset=Household.objects.all(),
        label='Haushalt auswählen',
        initial=0,
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
            for household, count in hh_dict.items():
                self.fields[household] = HouseholdField(household, count)
        self.fields['add_household'] = SubmitField(
            widget=DistrictSubmitWidget,
            label="",
            initial='Haushalt hinzufügen'
        )


class HouseholdForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.question_id = kwargs.pop('question_id', None)
        super(HouseholdForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = "Name vom Haushalt"
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['name'].widget.attrs['class'] = 'input - group - field'
        self.fields['name'].widget.attrs['id'] = 'household-name'
        self.fields['heat_demand'].widget.attrs['class'] = 'input-group-field'

    class Meta:
        model = Household
        exclude = ['districts']


class DistrictForm(ModelForm):
    class Meta:
        model = District
        fields = ['name']
