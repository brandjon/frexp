"""Plot the extracted result data."""


import pickle

from .workflow import Task


class Plotter(Task):
    
    # The use of two out files, for png and pdf, is a bit hackish.
    # Should rework how ExperimentWorkflow instantiates its Tasks,
    # and how Tasks deal with their input and output files.
    
    def __init__(self, fout, in_filename, out_filename, out_pdf_filename):
        super().__init__(fout, in_filename, out_filename)
        self.out_pdf_filename = out_pdf_filename
    
    def main(self):
        # Delay the import until here so if matplotlib can't be loaded
        # we can still do the rest of the testing.
        from .plot import draw_figure, save_figure
        
        with open(self.in_filename, 'rb') as in_file:
            plotdata = pickle.load(in_file)
        
        save_figure(plotdata, self.out_filename)
        save_figure(plotdata, self.out_pdf_filename)
        draw_figure(plotdata)
        self.print('Done.')
