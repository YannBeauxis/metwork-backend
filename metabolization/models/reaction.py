# coding: utf8
from __future__ import unicode_literals

from django.db import models

import os.path
import hashlib
import subprocess
import json
import sys
from base.modules import RDKit
from django.conf import settings
from base.modules import FileManagement, RDKit, ChemDoodle, ChemDoodleJSONError
from django.contrib.postgres.fields import JSONField

class Reaction(FileManagement, models.Model):

    class JSONAPIMeta:
        resource_name = "reactions"

    REACTANTS_MAX = 2

    METHODS_CHOICES = (
        ('reactor', 'Reactor'),
        ('rdkit', 'RDKit'),)

    name = models.CharField(
            max_length=128,
            default='new_reaction',
            unique=True)
    description = models.CharField(
                    max_length=255,
                    default='',
                    null= True,
                    blank=True)
    user = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    db_index = True)
    reactants_number = models.SmallIntegerField(
            default=0)
    method_priority = models.CharField(
            max_length=32,
            choices = METHODS_CHOICES,
            default='rdkit') # cls. methods_allowed
    smarts = models.CharField(
            max_length=1024,
            default=None,
            null= True,
            blank=True) # smarts used by rdkit method
    status_code = models.PositiveSmallIntegerField(
                    default=0,
                    db_index = True)
    chemdoodle_json = JSONField(
        default=None,
        null= True,
        blank=True)
    chemdoodle_json_error = models.CharField(
        max_length=128,
        default=None,
        null= True,
        blank=True)

    class status:
        INIT = 0
        EDIT = 10
        VALID = 20
        ACTIVE = 30
        OBSOLETE = 40
        ERROR = 90

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        res = super().__init__(*args, **kwargs)
        if self.smarts is None:
            try:
                self.smarts = self.get_smarts_from_mrv()
            except:
                pass
        if self.chemdoodle_json is None:
            try:
                cd  = ChemDoodle()
                self.chemdoodle_json = cd.react_to_json(
                    RDKit.reaction_from_smarts(
                        self.smarts))
            except:
                pass
        return res

    def save(self, *args, **kwargs):
        if self.id is not None:
            prev_status = Reaction.objects.get(id=self.id).status_code
        else:
            prev_status = Reaction.status.EDIT
        if self.smarts is None:
            self.smarts = self.get_smarts_from_mrv()
        if self.status_code == Reaction.status.INIT:
            self.status_code = Reaction.status.EDIT
        if self.status_code == Reaction.status.EDIT and prev_status != Reaction.status.VALID:
            try:
                cd  = ChemDoodle()
                smarts = cd.json_to_react(self.chemdoodle_json)
                self.smarts = smarts
                react = RDKit.reaction_from_smarts(smarts)
                self.chemdoodle_json = cd.react_to_json(react)
                self.chemdoodle_json_error = None
                if self.rdkit_ready():
                    self.status_code = Reaction.status.VALID
                else:
                    self.chemdoodle_json_error = 'error with RDKit'
            except ChemDoodleJSONError as error:
                self.chemdoodle_json_error = error
            except:
                self.chemdoodle_json_error = 'unexpected error'
        self.reactants_number = self.get_reactants_number()
        super(Reaction, self).save(*args, **kwargs)
        return self

    def load_smarts(self, smarts):
        try:
            cd  = ChemDoodle()
            react = RDKit.reaction_from_smarts(smarts)
            json.dumps(cd.react_to_json(react))
            self.smarts = smarts
            self.status_code = Reaction.status.VALID
        except:
            self.status_code = Reaction.status.EDIT
        self.save()
        return self

    def user_name(self):
        return self.user.username

    def gen_image(self):
        svg = subprocess.check_output(["molconvert", "svg:w400h200", self.mrv_path()]).decode('utf-8')
        with open( self.image_path(), 'w') as fw:
            fw.write(svg)

    def get_image(self):
        if not os.path.isfile(self.image_path()):
            self.gen_image()
        return open( self.image_path(), 'r').read()

    @classmethod
    def import_file(cls, file_object, name, user, description=None):
        r = cls(
            name = name,
            user=user,
            description=description,
            method_priority='reactor')
        r.save()
        with open(r.mrv_path(), 'w') as f:
            f.write(file_object.read().decode('utf-8'))
        r.save()
        r.gen_image()
        return r

    @classmethod
    def create_from_smarts(cls, smarts, name, user, description=None):
        smarts = RDKit.reaction_to_smarts(
                    RDKit.reaction_from_smarts(smarts))
        r = cls(
            name = name,
            user=user,
            description=description,
            smarts=smarts,
            method_priority='rdkit')
        r.save()
        return r

    def has_no_project(self):
        from metabolization.models import ReactionsConf
        return ReactionsConf.objects.filter(reactions__in = [self]).count() == 0

    def mrv_path(self):
        return '/'.join([
            self.item_path(),
            'reaction.mrv'])

    def image_path(self):
        return '/'.join([
            self.item_path(),
            'image.svg'])

    def mrv_exist(self):
        return os.path.isfile(self.mrv_path())

    def method_to_apply(self):
        prio = self.method_priority
        default = 'reactor'
        available = self.methods_available()
        if prio in available:
            return prio
        elif default in available:
            return default

    def methods_available(self):
        res = []
        if self.mrv_exist():
            res.append('reactor')
        if self.rdkit_ready():
            res.append('rdkit')
        return res

    def is_reactor(self):
        return 'reactor' in self.methods_available()

    def rdkit_ready(self):
        try:
            cd  = ChemDoodle()
            self.chemdoodle_json = cd.react_to_json(
                RDKit.reaction_from_smarts(
                    self.smarts))
            # self.save()
            rx = self.react_rdkit()
            return rx.Validate() == (0,0)
        except:
            return False

    def get_smarts_from_mrv(self):
        if self.mrv_exist():
            return subprocess.check_output(['molconvert', 'smarts', self.mrv_path()]).decode('utf-8')
        else:
            return None

    def react_rdkit(self):
        return self.react_rdkit_(self.smarts)

    def react_rdkit_(self, smarts):
        if smarts is not None:
            return RDKit.reaction_from_smarts(smarts)

    def get_reactants_number_from_mrv(self):
        smarts = self.get_smarts_from_mrv()
        if smarts:
            rx = self.react_rdkit_(smarts)
            return rx.GetNumReactantTemplates()
        else:
            return 0

    def get_reactants_number(self):
        smarts = self.smarts
        if smarts is not None:
            rx = self.react_rdkit_(smarts)
            return rx.GetNumReactantTemplates()
        else:
            return 0

    def run_reaction(self, reactants, method=None):
        from metabolization.models import ReactProcess
        rp = ReactProcess.objects.create()
        rp.reaction = self
        rp.reactants.set(reactants)
        if method in self.methods_available():
            rp.method = method
        else:
            rp.method = self.methods_available()[0]
        rp.save()
        rp.run_reaction()
        return rp

## Hash management ##
# file_hash aims to check if reaction file has not be changed since last DB update
    # def file_hash_compute(self):
    #     if self.mrv_exist():
    #         with open(self.mrv_path(), 'rb') as f:
    #             return hashlib.md5(f.read()).hexdigest()
    #     else:
    #         return ''
    #
    # def file_hash_update(self):
    #     self.file_hash = self.file_hash_compute()
    #     return self
    #
    # def file_hash_check(self):
    #     return self.file_hash == self.file_hash_compute()
    #
    # def __unicode__(self):
    #     return self.name

####
