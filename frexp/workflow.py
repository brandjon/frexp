"""Workflow management."""


__all__ = [
    'Task',
    'Workflow',
]


import builtins

from frexp.util import StopWatch


class Task:
    
    """Individual steps of a workflow."""
    
    show_time = False
    """If True, print total time taken for task, for informational
    purposes.
    """
    
    def __init__(self, workflow):
        self.workflow = workflow
        self.print = self.workflow.print
        self.prefix = self.workflow.prefix
    
    def run(self):
        """Execute this step."""
        raise NotImplementedError
    
    def cleanup(self):
        """Remote generated files."""
        pass


class Workflow:
    
    """Workflow, comprising a series of tasks to execute."""
    
    def __init__(self, fout, prefix):
        self.fout = fout
        """Output stream for status updates."""
        self.prefix = prefix
        """Prefix (including path) for generated file names."""
        
        self.tasks
    
    def print(self, *args, file=None, flush=True, **kargs):
        """Print, defaulting to stream self.fout with flushing."""
        if file is None:
            file = self.fout
        builtins.print(*args, file=file, flush=True, **kargs)
    
    def run(self):
        """Run the whole workflow."""
        for task in self.tasks:
            with StopWatch() as watch:
                task.run()
            if task.show_time:
                self.print('(took {:.3f} s)'.format(watch.elapsed))
    
    def cleanup(self):
        """Delete files generated by the workflow."""
        for task in self.tasks:
            task.cleanup()
