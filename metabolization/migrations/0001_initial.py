# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-20 15:23
from __future__ import unicode_literals

import base.modules.conf_management
import base.modules.file_management
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("base", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Reaction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default="new_reaction", max_length=128, unique=True
                    ),
                ),
                (
                    "description",
                    models.CharField(blank=True, default="", max_length=255, null=True),
                ),
                ("file_hash", models.CharField(default="", max_length=32)),
                ("reactants_number", models.SmallIntegerField(default=0)),
                (
                    "method_priority",
                    models.CharField(
                        choices=[("reactor", "Reactor"), ("rdkit", "RDKit")],
                        default="reactor",
                        max_length=32,
                    ),
                ),
                ("smarts", models.CharField(default="", max_length=1024)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=(base.modules.file_management.FileManagement, models.Model),
        ),
        migrations.CreateModel(
            name="ReactionsConf",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "method_priority",
                    models.CharField(
                        choices=[
                            ("reaction", "Reaction"),
                            ("reactor", "Reactor"),
                            ("rdkit", "RDKit"),
                        ],
                        default="reaction",
                        max_length=32,
                    ),
                ),
                ("reactions", models.ManyToManyField(to="metabolization.Reaction")),
            ],
            bases=(base.modules.conf_management.ConfManagement, models.Model),
        ),
        migrations.CreateModel(
            name="ReactProcess",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("method", models.CharField(default="reactor", max_length=32)),
                ("method_hash", models.CharField(default="", max_length=32)),
                ("achieved", models.BooleanField(default=False)),
                ("status_code", models.SmallIntegerField(default=0)),
                (
                    "products",
                    models.ManyToManyField(
                        default=None, related_name="products", to="base.Molecule"
                    ),
                ),
                (
                    "reactants",
                    models.ManyToManyField(
                        default=None, related_name="reactants", to="base.Molecule"
                    ),
                ),
                (
                    "reaction",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="metabolization.Reaction",
                    ),
                ),
            ],
        ),
    ]
