# Generated by Django 2.1.2 on 2018-10-26 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0033_auto_20181026_1037"),
    ]

    operations = [
        migrations.AddField(
            model_name="household",
            name="warm_water_per_day",
            field=models.IntegerField(default=44),
            preserve_default=False,
        ),
    ]
