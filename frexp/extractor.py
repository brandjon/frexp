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


class Extractor(Task):
    
    """Abstract base class for extractors. Defines utility functions
    for retrieving and manipulating data points.
    """
    
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
    
    def select_prog_series(self, points, prog, series):
        return [p for p in points
                  if p['prog'] == prog
                  if series is None or p['dsparams']['series'] == series]
    
    def project_x(self, p):
        return p['dsparams']['x']
    
    def project_seq_metric(self, p, seq, metric):
        return p['results']['seqs'][seq][metric]
    
    def project_totalsize(self, p):
        return sum(p['results']['sizes'].values())
    
    def project_mem(self, p):
        return p['results']['memory']
    
    def getter_x(self):
        def getter(p):
            return p['dsparams']['x']
        return getter
    
    def getter_seq_metric(self, seq, metric):
        def getter(p):
            return p['results']['seqs'][seq][metric]
        return getter
    
    def getter_memory(self):
        def getter(p):
            return p['results']['memory']
        return getter
    
    def getter_size(self, objname):
        def getter(p):
            return p['results']['sizes'][objname]
        return getter
    
    def getter_totalsize(self):
        def getter(p):
            return sum(p['results']['sizes'].values())
        return getter
    
    def average_data(self, xy_data, discard_ratio, error_bars):
        """Given a list of (x, y) data, return a list of
        
            (x, avg y, y low delta, y high delta)
        
        quadruples. All the y values for a common x are grouped
        together. Then the high and low percentile y values are
        discarded and the remaining values are averaged together
        to find avg y. The low and high deltas are the positive
        differences between this average and the min and max y
        values not thrown out, respectively.
        """
        xy_data = list(xy_data)
        xy_data.sort(key=itemgetter(0))
        
        xy_err_data = []
        for x, grouped in groupby(xy_data, key=itemgetter(0)):
            yvals = sorted(p[1] for p in grouped)
            
            # Compute average including outliers.
            avg_y = sum(yvals) / len(yvals)
            
            # Exclude outliers from error bars.
            discard_width = math.floor(len(yvals) * discard_ratio)
            if discard_width > 0:
                yvals = yvals[discard_width : -discard_width]
            
            min_y = min(yvals)
            max_y = max(yvals)
            xy_err_data.append((x, avg_y, avg_y - min_y, max_y - avg_y))
        
        if error_bars:
            result = xy_err_data
        else:
            result = [(p[0], p[1]) for p in xy_err_data]
        
        return result
    
    def get_plotdata(self):
        raise NotImplementedError
    
    def run(self):
        with open(self.workflow.data_filename, 'rb') as in_file:
            self.data = pickle.load(in_file)
        
        plotdata = self.get_plotdata()
        
        with open(self.workflow.plotdata_filename, 'wb') as out_file:
            pickle.dump(plotdata, out_file)
        
        self.print('Done.')


class AveragerMixin:
    
    # Outer percentile of high and low values to throw out.
    discard_ratio = 0.0
    # If True, show error bars for highest and lowest values not
    # thrown out.
    error_bars = False
    # If True, plot multiple trials as distinct points instead
    # of their average value.
    all_points = False
    
    def simple_avg(self, xy_data):
        if self.all_points:
            return xy_data
        else:
            return self.average_data(xy_data, self.discard_ratio,
                                     self.error_bars)


class SimpleExtractor(Extractor, AveragerMixin):
    
    """Base class for extractors that compare several progs/series on
    a single axes.
    """
    
    # Plot labeling.
    title = None
    ylabel = None
    xlabel = None
    
    # List of all possible displayable series.
    @property
    def series_list(self):
        return []
    
    @property
    def series_names(self):
        """Names of series to actually show. Override in subclass."""
        return [tup[0] for tup in self.series_list] 
    
    # Name replacements, if any. Override in subclass.
    name_map = {}
    
    @property
    def series_info(self):
        """List of (prog, series, label, color, style) tuples."""
        entries = [tup for tup in self.series_list
                       if tup[0] in self.series_names]
        entries = [(prog, series, self.name_map.get(prog, name), color, style)
                   for prog, series, name, color, style in entries]
        return entries
    
    def make_xy(self, p):
        return (self.project_x(p), self.project_y(p))
    
    def project_y(self, p):
        """Implement in subclass to control what data from the point
        is projected out as the y-value.
        """
        raise NotImplementedError
    
    def get_series_data(self, prog, series):
        """Return the series data tuples for the specified parameters."""
        points = self.select_prog_series(self.data, prog, series)
        xy_data = [self.make_xy(p) for p in points]
        result = self.simple_avg(xy_data)
        return result
    
    def make_series(self, name, color, style, prog, series):
        return dict(
            name = name,
            style = style,
            color = color,
            errorbars = self.error_bars,
            data = self.get_series_data(prog, series)
        )
    
    def get_plotdata(self):
        return dict(
            plot_title = self.title if self.title is not None
                         else '',
            axes = [dict(
                axes_title = None,
                ylabel = self.ylabel,
                xlabel = self.xlabel,
                logscale = False,
                series = [self.make_series(label, color, style, prog, series)
                          for prog, series, label, color, style in self.series_info],
            )],
            config = self.config,
        )


