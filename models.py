
import pandas
import sqlahelper
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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


class DistrictHouseholds(models.Model):
    district = models.ForeignKey('District', on_delete=models.CASCADE)
    household = models.ForeignKey('Household', on_delete=models.CASCADE)
    amount = models.IntegerField()


class Household(models.Model):
    name = models.CharField(max_length=255, unique=True)
    districts = models.ManyToManyField(
        'District', through='DistrictHouseholds')
    heat_demand = models.FloatField(verbose_name='Jährlicher Wärmebedarf')

    def __str__(self):
        text = self.name
        return text

    def annual_heat_demand(self):
        question = self.question_household.question
        return (
                self.heat_demand * question.get_heat_demand_profile() +
                question.get_hot_water_profile()
        )


class District(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def add_households(self, households):
        for hh_id, amount in households.items():
            hh = Household.objects.get(pk=hh_id)
            district_hh = DistrictHouseholds(
                district=self, household=hh, amount=amount)
            district_hh.save()

    def annual_heat_demand(self):
        return sum(
            [hh.annual_heat_demand() for hh in self.household_set.all()]
        )


class Question(models.Model):
    number_of_persons = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    EFH = ('EFH', 'Heat Demand EFH')
    MFH = ('MFH', 'Heat Demand EFH')
    HOUSE_TYPES = (
        (EFH[0], 'Einfamilienhaus'),
        (MFH[0], 'Mehrfamilienhaus')
    )
    house_type = models.CharField(
        max_length=3, choices=HOUSE_TYPES, default='EFH')

    class Meta:
        unique_together = ('number_of_persons', 'house_type')

    # Hot water and demand are accessed only once:
    oep_init_done = False
    timeseries = {}

    def get_oep_timeseries(self):
        from stemp import oep_models
        session = sqlahelper.get_session()
        for name in ('Hot Water', self.EFH[1], self.MFH[1]):
            self.timeseries[name] = pandas.Series(
                session.query(oep_models.OEPTimeseries).filter_by(
                    name=name
                ).first().data)

    def get_heat_demand_profile(self):
        if not self.oep_init_done:
            self.get_oep_timeseries()
        if self.house_type == self.EFH[0]:
            return self.timeseries[self.EFH[1]]
        elif self.house_type == self.MFH[0]:
            return self.timeseries[self.MFH[1]]

    def get_hot_water_profile(self):
        if not self.oep_init_done:
            self.get_oep_timeseries()
        return self.timeseries['Hot Water'] * self.number_of_persons

    def __str__(self):
        return self.house_type + f', {self.number_of_persons} persons'


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
