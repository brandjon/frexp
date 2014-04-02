"""Plot the extracted result data."""


__all__ = [
    'Plotter',
]


import pickle

from frexp.workflow import Task


class Plotter(Task):
    
    # The use of two out files, for png and pdf, is a bit hackish.
    # Should rework how ExperimentWorkflow instantiates its Tasks,
    # and how Tasks deal with their input and output files.
    
    def run(self):
        # Delay the import until here so if matplotlib can't be loaded
        # we can still do the rest of the testing.
        from .plot import draw_figure, save_figure
        
        with open(self.workflow.plotdata_filename, 'rb') as in_file:
            plotdata = pickle.load(in_file)
        
        save_figure(plotdata, self.workflow.png_filename)
        save_figure(plotdata, self.workflow.pdf_filename)
        draw_figure(plotdata)
        self.print('Done.')
