# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-15 12:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0014_auto_20180315_1152"),
    ]

    operations = [
        migrations.AddField(
            model_name="simulation",
            name="date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
