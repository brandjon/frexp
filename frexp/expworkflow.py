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
