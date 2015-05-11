"""Draw matplotlib plots from a description of the data,
in the format described in format.md.
"""


__all__ = [
    'plot_figure',
    'save_figure',
]


from copy import deepcopy
from collections import namedtuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator, FixedLocator

import numpy as np


default_plotdata = {
    'rcparams': {},
    'rcparams_file': None,
    
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
    
    'figsize': None,
    'dpi': None,
    'tight_layout': True,
    'tight_layout_rect': None,
    
    'series': [],
}

default_seriesdata = {
    'name': '...',
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


SeriesArtistInfo = namedtuple('SeriesArtistInfo', [
    'name',       # name of series
    'proxy',      # proxy artist used to create legend entry
    'plotlines',  # list of Line2Ds for plotting
    'legline',    # Line2D from legend entry, or None
    'legtext',    # Text from legend entry, or None
])


def do_series(seriesdata):
    """Run pyplot commands to draw a series on the current axes.
    seriesdata has the format of a "series" list element as described
    in format.md.
    
    Return a SeriesArtistInfo tuple listing the legend entry and
    lines created for this series.
    """
    d = deepcopy(default_seriesdata)
    d.update(seriesdata)
    
    name = d['name']
    if not (len(d['points']) > 0 and
            all(len(tup) == 2 for tup in d['points'])):
        raise ValueError('Invalid list of points')
    xs, ys = zip(*d['points'])
    format = d['format']
    
    # Setup separate kargs for drawing general lines, markers
    # only, and lines only.
    
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
    
    plotlines = []
    
    if format == 'normal':
        line = plt.plot(xs, ys, **plot_kargs)
        plotlines.extend(line)
    
    elif format == 'polyfit':
        line = plt.plot(xs, ys, **markeronly_kargs)
        plotlines.extend(line)
        # Generate a polynomial fit and plot the polynomial,
        # sampled at about 10 times as many points as are in
        # the given data.
        deg = d['polydeg']
        pol = np.polyfit(xs, ys, deg)
        fit_xs = np.linspace(xs[0], xs[-1], len(xs) * 10 + 1)
        fit_ys = np.polyval(pol, fit_xs)
        line = plt.plot(fit_xs, fit_ys, **lineonly_kargs)
        plotlines.extend(line)
    
    elif format == 'points':
        line = plt.plot(xs, ys, **markeronly_kargs)
        plotlines.extend(line)
    
    if d['errdata']:
        bad = not (len(d['errdata']) > 0 and
                   all(len(tup) == 2 for tup in d['errdata']))
        low_err, high_err = zip(*d['errdata'])
        bad |= not (len(low_err) == len(high_err) == len(xs) == len(ys))
        if bad:
            raise ValueError('Invalid error bar data')
        container = plt.errorbar(xs, ys, yerr=(low_err, high_err),
                                 fmt='None', ecolor=d['color'],
                                 **plot_kargs)
        # Getting the Line2Ds for errorbars is hackish.
        # The return value of plt.errorbar() doesn't appear
        # to be documented.
        plotlines.extend(container.lines[1])
        plotlines.extend(container.lines[2])
    
    proxyline = Line2D([], [], **plot_kargs)
    # legline and legtext will be filled in when the legend
    # is generated.
    return SeriesArtistInfo(name, proxyline, plotlines, None, None)


def do_figure(plotdata):
    """Plot and show the given data. plotdata is a dictionary
    structure as described in format.md.
    
    Return a list of SeriesArtistInfo tuples for the created
    series.
    """
    d = deepcopy(default_plotdata)
    d.update(plotdata)
    
    if d['rcparams_file']:
        matplotlib.rc_file(d['rcparams_file'])
    if d['rcparams']:
        matplotlib.rcParams.update(d['rcparams'])
    
    if d['title']:
        plt.title(d['title'])
    if d['x_label']:
        plt.xlabel(d['x_label'], labelpad=d['x_labelpad'])
    if d['y_label']:
        plt.ylabel(d['y_label'], labelpad=d['y_labelpad'])
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
    
    if d['figsize']:
        fig_width, fig_height = d['figsize']
        plt.gcf().set_size_inches(fig_width, fig_height, forward=True)
    if d['dpi']:
        plt.gcf().set_dpi(d['dpi'])
    if d['tight_layout']:
        plt.tight_layout(rect=d['tight_layout_rect'])
    
    seriesinfo = []
    for ser in d['series']:
        info = do_series(ser)
        seriesinfo.append(info)
    
    # For whatever reason, this needs to be done after the
    # series are already plotted, or else passing None to
    # set the limit automatically doesn't work.
    if not (d['x_min'] == d['x_max'] == None):
        plt.xlim(xmin=d['x_min'], xmax=d['x_max'])
    if not (d['y_min'] == d['y_max'] == None):
        plt.ylim(ymin=d['y_min'], ymax=d['y_max'])
    
    if d['legend']:
        legend_kargs = {}
        legend_kargs['loc'] = d['legend_loc']
        legend_kargs['bbox_to_anchor'] = d['legend_bbox']
        if d['legend_ncol']:
            legend_kargs['ncol'] = d['legend_ncol']
        legend = plt.legend([info.proxy for info in seriesinfo],
                            [info.name for info in seriesinfo],
                            **legend_kargs)
    
    # Fill in legtext.
    leglines = legend.get_lines()
    legtexts = legend.get_texts()
    assert len(leglines) == len(legtexts) == len(seriesinfo)
    seriesinfo = [info._replace(legline=line, legtext=text)
                  for info, line, text in zip(seriesinfo, leglines, legtexts)]
    
    return seriesinfo


class SelectorCursor:
    
    """An abstract cursor for selecting zero or one elements out of
    a fixed length sequence. Executes a callback when a position
    becomes selected or deselected.
    """
    
    BIG_JUMP = 5
    """Number of elements to skip for big jumps."""
    
    def __init__(self, num_elems, cb_activate, cb_deactivate):
        self.num_elems = num_elems
        """Length of sequence."""
        self.cb_activate = cb_activate
        """A callback function to be called as f(i, active=True)
        when an index i is activated.
        """
        self.cb_deactivate = cb_deactivate
        """A callback function to be called as f(i, active=False)
        when an index i is deactivated.
        """
        self.cursor = None
        """Cursor index. Valid values are None and 0 up to
        num_elems - 1, inclusive.
        """
    
    def goto(self, i):
        """Go to the new index. No effect if cursor is currently i."""
        if i == self.cursor:
            return
        
        if self.cursor is not None:
            self.cb_deactivate(self.cursor, active=False)
        self.cursor = i
        if self.cursor is not None:
            self.cb_activate(self.cursor, active=True)
    
    def changeby(self, offset):
        """Skip to an offset of the current position."""
        states = [None] + list(range(0, self.num_elems))
        i = states.index(self.cursor)
        i = (i + offset) % len(states)
        self.goto(states[i])
    
    def next(self):
        self.changeby(1)
    
    def bulknext(self):
        self.changeby(self.BIG_JUMP)
    
    def prev(self):
        self.changeby(-1)
    
    def bulkprev(self):
        self.changeby(-self.BIG_JUMP)
    
    def reset(self):
        self.goto(None)


class Plot:
    
    HIGHLIGHT_COLOR = '#00AAFF'
    @property
    def LINE_HIGHLIGHT(self):
        return {
            'zorder': 3,
            'color': self.HIGHLIGHT_COLOR,
            'linewidth': 3.0,
            'markerfacecolor': self.HIGHLIGHT_COLOR,
            'markeredgecolor': self.HIGHLIGHT_COLOR,
            'markersize': 8,
        }
    @property
    def TEXT_HIGHLIGHT(self):
        return {
            'color': self.HIGHLIGHT_COLOR,
        }
    
    def __init__(self, plotdata):
        self.plotdata = plotdata
        self.cursor = None
        self.xkcd = False
        self.seriesinfo = None
        self.canvas = None
        self.style_map = {}
    
    def redraw(self):
        if self.cursor is not None:
            self.cursor.reset()
        
        plt.clf()
        if self.xkcd:
            with plt.xkcd():
                self.seriesinfo = do_figure(self.plotdata)
        else:
            self.seriesinfo = do_figure(self.plotdata)
        
        self.canvas = plt.gcf().canvas
        self.style_map = {}
    
    def setup_handlers(self):
        self.cursor = SelectorCursor(len(self.seriesinfo),
                                     self.mark, self.mark)
        plt.gcf().canvas.mpl_connect('key_press_event',
                                     self.xkcd_handler)
        plt.gcf().canvas.mpl_connect('key_press_event',
                                     self.lineselector_handler)
    
    def xkcd_handler(self, event):
        k = event.key
        if k == 'x':
            self.xkcd = not self.xkcd
            self.redraw()
            self.canvas.draw()
    
    def lineselector_handler(self, event):
        k = event.key
        actionmap = {
            'down':         self.cursor.next,
            'up':           self.cursor.prev,
            'pagedown':     self.cursor.bulknext,
            'pageup':       self.cursor.bulkprev,
        }
        if k not in actionmap:
            return
        actionmap[k]()
    
    def mark(self, i, active):
        # We don't appear to be able to easily highlight the markers
        # in the legend entry. The artist for legend markers isn't
        # directly exposed by the Legend object.
        
        if i == None:
            return
        _name, _proxy, plotlines, legline, legtext = self.seriesinfo[i]
        
        def apply(artist, highlightprops):
            props.setdefault(artist, {})
            for attr, value in highlightprops.items():
                getter = getattr(artist, 'get_' + attr, None)
                setter = getattr(artist, 'set_' + attr, None)
                if getter is not None and setter is not None:
                    props[artist][attr] = getter()
                    setter(value)
        
        def revert(artist, highlightprops):
            for attr in highlightprops.keys():
                setter = getattr(artist, 'set_' + attr, None)
                if setter is not None:
                    setter(props[artist][attr])
        
        if active:
            self.style_map[i] = props = {}
            for line in plotlines:
                apply(line, self.LINE_HIGHLIGHT)
            apply(legline, self.LINE_HIGHLIGHT)
            apply(legtext, self.TEXT_HIGHLIGHT)
        
        else:
            # Load from style properties.
            props = self.style_map[i]
            for line in plotlines:
                revert(line, self.LINE_HIGHLIGHT)
            revert(legline, self.LINE_HIGHLIGHT)
            revert(legtext, self.TEXT_HIGHLIGHT)
        
        self.canvas.draw()
    
    def show(self):
        plt.show()
    
    def save(self, filename):
        plt.savefig(filename)


def plot_figure(plotdata):
    """Plot and display the given data. plotdata is a dictionary
    structure as described in format.md.
    """
    plot = Plot(plotdata)
    plot.redraw()
    plot.setup_handlers()
    plot.show()


def save_figure(plotdata, out_filename):
    """Plot and save the given data. plotdata is a dictionary
    structure as described in format.md.
    """
    plot = Plot(plotdata)
    plot.redraw()
    plot.save(out_filename)