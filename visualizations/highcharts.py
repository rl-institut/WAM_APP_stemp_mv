from utils.highcharts import Highchart, RLI_THEME


class HCStemp(Highchart):
    setup = {}

    def __init__(self, data=None, **kwargs):
        super(HCStemp, self).__init__(
            data, options=self.setup, **kwargs)


class HCCosts(HCStemp):
    setup = {
        'chart': {
            'type': 'column'
        },
        'yAxis': {
            'title': {
                'text': 'Wärmekosten [€/kWh]'
            },
            'stackLabels': {
                'enabled': True,
                'format': "{total:.2f}€",
                'style': {
                    'fontWeight': 'bold',
                    'color': "(Highcharts.theme && Highcharts.theme.textColor) || 'gray'"
                }
            },
            'plotLines': [{
                'color': '#002E4F',
                'dashStyle': 'dot',
                'width': 1,
                'value': 150,
                'label': {
                    'align': 'right',
                    'style': {
                        'fontStyle': 'italic'
                    },
                    'text': 'Zielvorgabe CO2-Emissionen',
                    'x': -10
                },
                'zIndex': 300
            }],
        },
        'tooltip': {
            'headerFormat': '<b>{point.x}</b><br/>',
            'pointFormat': '{series.name}: {point.y:.2f}€<br/>Total: {point.stackTotal:.2f}€'
        },
        'plotOptions': {
            'column': {
                'stacking': 'normal',
                'dataLabels': {
                    'enabled': True,
                    'format': "{point.y:.2f}€",
                    'color': "(Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'"
                },
            }
        },
    }


class HCEmissions(HCStemp):
    setup = {
        'chart': {
            'type': 'column'
        },
        'title': {
            'text': 'CO2-Emissionen'
        },
        'subtitle': {
            'text': 'Gramm pro kWh'
        },
        'xAxis': {
            'type': 'category',
        },
        'yAxis': {
            'min': 0,
            'title': {
                'text': 'Gramm pro kwh'
            },
            'plotLines': [{
                'color': '#002E4F',
                'dashStyle': 'dot',
                'width': 1,
                'value': 150,
                'label': {
                    'align': 'right',
                    'style': {
                        'fontStyle': 'italic'
                    },
                    'text': 'Zielvorgabe CO2-Emissionen',
                    'x': -10
                },
                'zIndex': 300
            }],
            'plotBands': [{
                'color': 'rgba(230,250,248,.5)',
                'from': 0,
                'to': 150,
                'zIndex': 400
            }]
        },
        'tooltip': {
            'headerFormat':
                '<span style="font-size:10px">{point.key}</span><table>',
            'pointFormat':
                '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                '<td style="padding:0"><b>{point.y:.1f} g/kWh</b></td></tr>',
            'footerFormat': '</table>',
            'shared': True,
            'useHTML': True
        },
        'plotOptions': {
            'column': {
                'pointPadding': 0.2,
                'borderWidth': 0
            }
        }
    }


class HCScatter(Highchart):
    setup = {
        'chart': {
            'type': 'scatter',
            'zoomType': 'xy'
        },
        'title': {
            'text': 'Kosten vs CO2-Emissionen pro kWh'
        },
        'xAxis': {
            'title': {
                'enabled': True,
                'text': 'Kosten (cent/kWh)'
            },
            'startOnTick': True,
            'endOnTick': True,
            'showLastLabel': True,
        },
        'yAxis': {
            'title': {
                'text': 'CO2-Emissionen (g/kWh)'
            },
            'plotLines': [{
                'color': '#002E4F',
                'dashStyle': 'dot',
                'width': 1,
                'value': 150,
                'label': {
                    'align': 'right',
                    'style': {
                        'fontStyle': 'italic'
                    },
                    'text': 'Zielvorgabe CO2-Emissionen',
                    'x': -10
                },
                'zIndex': 300
            }],
            'plotBands': [{
                'color': '#e6faf8',
                'from': 0,
                'to': 150
            }],
        },
        'plotOptions': {
            'scatter': {
                'marker': {
                    'radius': 5,
                    'states': {
                        'hover': {
                            'enabled': True,
                            'lineColor': 'rgb(100,100,100)'
                        }
                    }
                },
                'states': {
                    'hover': {
                        'marker': {
                            'enabled': False
                        }
                    }
                },
                'tooltip': {
                    'headerFormat': '<b>{series.name}</b><br>',
                    'pointFormat': '{point.x} g/kWh, {point.y} cent/kWh'
                }
            }
        }
    }

    def __init__(self, data):
        super(HCScatter, self).__init__(
            data, style='scatter', theme=RLI_THEME, setup=self.setup)


class LCOEHighchart(HCCosts):
    def __init__(self, data):
        super(LCOEHighchart, self).__init__(data=data)
        self.set_options('title', {'text': 'Wärmekosten'})
        self.set_options('subtitle', {'text': 'Euro pro Kilowattstunde'})
