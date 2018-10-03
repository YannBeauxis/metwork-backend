# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.contrib.auth import get_user_model
from base.modules import TestManagement
from metabolization.models import Reaction, ReactProcess

class ReactionTestManagement(TestManagement):

    UPLOAD_PATH = 'metabolization/tests/mrv'

    def import_file(self, reaction_name = "methylation", user = None):
        if user == None:
            user = self.get_user()
        file_path = ReactionTestManagement.UPLOAD_PATH + '/' + reaction_name + '.mrv'
        with open(file_path, 'rb') as f:
            r = Reaction.import_file(f, reaction_name, user)
        return r


    def create_reacts(self, reacts, email='create@react.com'):
        user = self.get_user(email)
        rd = {}
        for r_name in reacts:
            try:
                r = self.import_file(
                        reaction_name=r_name,
                        user = user,
                        )
            except:
                r = Reaction(user=user, name = r_name)
                r.save()
            rd[r_name]  = r
        return rd
