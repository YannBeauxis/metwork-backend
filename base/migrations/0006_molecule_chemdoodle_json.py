# Generated by Django 2.0.7 on 2018-09-27 14:17

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0005_auto_20180904_1626"),
    ]

    operations = [
        migrations.AddField(
            model_name="molecule",
            name="chemdoodle_json",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, default=None, null=True
            ),
        ),
    ]
