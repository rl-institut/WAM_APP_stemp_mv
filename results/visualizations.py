
from collections import namedtuple

from stemp.results import aggregations as agg
from stemp.results import highcharts
from stemp.results import rankings

Visualization = namedtuple(
    'Visualization',
    ['name', 'aggregation', 'template']
)

VISUALIZATIONS = [
    Visualization(
        'ranked_invest',
        agg.InvestmentAggregation,
        rankings.Ranking(
            'Anfangsinvestitionen',
            ['Szenario', 'Investitionskosten'],
            unit='€'
        )
    ),
    Visualization(
        'ranked_co2',
        agg.CO2Aggregation,
        rankings.Ranking(
            'CO2 Verbrauch',
            ['Szenario', 'CO2 Verbrauch'],
            unit='g/kWh',
            precision=2
        )
    ),
    Visualization(
        'lcoe',
        agg.LCOEAggregation,
        highcharts.HCCosts(
            title='Wärmekosten',
            subtitle='Euro pro Kilowattstunde'
        )
    ),
    Visualization(
        'invest',
        agg.InvestmentAggregation,
        highcharts.HCCosts(
            title='Investition',
            subtitle='Euro'
        )
    ),
    Visualization(
        'size',
        agg.SizeAggregation,
        highcharts.HCStemp(
            title='Installierte Leistungen',
            subtitle='kW',
            stacked=True
        )
    ),
    Visualization(
        'demand',
        agg.TotalDemandAggregation,
        highcharts.HCStemp(title='Verbrauch', stacked=True)
    ),
    Visualization(
        'co2',
        agg.CO2Aggregation,
        highcharts.HCStemp(
            title='CO2-Verbrauch',
            subtitle='g/kWh',
            stacked=True
        )
    ),
    Visualization(
        'profile',
        agg.ProfileAggregation,
        highcharts.HCStemp(title='Profile', style='line')
    )
]
