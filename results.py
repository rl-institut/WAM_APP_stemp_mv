
from collections import namedtuple
from oemof.solph import analyzer


VisualizationMeta = namedtuple(
    'VisualizationMeta',
    [
        'label',
        'analyzer',
        'unit'
    ]
)
VisualizationMeta.__new__.__defaults__ = (None, None, {}, None, {})

DEFAULT_VISUALIZATIONS = {
    'lcoe': VisualizationMeta(
        label='LCOE',
        analyzer=analyzer.LCOEAnalyzer,
        unit='LCOE [€/kWh]'
    ),
}
