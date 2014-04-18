"""Plot the extracted result data."""


__all__ = [
    'Plotter',
]


import pickle

from frexp.workflow import Task


class Plotter(Task):
    
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
    
    def cleanup(self):
        self.remove_file(self.workflow.png_filename)
        self.remove_file(self.workflow.pdf_filename)
