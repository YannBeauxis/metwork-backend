# Generated by Django 2.1.2 on 2019-07-27 07:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fragmentation", "0019_fragsample_tags"),
    ]

    operations = [
        migrations.RemoveField(model_name="fragsample", name="mass_delta_double",),
        migrations.RemoveField(model_name="fragsample", name="mass_delta_single",),
        migrations.RemoveField(model_name="fragsample", name="reaction_mass_max",),
    ]
