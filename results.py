
from warnings import warn
# from functools import partial
from collections import namedtuple
import pandas
from oemof.outputlib import views, processing
from oemof.solph import economics
from oemof.tools.economics import LCOE

from utils.highcharts import Highchart


VisualizationMeta = namedtuple(
    'VisualizationMeta',
    [
        'label',
        'data_function',
        'default_none',
        'value_function',
        'total_function',
        'total_hc',
        'detail_function',
        'detail_hc'
    ]
)
VisualizationMeta.__new__.__defaults__ = (None, None, {}, None, {})

Visualization = namedtuple(
    'Visualization',
    [
        'label',
        'value',
        'total',
        'detail'
    ]
)
Visualization.__new__.__defaults__ = (None, None, None)

DEFAULT_VISUALIZATIONS = {
    'lcoe': VisualizationMeta(
        label='LCOE',
        data_function=economics.calculate_lcoe,
        default_none=LCOE(0.0, 0.0, 0.0),
        value_function=lambda x: '{:.2f} €/kWh'.format(x.sum().sum()),
        total_function=lambda x: x.sum(),
        total_hc={
            'style': 'pie',
            'title': 'LCOE',
            'y_title': 'LCOE [€/kWh]',
        },
        detail_function=lambda x: x,
        detail_hc={
            'style': 'column',
            'title': 'LCOE',
            'y_title': 'LCOE [€/kWh]',
            'stacked': True,
        }
    ),
    # 'investment': VisualizationMeta(
    #     label='Investment',
    #     data_function=oemof_results.get_invest_for_node,
    #     value_function=lambda x: '{:.2f} €'.format(x.sum().sum()),
    #     total_function=lambda x: x,
    #     total_hc={
    #         'style': 'column',
    #         'title': 'Investment',
    #         'y_title': 'Investment [€]',
    #     }
    # ),
    # 'energy': VisualizationMeta(
    #     label='Energieflüsse',
    #     data_function=partial(
    #         oemof_results.sum_flows_for_node,
    #         flow_type=views.FlowType.Output
    #     ),
    #     value_function=lambda x: '{:.2f} kWh'.format(x.sum().sum()),
    #     total_function=lambda x: x,
    #     total_hc={
    #         'style': 'column',
    #         'title': 'Energie',
    #         'y_title': 'Energie [kWh]',
    #     }
    # )
}


def oemof_result_to_json(data):
    json_results = {}
    for key, value in data.items():
        if isinstance(key, tuple):
            new_key = ','.join(key)
        else:
            new_key = key

        if isinstance(value, dict):
            value = oemof_result_to_json(value)
        if (
                isinstance(value, pandas.Series) or
                isinstance(value, pandas.DataFrame)
        ):
            new_value = value.to_json()
        else:
            new_value = value
        json_results[new_key] = new_value
    return json_results


class Results(object):
    def __init__(self, results=None, param_results=None):
        self.results = self.__results_with_str_keys(results)
        self.param_results = self.__results_with_str_keys(param_results)
        self.cost_results = economics.cost_results(self.results, param_results)
        self.visualizations = {}
        self.node_results = {}
        self.node_flows = {}
        self.json = {}

    @staticmethod
    def __results_with_str_keys(result):
        if isinstance(next(iter(result.keys()))[0], str):
            return result
        else:
            return processing.convert_keys_to_strings(result)

    def add_visualization(self, name, visualization):
        if isinstance(visualization, VisualizationMeta):
            self.visualizations[name] = visualization
        else:
            warn(
                'Error while adding visualization: Visualization "' + name +
                '" is not of type "VisualizationMeta"'
            )

    def load_data(self, data):
        self.json = data

    def __check_nodes(self, nodes):
        if isinstance(nodes, views.NodeOption):
            return list(views.filter_nodes(
                self.results,
                nodes,
                exclude_busses=True
            ))

        if isinstance(nodes, list):
            return views.get_node_by_name(self.results, *nodes)

        try:
            nodes = views.NodeOption[nodes]
        except KeyError:
            return [views.get_node_by_name(self.results, nodes)]
        else:
            return list(views.filter_nodes(
                self.results,
                nodes,
                exclude_busses=True
            ))

    def get_node_results(self, node):
        if node not in self.node_results:
            self.node_results[node] = views.node(self.results, node)
        return self.node_results[node]

    def create_visualization_data(self, config):
        if config is None:
            return {}

        for vis_name in config:
            visualization = DEFAULT_VISUALIZATIONS.get(vis_name)
            if visualization is not None:
                nodes = self.__check_nodes(config[vis_name])
                nodes = [node for node in nodes if node is not None]

                data = {}
                for node in nodes:
                    node_data = visualization.data_function(
                        node, self.results, self.cost_results)
                    node_data = (
                        visualization.default_none
                        if node_data is None else node_data
                    )
                    data[str(node)] = node_data
                self.store_data(vis_name, data)

    def get_visualizations(self):
        for vis_name, data in self.json.items():
            df = pandas.DataFrame.from_dict(data, orient='index')
            meta = self.visualizations.get(
                vis_name,
                DEFAULT_VISUALIZATIONS.get(vis_name)
            )
            if meta is None:
                warn(
                    'Could not get visualization meta for visualization "' +
                    vis_name + '"'
                )
                continue
            params = {}
            attrs = ['value', 'total', 'detail']
            for attr in attrs:
                attr_fcuntion = getattr(meta, attr + '_function')
                if attr_fcuntion is not None:
                    if attr == 'value':
                        params[attr] = attr_fcuntion(df)
                    else:
                        params[attr] = Highchart(
                            data=attr_fcuntion(df),
                            **getattr(meta, attr + '_hc')
                        ).render(vis_name + '_' + attr)
            yield Visualization(
                label=meta.label,
                **params
            )

    def store_data(self, key, data):
        self.json[key] = data


class Comparison(object):
    def __init__(self, simulations):
        self.results = {}

        for simulation in simulations:
            result = Results()
            if simulation.result is not None:
                result.load_data(simulation.result.data)
            self.results[simulation.id] = result

    def get_visualizations(self):
        visualizations = {}
        for sim_id, result in self.results.items():
            visualizations[sim_id] = result.get_visualizations()
        return visualizations
