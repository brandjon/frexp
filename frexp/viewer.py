"""View the extracted result data."""


__all__ = [
    'Printer',
    'Plotter',
]


import pickle

from frexp.workflow import Task


class Printer(Task):
    
    def run(self):
        # Delay the import.
        from tabulate import tabulate
        
        with open(self.workflow.plotdata_filename, 'rb') as in_file:
            plotdata = pickle.load(in_file)
        
        if plotdata['plot_title']:
            print(plotdata['plot_title'])
        
        for ax in plotdata['axes']:
            if ax['axes_title']:
                print(ax['axes_title'])
            
            series_names = []
            series_data = {}
            all_xs = set()
            
            for s in ax['series']:
                name = s['name']
                series_names.append(name)
                series_data[name] = curdata = {}
                for (x, y, _lo, _hi) in s['data']:
                    all_xs.add(x)
                    assert y not in curdata, 'Multiple values for same point'
                    curdata[x] = y
            
            xs = sorted(all_xs)
            data = []
            for x in xs:
                row = [x]
                row += [series_data[name][x] for name in series_names]
                data.append(row)
            tabulate(data)


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
