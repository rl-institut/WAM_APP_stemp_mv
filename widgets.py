
import warnings
from django.forms import Select, RadioSelect


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
