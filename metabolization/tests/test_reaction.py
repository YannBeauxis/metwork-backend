# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from shutil import copyfile
import string
import os
import collections
from metabolization.modules import ReactionTestManagement
from metabolization.models import Reaction, ReactProcess

class ReactionModelTests(ReactionTestManagement):

	def user(self):
		return get_user_model().objects.create()

	def test_default_name(self):
		default_name = 'new_reaction'
		r = Reaction()
		self.assertEqual(r.name, default_name)

	def test_name_unique(self):
		u = self.get_user()
		n = 'name_duplicate'
		r_1 = Reaction(name = n, user = u)
		r_1.save()
		r_2 = Reaction(name = n, user = u)
		self.assertRaises(Exception,r_2.save)


	def test_import_file(self):
		reaction_name = "methylation"
		r = self.import_file(reaction_name)
		self.assertEqual(r.name, reaction_name)
		self.assertTrue(r.mrv_exist())
		r_path = r.item_path()
		r.delete()
		self.assertFalse( os.path.isdir(r_path) )

	def test_method_to_apply(self):
		reacts = {
			'methylation': ['reactor', 'reactor'],
			'bromination_of_phenols': ['rdkit', 'reactor'],
			'diels_alder_cycloaddition': ['rdkit', 'rdkit'],
			'error': ['reactor', None], }
		rd = self.create_reacts(reacts)
		for r_name in reacts:
			r = rd[r_name]
			r.method_priority =  reacts[r_name][0]
			r.save()
			self.assertEqual(r.method_to_apply(), reacts[r_name][1])

	def test_methods_available(self):
		reacts = {
			'methylation': ['reactor'],
			'diels_alder_cycloaddition': ['reactor', 'rdkit'],
			'error': [], }
		rd = self.create_reacts(reacts)
		for r_name in reacts:
			self.assertEqual( rd[r_name].methods_available(),
				reacts[r_name],
				[r_name, rd[r_name].methods_available()])

	def test_rdkit_ready(self):
		reacts = {
			'methylation': False,
			'bromination_of_phenols': False,
			'diels_alder_cycloaddition': True,
			'error': False, }
		rd = self.create_reacts(reacts)
		for r_name in reacts:
			self.assertEqual(rd[r_name].rdkit_ready(), reacts[r_name])
		r = Reaction.objects.get(name='methylation')
		r.smarts = '[#7,#8,#16:1]>>[#6]-[*:1]'
		r.save()
		self.assertTrue(r.rdkit_ready())

	def test_reactants_number(self):
		reacts = {
			'methylation': 1,
			'diels_alder_cycloaddition': 2,
			'error': 0, }
		rd = self.create_reacts(reacts)
		for r_name in reacts:
			r = rd[r_name]
			self.assertEqual(r.get_reactants_number_from_mrv(), reacts[r_name])
			self.assertEqual(r.reactants_number, reacts[r_name])
			