class SeqExtractor(SimpleExtractor):
    
    """Show seq/metric data on one axes."""
    
    # seq/metric info to display.
    seq = None
    metric = None
    
    def project_y(self, p):
        return self.project_seq_metric(p, self.seq, self.metric)


class TotalSizeExtractor(SimpleExtractor):
    
    """Show total structure size on one axes."""
    
    ylabel = '# aux. entries'
    
    def project_y(self, p):
        return self.project_totalsize(p)


class MemExtractor(SimpleExtractor):
    
    """Show total mem usage on one axes."""
    
    ylabel = 'Bytes'
    
    def project_y(self, p):
        return self.project_mem(p)


class NormalizedExtractor(SimpleExtractor):
    
    """Base class for extractors that normalize (e.g. by subtraction
    or division) the results for their series relative to a specific
    series.
    
    Since normalization operates on the average value, error bar
    output is not allowed.
    """
    
    base_prog = None
    base_series = None
    
    error_bars = False
    
    def normalize(self, pre_y, base_y):
        """Return the normalized value of pre_y relative to base_y."""
        raise NotImplementedError
    
    @property
    def series_info(self):
        return [e for e in super().series_info
                  if not (e[0:2] == (self.base_prog, self.base_series))]
    
    def get_series_data(self, prog, series):
        """Return the series data tuples for the specified parameters."""
        points = self.select_prog_series(self.data, prog, series)
        xy_data = [self.make_xy(p) for p in points]
        pre_result = self.simple_avg(xy_data)
        
        base_points = self.select_prog_series(
                        self.data, self.base_prog, self.base_series)
        base_xy_data = [self.make_xy(p) for p in base_points]
        base_avg_data = self.simple_avg(base_xy_data)
        
        result_xy = []
        assert len(pre_result) == len(base_avg_data)
        for (pre_x, pre_y), (base_x, base_y) in zip(pre_result, base_avg_data):
            assert pre_x == base_x
            result_y = self.normalize(pre_y, base_y)
            result_xy.append((pre_x, result_y))
        
        return result_xy


class SizeBreakdownExtractor(Extractor, AveragerMixin):
    
    """Extractor that shows all the set sizes for the given
    progs/series, each in a different axes.
    """
    
    # List of (prog, series) tuples.
    progseries = None
    
    xlabel = None
    
    def getter_xy(self, objname):
        def getter(p):
            return (self.getter_x()(p), self.getter_size(objname)(p))
        return getter
    
    def make_series(self, prog, series):
        def randcolor():
            return (random.random(), random.random(), random.random())
        
        # Assumption: All datapoints for a given prog/series have size
        # data available for the exact same set of object names.
        points = self.select_prog_series(self.data, prog, series)
        if len(points) == 0:
            return []
        
        objnames = sorted(points[0]['results']['sizes'].keys())
        series_list = []
        for n in objnames:
            obj_points = [self.getter_xy(n)(p) for p in points]
            xy_points = self.simple_avg(obj_points)
            
            series_list.append(dict(
                # If the label name were allowed to start with an
                # underscore (as many of the names of objects
                # introduced by our transformation do), it would be
                # omitted from the legend.
                name = n.lstrip('_'),
                style = '-o',
                color = randcolor(),
                errorbars = self.error_bars,
                data = xy_points,
            ))
        
        return series_list
    
    def get_plotdata(self):
        return dict(
            plot_title = 'Structure sizes',
            axes = [
                dict(
                    axes_title = prog,
                    ylabel = 'Size',
                    xlabel = self.xlabel,
                    logscale = False,
                    series = self.make_series(prog, series),
                )
                for prog, series in self.progseries
            ],
            config = self.config,
        )
