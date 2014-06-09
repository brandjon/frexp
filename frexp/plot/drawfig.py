"""Draw matplotlib plots from a description of the data."""


import math

import matplotlib
# Use a Qt backend since Tk seems to mess up my keypresses (under Windows).
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FixedLocator, ScalarFormatter

import numpy as np

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
    title, axes = plot['plot_title'], plot['axes']
    rcparams_file, rcparams = plot['rcparams_file'], plot['rcparams']
    config = plot['config']
    
    if rcparams_file is not None:
        matplotlib.rc_file(rcparams_file)
    if rcparams is not None:
        matplotlib.rcParams.update(rcparams)
    
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
        ax.yaxis.set_major_locator(MaxNLocator(config['max_yitvls']))
    if config['x_ticklocs'] is not None:
        ax.xaxis.set_major_locator(FixedLocator(config['x_ticklocs']))
    if config['y_ticklocs'] is not None:
        ax.yaxis.set_major_locator(FixedLocator(config['y_ticklocs']))
    
    plt.tight_layout()

def do_axes(ax):
    title, series = ax['axes_title'], ax['series']
    logx, logy = ax['logx'], ax['logy']
    ylabel, xlabel = ax['ylabel'], ax['xlabel']
    scalarx, scalary = ax['scalarx'], ax['scalary']
    legend_ncol = ax['legend_ncol']
    legend_loc = ax['legend_loc']
    ylabelpad = ax['ylabelpad']
    xlabelpad = ax['xlabelpad']
    
    if title:
        plt.title(title)
    if ylabel:
        plt.ylabel(ylabel, labelpad=ylabelpad)
    if xlabel:
        plt.xlabel(xlabel, labelpad=xlabelpad)
    if logx:
        plt.gca().set_xscale('log')
    if logy:
        plt.gca().set_yscale('log')
    if scalarx:
        plt.gca().xaxis.set_major_formatter(ScalarFormatter())
    if scalary:
        plt.gca().yaxis.set_major_formatter(ScalarFormatter())
    if legend_ncol is None:
        legend_ncol = 1
    
    leg_artists = []
    leg_texts = []
    for ser in series:
        la, lt = do_series(ser)
        if la is not None:
            leg_artists.append(la)
            leg_texts.append(lt)
    
    plt.legend(leg_artists, leg_texts, loc=legend_loc, ncol=legend_ncol)

def do_series(ser):
    name, color = ser['name'], ser['color']
    errorbars = ser['errorbars']
    line_style = ser['linestyle']
    marker_style = ser['markerstyle']
    series_format = ser['format']
    hollow_markers = ser['hollow_markers']
    dashes = ser['dashes']
    data = ser['data']
    if len(data) == 0:
        return None, None
    unzipped = list(zip(*data))
    xs, ys, lowerrs, hierrs = unzipped
    
    plotkargs = {}
    plotkargs['marker'] = marker_style
    plotkargs['color'] = color
    if hollow_markers:
        plotkargs['markerfacecolor'] = 'none'
        plotkargs['markeredgecolor'] = color
    else:
        plotkargs['markerfacecolor'] = color
        if not ser['marker_border']:
            plotkargs['markeredgecolor'] = color
    if dashes is not None:
        plotkargs['dashes'] = dashes
    else:
        plotkargs['linestyle'] = line_style
    
    markeronly_kargs = dict(plotkargs)
    markeronly_kargs.pop('linestyle', None)
    markeronly_kargs.pop('dashes', None)
    
    lineonly_kargs = dict(plotkargs)
    lineonly_kargs.pop('marker', None)
    
    if series_format == 'normal':
        leg_artist = plt.plot(xs, ys, label=name, **plotkargs)
        assert len(leg_artist) == 1
        leg_artist = leg_artist[0]
    
    elif series_format.startswith('poly'):
        deg = int(series_format[4:])
        pol = np.polyfit(xs, ys, deg)
        plt.plot(xs, ys, label='_nolegend_',
                 linestyle='None', **markeronly_kargs)
        plt.plot(xs, np.polyval(pol, xs), label=name, **lineonly_kargs)
        leg_artist = Line2D([0, 1], [0, 1], label=name, **plotkargs)
    
    elif series_format == 'points':
        leg_artist = plt.plot(xs, ys, label=name, **plotkargs)
        assert len(leg_artist) == 1
        leg_artist = leg_artist[0]
    
    if errorbars:
        # Make sure to use fmt and label kargs to get rid of extraneous
        # plot lines and legend entries, both of which would screw up
        # the lineselector.
        plt.errorbar(xs, ys, yerr=(lowerrs, hierrs),
                     ecolor=color, fmt=None, label='_nolegend_')
    
    return leg_artist, name


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
