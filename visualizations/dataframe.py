
import pandas
import numpy
from collections import namedtuple
from functools import partial

from utils.visualizations import VisualizationTemplate
from stemp.constants import CATEGORIZED_COLOR_NAMES

CATEGORIES = len(CATEGORIZED_COLOR_NAMES)
CATEGORY_STATS = namedtuple(
    'CategoryStats', ['min', 'max', 'is_demand_related'])


class Dataframe(VisualizationTemplate):
    template_name = 'visualizations/dataframe.html'

    def __init__(self, title, data=None):
        self.title = title
        self.data = None
        super(Dataframe, self).__init__(data)

    def set_data(self, data: pandas.DataFrame):
        self.data = data

    def render_data(self):
        return self.data.style.render()

    def get_context(self, **kwargs):
        context = super(Dataframe, self).get_context(**kwargs)
        context['title'] = self.title
        context['data'] = self.render_data()
        return context

    @staticmethod
    def format_row_wise(styler, formatter):
        for row, row_formatter in formatter.items():
            row_num = styler.index.get_loc(row)

            for col_num in range(len(styler.columns)):
                styler._display_funcs[(row_num, col_num)] = row_formatter
        return styler


class ComparisonDataframe(Dataframe):
    formatters = {
        'Wärmekosten': lambda x: f'{x:.2f} €/kWh',
        'Investment': lambda x: f'{x:,.0f} €',
        'CO2': lambda x: f'{x:,.0f} g/kWh',
        'Brennstoffkosten': lambda x: f'{x:,.0f} €/Jahr',
        'Primärfaktor': lambda x: f'{x:.1f}',
        'Primärenergie': lambda x: f'{x:,.0f} kWh',
    }
    color_ranges = {
        'Wärmekosten': CATEGORY_STATS(0, 0.2, False),
        'Investment': CATEGORY_STATS(0.1, 0.4, True),
        'CO2': CATEGORY_STATS(100.0, 300.0, False),
        'Brennstoffkosten': CATEGORY_STATS(0.0, 0.1, True),
        'Primärfaktor': CATEGORY_STATS(0.0, 3.0, False),
        'Primärenergie': CATEGORY_STATS(0.0, 3.0, True),
    }

    def __init__(self, data):
        self.demand = data.loc['Demand'][0]
        data = data.drop('Demand')
        super(ComparisonDataframe, self).__init__(
            'Technologievergleich',
            data=data,
        )
        self.__color_bins = {
            cat: [
                (
                    (cat_range.max - cat_range.min) /
                    (CATEGORIES - 2) * i + cat_range.min
                )
                for i in range(CATEGORIES - 1)
            ]
            for cat, cat_range in self.color_ranges.items()
        }

    def set_data(self, data: pandas.DataFrame):
        self.data = data

    def _style_color_per_category(self, df: pandas.DataFrame):
        def set_quality(value, category):
            if self.color_ranges[category].is_demand_related:
                value /= self.demand
            cat_num = numpy.digitize(
                [value], self.__color_bins[category], right=True)[0]
            return list(CATEGORIZED_COLOR_NAMES.values())[cat_num]

        series = []
        for cname, row in df.iterrows():
            if cname not in self.color_ranges:
                series.append(row)
                continue
            series.append(row.apply(partial(set_quality, category=cname)))
        concat = pandas.concat(series, axis=1)
        return concat.transpose()

    def render_data(self):
        # Apply styles:
        styler = self.format_row_wise(self.data.style, self.formatters)
        styler = styler.apply(self._style_color_per_category, axis=None)
        return styler.render()
