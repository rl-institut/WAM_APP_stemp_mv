# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-12 11:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0010_auto_20180312_1243"),
    ]

    operations = [
        migrations.RemoveField(model_name="simulation", name="date",),
        migrations.AddField(
            model_name="result",
            name="date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
