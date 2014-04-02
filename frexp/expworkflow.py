"""Experiment workflows."""


__all__ = [
    'ExperimentWorkflow',
]


import sys

from frexp.workflow import Workflow
from frexp.runner import Runner
from frexp.verifier import Verifier
from frexp.plotter import Plotter


class ExperimentWorkflow(Workflow):
    
    """Workflow describing the setup, execution, and analysis of
    an experiment.
    """
    
    @property
    def ds_dirname(self):
        return self.prefix + '_datasets/'
    
    ds_filename_pattern = 'ds_*.pickle'
    
    def get_ds_filename(self, dsid):
        return self.ds_dirname + 'ds_{}.pickle'.format(dsid)
    
    @property
    def params_filename(self):
        return self.prefix + '_params.pickle'
    
    @property
    def pipe_filename(self):
        return self.prefix + '_pipe.pickle'
    
    @property
    def data_filename(self):
        return self.prefix + '_data.pickle'
    
    @property
    def plotdata_filename(self):
        return self.prefix + '_plotdata.pickle'
    
    imagename = 'plot'
    
    @property
    def png_filename(self):
        return self.prefix + '_' + self.imagename + '.png'
    
    @property
    def pdf_filename(self):
        return self.prefix + '_' + self.imagename + '.pdf'
    
    @property
    def ExpDatagen(self):
        raise NotImplementedError
    
    @property
    def ExpExtractor(self):
        raise NotImplementedError
    
    ExpRunner = Runner
    ExpVerifier = Verifier
    ExpPlotter = Plotter
    
    def __init__(self, prefix, fout=sys.stdout):
        super().__init__('results/' + prefix, fout=fout)
        
        self.datagen = self.ExpDatagen(self)
        self.runner = self.ExpRunner(self)
        self.verifier = self.ExpVerifier(self)
        self.extractor = self.ExpExtractor(self)
        self.plotter = self.ExpPlotter(self)
        
        self.tasks = [
            self.datagen,
            self.runner,
#            self.verifier,
            self.extractor,
            self.plotter,
        ]
    
    def generate(self):
        self.datagen.run()
    
    def benchmark(self):
        self.runner.run()
    
    def verify(self):
        self.verifier.run()
    
    def extract(self):
        self.extractor.run()
    
    def plot(self):
        self.plotter.run()
