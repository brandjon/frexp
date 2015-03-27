"""Result data extraction."""


__all__ = [
    'Extractor',
    'SimpleExtractor',
    'MetricExtractor',
    'TotalSizeExtractor',
    'NormalizedExtractor',
    'ScaledExtractor',
]


import pickle
import math
from itertools import groupby
from operator import itemgetter
import csv

from .workflow import Task


def parse_style(style):
    """Parse a style string. The format is a space-separated list of
    tokens, in order
    
        <lineformat> <markerformat> <seriesformat>
    
    Valid values:
    
        lineformat: matplotlib line style, or dash sequence as
          list of "-"-separated integers
        
        markerformat: matplotlib marker style, optionally prefixed
          by '_' for hollow markers
        
        seriesformat: 'normal' for connect-the-dots, 'polyN' for
          polynomial fit of degree N, 'points' for point cloud
          with no lines
    """
    lf, mf, series_format = style.split()
    
    parts = lf.split('-')
    if all(p.isdigit() for p in parts):
        # Dash sequence
        lf = ''
        dashes = [int(p) for p in parts]
    else:
        dashes = None
    
    if mf.startswith('_'):
        mf = mf[1:]
        hollow_markers = True
    else:
        hollow_markers = False
    if mf.startswith('!'):
        mf =  mf[1:]
        marker_border = True
    else:
        marker_border = False
    
    style = lf + mf
    
    return lf, mf, hollow_markers, marker_border, series_format, dashes


class Extractor(Task):
    
    """Abstract base class for extractors. Defines utility functions
    for retrieving and manipulating data points.
    """
    
    generate_csv = True
    
    # Override to alter display characteristics.
    rcparams_file = None
    """Path to matplotlib rc file."""
    rcparams = None
    """Dictionary of key/value overrides to apply on top
    of rc file.
    """
    
    figsize = None
    dpi = None
    xmin = None
    xmax = None
    ymin = None
    ymax = None
    max_xitvls = None
    max_yitvls = None
    x_ticklocs = None
    y_ticklocs = None
    tightlayout_bbox = None
    no_legend = False
    legend_ncol = None
    legend_loc = 'upper left'
    legend_bbox = None
    xlabelpad = None
    ylabelpad = None
    
    @property
    def config(self):
        return {key: getattr(self, key)
                for key in ['figsize', 'dpi',
                            'xmin', 'xmax', 'ymin', 'ymax',
                            'max_xitvls', 'max_yitvls',
                            'x_ticklocs', 'y_ticklocs',
                            'tightlayout_bbox']}
    
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
    
    def get_dispname(self, sid, dispname):
        """Hook for changing the display name of a series."""
        return dispname
    
    def scale_data(self, sid, data):
        """Hook for scaling data."""
        return data
    
    def get_series(self):
        results = []
        for sid, dispname, color, style in self.series:
            (linestyle, markerstyle, hollow_markers, marker_border,
                series_format, dashes) = parse_style(style)
            data = self.get_series_points(self.data, sid,
                                          average=(series_format != 'points'))
            dispname = self.get_dispname(sid, dispname)
            data = self.scale_data(sid, data)
            results.append(dict(
                name = dispname,
                linestyle = linestyle,
                markerstyle = markerstyle,
                color = color,
                errorbars = self.error_bars,
                format = series_format,
                hollow_markers = hollow_markers,
                marker_border = marker_border,
                dashes = dashes,
                data = data,
            ))
        return results
    
    def get_plotdata(self):
        return dict(
            plot_title = None,
            axes = [dict(
                axes_title = self.title,
                ylabel = self.ylabel,
                xlabel = self.xlabel,
                logx = self.logx,
                logy = self.logy,
                scalarx = self.scalarx,
                scalary = self.scalary,
                no_legend = self.no_legend,
                legend_ncol = self.legend_ncol,
                legend_loc = self.legend_loc,
                legend_bbox = self.legend_bbox,
                ylabelpad = self.ylabelpad,
                xlabelpad = self.xlabelpad,
                series = self.get_series(),
            )],
            rcparams_file = self.rcparams_file,
            rcparams = self.rcparams,
            config = self.config,
        )
    
    def get_csvdata(self, axes):
        header = ['x']
        all_x = set()
        data = {}
        for s in axes['series']:
            if len(s['data']) == 0:
                continue
            series_name = s['name']
            header.append(series_name)
            series_data = data.setdefault(series_name, {})
            for (x, y, _, _) in s['data']:
                assert x not in series_data
                series_data[x] = y
                all_x.add(x)
        
        csvdata = []
        for x in sorted(all_x):
            row = {'x': x}
            row.update((series_name, series_data.get(x, None))
                       for series_name, series_data in data.items())
            csvdata.append(row)
        
        return header, csvdata
    
    def run(self):
        with open(self.workflow.data_filename, 'rb') as in_file:
            self.data = pickle.load(in_file)
        
        plotdata = self.get_plotdata()
        
        with open(self.workflow.plotdata_filename, 'wb') as out_file:
            pickle.dump(plotdata, out_file)
        
        if self.generate_csv:
            assert len(plotdata['axes']) == 1
            header, csvdata = self.get_csvdata(plotdata['axes'][0])
            
            with open(self.workflow.csv_filename, 'wt', newline='') \
                    as out_csv_file:
                wr = csv.DictWriter(out_csv_file, header)
                wr.writeheader()
                wr.writerows(csvdata)
        
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


