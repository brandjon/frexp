"""Workflow management."""


__all__ = [
    'Task',
    'Workflow',
]


import builtins
import sys
import os


class Task:
    
    """Individual steps of a workflow."""
    
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
    
    def remove_file(self, filepath):
        """If filepath exists, delete it and print a message.
        Otherwise, ignore. filepath may also point to an empty
        directory.
        """
        try:
            if os.path.isdir(filepath):
                os.rmdir(filepath)
            else:
                os.remove(filepath)
            self.print('Removed ' + filepath)
        except FileNotFoundError:
            pass


class Workflow:
    
    """Workflow, comprising a series of tasks to execute."""
    
    prefix = None
    """Prefix (including path) for generated file names.
    Can be overridden in constructor.
    """
    
    def __init__(self, prefix=None, fout=sys.stdout):
        if prefix is not None:
            self.prefix = prefix
        
        self.fout = fout
        """Output stream for status updates."""
        
        self.tasks = []
        """Task instances."""
    
    def print(self, *args, file=None, flush=True, **kargs):
        """Print, defaulting to stream self.fout with flushing."""
        if file is None:
            file = self.fout
        builtins.print(*args, file=file, flush=True, **kargs)
    
    def run(self):
        """Run the whole workflow."""
        for task in self.tasks:
            task.run()
    
    def cleanup(self):
        """Delete files generated by the workflow."""
        for task in self.tasks:
            task.cleanup()
