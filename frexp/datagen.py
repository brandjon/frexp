"""Dataset generation."""


__all__ = [
    'Datagen',
]


import os
import glob
import pickle

from frexp.util import StopWatch
from frexp.workflow import Task


class Datagen(Task):
    
    """Abstract base class for generating datasets. Subclasses
    should override progs, get_dsparams_list(), and generate().
    """
    
    @property
    def progs(self):
        """List of programs to run."""
        return []
    
    def get_tparams_list(self, dsparams_list):
        """Produce a list of trial params objects from a list of
        dataset params objects. By default, just cross-product with
        the progs list.
        """
        return [
            dict(
                tid = dsp['dsid'],
                dsid = dsp['dsid'],
                prog = prog,
            )
            for prog in self.progs
            for dsp in dsparams_list
        ]
    
    def get_dsparams_list(self):
        """Return a list of dataset params object."""
        raise NotImplementedError
    
    def generate(self, dsparams):
        """Given a dataset params object, return a dataset."""
        raise NotImplementedError
    
    def generate_multiple(self, dsparams):
        """Given a dataset params object, return a list of datasets.
        Hook for allowing the same dsparams to produce similar
        datasets.
        """
        return [self.generate(dsparams)]
    
    def _run(self):
        # Determine dataset parameters.
        dsparams_list = list(self.get_dsparams_list())
        
        os.makedirs(self.workflow.ds_dirname, exist_ok=True)
        total_size = 0
        seen_dsids = set()
        
        # Generate datasets, save to files.
        for i, dsp in enumerate(dsparams_list, 1):
            itemstring = (
                '  Generating for params {:<10} ({} of {})...'.format(
                dsp['dsid'], i, len(dsparams_list)))
            self.print(itemstring, end='')
            ds_list = self.generate_multiple(dsp)
            
            for j, ds in enumerate(ds_list):
                dsid = ds['dsparams']['dsid']
                if dsid in seen_dsids:
                    raise AssertionError('Duplicate dsid: ' + dsid)
                seen_dsids.add(dsid)
                ds_filename = self.workflow.get_ds_filename(dsid)
                with open(ds_filename, 'wb') as dsfile:
                    pickle.dump(ds, dsfile)
                ds_size = os.stat(ds_filename).st_size
                total_size += ds_size
                if j > 0:
                    self.print(' ' * len(itemstring), end='')
                self.print(' ({:,} bytes)'.format(ds_size))
        
        self.print('Total dataset size: {:,} bytes'.format(total_size))
        
        # Generate trials, save to file.
        out_fn = self.workflow.params_filename
        tparams_list = self.get_tparams_list(dsparams_list)
        with open(out_fn, 'wb') as outfile:
            pickle.dump(tparams_list, outfile)
    
    def run(self):
        self.print('Generating test data...')
        with StopWatch() as w:
            self._run()
        self.print('(Datagen time: {:.3f} seconds)'.format(w.elapsed))
    
    def cleanup(self):
        # Remove dataset files, dataset dir, and params file.
        ds_files = glob.glob(self.workflow.ds_filename_glob)
        for dsf in ds_files:
            self.remove_file(dsf)
        self.remove_file(self.workflow.ds_dirname)
        self.remove_file(self.workflow.params_filename)
