
import pandas
from django.utils import timezone

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

from utils.highcharts import Highchart


class Parameter(models.Model):
    data = JSONField(unique=True)

    def __str__(self):
        return self.__class__.__name__ + '#' + str(self.id)


class Scenario(models.Model):
    name = models.CharField(max_length=255, unique=True)
    last_change = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Simulation(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    result_id = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        ids = map(
            str,
            [self.scenario, self.parameter, self.result_id]
        )
        return '(' + ','.join(ids) + ')'


class District(models.Model):
    name = models.CharField(max_length=255)

    layout = {
        'x_title': 'Zeit [h]',
        'y_title': 'Verbrauch [kWh]',
        'title': 'Strom- und Wärmeverbrauch'
    }

    def __str__(self):
        return self.name

    def annual_load_demand(self):
        return sum(
            [hh.annual_load_demand() for hh in self.household_set.all()]
        )

    def annual_heat_demand(self):
        return sum(
            [hh.annual_heat_demand() for hh in self.household_set.all()]
        )

    def as_highchart(self, style='line'):
        layout = self.layout.copy()
        df = pandas.DataFrame(
            {
                'Stromverbrauch': self.annual_load_demand(),
                'Wärmebedarf': self.annual_heat_demand()
            }
        )
        return Highchart(df, style, **layout)


class ProfileMixin(object):
    def as_series(self):
        return pandas.Series(self.profile)

    @classmethod
    def get_ids_and_names(cls):
        profiles = cls.objects.all()
        return [(p.id, p.name) for p in profiles]

    def as_highchart(self, style='line'):
        layout = self.layout.copy()
        profile_series = self.as_series()
        return Highchart(profile_series, style, **layout)


class LoadProfile(models.Model, ProfileMixin):
    name = models.CharField(max_length=255)
    profile = ArrayField(models.FloatField(), size=8760, null=True)

    layout = {
            'x_title': 'Zeit [h]',
            'y_title': 'Stromverbrauch [kWh]',
            'title': 'Stromverbrauch'
    }

    def __str__(self):
        return self.name


class HeatProfile(models.Model, ProfileMixin):
    name = models.CharField(max_length=255)
    profile = ArrayField(models.FloatField(), size=8760, null=True)

    layout = {
        'x_title': 'Zeit [h]',
        'y_title': 'Wärmeverbrauch [kWh]',
        'title': 'Wärmeverbrauch'
    }

    def __str__(self):
        return self.name


class Household(models.Model):
    name = models.CharField(max_length=255, unique=True)
    districts = models.ManyToManyField(District, through='DistrictHouseholds')
    load_demand = models.FloatField(verbose_name='Jährlicher Strombedarf')
    heat_demand = models.FloatField(verbose_name='Jährlicher Wärmebedarf')
    load_profile = models.ForeignKey(LoadProfile, on_delete=models.CASCADE)
    heat_profile = models.ForeignKey(HeatProfile, on_delete=models.CASCADE)
    predefined = models.BooleanField(
        verbose_name='Vordefiniert', default=False)

    layout = {
        'x_title': 'Zeit [h]',
        'y_title': 'Verbrauch [kWh]',
        'title': 'Strom- und Wärmeverbrauch'
    }

    def __str__(self):
        text = self.name
        if self.predefined:
            text += ', VORDEFINIERT'
        return text

    def annual_load_demand(self):
        return self.load_demand * self.load_profile.as_series()

    def annual_heat_demand(self):
        return self.heat_demand * self.heat_profile.as_series()

    def as_highchart(self, style='line'):
        layout = self.layout.copy()
        df = pandas.DataFrame(
            {
                'Stromverbrauch': self.annual_load_demand(),
                'Wärmebedarf': self.annual_heat_demand()
            }
        )
        return Highchart(df, style, **layout)


class Question(models.Model):
    number_of_persons = models.IntegerField()
    at_home = models.BooleanField()
    modernized = models.BooleanField()

    class Meta:
        unique_together = ('number_of_persons', 'at_home', 'modernized')


class QuestionHousehold(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_household'
    )
    household = models.OneToOneField(
        Household,
        on_delete=models.CASCADE,
        related_name='question_household',
    )
    default = models.BooleanField(default=False)


class DistrictHouseholds(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    amount = models.IntegerField()
