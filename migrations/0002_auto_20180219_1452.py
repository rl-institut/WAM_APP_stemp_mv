# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-02-19 14:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stemp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='household',
            name='district',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stemp.District'),
        ),
    ]
