
from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer

from utils.visualizations import VisualizationTemplate


class RankingDataHandler(object):
    def __init__(self, ascending=True, precision=0):
        self.ascending = ascending
        self.precision = precision

    def handle(self, data):
        data.sort_values(ascending=self.ascending, inplace=True)
        data = data.round(decimals=self.precision)
        return data


class Ranking(VisualizationTemplate):
    template_name = 'widgets/ranking.html'

    def __init__(self, title, headers, unit, data=None, **kwargs):
        self.title = title
        self.headers = headers
        self.unit = unit
        self.data = None
        self.data_handler = RankingDataHandler(**kwargs)
        super(Ranking, self).__init__(data)

    def set_data(self, data):
        self.data = data.sum(axis=1)
        self.data = self.data_handler.handle(self.data)

    def get_context(self, **kwargs):
        return {
            'div_id': kwargs.get('div_id', f'rank_{self.id}'),
            'div_kwargs': kwargs.get('div_kwargs', {}),
            'title': self.title,
            'headers': self.headers,
            'data': self.data,
            'unit': self.unit
        }

    def render(self, **kwargs):
        renderer = get_default_renderer()
        context = self.get_context(**kwargs)
        return mark_safe(renderer.render(self.template_name, context))


class InvestmentRanking(Ranking):
    def __init__(self, data):
        super(InvestmentRanking, self).__init__(
            'Anfangsinvestitionen',
            ['Szenario', 'Investitionskosten'],
            unit='€',
            data=data
        )


class CO2Ranking(Ranking):
    def __init__(self, data):
        super(CO2Ranking, self).__init__(
            'CO2 Verbrauch',
            ['Szenario', 'CO2 Verbrauch'],
            unit='g/kWh',
            precision=2,
            data=data
        )
