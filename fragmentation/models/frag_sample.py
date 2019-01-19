# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import *
import time
from django.db import models, IntegrityError
from django.conf import settings
from base.models import Molecule, Array1DModel, Array2DModel
from libmetgem.cosine import compute_distance_matrix
from django.contrib.postgres.fields import ArrayField
import numpy as np
from libmetgem.mgf import filter_data

class FragSample(models.Model):

    class JSONAPIMeta:
        resource_name = "fragsamples"

    class Meta:
        ordering = ('name', )

    user = models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                default=None)
    name = models.CharField(
                    max_length=128,
                    default='')
    file_name = models.CharField(
                    max_length=255,
                    default='')
    description = models.CharField(
                    max_length=255,
                    default='',
                    null= True,
                    blank=True)
    ions_total = models.PositiveSmallIntegerField(
                    default=0,
                    db_index = True)
    cosine_matrix = models.OneToOneField(
        Array2DModel,
        related_name='cosine_matrix',
        on_delete=models.CASCADE,
        null= True,
    )
    mass_delta_single = models.OneToOneField(
        Array1DModel,
        related_name='mass_delta_single',
        on_delete=models.CASCADE,
        null= True,
    )
    mass_delta_double = models.OneToOneField(
        Array1DModel,
        related_name='mass_delta_double',
        on_delete=models.CASCADE,
        null= True,
    )
    # reaction_mass_max is the max value of reactions mass
    # when mass_delta_* lists where evaluated
    reaction_mass_max = models.FloatField(\
            default = 0)
    status_code = models.PositiveIntegerField(
                    default=0,
                    db_index = True)

    # Limit the number of ions per sample
    IONS_LIMIT = 9000

    class status:
        INIT = 0
        READY = 1
        RUNNING = 2
        DONE = 3
        ERROR = 99

    def __str__(self):
        return self.name

    def obsolete(self):
        return True in ( fms.obsolete() \
            for fms in self.fragmolsample_set.all() )

    def has_no_project(self):
        return self.sampleannotationproject_set.count() == 0

    def ions_count(self):
        return self.fragmolsample_set.count()

    def annotations_count(self):
        from fragmentation.models import FragAnnotationDB
        return FragAnnotationDB.objects.filter(frag_mol_sample__frag_sample = self).count()

    def add_annotation(self, ion_id, smiles, db_source='', db_id=''):
    # ===> Add ion_name !
        from fragmentation.models import FragAnnotationDB
        fms = self.fragmolsample_set.get(ion_id = int(ion_id))
        return FragAnnotationDB.objects.create(
            frag_mol_sample = fms,
            molecule = Molecule.load_from_smiles(smiles),
            db_source = db_source,
            db_id = db_id)

    @classmethod
    def import_sample(cls, file_object, user, name='', file_name='', description='', energy=1, task=False):
        from fragmentation.models import FragMolSample
        from fragmentation.tasks import import_sample_task

        data = [l.decode('utf-8') for l in file_object.readlines()]
        #data = file_object.readlines()
        error_log = []
        total_ions = data.count('BEGIN IONS\n')
        if total_ions > FragSample.IONS_LIMIT:
            raise IntegrityError(
                '{0} ions max authorized, {1} in the sample.'.format(FragSample.IONS_LIMIT, total_ions))
        fs = FragSample.objects.create(
            user = user,
            name = name,
            file_name = file_name,
            description = description,
            status_code = 1,
            ions_total = total_ions)
        fs.status_code = 2
        fs.save()
        if task:
            import_sample_task.apply_async(args = [fs.id, data, energy], queue = settings.CELERY_WEB_QUEUE)
        else:
            fs.import_sample_(data, energy, task)
        return fs

    def import_sample_(self, data, energy, task=False):
        from fragmentation.models import FragMolSample, FragMolAttribute, FragMolSpectrum
        from fragmentation.tasks import gen_cosine_matrix_task, gen_mass_delta_task
        import re
        error_log = []

        for ion in re.findall("(?<=BEGIN IONS\|)(.+?)(?=END IONS)", ''.join(data).replace('\n', '|'), re.U):

            params = re.findall( "([^|]*)=([^|]*)" , ion, re.U)
            peaks = re.findall( "([\d]*\.+[\d]*) ([\d]*\.+[\d]*)" , ion, re.U)
            has_pepmass = 'PEPMASS' in [ v[0] for v in params ]
            has_id = 'SCANS' in [ v[0] for v in params ]
            has_peaks = len(peaks) > 1

            if has_pepmass and has_id and has_peaks:
                fsm = FragMolSample.objects.create(frag_sample = self)
                p = 1
                for param in params:
                    if param[0] == 'PEPMASS':
                        fsm.parent_mass = float(param[1])
                        # fsm.mass = Decimal(av[1])
                        fsm.save()
                    elif param[0] == 'SCANS':
                        fsm.ion_id = int(param[1])
                        fsm.save()
                    else:
                        FragMolAttribute.objects.create(
                            frag_mol = fsm,\
                            title = param[0],\
                            value = param[1],\
                            position = p)
                    p +=1
                FragMolSpectrum.objects.create(
                    frag_mol = fsm,
                    spectrum = \
                        [ [float(peak[0]), float(peak[1])] \
                        for peak in peaks ],
                    energy = energy,
                    )
            else:
                self.ions_total -= 1
            #except:
            #    error_log.append(l)

        if task:
            gen_cosine_matrix_task.apply_async(args = [self.id], queue = settings.CELERY_WEB_QUEUE)
            gen_mass_delta_task.apply_async(args = [self.id], queue = settings.CELERY_WEB_QUEUE)
        else:
            self.gen_cosine_matrix()
            self.gen_mass_delta()

        # if len(error_log) > 0 : print ('ERROR LOG', error_log )
        self.status_code = 3
        self.save()

    def gen_mass_delta(self, update_reaction_mass_max=True):
        from metabolization.models import Reaction
        reaction_max = Reaction.max_delta()

        allfms = np.array([
            fms.parent_mass for fms in self.fragmolsample_set.all() ])
        allfms = np.unique(allfms)

        if update_reaction_mass_max:
            self.reaction_mass_max = max(reaction_max, min(allfms))

        def diff_values(a1,a2):
            res = np.reshape(a2, (len(a2),1))
            res = np.round(a1 - res,6)
            res = np.unique(np.abs(res))
            mass_max = self.reaction_mass_max + settings.PROTON_MASS
            res = res[np.where( res <= mass_max )[0]]
            return res

        single = diff_values(allfms ,allfms)
        double = diff_values(single, allfms - settings.PROTON_MASS)

        mass_delta_single = Array1DModel.objects.create(value=single.tolist())
        mass_delta_double = Array1DModel.objects.create(value=double.tolist())
        self.mass_delta_single = mass_delta_single
        self.mass_delta_double = mass_delta_double
        self.save()
        return self

    def ions_list(self):
        return self.fragmolsample_set.all().order_by('ion_id').distinct()

    def mzs(self):
        return [ fms.parent_mass for fms in self.ions_list() ]

    def gen_cosine_matrix(self):
        query = self.ions_list()
        try:
            cosine_matrix = compute_distance_matrix(
                [ fms.parent_mass for fms in query ],
                [ filter_data(
                    np.array(fms.fragmolspectrum_set.get(energy = 1).spectrum),
                    fms.parent_mass,
                    0.0, 0.0, 0.0, 0)
                    for fms in query ],
                0.002,
                5
            )
            cosine_matrix = Array2DModel.objects.create(value=cosine_matrix.tolist())
            self.cosine_matrix = cosine_matrix
            self.save()
        except:
            pass
        return self

    def molecular_network(self):
        if self.cosine_matrix is None:
            self.gen_cosine_matrix()
        from fragmentation.modules import MolGraph
        mg = MolGraph(self)
        return mg.gen_molecular_network()

    def wait_import_done(self, timeout=360):
        begin = time.time()
        while self.status_code == FragSample.status.RUNNING:
            time.sleep(0.5)
            if (time.time() - begin) > timeout:
                print ('\n#### close due to timeout #####\n')
                return self
            else:
                self.refresh_from_db()
        #time.sleep(20)
        return self

    def import_annotation_file(self, file_object, file_format='default'):
        from fragmentation.models import FragMolSample, FragAnnotationDB
        fls = [l.decode('utf-8') for l in file_object.readlines()]
        errors = {}
        col_titles = fls[0].split("\t")
        for i, fl in enumerate(fls[1:]):
            try:
                if file_format == 'default':
                    adduct = 'M+H'
                    ion_id, name, smiles, db_source, db_id = fl.split("\n")[0].split(",")
                    adduct = 'M+H'
                elif file_format == 'GNPS':
                    data = fl.split("\t")
                    ion_id = data[col_titles.index('#Scan#')]
                    adduct = data[col_titles.index('Adduct')]
                    name = data[col_titles.index('Compound_Name')]
                    smiles = data[col_titles.index('Smiles')]

                    db_source =  'GNPS : {0}, {1}'.format(
                        data[col_titles.index('Compound_Source')],
                        data[col_titles.index('Data_Collector')])
                    db_id = data[col_titles.index('CAS_Number')]

                if int(ion_id) > 0 and adduct == 'M+H':
                    m = Molecule.load_from_smiles(smiles)
                    fms = self.fragmolsample_set.get(
                            ion_id = ion_id)

                    fa = FragAnnotationDB.objects.create(
                        frag_mol_sample = fms,
                        molecule = m,
                        name = name,
                        db_source = db_source,
                        db_id = db_id)
            except Exception as err:
                # print(err)
                errors[i] = {'err': str(err), 'smiles': smiles}
        return {'success': 'Annotations successfully imported', 'errors': errors}

    def gen_mgf(self, energy = 2, decimal = 6):
        from fragmentation.models import FragMolSample
        res = '\n'.join([\
                    fm.gen_mgf(energy) \
                    for fm in FragMolSample.objects.filter(frag_sample = self).order_by("ion_id") ])
        return res
