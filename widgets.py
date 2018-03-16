
import warnings
from django.forms import Select, RadioSelect, Widget, Field


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
