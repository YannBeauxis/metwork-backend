# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from base.models import Molecule, SampleAnnotationProject
from django.db import models

class APIStatus(models.Model):

    class JSONAPIMeta:
        resource_name = "api-statuses"

    def available(self):
        return True

    def molecules_count(self):
        return Molecule.objects.count()

    def achieved_projects_count(self):
        return SampleAnnotationProject.achieved_projects().count()

    def running_projects_count(self):
        return SampleAnnotationProject.running_projects().count()
