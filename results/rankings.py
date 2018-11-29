
from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer

from utils.visualizations import VisualizationTemplate


class Ranking(VisualizationTemplate):
    template_name = 'widgets/ranking.html'

    def __init__(self, title, headers, data=None):
        super(Ranking, self).__init__(data)
        self.title = title
        self.headers = headers
        self.data = None

    def set_data(self, data):
        self.data = data.sum(axis=1)
        self.data.sort_values(inplace=True)

    def get_context(self, **kwargs):
        return {
            'div_id': kwargs.get('div_id', f'rank_{self.id}'),
            'div_kwargs': kwargs.get('div_kwargs', {}),
            'title': self.title,
            'headers': self.headers,
            'data': self.data
        }

    def render(self, **kwargs):
        renderer = get_default_renderer()
        context = self.get_context(**kwargs)
        return mark_safe(renderer.render(self.template_name, context))
