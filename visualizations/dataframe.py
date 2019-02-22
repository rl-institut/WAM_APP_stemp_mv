
import numpy
import pandas
from collections import OrderedDict
from itertools import accumulate

from utils.visualizations import VisualizationTemplate
from stemp.constants import RESULT_COLORS
from stemp.app_settings import LABELS


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
        'Wärmekosten': lambda x: (
                f'<pre>{x:.2f}' + f"{' €/kWh':<7}</pre>"),
        'Investition': lambda x: (
                f'<pre>{x:,.0f}' + f"{' €':<7}</pre>"),
        'CO2 Emissionen': lambda x: (
                f'<pre>{x:,.0f}' + f"{' g/kWh':<7}</pre>"),
        'Brennstoffkosten': lambda x: (
                f'<pre>{x:,.0f}' + f"{' €/Jahr':<7}</pre>"),
        'Primärenergiefaktor': lambda x: (
            f'<pre>{x:.1f}' + f"{'':<7}</pre>" if x <= 1.3
            else f'<pre>1.3 ({x:.1f})*' + f"{'':<7}</pre>"
        ),
        'Primärenergie': lambda x: (
            f'<pre>{x:,.0f}' + f"{' kWh':<7}</pre>"),
    }
    colored = (
        'Wärmekosten',
        'Investition',
        'Brennstoffkosten',
        'CO2 Emissionen',
        'Primärenergiefaktor',
        'Primärenergie',
    )
    information = {k: v for k, v in LABELS['result']['information'].items()}

    def __init__(self, data):
        super(ComparisonDataframe, self).__init__(
            'Technologievergleich',
            data=data,
        )
        self.bins = list(accumulate([r.percentage for r in RESULT_COLORS]))

    def set_data(self, data: pandas.DataFrame):
        self.data = data

    def __style_color(self, row):
        row_style = []
        for value in row:
            color_index = numpy.digitize(
                [(value - row.min()) / (row.max() - row.min())],
                self.bins
            )[0]
            color_index = min(color_index, len(RESULT_COLORS) - 1)
            row_style.append(RESULT_COLORS[color_index].style)
        return row_style

    def __create_column_name_with_info(self, column):
        info = self.information.get(column)

        if info is not None:
            return f"""\
{column}
<span class ="has-tip--no-border" data-tooltip title='{info}' data-position="right" data-alignment="center">
  <i class="icon ion-information-circled icon--small info-box"></i>
</span>
"""
        else:
            return column

    def render_data(self):
        # Exchange columns with columns plus information:
        columns_dict = OrderedDict(
            [
                (i, self.__create_column_name_with_info(i))
                for i in self.data.index
            ]
        )
        self.data.index = pandas.Index(columns_dict.values())

        # Apply styles:
        styler = self.format_row_wise(
            self.data.style,
            {
                columns_dict[column]: formatter
                for column, formatter in self.formatters.items()
            }
        )

        if len(self.data.columns) > 1:
            styler = styler.apply(
                self.__style_color,
                axis=1,
                subset=pandas.IndexSlice[
                    [columns_dict[colored] for colored in self.colored],
                    :
                ]
            )
        pro_con_align = [
            {
                "selector": f"td.data.row{row}.col{col}",
                "props": [("text-align", "left")]
            }
            for row in range(6, 8)
            for col in range(len(self.data.columns))
        ]
        styler.set_table_styles(
            [
                {
                    "selector": "td",
                    "props": [("text-align", "right")]
                },
            ] + pro_con_align
        )
        return styler.render()
