
import pandas
import sqlahelper
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField, JSONField

from utils.highcharts import Highchart
from stemp import constants


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


class HeatProfile(models.Model):
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
    timeseries = None

    name = models.CharField(max_length=255, unique=True)
    house_type = models.CharField(
        max_length=3,
        choices=constants.HOUSE_TYPES,
        default='EFH',
        verbose_name='Haustyp'
    )
    heat_demand = models.FloatField(verbose_name='Jährlicher Wärmebedarf')
    number_of_persons = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    square_meters = models.IntegerField(verbose_name='Quadratmeter')
    heat_type = models.CharField(
        choices=((ht.name, ht.value) for ht in constants.HeatType),
        default='radiator',
        max_length=10,
        verbose_name='Heizungsmodell'
    )
    warm_water_per_day = models.IntegerField()

    def get_oep_timeseries(self, name):
        if self.timeseries is None:
            from stemp import oep_models
            session = sqlahelper.get_session()
            keys = ('Hot Water Energy', constants.EFH[1], constants.MFH[1])
            self.timeseries = {
                name: pandas.Series(
                    session.query(
                        oep_models.OEPTimeseries
                    ).filter_by(name=name).first().data)
                for name in keys
            }
        return self.timeseries[name]

    def get_heat_demand_profile(self):
        if self.house_type == constants.EFH[0]:
            return self.get_oep_timeseries(constants.EFH[1])
        elif self.house_type == constants.MFH[0]:
            return self.get_oep_timeseries(constants.MFH[1])

    def get_hot_water_profile(self):
        return (
            self.get_oep_timeseries('Hot Water Energy') *
            self.number_of_persons
        )

    def __str__(self):
        return self.name

    def annual_heat_demand(self):
        return (
                self.heat_demand * self.get_heat_demand_profile() +
                self.get_hot_water_profile()
        )

    def contains_radiator(self):
        return self.heat_type == constants.HeatType.radiator.name


class District(models.Model):
    name = models.CharField(max_length=255)
    households = models.ManyToManyField(
        'Household', through='DistrictHouseholds')

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
            [
                dh.household.annual_heat_demand() * dh.amount
                for dh in self.districthouseholds_set.all()
            ]
        )

    def contains_radiator(self):
        return any(
            [
                hh.heat_type == constants.HeatType.radiator.name
                for hh in self.households.all()
            ]
        )
