
from collections import defaultdict
import warnings
from django.forms import Select, RadioSelect, Widget, NumberInput
from django.forms.widgets import CheckboxSelectMultiple
from django.utils import html

from wam.settings import APP_LABELS
from stemp.app_settings import ADDITIONAL_PARAMETERS
from utils.widgets import CustomWidget


class DynamicWidgetMixin(object):
    """Extends ChoiceWidgets to show dynamic views based on chosen option"""
    template_name = 'widgets/dynamic_select.html'

    def __init__(
            self,
            url,
            attrs,
            widget,
            dynamic_function_name,
            dynamic_id,
            initial
    ):
        self.url = url
        self.widget = widget
        self.dynamic_function_name = dynamic_function_name
        self.dynamic_id = dynamic_id
        self.initial = initial

        if attrs is None:
            attrs = {}

        # # Set choice id to connect Select with Graph:
        # choice_name = attrs.get('name', 'choice_name')
        # attrs['name'] = choice_name
        # if isinstance(widget, RadioSelect):
        #     self.choice_name = 'input[name=' + choice_name + ']:radio'
        # else:
        #     self.choice_name = '#' + choice_name

        # Set OnChange attribute:
        if 'onChange' in attrs:
            warnings.warn('"OnChange" event will be overwritten by '
                          'SelectGraphWidget')
        self.changed_attrs = attrs

    def update_context(self, context):
        if self.widget.input_type == 'radio':
            choice_name = 'input:radio[name=' + context['widget']['name'] + ']'
        else:
            choice_name = 'select[name=' + context['widget']['name'] + ']'
        context.update({
            'dynamic_url': self.url,
            'choice_name': choice_name,
            'widget_template': self.widget.template_name,
            'dynamic_id': self.dynamic_id,
            'dynamic_function_name': self.dynamic_function_name,
            'initial': self.initial
        })


class DynamicSelectWidget(DynamicWidgetMixin, Select):
    def __init__(
            self,
            dynamic_url,
            attrs=None,
            choices=(),
            dynamic_function_name='dynamic_widget',
            dynamic_id='dynamic_id',
            initial=0
    ):
        DynamicWidgetMixin.__init__(
            self,
            dynamic_url,
            attrs,
            Select,
            dynamic_function_name,
            dynamic_id,
            initial
        )
        Select.__init__(self, self.changed_attrs, choices)

    def get_context(self, name, value, attrs):
        context = Select.get_context(self, name, value, attrs)
        DynamicWidgetMixin.update_context(self, context)
        return context


class DynamicRadioWidget(DynamicWidgetMixin, RadioSelect):
    def __init__(
            self,
            dynamic_url,
            attrs=None,
            choices=(),
            dynamic_function_name='dynamic_widget',
            dynamic_id='dynamic_id',
            initial=0
    ):
        DynamicWidgetMixin.__init__(
            self,
            dynamic_url,
            attrs,
            RadioSelect,
            dynamic_function_name,
            dynamic_id,
            initial
        )
        RadioSelect.__init__(self, self.changed_attrs, choices)

    def get_context(self, name, value, attrs):
        context = RadioSelect.get_context(self, name, value, attrs)
        DynamicWidgetMixin.update_context(self, context)
        return context


class SelectWithDisabled(Select):
    """
    Subclass of Django's select widget that allows disabling options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    From: https://djangosnippets.org/snippets/2453/
    """

    def create_option(self, name, value, label, selected, index,
                      subindex=None, attrs=None):
        disabled = False
        if isinstance(label, dict):
            label, disabled = label['label'], label['disabled']
        option_dict = super(SelectWithDisabled, self).create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs
        )
        if disabled:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


class HouseholdWidget(Widget):
    template_name = 'widgets/district_household.html'


class DistrictSubmitWidget(Widget):
    template_name = 'widgets/district_submit.html'


class TechnologyWidget(CheckboxSelectMultiple):
    """
    From: https://www.abidibo.net/blog/2017/10/16/add-data-attributes-option-
    tags-django-admin-select-field/
    """
    template_name = 'widgets/technology.html'

    def __init__(self, attrs=None, choices=(), information=None):
        super(TechnologyWidget, self).__init__(attrs, choices)
        self.information = {} if information is None else information

    def create_option(
            self,
            name,
            value,
            label,
            selected,
            index,
            subindex=None,
            attrs=None
    ):
        option = super(TechnologyWidget, self).create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=None,
            attrs=None
        )
        data = self.information.get(value, {})
        for k, v in data.items():
            option['attrs'][k] = v

        return option


class SubmitWidget(Widget):
    """From https://djangosnippets.org/snippets/2312/"""
    def render(self, name, value, attrs=None, renderer=None):
        return '<input type="submit" name="%s" value="%s">' % (
            html.escape(name), html.escape(value)
        )


class HouseholdSummary(CustomWidget):
    template_name = 'widgets/summary_household.html'

    def __init__(self, household, use_header=True):
        self.household = household
        self.base_class = (
            'widgets/summary_household_accordion.html'
            if use_header else 'widgets/summary_household_simple.html'
        )

    def get_context(self):
        return {
            'household': self.household,
            'warm_water_demand': self.household.get_hot_water_profile().sum(),
            'base_class': self.base_class
        }


class TechnologySummary(CustomWidget):
    template_name = 'widgets/summary_technology.html'

    def __init__(self, scenario_config):
        self.config = scenario_config

    def get_context(self):
        return {
            'name': self.config['LABELS']['name'],
            'icon': self.config['LABELS'].get('icon', None),
            'icon_class': self.config['LABELS'].get('icon_class', None),
        }


class ParameterSummary(CustomWidget):
    template_name = 'widgets/summary_parameter.html'

    def __init__(self, changed_parameters):
        self.parameters = changed_parameters

    def get_context(self):
        labels = defaultdict(dict)
        icons = {}
        for comp, parameters in self.parameters.items():
            icons[comp] = APP_LABELS['stemp']['technologies']['icons'].get(
                comp, None)
            for parameter in parameters:
                labels[comp][parameter] = (
                    ADDITIONAL_PARAMETERS.get(comp, {}).get(
                        parameter, ADDITIONAL_PARAMETERS.get(parameter, {})
                    ).get('label', parameter)
                )
        context = {
            'parameters':  self.parameters,
            'labels': labels,
            'icons': icons
        }
        return context


class SliderInput(NumberInput):
    input_type = 'number'
    template_name = 'widgets/slider.html'

    def __init__(self, step_size=1, attrs=None):
        super(SliderInput, self).__init__(attrs)
        self.step_size = step_size

    def __get_precision(self):
        try:
            return len(str(self.step_size).split('.')[1])
        except IndexError:
            return 0

    def get_context(self, name, value, attrs):
        context = super(SliderInput, self).get_context(name, value, attrs)
        context['widget']['step_size'] = self.step_size
        context['widget']['precision'] = self.__get_precision()
        return context
