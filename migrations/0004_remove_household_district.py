# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-01 09:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0003_add_household_predefined"),
    ]

    operations = [
        migrations.RemoveField(model_name="household", name="district",),
    ]
