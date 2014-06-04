"""Experiment workflows."""


__all__ = [
    'ExpWorkflow',
]


import sys

from frexp.workflow import Workflow
from frexp.runner import Runner
from frexp.verifier import Verifier
from frexp.viewer import Plotter


class ExpWorkflow(Workflow):
    
    """Workflow describing the setup, execution, and analysis of
    an experiment.
    """
    
    stddev_window = None
    """If non-None, standard deviation must be within this fraction
    of mean before tests stop.
    """
    min_repeats = 1
    """Minimum number of repeats to do, even when standard deviation
    looks good.
    """
    max_repeats = None
    """Maximum number of repeats to do, regardless of standard
    deviation. Ignored if None.
    """
    repeat_ylimit = 0
    """If y is below this value, don't worry about standard deviation
    stabilizing. Just run min times.
    """
    do_repeats = True
    """Set False to skip converging altogether."""
    
    # This has saved me countless times from accidentally running
    # tests on power-saving procesor speed.
    require_ac = True
    """If True, abort benchmarking if known to be running on battery
    power.
    """
    
    @property
    def ds_dirname(self):
        """Directory containing generated datasets."""
        return self.prefix + '_datasets/'
    
    @property
    def ds_filename_glob(self):
        """Glob pattern for generated datasets."""
        return self.ds_dirname + 'ds_*.pickle'
    
    def get_ds_filename(self, dsid):
        """Get filename for the dataset named dsid."""
        return self.ds_dirname + 'ds_{}.pickle'.format(dsid)
    
    @property
    def params_filename(self):
        """Filename for list of test params."""
        return self.prefix + '_params.pickle'
    
    @property
    def pipe_filename(self):
        """Filename for pipe file used to communicate with
        driver program.
        """
        return self.prefix + '_pipe.pickle'
    
    @property
    def data_filename(self):
        """Filename for result data."""
        return self.prefix + '_data.pickle'
    
    @property
    def plotdata_filename(self):
        """Filename for extracted plot data."""
        return self.prefix + '_plotdata.pickle'
    
    imagename = 'plot'
    """Component of filename for generated image files."""
    
    @property
    def png_filename(self):
        """Filename for png output."""
        return self.prefix + '_' + self.imagename + '.png'
    
    @property
    def pdf_filename(self):
        """Filename for pdf output."""
        return self.prefix + '_' + self.imagename + '.pdf'
    
    @property
    def ExpDatagen(self):
        raise NotImplementedError
    
    @property
    def ExpExtractor(self):
        raise NotImplementedError
    
    ExpRunner = Runner
    ExpVerifier = Verifier
    ExpViewer = Plotter
    
    @property
    def ExpDriver(self):
        """Function or class to call in the child process to run a
        benchmark. Must be pickleable.
        """
        raise NotImplementedError
    
    @property
    def ExpVerifyDriver(self):
        """Function or class to call in the child process to verify
        results. Must be pickleable.
        """
        raise NotImplementedError
    
    def __init__(self, prefix=None, fout=sys.stdout):
        super().__init__(prefix, fout=fout)
        
        self.datagen = self.ExpDatagen(self)
        self.runner = self.ExpRunner(self)
        self.verifier = self.ExpVerifier(self)
        self.extractor = self.ExpExtractor(self)
        self.viewer = self.ExpViewer(self)
        
        self.tasks = [
            self.datagen,
            self.runner,
#            self.verifier,
            self.extractor,
            self.viewer,
        ]
    
    def generate(self):
        self.datagen.run()
    
    def benchmark(self):
        self.runner.run()
    
    def verify(self):
        self.verifier.run()
    
    def extract(self):
        self.extractor.run()
    
    def view(self):
        self.viewer.run()
