# Generated by Django 2.0.7 on 2018-08-07 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fragmentation", "0007_auto_20180807_1813"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fragmolattribute",
            name="value",
            field=models.CharField(default="", max_length=128),
        ),
    ]
