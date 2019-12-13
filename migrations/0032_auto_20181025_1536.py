# Generated by Django 2.1.2 on 2018-10-25 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0030_auto_20180709_1051"),
    ]

    operations = [
        migrations.RemoveField(model_name="household", name="districts",),
        migrations.AddField(
            model_name="district",
            name="households",
            field=models.ManyToManyField(
                through="stemp.DistrictHouseholds", to="stemp.Household"
            ),
        ),
    ]
