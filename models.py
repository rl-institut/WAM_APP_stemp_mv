
import pandas
import sqlahelper
import transaction
from django.utils import timezone
from django.db import models
from django.utils.safestring import mark_safe
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField, JSONField

from stemp import constants
from stemp import oep_models


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

    name = models.CharField(
        max_length=22,
        unique=True,
        error_messages={
            'unique': (
                'Es ist schon ein Haushalt mit diesem Namen vorhanden - '
                'bitte einen neuen Namen auswählen'
            )
        }
    )
    house_type = models.CharField(
        max_length=3,
        choices=((ht.name, ht.value) for ht in constants.HouseType),
        default='EFH',
        verbose_name='Haustyp'
    )
    heat_demand = models.FloatField(
        verbose_name='Jährlicher Wärmebedarf',
        validators=[
            MaxValueValidator(
                1e5,
                message=(
                    'Der jährliche, mögliche Heizwärmebedarf ist auf ein '
                    'Limit von %(limit_value)s kWh begrenzt.'
                )
            )
        ]
    )
    number_of_persons = models.IntegerField(
        validators=[
            MinValueValidator(
                1, message='Mindestens eine Person muss im Haushalt leben.'),
            MaxValueValidator(
                10,
                message='Bitte nur maximal %(limit_value)s Personen angeben.'
            )
        ],
    )
    square_meters = models.IntegerField(
        verbose_name='Quadratmeter',
        validators=[
            MaxValueValidator(
                1e3,
                message=(
                    'Die Angabe der Quadratmeter ist auf %(limit_value)s qm '
                    'begrenzt.'
                )
            )
        ]
    )
    heat_type = models.CharField(
        choices=((ht.name, ht.value) for ht in constants.HeatType),
        default='radiator',
        max_length=10,
        verbose_name='Heizungsmodell'
    )
    warm_water_per_day = models.IntegerField(
        verbose_name='Warmwasserbedarf'
    )
    roof_area = models.FloatField(
        verbose_name='Verfügbare Dachfläche für Photovoltaik',
        validators=[
            MaxValueValidator(
                400,
                'Die verfügbare Dachfläche ist auf %(limit_value)s qm '
                'begrenzt.'
            )
        ]
    )

    def get_oep_timeseries(self, name):
        if self.timeseries is None:
            session = sqlahelper.get_session()
            with transaction.manager:
                self.timeseries = {
                    name: pandas.Series(
                        session.query(
                            oep_models.OEPTimeseries
                        ).filter_by(name=house_type.value).first().data)
                    for house_type in constants.HouseType
                }
        return self.timeseries[name]

    def get_heat_demand_profile(self):
        house_type = constants.HouseType[self.house_type]
        return self.get_oep_timeseries(house_type.value)

    def annual_hot_water_demand(self):
        session = sqlahelper.get_session()
        with transaction.manager:
            hot_water = session.query(oep_models.OEPHotWater).filter_by(
                    liter=self.warm_water_per_day * self.number_of_persons
            ).first()
            if hot_water is None:
                raise KeyError(
                    f'No hot water profile found for '
                    f'liter={self.warm_water_per_day}'
                )
            return pandas.Series(hot_water.data)

    def __str__(self):
        return self.name

    def annual_total_demand(self):
        return (
                self.heat_demand * self.get_heat_demand_profile() +
                self.annual_hot_water_demand()
        )

    def annual_heat_demand(self):
        return self.heat_demand * self.get_heat_demand_profile()

    def warm_water_demand(self):
        return self.annual_hot_water_demand().sum()

    def contains_radiator(self):
        return self.heat_type == constants.HeatType.radiator.name

    @property
    def max_pv_size(self):
        return self.roof_area / constants.QM_PER_PV_KW


class District(models.Model):
    name = models.CharField(max_length=22)
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

    def annual_total_demand(self):
        return sum(
            [
                dh.household.annual_total_demand() * dh.amount
                for dh in self.districthouseholds_set.all()
            ]
        )

    def annual_heat_demand(self):
        return sum(
            [
                dh.household.annual_heat_demand() * dh.amount
                for dh in self.districthouseholds_set.all()
            ]
        )

    def annual_hot_water_demand(self):
        return sum(
            [
                dh.household.annual_hot_water_demand() * dh.amount
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

    @property
    def max_pv_size(self):
        return sum([hh.max_pv_size for hh in self.households.all()])
