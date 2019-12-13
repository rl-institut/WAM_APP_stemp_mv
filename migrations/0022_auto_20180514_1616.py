# Generated by Django 2.0.4 on 2018-05-14 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0021_auto_20180514_1559"),
    ]

    operations = [
        migrations.RenameField(
            model_name="question",
            old_name="number_of_person",
            new_name="number_of_persons",
        ),
        migrations.AddField(
            model_name="question",
            name="at_home",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="question",
            name="renovated",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
