"""Draw matplotlib plots from a description of the data,
in the format described in format.md.
"""


__all__ = [
    'plot_figure',
    'save_figure',
]


import math
from copy import deepcopy

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FixedLocator

import numpy as np

from .lineselector import add_lineselector


default_plotdata = {
    'title': None,
    
    'x_label': None,
    'x_labelpad': None,
    'x_min': None,
    'x_max': None,
    'x_maxitvls': None,
    'x_ticklocs': None,
    'x_log': False,
    
    'y_label': None,
    'y_labelpad': None,
    'y_min': None,
    'y_max': None,
    'y_maxitvls': None,
    'y_ticklocs': None,
    'y_log': False,
    
    'legend': True,
    'legend_ncol': None,
    'legend_loc': 'upper left',
    'legend_bbox': None,
    
    'rcparams': {},
    'rcparams_file': None,
    
    'figsize': None,
    'dpi': None,
    'tight_layout': True,
    'tight_layout_rect': None,
    
    'series': [],
}

default_seriesdata = {
    'name': None,
    'format': 'normal',
    'polydeg': 1,
    'points': [],
    'errdata': None,
    'color': 'black',
    'linestyle': '-',
    'marker': 'o',
    'hollow_markers': False,
    'marker_border': True,
    'dashes': None,
}


def do_series(seriesdata):
    """Run pyplot commands to draw a series on the current axes.
    seriesdata has the format of a "series" list element as described
    in format.md.
    
    Return a Line2D instance for the legend and a legend label string.
    """
    d = deepcopy(default_seriesdata)
    d.update(seriesdata)
    
    name = d['name']
    if not (len(d['points']) > 0 and
            all(len(tup) == 2 for tup in d['points'])):
        raise ValueError('Invalid list of points')
    xs, ys = zip(*d['points'])
    format = d['format']
    
    plot_kargs = {k: d[k] for k in ['color', 'marker']}
    if d['hollow_markers']:
        plot_kargs['markerfacecolor'] = 'None'
        plot_kargs['markeredgecolor'] = d['color']
    else:
        plot_kargs['markerfacecolor'] = d['color']
        if not d['marker_border']:
            plot_kargs['markeredgecolor'] = d['color']
    if d['dashes']:
        plot_kargs['dashes'] = d['dashes']
    else:
        plot_kargs['linestyle'] = d['linestyle']
    
    markeronly_kargs = dict(plot_kargs)
    markeronly_kargs['linestyle'] = 'None'
    markeronly_kargs.pop('dashes', None)
    lineonly_kargs = dict(plot_kargs)
    lineonly_kargs['marker'] = 'None'
    
    if format == 'normal':
        plt.plot(xs, ys, **plot_kargs)
    
    elif format == 'polyfit':
        plt.plot(xs, ys, **markeronly_kargs)
        # Generate a polynomial fit and plot the polynomial,
        # sampled at about 10 times as many points as are in
        # the given data.
        deg = d['polydeg']
        pol = np.polyfit(xs, ys, deg)
        fit_xs = np.linspace(xs[0], xs[-1], len(xs) * 10 + 1)
        fit_ys = np.polyval(pol, fit_xs)
        plt.plot(fit_xs, fit_ys, **lineonly_kargs)
    
    elif format == 'points':
        plt.plot(xs, ys, **markeronly_kargs)
    
    if d['errdata']:
        bad = not (len(d['errdata']) > 0 and
                   all(len(tup) == 2 for tup in d['errdata']))
        low_err, high_err = zip(*d['errdata'])
        bad |= not (len(low_err) == len(high_err) == len(xs) == len(ys))
        if bad:
            raise ValueError('Invalid error bar data')
        plt.errorbar(xs, ys, yerr=(low_err, high_err), ecolor=d['color'])
    
    legline = Line2D([], [], **plot_kargs)
    return legline, name


def do_figure(plotdata):
    """Plot and show the given data. plotdata is a dictionary
    structure as described in format.md.
    """
    d = deepcopy(default_plotdata)
    d.update(plotdata)
    
    if d['title']:
        plt.title(d['title'])
    if d['x_label']:
        plt.xlabel(d['x_label'], labelpad=d['x_labelpad'])
    if d['y_label']:
        plt.ylabel(d['y_label'], labelpad=d['y_labelpad'])
    if not (d['x_min'] == d['x_max'] == None):
        plt.xlim(xmin=d['x_min'], xmax=d['x_max'])
    if not (d['y_min'] == d['y_max'] == None):
        plt.ylim(ymin=d['y_min'], ymax=d['y_max'])
    ax = plt.gca()
    if d['x_maxitvls']:
        ax.xaxis.set_major_locator(MaxNLocator(d['x_maxitvls']))
    if d['y_maxitvls']:
        ax.yaxis.set_major_locator(MaxNLocator(d['y_maxitvls']))
    if d['x_ticklocs']:
        ax.xaxis.set_major_locator(FixedLocator(d['x_ticklocs']))
    if d['y_ticklocs']:
        ax.yaxis.set_major_locator(FixedLocator(d['y_ticklocs']))
    if d['x_log']:
        ax.set_xscale('log')
    if d['y_log']:
        ax.set_yscale('log')
    
    if d['rcparams_file']:
        matplotlib.rc_file(d['rcparams_file'])
    if d['rcparams']:
        matplotlib.rcParams.update(d['rcparams'])
    
    if d['figsize']:
        fig_width, fig_height = d['figsize']
        plt.gcf().set_size_inches(fig_width, fig_height, forward=True)
    if d['dpi']:
        plt.gcf().set_dpi(d['dpi'])
    if d['tight_layout']:
        plt.tight_layout(rect=d['tight_layout_rect'])
    
    leglines = []
    legtexts = []
    for ser in d['series']:
        legline, legtext = do_series(ser)
        leglines.append(legline)
        legtexts.append(legtext)
    
    if d['legend']:
        legend_kargs = {}
        legend_kargs['loc'] = d['legend_loc']
        legend_kargs['bbox_to_anchor'] = d['legend_bbox']
        if d['legend_ncol']:
            legend_kargs['ncol'] = d['legend_ncol']
        plt.legend(leglines, legtexts, **legend_kargs)


def plot_figure(plotdata):
    xkcd = False
    
    def redraw():
        plt.clf()
        if xkcd:
            with plt.xkcd():
                do_figure(plotdata)
        else:
            do_figure(plotdata)
    
    def handler(event):
        nonlocal xkcd
        k = event.key
        if k == 'x':
            xkcd = not xkcd
            redraw()
    
    redraw()
#    add_lineselector(plt.gcf())
    plt.gcf().canvas.mpl_connect('key_press_event', handler)
    plt.show()


def save_figure(plotdata, out_filename):
    """Plot and save the given data. plotdata is a dictionary
    structure as described in format.md.
    """
    plt.clf()
    do_figure(plotdata)
    plt.savefig(out_filename)
