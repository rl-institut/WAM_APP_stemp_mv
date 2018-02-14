
from django.forms import Form, CharField

from oemof.outputlib import processing, views


class FormGroup(object):
    def __init__(self):
        self.forms = []

    def is_valid(self):
        return all([form.is_valid() for form in self.forms])

    def adapt_changes(self):
        for form in self.forms:
            form.adapt_changes()


class NodeFormGroup(FormGroup):
    """Base form can hold multiple forms (i.e. FlowForms)"""

    def __init__(self, node, param_results, *args, **kwargs):
        super(NodeFormGroup, self).__init__()
        self.label = str(node)
        self.flows = {}
        flows = views.get_flow_type(node, param_results)
        for flow_type, nodes in flows.items():
            self.flows[flow_type] = []
            for node_tuple in nodes:
                attributes = param_results[node_tuple]
                data = args[0] if len(args) > 0 else None
                attr_form = AttributesForm(
                    label=self.__attribute_label(flow_type, node_tuple),
                    top_label=self.label,
                    flow_type=flow_type,
                    attributes=attributes,
                    data=data
                )
                self.flows[flow_type].append(attr_form)
                self.forms.append(attr_form)

    @staticmethod
    def __attribute_label(flow_type, node_tuple):
        if flow_type == views.FlowType.Input:
            return str(node_tuple[0])
        elif flow_type == views.FlowType.Output:
            return str(node_tuple[1])
        else:
            return None


class AttributesForm(Form):
    def __init__(
            self, label, top_label, flow_type, attributes, data,
            *args, **kwargs
    ):
        super(AttributesForm, self).__init__(*args, **kwargs)
        self.label = label
        self.is_bound = data is not None
        self.data = data or {}

        scalar_attrs = attributes.get('scalars', {})
        for name, attr in scalar_attrs.items():
            field_name = '_'.join([top_label, flow_type.value, name])
            self.fields[field_name] = (
                CharField(label=name, initial=str(attr))
            )

        sequence_attrs = attributes.get('sequence', {})
        for name, attr in sequence_attrs.items():
            field_name = '_'.join([top_label, flow_type.value, name])
            self.fields[field_name] = (
                CharField(label=name, initial=str(attr))
            )

    def adapt_changes(self):
        pass


class EnergysystemFormGroup(FormGroup):
    """Creates forms from energysystem. Can contain multiple BaseForms"""
    def __init__(self, es, *args, **kwargs):
        super(EnergysystemFormGroup, self).__init__()
        param_results = processing.param_results(es)
        nodes = views.filter_nodes(param_results)
        for node in nodes:
            self.forms.append(NodeFormGroup(
                node, param_results, *args, **kwargs))
