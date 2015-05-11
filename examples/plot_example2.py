"""Slightly more complex plotting example."""

from frexp.newapi.plot import plot_figure
from random import random

plotdata = {
    'title': 'Example',
    'x_label': 'X axis',
    'y_label': 'Y axis',
    'y_min': 0,
    
    'series':  [
        {
            'name': 'Series 1',
            'format': 'polyfit',
            'polydeg': 2,
            'points': [(x, x**2 * (.75 + random()/2) * .2)
                       for x in range(20)],
            'color': 'red',
        },
        {
            'name': 'Series 2',
            'format': 'normal',
            'points': [(x, x * (.75 + random()/2))
                       for x in range(20)],
            'errdata': [(3 * random(), 3 * random())
                        for x in range(20)],
            'color': 'green',
            'linestyle': '--',
            'marker': 'o',
            'hollow_markers': True,
        },
        {
            'name': 'Series 3',
            'format': 'points',
            'points': [(x, 35 + random()*10)
                       for x in list(range(20)) * 3],
            'color': 'blue',
            'marker': '^',
            'marker_border': False,
        },
    ],
    
    'rcparams': {
        'font.size':           24,
        'legend.fontsize':     24,
        'lines.linewidth':     2,
        'lines.markersize':    6,
        'lines.markeredgewidth': 1,
        
        'xtick.major.size':    10,
        'ytick.major.size':    10,
        'xtick.minor.size':    8,
        'ytick.minor.size':    8,
        'xtick.major.width':   2,
        'ytick.major.width':   2,
        'xtick.minor.width':   1,
        'ytick.minor.width':   1,
        
        'legend.frameon':      False,
    },
    
    'figsize': (10, 8), 
}

plot_figure(plotdata)
