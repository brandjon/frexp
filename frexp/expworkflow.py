"""Experiment workflows."""


__all__ = [
    'ExperimentWorkflow',
]


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
    def datagen(self):
        raise NotImplementedError
    
    @property
    def extractor(self):
        raise NotImplementedError
    
    runner = Runner
    verifier = Verifier
    plotter = Plotter
    
    @property
    def tasks(self):
        return [
            self.datagen,
            self.runner,
            self.verifier,
            self.extractor,
            self.plotter,
        ]
