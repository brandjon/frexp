"""Simple plotting example."""

from frexp.newapi.plot import plot_figure

plotdata = {
    'series':  [
        {
            'name': 'Series 1',
            'points': [(x, x) for x in range(20)],
            'color': 'red',
        },
        {
            'name': 'Series 2',
            'points': [(x, x**2 / 10) for x in range(20)],
            'color': 'green'
        },
    ], 
}

plot_figure(plotdata)
