"""Result data extraction."""


__all__ = [
    'Extractor',
    'SimpleExtractor',
    'MetricExtractor',
    'TotalSizeExtractor',
#    'NormalizedExtractor',
]


import pickle
import math
from itertools import groupby
from operator import itemgetter

from .workflow import Task


def parse_style(style):
    """Parse a style string. The format is a space-separated list of
    tokens, in order
    
        <lineformat> <markerformat> <seriesformat>
    
    Valid values:
    
        lineformat: matplotlib line style
        
        markerformat: matplotlib marker style, optionally prefixed
          by '_' for hollow markers
        
        seriesformat: 'normal' for connect-the-dots, 'polyN' for
          polynomial fit of degree N, 'points' for point cloud
          with no lines 
    """
    lf, mf, series_format = style.split()
    
    if mf.startswith('_'):
        mf = mf[1:]
        hollow_markers = True
    else:
        hollow_markers = False
    
    style = lf + mf
    
    return style, hollow_markers, series_format


class Extractor(Task):
    
    """Abstract base class for extractors. Defines utility functions
    for retrieving and manipulating data points.
    """
    
    # Override to alter display characteristics.
    rcparams_file = None
    """Path to matplotlib rc file."""
    rcparams = None
    """Dictionary of key/value overrides to apply on top
    of rc file.
    """
    
    figsize = None
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    max_xitvls = None
    max_yitvls = None
    x_ticklocs = None
    y_ticklocs = None
    legend_ncol = None
    
    @property
    def config(self):
        return {key: getattr(self, key)
                for key in ['figsize',
                            'xmin', 'xmax', 'ymin', 'ymax',
                            'max_xitvls', 'max_yitvls',
                            'x_ticklocs', 'y_ticklocs']}
    
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
    
    title = None
    ylabel = None
    xlabel = None
    
    logx = False
    logy = False
    
    scalarx = False
    scalary = False
    
    error_bars = False
    discard_ratio = 0.0
    
    series = []
    """List of (series name, display name, color, style),
    in order of display.
    """
    
    # x and y can be scaled in a derived class by overriding
    # project_x() and project_y().
    
    def project_x(self, p):
        """Grab x value from datapoint."""
        return p['dsparams']['x']
    
    def project_y(self, p):
        """Grab y value from datapoint."""
        raise NotImplementedError
    
    def get_series_data(self, datapoints, sid):
        """Given datapoints and a series id, return a list of
        datapoints in that series.
        """
        raise NotImplementedError
    
    def project_data(self, datapoints):
        """Given datapoints, apply the projection function to get
        (x, y) coordinates.
        """
        return [(self.project_x(p), self.project_y(p))
                for p in datapoints]
    
    def project_and_average_data(self, datapoints, average):
        """Given datapoints, project and optionally average."""
        xy = self.project_data(datapoints)
        if average:
            points = self.average_points(xy, self.discard_ratio)
        else:
            points = [(x, y, 0, 0) for (x, y) in xy]
        return points
    
    def get_series_points(self, datapoints, sid, *,
                          average):
        """Given datapoints and a series id, return a list of
        (x, y) points with error data.
        """
        data = self.get_series_data(datapoints, sid)
        points = self.project_and_average_data(data, average=average)
        return points
    
    def get_series(self):
        results = []
        for sid, dispname, color, style in self.series:
            style, hollow_markers, series_format = parse_style(style)
            data = self.get_series_points(self.data, sid,
                                          average=(series_format != 'points'))
            results.append(dict(
                name = dispname,
                style = style,
                color = color,
                errorbars = self.error_bars,
                format = series_format,
                hollow_markers = hollow_markers,
                data = data,
            ))
        return results
    
    def get_plotdata(self):
        return dict(
            plot_title = self.title if self.title is not None
                         else '',
            axes = [dict(
                axes_title = None,
                ylabel = self.ylabel,
                xlabel = self.xlabel,
                logx = self.logx,
                logy = self.logy,
                scalarx = self.scalarx,
                scalary = self.scalary,
                legend_ncol = self.legend_ncol,
                series = self.get_series(),
            )],
            rcparams_file = self.rcparams_file,
            rcparams = self.rcparams,
            config = self.config,
        )
    
    def run(self):
        with open(self.workflow.data_filename, 'rb') as in_file:
            self.data = pickle.load(in_file)
        
        plotdata = self.get_plotdata()
        
        with open(self.workflow.plotdata_filename, 'wb') as out_file:
            pickle.dump(plotdata, out_file)
        
        self.print('Done.')
    
    def cleanup(self):
        self.remove_file(self.workflow.plotdata_filename)


class SimpleExtractor(Extractor):
    
    """Scaffolding for an extractor that grabs each datapoint of
    a prog series.
    """
    
    # Series ids are just prog names.
    
    def get_series_data(self, datapoints, sid):
        # Pick out the points for this prog.
        data = [p for p in datapoints if p['prog'] == sid]
        return data


class MetricExtractor(SimpleExtractor):
    
    """Extractor that shows each prog's results for a particular
    metric.
    """
    
    metric = None
    """Metric to plot, e.g. 'time_cpu'."""
    
    def project_y(self, p):
        """Grab y value from datapoint. Can be overridden e.g.
        for scaling.
        """
        return p['results'][self.metric]


class TotalSizeExtractor(SimpleExtractor):
    
    """Show total auxiliary structure size."""
    
    ylabel = '# aux. space'
    
    def project_y(self, p):
        return p['results']['size']



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
