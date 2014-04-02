"""Result data extraction."""


__all__ = [
    'Extractor',
    'AveragerMixin',
    'SimpleExtractor',
    'SeqExtractor',
    'TotalSizeExtractor',
    'MemExtractor',
    'NormalizedExtractor',
    'SizeBreakdownExtractor',
]


import pickle
import math
import random
from itertools import groupby
from operator import itemgetter

from .workflow import Task


def average_points(self, xy, discard_ratio):
    """Given a list of (x, y) pairs, return a list of quadruples
    
        (x, avg y, y low delta, y high delta).
    
    For each x value, all the corresponding y values are grouped
    together. These y values are averaged, then the high and low
    percentile values are discarded. The difference between the
    remaining extreme values and the average become the low and high
    deltas.
    """
    xy = list(xy)
    xy.sort(key=itemgetter(0))
    
    result = []
    for x, grouped in groupby(xy, key=itemgetter(0)):
        ys = sorted(p[1] for p in grouped)
        
        # Compute average including outliers.
        avg_y = sum(ys) / len(ys)
        
        # Exclude high/lo percentile values.
        discard_width = math.floor(len(ys) * discard_ratio)
        if discard_width > 0:
            ys = ys[discard_width : -discard_width]
        
        min_y = min(ys)
        max_y = max(ys)
        result.append((x, avg_y, avg_y - min_y, max_y - avg_y))
    
    return result


class Extractor(Task):
    
    """Abstract base class for extractors. Defines utility functions
    for retrieving and manipulating data points.
    """
    
    # Default display characteristics.
    fontsize = 36
    legfontsize = 20
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    linewidth = 2
    markersize = 10
    ticksize = 16
    tickwidth = 2
    figsize = (12, 9)
    max_xitvls = None
    max_yitvls = None
    
    @property
    def config(self):
        return {k: getattr(self, k)
                for k in [
            'fontsize', 'legfontsize',
            'xmin', 'xmax', 'ymin', 'ymax',
            'linewidth', 'markersize', 'ticksize', 'tickwidth',
            'figsize', 'max_xitvls', 'max_yitvls'
        ]}
    
    title = None
    ylabel = None
    xlabel = None
    
    error_bars = False
    discard_ratio = 0.0
    
    series = []
    """List of """
    
#    def select_prog_series(self, points, prog, series):
#        return [p for p in points
#                  if p['prog'] == prog
#                  if series is None or p['dsparams']['series'] == series]
#    
#    def project_x(self, p):
#        return p['dsparams']['x']
#    
#    def project_seq_metric(self, p, seq, metric):
#        return p['results']['seqs'][seq][metric]
#    
#    def project_totalsize(self, p):
#        return sum(p['results']['sizes'].values())
#    
#    def project_mem(self, p):
#        return p['results']['memory']
#    
#    def getter_x(self):
#        def getter(p):
#            return p['dsparams']['x']
#        return getter
#    
#    def getter_seq_metric(self, seq, metric):
#        def getter(p):
#            return p['results']['seqs'][seq][metric]
#        return getter
#    
#    def getter_memory(self):
#        def getter(p):
#            return p['results']['memory']
#        return getter
#    
#    def getter_size(self, objname):
#        def getter(p):
#            return p['results']['sizes'][objname]
#        return getter
#    
#    def getter_totalsize(self):
#        def getter(p):
#            return sum(p['results']['sizes'].values())
#        return getter
    
    def get_series_data(self):
        raise NotImplemented
    
    def get_series(self):
        series = []
        for name, data in self.get_series_data():
            if name not in self.series:
                continue
            color, style = self.series[name]
            series.append(dict(
                name = name,
                style = style,
                color = color,
                errorbars = self.error_bars,
                data = data,
            ))
        return series
    
    def get_plotdata(self):
        return dict(
            plot_title = self.title if self.title is not None
                         else '',
            axes = [dict(
                axes_title = None,
                ylabel = self.ylabel,
                xlabel = self.xlabel,
                logscale = False,
                series = self.get_series(),
            )],
            config = self.config,
        )
    
    def run(self):
        with open(self.workflow.data_filename, 'rb') as in_file:
            self.data = pickle.load(in_file)
        
        plotdata = self.get_plotdata()
        
        with open(self.workflow.plotdata_filename, 'wb') as out_file:
            pickle.dump(plotdata, out_file)
        
        self.print('Done.')


class SimpleExtractor(Extractor):
    
    """Extractor that shows each prog's results on a particular seq."""
    
    seq = None
    """Operation sequence to show, e.g. 'all'."""
    metric = None
    """Metric to plot, e.g. 'ttltime'."""
    
    def project_x(self, p):
        """Grab x value from datapoint. Can be overridden e.g.
        for scaling."""
        return p['dsparams']['x']
    
    def project_y(self, p):
        """Grab y value from datapoint. Can be overridden e.g.
        for scaling.
        """
        return p['results']['seqs'][self.seq][self.metric]
    
    def get_series_data(self):
        results = []
        for prog in self.series.keys():
            points = [p for p in self.data if p['prog'] == prog]
            xy = [(self.project_x(p), self.project_y(p))
                  for p in points]
            data = average_points(xy, self.discard_ratio)
            results.append((prog, data))
        return results



#class TotalSizeExtractor(SimpleExtractor):
#    
#    """Show total structure size on one axes."""
#    
#    ylabel = '# aux. entries'
#    
#    def project_y(self, p):
#        return self.project_totalsize(p)
#
#
#class MemExtractor(SimpleExtractor):
#    
#    """Show total mem usage on one axes."""
#    
#    ylabel = 'Bytes'
#    
#    def project_y(self, p):
#        return self.project_mem(p)
#
#
#class NormalizedExtractor(SimpleExtractor):
#    
#    """Base class for extractors that normalize (e.g. by subtraction
#    or division) the results for their series relative to a specific
#    series.
#    
#    Since normalization operates on the average value, error bar
#    output is not allowed.
#    """
#    
#    base_prog = None
#    base_series = None
#    
#    error_bars = False
#    
#    def normalize(self, pre_y, base_y):
#        """Return the normalized value of pre_y relative to base_y."""
#        raise NotImplementedError
#    
#    @property
#    def series_info(self):
#        return [e for e in super().series_info
#                  if not (e[0:2] == (self.base_prog, self.base_series))]
#    
#    def get_series_data(self, prog, series):
#        """Return the series data tuples for the specified parameters."""
#        points = self.select_prog_series(self.data, prog, series)
#        xy_data = [self.make_xy(p) for p in points]
#        pre_result = self.simple_avg(xy_data)
#        
#        base_points = self.select_prog_series(
#                        self.data, self.base_prog, self.base_series)
#        base_xy_data = [self.make_xy(p) for p in base_points]
#        base_avg_data = self.simple_avg(base_xy_data)
#        
#        result_xy = []
#        assert len(pre_result) == len(base_avg_data)
#        for (pre_x, pre_y), (base_x, base_y) in zip(pre_result, base_avg_data):
#            assert pre_x == base_x
#            result_y = self.normalize(pre_y, base_y)
#            result_xy.append((pre_x, result_y))
#        
#        return result_xy
