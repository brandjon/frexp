"""Draw matplotlib plots from a description of the data.

See readme-explib.txt for data format.
"""


import math

import matplotlib
# Use a Qt backend since Tk seems to mess up my keypresses (under Windows).
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from .lineselector import add_lineselector


def get_subplot_grid(n):
    """Get a (h, w) arrangement for up to 9 subplots."""
    assert 0 <= n <= 9
    if n <= 3:
        return 1, n
    elif n <= 6:
        return 2, n - 3
    else:
        return 3, n - 6


def get_square_subplot_grid(n):
    """Get a (h, w) square arrangement for any number of subplots."""
    side = math.ceil(n ** .5)
    return side, side


# Structurally break down a plot into axes into series, and execute
# matplotlib.pyplot commands.

def do_plot(plot, xkcd=False):
    if xkcd:
        with plt.xkcd():
            do_plot_helper(plot)
    else:
        do_plot_helper(plot)

def do_plot_helper(plot):
    title, axes, config = plot['plot_title'], plot['axes'], plot['config']
    
    if config['fontsize'] is not None:
        matplotlib.rcParams['font.size'] = config['fontsize']
    if config['legfontsize'] is not None:
        matplotlib.rcParams['legend.fontsize'] = config['legfontsize']
    if config['linewidth'] is not None:
        matplotlib.rcParams['lines.linewidth'] = config['linewidth']
    if config['markersize'] is not None:
        matplotlib.rcParams['lines.markersize'] = config['markersize']
    if config['ticksize'] is not None:
        ts = config['ticksize']
        matplotlib.rcParams['xtick.major.size'] = ts
        matplotlib.rcParams['ytick.major.size'] = ts
        matplotlib.rcParams['xtick.major.size'] = ts / 2
        matplotlib.rcParams['ytick.major.size'] = ts / 2
    if config['tickwidth'] is not None:
        tw = config['tickwidth']
        matplotlib.rcParams['xtick.major.width'] = tw
        matplotlib.rcParams['ytick.major.width'] = tw
        matplotlib.rcParams['xtick.minor.width'] = tw
        matplotlib.rcParams['ytick.minor.width'] = tw
    if config['figsize'] is not None:
        fig_width, fig_height = config['figsize']
        plt.gcf().set_size_inches(fig_width, fig_height, forward=True)
    
    plt.suptitle(title, size='x-large')
    h, w = get_square_subplot_grid(len(axes))
    for i, ax in enumerate(axes, 1):
        plt.subplot(h, w, i)
        do_axes(ax)
    
    ax = plt.gca()
    ax.set_xlim(left=config['xmin'], right=config['xmax'])
    ax.set_ylim(bottom=config['ymin'], top=config['ymax'])
    if config['max_xitvls']:
        ax.xaxis.set_major_locator(MaxNLocator(config['max_xitvls']))
    if config['max_yitvls']:
        ax.yaxis.set_major_locator(MaxNLocator(config['max_xitvls']))
    
    plt.subplots_adjust(bottom=.15, left=.15)

def do_axes(ax):
    title, series, logscale = ax['axes_title'], ax['series'], ax['logscale']
    ylabel, xlabel = ax['ylabel'], ax['xlabel']
    if title:
        plt.title(title)
    if ylabel:
        plt.ylabel(ylabel)
    if xlabel:
        plt.xlabel(xlabel)
    if logscale:
        plt.gca().set_yscale('log')
    for ser in series:
        do_series(ser)
    
    plt.legend(loc='upper left')

def do_series(ser):
    name, style, color = ser['name'], ser['style'], ser['color']
    errorbars = ser['errorbars']
    data = ser['data']
    if len(data) == 0:
        return
    unzipped = list(zip(*data))
    
    if errorbars:
        have_err = True
        xs, ys, lowerrs, hierrs = unzipped
    else:
        have_err = False
        xs, ys = unzipped
    
    plt.plot(xs, ys, style, label=name, color=color)
    
    if have_err:
        # Make sure to use fmt and label kargs to get rid of extraneous
        # plot lines and legend entries, both of which would screw up
        # the lineselector.
        plt.errorbar(xs, ys, yerr=(lowerrs, hierrs),
                     ecolor=color, fmt=None, label='_nolegend_')


class Plot:
    
    def __init__(self, data):
        self.data = data
        self.line_cid = None
        self.xkcd_cid = None
        self.xkcd = False
    
    def replot(self):
        """Plot or replot the data, replacing the lineselector."""
        if self.line_cid is not None:
            plt.gcf().canvas.mpl_disconnect(self.line_cid)
        if self.xkcd_cid is not None:
            plt.gcf().canvas.mpl_disconnect(self.xkcd_cid)
        plt.clf()
        
        do_plot(self.data, self.xkcd)
        plt.gcf().canvas.draw()
        
        self.line_cid = add_lineselector(plt.gcf())
        self.xkcd_cid = self.add_xkcd(plt.gcf())
    
    def add_xkcd(self, figure):
        def handler(event):
            k = event.key
            if k == 'x':
                self.xkcd = not self.xkcd
                self.replot()
        return figure.canvas.mpl_connect('key_press_event', handler)

def draw_figure(plotdata):
    """Plot the given data and show the figure, with a lineselector."""
    plot = Plot(plotdata)
    plot.replot()
    plt.show()

def save_figure(plotdata, out_filename):
    plot = Plot(plotdata)
    plot.replot()
    plt.savefig(out_filename)
