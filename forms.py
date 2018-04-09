
from collections import defaultdict
from django.forms import (
    Form, ChoiceField, IntegerField, Select, CharField, FloatField,
    BooleanField, MultipleChoiceField, CheckboxSelectMultiple, ModelForm,
    ModelChoiceField
)

from stemp.fields import HouseholdField, SubmitField
from stemp.widgets import DynamicSelectWidget, DynamicRadioWidget, SliderInput
from stemp.models import LoadProfile, Household, Simulation, District


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
    delimiter = '-'

    @staticmethod
    def __init_field(parameter_data):
        if parameter_data['value_type'] == 'boolean':
            return BooleanField(initial=bool(parameter_data['value']))
        elif parameter_data['value_type'] == 'float':
            if all(map(lambda x: x in parameter_data, ('min', 'max'))):
                step_size = parameter_data.get('step_size', 0.1)
                return FloatField(
                    widget=SliderInput(
                        step_size=step_size,
                    ),
                    initial=float(parameter_data['value']),
                    min_value=float(parameter_data['min']),
                    max_value=float(parameter_data['max']),
                )
            else:
                return FloatField(initial=float(parameter_data['value']))
        elif parameter_data['value_type'] == 'integer':
            if all(map(lambda x: x in parameter_data, ('min', 'max'))):
                return IntegerField(
                    widget=SliderInput,
                    initial=int(parameter_data['value']),
                    min_value=int(parameter_data['min']),
                    max_value=int(parameter_data['max']),
                )
            else:
                return IntegerField(initial=int(parameter_data['value']))
        else:
            raise TypeError(
                'Unknown value type "' + parameter_data['value_type'] +
                '" - cannot convert into FormField'
            )

    def __init__(self, parameters, data=None, *args, **kwargs):
        super(ParameterForm, self).__init__(*args, **kwargs)
        if parameters is not None:
            for component, component_data in parameters.items():
                for parameter, parameter_data in component_data.items():
                    field_name = self.delimiter.join((component, parameter))
                    field = self.__init_field(parameter_data)
                    field.group = component
                    self.fields[field_name] = field

        self.is_bound = data is not None
        self.data = data or {}

    def prepared_data(self):
        data = defaultdict(dict)
        if not self.is_bound:
            for field_name, field in self.fields.items():
                component, parameter = field_name.split(self.delimiter)
                data[component][parameter] = field.initial
            return data
        for item, value in self.cleaned_data.items():
            component, parameter = item.split(self.delimiter)
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
    count = IntegerField(
        widget=SliderInput(attrs={'id': 'hh_question_count'}),
        label='Anzahl Personen im Haushalt',
        initial=2,
        max_value=10,
        min_value=1,
    )
    at_home = BooleanField(
        label='Sind Personen tagsüber zu Hause?',
        required=False
    )
    modernised = BooleanField(
        label='Ist das Haus modernisiert?',
        required=False
    )

    def hh_proposal(self):
        if self.data is not None:
            return HouseholdForm()


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
                self.fields[household] = HouseholdField(
                    household, count)
        self.fields['add_household'] = SubmitField(
            label="",
            initial='Haushalt hinzufügen'
        )

    def as_table(self):
        return self._html_output(
            normal_row=(
                '<tr%(html_class_attr)s>'
                '%(errors)s%(field)s%(help_text)s'
                '</tr>'
            ),
            error_row='<tr><td colspan="2">%s</td></tr>',
            row_ender='</td></tr>',
            help_text_html='<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False
        )

    def _html_output(self, normal_row, error_row, row_ender, help_text_html,
                     errors_on_separate_row):
        html_output = super(DistrictListForm, self)._html_output(
                normal_row, error_row, row_ender, help_text_html,
                errors_on_separate_row
            )
        if len(self.fields) <= 1:
            html_output = (
                '<tr><td>Noch keine Haushalte im Quartier</td></tr>' +
                html_output
            )
        return html_output


class HouseholdForm(ModelForm):
    class Meta:
        model = Household
        exclude = ['districts']


class DistrictForm(ModelForm):
    class Meta:
        model = District
        fields = ['name']
