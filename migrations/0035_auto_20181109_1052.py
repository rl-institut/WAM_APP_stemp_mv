# Generated by Django 2.1.2 on 2018-11-09 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stemp", "0034_auto_20181026_1216"),
    ]

    operations = [
        migrations.DeleteModel(name="LoadProfile",),
        migrations.AddField(
            model_name="household",
            name="roof_area",
            field=models.FloatField(
                default=10, verbose_name="Verfügbare Dachfläche für Photovoltaik"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="household",
            name="heat_type",
            field=models.CharField(
                choices=[("radiator", "Heizkörper"), ("floor", "Fussbodenheizung")],
                default="radiator",
                max_length=10,
                verbose_name="Heizungsmodell",
            ),
        ),
        migrations.AlterField(
            model_name="household",
            name="house_type",
            field=models.CharField(
                choices=[("EFH", "Einfamilienhaus"), ("MFH", "Mehrfamilienhaus")],
                default="EFH",
                max_length=3,
                verbose_name="Haustyp",
            ),
        ),
        migrations.AlterField(
            model_name="household",
            name="square_meters",
            field=models.IntegerField(verbose_name="Quadratmeter"),
        ),
    ]
