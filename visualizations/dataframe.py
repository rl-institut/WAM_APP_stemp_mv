
import numpy
import pandas
from itertools import accumulate

from utils.visualizations import VisualizationTemplate
from stemp.constants import RESULT_COLORS


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
    colored = (
        'Wärmekosten',
        'Investment',
        'Brennstoffkosten',
        'CO2',
        'Primärfaktor',
        'Primärenergie',
    )

    def __init__(self, data):
        super(ComparisonDataframe, self).__init__(
            'Technologievergleich',
            data=data,
        )
        self.bins = list(accumulate([r.percentage for r in RESULT_COLORS]))

    def set_data(self, data: pandas.DataFrame):
        self.data = data

    def _style_color(self, row):
        row_style = []
        for value in row:
            color_index = numpy.digitize(
                [(value - row.min()) / (row.max() - row.min())],
                self.bins
            )[0]
            color_index = min(color_index, len(RESULT_COLORS) - 1)
            row_style.append(RESULT_COLORS[color_index].style)
        return row_style

    def render_data(self):
        # Apply styles:
        styler = self.format_row_wise(self.data.style, self.formatters)
        styler = styler.apply(
            self._style_color,
            axis=1,
            subset=pandas.IndexSlice[self.colored, :]
        )
        return styler.render()
