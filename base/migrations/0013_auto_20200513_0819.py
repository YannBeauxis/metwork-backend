# Generated by Django 2.2.4 on 2020-05-13 08:19

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0012_graph_moleculargraph"),
    ]

    operations = [
        migrations.AlterField(
            model_name="graph",
            name="data",
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="moleculargraph",
            name="frag_sample",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="molecular_network",
                to="fragmentation.FragSample",
            ),
        ),
        migrations.CreateModel(
            name="MetabolizationGraph",
            fields=[
                (
                    "graph_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="base.Graph",
                    ),
                ),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="metabolization_network",
                        to="base.SampleAnnotationProject",
                    ),
                ),
            ],
            options={"abstract": False, "base_manager_name": "objects",},
            bases=("base.graph",),
        ),
    ]