class NormalizedExtractor(SimpleExtractor):
    
    """Base class for extractors that normalize (e.g. by subtraction
    or division) the results for their series relative to a specific
    series.
    
    Since normalization operates on the average value, error bar
    output is not allowed.
    """
    
    # Map from sid to base sid used to normalize it.
    # sids not in the map are not displayed.
    base_sid_map = None
    # Alternatively, set base_sid to a single sid used
    # to normalize all other sids.
    base_sid = None
    
    error_bars = False
    
    def normalize(self, pre_y, base_y):
        """Return the normalized value of pre_y relative to base_y."""
        raise NotImplementedError
    
    def get_series_points(self, datapoints, sid, *,
                          average):
        """Given datapoints and a series id, return a list of
        (x, y) points with error data.
        """
        
        # Only use one or the other.
        assert not (self.base_sid_map is not None and
                    self.base_sid is not None)
        
        if self.base_sid_map is not None:
            base_sid = self.base_sid_map.get(sid, None)
            if base_sid is None:
                return []
        elif self.base_sid is not None:
            base_sid = self.base_sid
            if sid == base_sid:
                return []
        else:
            assert()
        
        base_points = super().get_series_points(datapoints, base_sid,
                                                average=True)
        sid_points = super().get_series_points(datapoints, sid,
                                               average=True)
        
        points = []
        for (x, y, _, _), (base_x, base_y, _, _) in \
                zip(sid_points, base_points):
            assert x == base_x
            adjusted_y = self.normalize(y, base_y)
            points.append((x, adjusted_y, 0, 0))
        return points


class ScaledExtractor(Extractor):
    
    """Base class for extractors that scale a series by a multiplier."""
    
    multipliers = None
    """Dictionary from sid to multiplier to use."""
    
    # Characters to use for displaying a multiplier greater than
    # or less than 1, respectively. Overriding timesop is useful
    # when using LaTeX.
    timesop = 'x'
    divop = '/'
    
    def get_dispname(self, sid, dispname):
        dispname = super().get_dispname(sid, dispname)
        mult = self.multipliers.get(sid, None)
        if mult is not None:
            # Add the multiplier to the series name.
            if mult >= 1:
                op = ' ' + self.timesop + ' '
            else:
                op = ' ' + self.divop + ' '
                mult = 1 / mult
            # Round off multiplier to 3 decimal places, or
            # to integer if it appears to represent one.
            if round(mult, 3) == round(mult):
                mult = round(mult)
            else:
                mult = round(mult, 3)
            dispname += op + str(mult)
        return dispname
    
    def scale_data(self, sid, data):
        data = super().scale_data(sid, data)
        mult = self.multipliers.get(sid, None)
        if mult is not None:
            data = [(x, y * mult, lo * mult, hi * mult)
                    for (x, y, lo, hi) in data]
        return data
