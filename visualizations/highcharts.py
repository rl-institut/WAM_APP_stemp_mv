from copy import deepcopy
from utils.highcharts import Highchart


class LCOEHighchart(Highchart):
    setup = {
        "chart": {"type": "column"},
        "yAxis": {
            "title": {"text": "Wärmekosten [€/kWh]"},
            "stackLabels": {
                "enabled": True,
                "format": "{total:.2f}€",
                "style": {
                    "fontWeight": "bold",
                    "color": "(Highcharts.theme && Highcharts.theme.textColor) || 'gray'",
                },
            },
            "plotLines": [
                {
                    "color": "#002E4F",
                    "dashStyle": "dot",
                    "width": 1,
                    "value": 150,
                    "label": {
                        "align": "right",
                        "style": {"fontStyle": "italic"},
                        "text": "Zielvorgabe CO2-Emissionen",
                        "x": -10,
                    },
                    "zIndex": 300,
                }
            ],
        },
        "tooltip": {
            "headerFormat": "<b>{point.x}</b><br/>",
            "pointFormat": "{series.name}: {point.y:.2f}€",
        },
        "plotOptions": {
            "column": {
                "stacking": "normal",
                "dataLabels": {
                    "enabled": True,
                    "format": "{point.y:.2f}€",
                    "color": "(Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'",
                },
            }
        },
    }

    sum_line_options = {
        "color": "black",
        "showInLegend": False,
        "dataLabels": {
            "enabled": True,
            "format": "{point.y:.2f}€",
            "align": "left",
            "verticalAlign": "middle",
            "filter": {"property": "x", "value": 0.3, "operator": "=="},
        },
        "enableMouseTracking": False,
        "marker": {"enabled": False},
    }
    colors = {
        "Betriebskosten": "#fc8e65",
        "Brennstoffkosten": "#55aae5",
        "Investitionskosten": "#7fadb7",
        "Strombezugskosten": "#fce288",
        "Stromgutschrift": "#f69c3a",
    }

    def __init__(self, data):
        super(LCOEHighchart, self).__init__()
        self.set_dict_options(self.setup)
        self.add_pandas_data_set(data, series_type="column")
        self.set_options("title", {"text": "Wärmekosten"})
        self.set_options("subtitle", {"text": "Euro pro Kilowattstunde"})
        self.set_options("colors", [self.colors[column] for column in data.columns])

        # Add lcoe sum per scenario as horizontal lines:
        summed_data = data.sum(axis=1)
        for i, lcoe_sum in enumerate(summed_data):
            current_options = deepcopy(self.sum_line_options)
            current_options["dataLabels"]["filter"]["value"] = i + 0.3
            self.add_data_set(
                [[i - 0.3, lcoe_sum], [i + 0.3, lcoe_sum]],
                series_type="line",
                name=f"{i}",
                **current_options,
            )
