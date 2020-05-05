# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0002_auto_20180219_1452"),
    ]

    operations = [
        migrations.AddField(
            model_name="household",
            name="predefined",
            field=models.BooleanField(verbose_name="Vordefiniert", default=False),
        ),
    ]
