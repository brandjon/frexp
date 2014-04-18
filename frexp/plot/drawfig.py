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


def styleparts(style):
    """Break up a plt.plot() line style into its line part
    and marker part.
    """
    # Not sure what the exact format of the style parameter
    # is, but in my use I always put the line style before
    # the marker style.
    if style.startswith('--'):
        i = 2
    elif style.startswith('-'):
        i = 1
    elif style.startswith('_'):
        i = 1
    elif style.startswith(':'):
        i = 1
    return style[:i], style[i:]


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
        ax.yaxis.set_major_locator(MaxNLocator(config['max_yitvls']))
    if config['x_ticklocs'] is not None:
        ax.xaxis.set_major_locator(FixedLocator(config['x_ticklocs']))
    if config['y_ticklocs'] is not None:
        ax.yaxis.set_major_locator(FixedLocator(config['y_ticklocs']))
    
    plt.subplots_adjust(bottom=.15, left=.15)

def do_axes(ax):
    title, series = ax['axes_title'], ax['series']
    logx, logy = ax['logx'], ax['logy']
    ylabel, xlabel = ax['ylabel'], ax['xlabel']
    scalarx, scalary = ax['scalarx'], ax['scalary']
    if title:
        plt.title(title)
    if ylabel:
        plt.ylabel(ylabel)
    if xlabel:
        plt.xlabel(xlabel)
    if logx:
        plt.gca().set_xscale('log')
    if logy:
        plt.gca().set_yscale('log')
    if scalarx:
        plt.gca().xaxis.set_major_formatter(ScalarFormatter())
    if scalary:
        plt.gca().yaxis.set_major_formatter(ScalarFormatter())
    
    leg_artists = []
    leg_texts = []
    for ser in series:
        la, lt = do_series(ser)
        if la is not None:
            leg_artists.append(la)
            leg_texts.append(lt)
    
    plt.legend(leg_artists, leg_texts, loc='upper left')

def do_series(ser):
    name, style, color = ser['name'], ser['style'], ser['color']
    errorbars = ser['errorbars']
    series_format = ser['format']
    hollow_markers = ser['hollow_markers']
    data = ser['data']
    if len(data) == 0:
        return None, None
    unzipped = list(zip(*data))
    xs, ys, lowerrs, hierrs = unzipped
    
    if hollow_markers:
        plotkargs = {'markerfacecolor': 'none',
                     'markeredgecolor': color,
                     'markeredgewidth': 1}
    else:
        plotkargs = {}
    
    if series_format == 'normal':
        leg_artist = plt.plot(xs, ys, style,
                              label=name, color=color, **plotkargs)
        assert len(leg_artist) == 1
        leg_artist = leg_artist[0]
    
    elif series_format.startswith('poly'):
        deg = int(series_format[4:])
        pol = np.polyfit(xs, ys, deg)
        line_style, point_style = styleparts(style)
        plt.plot(xs, ys, point_style,
                 label='_nolegend_', color=color, **plotkargs)
        plt.plot(xs, np.polyval(pol, xs), line_style,
                 label=name, color=color, **plotkargs)
        leg_artist = Line2D([0, 1], [0, 1], linestyle=line_style,
                            marker=point_style,
                            label=name, color=color, **plotkargs)
    
    elif series_format == 'points':
        line_style, point_style = styleparts(style)
        leg_artist = plt.plot(xs, ys, point_style,
                              label=name, color=color, **plotkargs)
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
