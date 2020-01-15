from collections import defaultdict
from django.forms import Select, Widget, NumberInput
from django.forms.widgets import CheckboxSelectMultiple
from django.utils import html

from wam.settings import APP_LABELS
from stemp.app_settings import ADDITIONAL_PARAMETERS
from utils.widgets import CustomWidget


class SelectWithDisabled(Select):
    """
    Subclass of Django's select widget that allows disabling options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    From: https://djangosnippets.org/snippets/2453/
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        disabled = False
        if isinstance(label, dict):
            label, disabled = label["label"], label["disabled"]
        option_dict = super(SelectWithDisabled, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if disabled:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict


class HouseholdWidget(Widget):
    template_name = "widgets/district_household.html"


class DistrictSubmitWidget(Widget):
    template_name = "widgets/district_submit.html"


class TechnologyWidget(CheckboxSelectMultiple):
    """
    From: https://www.abidibo.net/blog/2017/10/16/add-data-attributes-option-
    tags-django-admin-select-field/
    """

    template_name = "widgets/technology.html"

    def __init__(self, attrs=None, choices=(), information=None):
        super(TechnologyWidget, self).__init__(attrs, choices)
        self.information = {} if information is None else information

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super(TechnologyWidget, self).create_option(
            name, value, label, selected, index, subindex=None, attrs=None
        )
        data = self.information.get(value, {})
        for k, v in data.items():
            option["attrs"][k] = v

        return option


class SubmitWidget(Widget):
    """From https://djangosnippets.org/snippets/2312/"""

    def render(self, name, value, attrs=None, renderer=None):
        return '<input type="submit" name="%s" value="%s">' % (
            html.escape(name),
            html.escape(value),
        )


class HouseholdSummary(CustomWidget):
    def __init__(self, household, use_header=True, count=None):
        self.template_name = (
            "widgets/summary_household_accordion.html"
            if use_header
            else "widgets/summary_household_simple.html"
        )
        self.household = household
        self.count = count

    def get_context(self):
        return {"household": self.household, "count": self.count}


class TechnologySummary(CustomWidget):
    template_name = "widgets/summary_technology.html"

    def __init__(self, scenario_config):
        self.config = scenario_config

    def get_context(self):
        return {
            "name": self.config["LABELS"]["name"],
            "icon": self.config["LABELS"].get("icon", None),
            "icon_class": self.config["LABELS"].get("icon_class", None),
        }


class ParameterSummary(CustomWidget):
    template_name = "widgets/summary_parameter.html"

    def __init__(self, changed_parameters):
        self.parameters = changed_parameters

    def get_context(self):
        labels = defaultdict(dict)
        icons = {}
        for comp, parameters in self.parameters.items():
            icons[comp] = APP_LABELS["stemp"]["technologies"]["icons"].get(comp, None)
            for parameter in parameters:
                labels[comp][parameter] = (
                    ADDITIONAL_PARAMETERS.get(comp, {})
                    .get(parameter, ADDITIONAL_PARAMETERS.get(parameter, {}))
                    .get("label", parameter)
                )
        context = {"parameters": self.parameters, "labels": labels, "icons": icons}
        return context


class SliderInput(NumberInput):
    input_type = "number"
    template_name = "widgets/slider.html"

    def __init__(self, step_size=1, attrs=None):
        super(SliderInput, self).__init__(attrs)
        self.step_size = step_size

    def __get_precision(self):
        try:
            return len(str(self.step_size).split(".")[1])
        except IndexError:
            return 0

    def get_context(self, name, value, attrs):
        context = super(SliderInput, self).get_context(name, value, attrs)
        context["widget"]["step_size"] = self.step_size
        context["widget"]["precision"] = self.__get_precision()
        return context
