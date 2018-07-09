# Generated by Django 2.0.4 on 2018-07-09 10:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stemp', '0030_auto_20180709_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='household',
            name='load_demand',
            field=models.FloatField(default=1600, verbose_name='Jährlicher Strombedarf'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='household',
            name='load_profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='stemp.LoadProfile'),
            preserve_default=False,
        ),
    ]
