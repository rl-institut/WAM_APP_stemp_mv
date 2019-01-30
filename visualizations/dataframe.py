
import pandas
import itertools

from utils.visualizations import VisualizationTemplate


class Dataframe(VisualizationTemplate):
    template_name = 'visualizations/dataframe.html'

    def __init__(self, title, units=None, data=None, **kwargs):
        self.title = title
        self.units = units
        self.data: pandas.DataFrame = data
        super(Dataframe, self).__init__(data)

    def set_data(self, data: pandas.DataFrame):
        self.data = data

    def get_context(self, **kwargs):
        context = super(Dataframe, self).get_context(**kwargs)
        context['title'] = self.title
        context['data'] = self.data.to_html(escape=False)
        context['units'] = self.__get_units()
        return context

    def __get_units(self):
        if isinstance(self.units, list):
            if len(self.units) == len(self.data.columns):
                return self.units
            else:
                raise IndexError('Length of unit list differs from columns')
        elif isinstance(self.units, str):
            return itertools.repeat(self.units)
        else:
            raise TypeError(
                'Units must be str or list-of-str with length of columns')


class InvestmentDataframe(Dataframe):
    def __init__(self, data):
        super(InvestmentDataframe, self).__init__(
            'Anfangsinvestitionen',
            units='€',
            data=data
        )


class CO2Dataframe(Dataframe):
    def __init__(self, data):
        super(CO2Dataframe, self).__init__(
            'CO2 Verbrauch',
            units='g/kWh',
            data=data
        )


class ComparisonDataframe(Dataframe):
    def __init__(self, data):
        super(ComparisonDataframe, self).__init__(
            'Technologievergleich',
            units='€',
            data=data,
        )
