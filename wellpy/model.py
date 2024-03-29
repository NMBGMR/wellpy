# ===============================================================================
# Copyright 2016 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os
import time
from datetime import datetime
from itertools import groupby
from operator import itemgetter

from chaco.lasso_overlay import LassoOverlay
from chaco.plot_factory import add_default_axes, create_line_plot
from chaco.tools.broadcaster import BroadcasterTool
from chaco.tools.lasso_selection import LassoSelection
from numpy import array, diff, where, ones, logical_and, hstack, zeros_like, vstack, column_stack, asarray, savetxt, \
    ones_like, zeros, delete

from chaco.axis import PlotAxis
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from chaco.plot_containers import VPlotContainer
from chaco.tools.api import ZoomTool
from chaco.array_plot_data import ArrayPlotData
from chaco.plot import Plot
from chaco.tools.range_selection import RangeSelection
from chaco.tools.range_selection_overlay import RangeSelectionOverlay
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator

from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.file_dialog import FileDialog
from pyface.message_dialog import information, warning
from traits.api import HasTraits, Instance, Float, List, Property, Str, Button, Int, Any, Bool

from wellpy.axistool import AxisTool
from wellpy.data_model import DataModel
from wellpy.database_connector import DatabaseConnector, PointIDRecord
from wellpy.fuzzyfinder import fuzzyfinder
from wellpy.tools import DataTool, DataToolOverlay

from globals import DATABSE_DEBUG, FILE_DEBUG, QC_DEBUG, DEBUG

MARKER_SIZE = 4

DEPTH_TO_WATER_TITLE = 'Depth To Water (ft bgs)'
SENSOR_TITLE = 'Sensor BGS'
HEAD_TITLE = 'Head'
ADJUSTED_HEAD_TITLE = 'Adjusted Head'
MANUAL_WATER_DEPTH_TITLE = 'Manual Water BGS'

MANUAL_WATER_DEPTH_Y = 'manual_water_depth_y'
MANUAL_WATER_DEPTH_X = 'manual_water_depth_x'

ADJUSTED_WATER_HEAD_Y = 'adjusted_water_head_y'
ADJUSTED_WATER_HEAD_X = 'adjusted_water_head_x'

QC_ADJUSTED_WATER_HEAD_Y = 'qc_adjusted_water_head_y'
QC_ADJUSTED_WATER_HEAD_X = 'qc_adjusted_water_head_x'
QC_MANUAL_X = 'qc_manual_x'
QC_MANUAL_Y = 'qc_manual_y'

WATER_HEAD_Y = 'water_head_y'
WATER_HEAD_X = 'water_head_x'

DEPTH_SENSOR_Y = 'depth_sensor_y'
DEPTH_SENSOR_X = 'depth_sensor_x'

DEPTH_Y = 'depth_y'
DEPTH_X = 'depth_x'

HEAD_Y = 'head_y'

EXISTING_DEPTH_Y = 'existing_depth_y'
EXISTING_DEPTH_X = 'exisiting_depth_x'

QC_DEPTH_Y = 'qc_depth_y'
QC_DEPTH_X = 'qc_depth_x'

WATER_HEAD = 'water_head'
ADJ_WATER_HEAD = 'adjusted_water_head'
QC_ADJ_WATER_HEAD = 'qc_adjusted_water_head'
DEPTH_TO_SENSOR = 'depth_to_sensor'
DEPTH_TO_WATER = 'depth_to_water'
EXISTING_DEPTH_TO_WATER = 'exisiting_depth_to_water'
QC_DEPTH_TO_WATER = 'depth_to_water'
MANUAL_WATER_LEVEL = 'manual_water_level'


class NoSelectionError(BaseException):
    pass


class AutoResult(HasTraits):
    start = None
    end = None
    offset = Float

    def __init__(self, offset, sidx, eidx, s, e):
        self.offset = offset
        self.start = datetime.fromtimestamp(s)
        self.end = datetime.fromtimestamp(e)


class SaveSpec:
    point_id = None

    note = None
    data_source = None
    measuring_agency = None
    measurement_method = None


class Deviation(HasTraits):
    idx = Int
    time_s = Int
    manual = Float
    continuous = Float

    @property
    def deviation(self):
        return self.manual - self.continuous


class WellpyModel(HasTraits):
    plot_container = Instance(VPlotContainer)
    _tool = None
    _series = None
    _plots = None
    data_model = Instance(DataModel)

    point_id_entry = Str
    point_ids = List
    selected_point_id = Instance(PointIDRecord)
    filtered_point_ids = Property(depends_on='point_id_entry, viewer_point_ids')

    qc_point_ids = List
    selected_qc_point_id = Instance(PointIDRecord)
    selected_viewer_point_id = Instance(PointIDRecord)
    viewer_point_ids = List

    dclick_qc_point_id = Any

    path = Str
    filename = Property(depends_on='path')

    data_source = Str
    data_sources = List

    measurement_agency = Str
    measurement_agencies = List

    measurement_method = Str
    measurement_methods = List

    auto_results = List
    db = Instance(DatabaseConnector)

    scroll_to_row = Int

    deviations = List(Deviation)
    use_daily_mins = Bool(False)
    viewer_use_daily_mins = Bool(False)

    is_pressure = Property
    
    def activated(self):
        #if DATABSE_DEBUG:
        #    pids = ['A', 'B', 'C']
        #    self.point_ids = [PointIDRecord(p, '', '') for p in pids]
        #else:
        #    try:
        #    pids = self.db.get_point_ids()
        #    self.point_ids = pids
         #   except BaseException:
          #      pass
        #if self.point_ids:
        #    self.selected_point_id = self.point_ids[0]

        if DEBUG:
            if FILE_DEBUG:
                self.path = FILE_DEBUG
                if self.load_file(FILE_DEBUG):
                    self.fix_adj_head_data(0.25)
                    # self.calculate_depth_to_water()
                    # self.save_db()
            self.point_id_entry = os.environ.get('POINTID_DEBUG', 'SO-0227')

        self.load_qc()
        self.load_viewer()

    def undo(self):
        if self.data_model.is_acoustic:
            ys = self.data_model.raw_depth_to_water_y
            plot = self._plots[DEPTH_TO_WATER]
            plot.data.set_data('depth_y2', ys)
            self.data_model.depth_to_water_y = ys
            
            self.calculate_depth_to_water()
        else:
            self.unfix_adj_head_data()

    def apply_qc(self):
        self._apply_qc()

    def get_continuous(self, name, qced=0, is_acoustic=False):
        if self.data_model:
            is_acoustic = self.data_model.is_acoustic

        if is_acoustic:
            records = self.db.get_acoustic_water_levels(name, qced=qced)
        else:
            records = self.db.get_continuous_water_levels(name, qced=qced)

        if records:
            # records = sorted(records, key=lambda x: x[1])
            records = sorted(records, key=itemgetter(1))
            n = len(records)
            xs = zeros(n)
            
            if is_acoustic:
                ys = zeros(n)
                for i, ri in enumerate(records):
                    try:
                        xs[i]=ri[0]
                    except TypeError:
                        xs[i] = time.mktime(ri[0].timetuple())

                    ys[i]=ri[1]
                
                data = zip(xs, ys)
                data = sorted(data)
                xs, ys = zip(*data)
                return xs, ys
            else:
                if self.viewer_use_daily_mins:
                    xs, wts, hs, ahs, ds = [], [], [], [], []
                    # for day, records in groupby(records, key=itemgetter(1)):
                    for day, records in groupby(records, key=lambda x: x[1].date()):
                        records = list(records)
                        ri = records[0]
                        x = time.mktime(ri[1].timetuple())
                        xs.append(x)

                        wtss = [r[2] for r in records]
                        hss = [r[3] for r in records]
                        ahss = [r[4] for r in records]
                        dss = [r[5] for r in records]

                        ah = min(ahss)
                        idx = ahss.index(ah)

                        hs.append(hss[idx])
                        wts.append(wtss[idx])
                        ahs.append(ah)
                        ds.append(dss[idx])
                else:
                    
                    hs = zeros(n)
                    ahs = zeros(n)
                    ds = zeros(n)
                    wts = zeros(n)

                    for i, ri in enumerate(records):
                        x = time.mktime(ri[1].timetuple())
                        xs[i] = x
                        wts[i] = float(ri[2])
                        hs[i] = float(ri[3])
                        ahs[i] = float(ri[4])
                        ds[i] = float(ri[5])

                return xs, wts, hs, ahs, ds

    def _viewer_use_daily_mins_changed(self, new):
        self.load_viewer_data()

    def load_viewer_data(self):
        pid = self.selected_viewer_point_id
        if pid is None:
            return

        nqc_args = self.get_continuous(pid.name, qced=0)
        args = self.get_continuous(pid.name, qced=1)

        is_acoustic = self.data_model.is_acoustic
        if args or nqc_args:
            self.initialize_plot(qc=True)
            """
            PointID, Timestamp, 'temp', 'head', 'adjusted_head', 'depth_to_water'', note
            """
            plot = self._plots[DEPTH_TO_WATER]
            ocxs = []
            ohs = []
            if args:
                if is_acoustic:
                    xs, ys = args
                    plot.data.set_data(QC_DEPTH_X, xs)
                    plot.data.set_data(QC_DEPTH_Y, ys)
             
                else:
                    cxs, wts, hs, ahs, ds = args
                    plot.data.set_data(QC_DEPTH_X, cxs)
                    plot.data.set_data(QC_DEPTH_Y, ds)
                
                ocxs.extend(cxs)
                ohs.extend(hs)

            if nqc_args:
                if is_acoustic:
                    xs, ys = nqc_args
                    plot.data.set_data(DEPTH_X, cxs)
                    plot.data.set_data(DEPTH_Y, ys)
                else:
                    cxs, wts, hs, ahs, ds = nqc_args
                    plot.data.set_data(DEPTH_X, cxs)
                    plot.data.set_data(DEPTH_Y, ds)
                ocxs.extend(cxs)
                ohs.extend(hs)

            xs, ys, ss = self.get_manual_measurements(pid.name)

            plot.data.set_data(QC_MANUAL_X, xs)
            plot.data.set_data(QC_MANUAL_Y, ys)
            plot.plot((QC_MANUAL_X, QC_MANUAL_Y),
                      marker='circle', marker_size=2.5,
                      type='scatter', color='yellow')
            
            if is_acoustic:
                pass
            else:
                self._add_head(plot, ocxs, ohs)

            self._calculate_deviations(xs, ys, cxs, ds)
            self.refresh_plot()

    def load_qc_data(self):
        pid = self.selected_qc_point_id
        if pid is None:
            return

        args = self.get_continuous(pid.name, qced=0, is_acoustic=pid.is_acoustic)
        if args:
            self.initialize_plot(qc=True)

            """
            PointID, Timestamp, 'temp', 'head', 'adjusted_head', 'depth_to_water'', note
            """
            if pid.is_acoustic:
                cxs, ds = args
            else:
                cxs, wts, hs, ahs, ds = args
                # plot.plot((DEPTH_X, HEAD_Y), color='blue')
                
            self._qc_limits = min(cxs), max(cxs)
            
            plot = self._plots[DEPTH_TO_WATER]

            plot.data.set_data(DEPTH_X, cxs)
            plot.data.set_data(DEPTH_Y, ds)
            xs, ys, ss = self.get_manual_measurements(pid.name)

            if pid.is_acoustic:
                self._add_head(plot, cxs, hs)
                self._calculate_deviations(xs, ys, cxs, ds)

            plot.data.set_data(QC_MANUAL_X, xs)
            plot.data.set_data(QC_MANUAL_Y, ys)
            plot.plot((QC_MANUAL_X, QC_MANUAL_Y),
                    marker='circle', marker_size=2.5,
                    type='scatter', color='yellow')
            self.refresh_plot()
        else:
            information(None, 'No records required QC for this point id: "{}"'.format(self.selected_qc_point_id.name))

    def set_head_visibility(self, state):
        try:
            plot = self._plots['HEAD']
            plot.visible = state
            plot.request_redraw()
        except KeyError:
            pass

    def _add_head(self, plot, cxs, hs):
        foreign_plot = create_line_plot((cxs, hs), color='blue')
        left, bottom = add_default_axes(foreign_plot)
        left.orientation = "right"
        bottom.orientation = "top"

        foreign_plot.index_mapper = plot.index_mapper

        plot.add(foreign_plot)
        self._plots['HEAD'] = foreign_plot
        self._broadcast_zoom(plot, foreign_plot)

    def _broadcast_zoom(self, plot, foreign_plot):
        zoom = plot.plots['plot0'][0].overlays.pop(1)
        fz = ZoomTool(component=foreign_plot,
                      enable_wheel=True,
                      alpha=0.3,
                      axis='index',
                      always_on=False, tool_mode='range',
                      max_zoom_out_factor=1,
                      max_zoom_in_factor=10000)

        broadcaster = BroadcasterTool()
        broadcaster.tools.append(zoom)
        broadcaster.tools.append(fz)
        foreign_plot.overlays.append(fz)
        plot.tools.append(broadcaster)

    def _calculate_deviations(self, mxs, mys, cxs, cys):
        devs = []
        for midx, (mx, my) in enumerate(zip(mxs, mys)):
            idx = where(cxs - mx < 60)[0]
            if idx.size:
                idx = idx[-1]
                dev = Deviation(idx=midx, time_s=int(idx),
                                timestamp=datetime.fromtimestamp(mx).strftime('%m/%d/%Y'),
                                manual=my, continuous=cys[idx])
                devs.append(dev)

        self.deviations = devs

    def load_viewer(self):
        self.viewer_point_ids = self.db.get_point_ids_simple()
        
    def load_qc(self):
        self.qc_point_ids = self.db.get_qc_point_ids()

    def get_selection(self):
        pt = self._plots[MANUAL_WATER_LEVEL]
        scatterplot = pt.plots['plot1'][0]
        sel = scatterplot.index.metadata['selections']
        if sel:
            low, high = sel

            # for p in (lineplot, scatterplot):
            xs = scatterplot.index.get_data()

            mask = where(logical_and(xs >= low, xs <= high))[0]
            return mask

    def remove_selection(self):
        self.omit_selection(remove=True)

    def omit_selection(self, remove=False):
        pt = self._plots[MANUAL_WATER_LEVEL]
        scatterplot = pt.plots['plot1'][0]

        mask = self.get_selection()
        if mask is not None:
            xs = scatterplot.index.get_data()
            ys = scatterplot.value.get_data()
            scatterplot.index.set_data(delete(xs, mask))
            scatterplot.value.set_data(delete(ys, mask))
            scatterplot.index.metadata['selections'] = []

            if remove:
                x, y = self.data_model.manual_water_depth_x, self.data_model.manual_water_depth_y
                self.data_model.manual_water_depth_x = delete(x, mask)
                self.data_model.manual_water_depth_y = delete(y, mask)
            else:
                self.data_model.omissions.extend(mask)

            self.refresh_plot()

    def save_png(self):
        information(None, 'Save as png not enabled')
        # plot = self._plots[DEPTH_TO_WATER]
        # gc = PlotGraphicsContext((int(plot.outer_width), int(plot.outer_height)))
        # self._save_depth_to_water(gc, plot, '.tiff')

    def save_pdf(self):

        self._save_depth_to_water(self._plots[DEPTH_TO_WATER], '.pdf')

    def save_csv(self, p, delimiter=','):
        if self.selected_point_id:
            header, data, _ = self._gather_data(use_excel_format=True)
            if not p.endswith('.csv'):
                p = '{}.csv'.format(p)

            with open(p, 'w') as wfile:
                wfile.write('{}\n'.format(delimiter.join(('SerialNumber', self.selected_point_id.serial_num))))
                wfile.write('{}\n'.format(delimiter.join(('PointID', self.selected_point_id.name))))
                wfile.write('{}\n'.format(header))
                for row in data:
                    row = delimiter.join(map(str, row))
                    wfile.write('{}\n'.format(row))
            information(None, 'CSV file saved to "{}"'.format(p))

    def save_db(self):
        self._save_db()

    def retrieve_depth_to_water(self):
        """
        retrieve the depth to sensor measurements from database for selected_pointID
        :return:
        """

        pid = self.selected_point_id
        if pid is not None:
            # pid.name same as pointid
            self.plot_manual_measurements(pid.name)
            self.plot_existing_continuous(pid.name)

    def get_manual_measurements(self, name):
        ms = self.db.get_depth_to_water(name)

        xs, ys, ss = array(sorted([mi.measurement for mi in ms],
                                  # reverse=True,
                                  key=lambda x: x[0])).T
        xs = asarray(xs, dtype=float)
        # xs[0] = 0
        ys = asarray(ys, dtype=float)
        ss = asarray(ss, dtype=bool)
        return xs, ys, ss

    def plot_existing_continuous(self, name):
        args = self.get_continuous(name, qced=1)
        if args:
            if self.data_model.is_acoustic:
                xs, ds = args
            else:
                xs, wts, hs, ahs, ds = args

            plot = self._plots[DEPTH_TO_WATER]
            plot.data.set_data(QC_DEPTH_X, xs)
            plot.data.set_data(QC_DEPTH_Y, ds)

        nargs = self.get_continuous(name)
        if nargs:
            xs, wts, hs, ahs, ds = nargs

            plot = self._plots[DEPTH_TO_WATER]
            plot.data.set_data(EXISTING_DEPTH_X, xs)
            plot.data.set_data(EXISTING_DEPTH_Y, ds)

    def plot_manual_measurements(self, name):

        xs, ys, ss = self.get_manual_measurements(name)

        max_x = self.data_model.x[-1]
        idx = where(xs <= max_x)[0]
        try:
            mask = hstack((idx, idx[-1] + 1))
            xs = xs[mask]
        except IndexError:
            mask = idx
            xs = xs[mask]

        ys = ys[mask]
        ss = ss[mask]

        plot = self._plots[MANUAL_WATER_LEVEL]
        self.data_model.manual_water_depth_x = xs
        self.data_model.manual_water_depth_y = ys
        self.data_model.water_depth_status = ss

        for p in (plot, self._plots[DEPTH_TO_WATER]):
            p.data.set_data(MANUAL_WATER_DEPTH_X, xs)
            p.data.set_data(MANUAL_WATER_DEPTH_Y, ys)

        ss = where(asarray(ss, dtype=bool))[0]
        plot.default_index.metadata['selection'] = ss

        plot.title = self.selected_point_id.name

        self.refresh_plot()
    
    def snap(self):

        sel = self.get_selection()
        if sel is not None and len(sel):
            idx = sel[0]

            mxs = self.data_model.manual_water_depth_x
            mys = self.data_model.manual_water_depth_y
            if self.data_model.is_acoustic:
                ah = self.data_model.raw_depth_to_water_y
            else:
                ah = self.data_model.adjusted_water_head

            xs = self.data_model.x
            v = mys[idx]

            x = mxs[idx]
            l, h = x - (3600 * 12), x + (3600 * 12)
            mask = where(logical_and(xs >= l, xs < h))[0]
            if not len(mask):
                m = ah[0]
            else:
                m = ah[mask].mean()

            dev = m - ah
            #print(v, m)
            if self.data_model.is_acoustic:
                dev = -dev
            self.calculate_depth_to_water(value=v + dev)

    def offset_depth_to_water(self, offset):
        dtw = self.data_model.depth_to_water_y
        if not len(dtw):
            self.calculate_depth_to_water()

        dtw = self.data_model.depth_to_water_y
        plot = self._plots[DEPTH_TO_WATER]

        sel = plot.default_index.metadata['selection']
        if sel is not None and len(sel):
            dtw[sel] += offset
        else:
            dtw = dtw + offset
        self._set_dtw(dtw)
        self.refresh_plot()

    def calculate_depth_to_water(self, value=None, correct_drift=False, offset=None):
        """

        :return:
        """

        def calculated_dtw_bin(d1, d0, x, h):
            l1 = d1 + h[-1]
            l0 = d0 + h[0]

            l = l1 * ones(h.shape[0])
            if correct_drift:
                m = (l1 - l0) / (x[-1] - x[0])
                # l = [l1 - m * (t - x[0]) for t in x]
                l = l0 + m * (x - x[0])

            return l - h

        mxs = self.data_model.manual_water_depth_x
        mys = self.data_model.manual_water_depth_y
        mss = self.data_model.omissions
        ds = column_stack((delete(mxs, mss), delete(mys, mss)))
        xs = self.data_model.x
        if value is not None:
            dtw = value
        else:

            if self.data_model.is_acoustic:
                dtw = self.data_model.raw_depth_to_water_y
            else:
                ah = self.data_model.adjusted_water_head

                dtw = zeros_like(ah)
                for i in xrange(len(ds) - 1):
                    m0, m1 = ds[i], ds[i + 1]
                    mask = where(logical_and(xs >= m0[0], xs < m1[0]))[0]
                    if mask.any():
                        v = calculated_dtw_bin(m1[1], m0[1], xs[mask], ah[mask])
                        dtw[mask] = v

        plot = self._plots[DEPTH_TO_WATER]
        plot.data.set_data(DEPTH_X, xs)
        plot.data.set_data(DEPTH_Y, dtw)

        # plot.default_index.metadata['selection'] = mss

        self.data_model.depth_to_water_x = xs
        self.data_model.depth_to_water_y = dtw

        self.refresh_plot()

    def unfix_adj_head_data(self):
        ys = self.data_model.get_owater_head()
        self._plot_adj_head(ys)

    def fix_adj_head_data(self, threshold):
        """
        automatically remove offsets and zeros
        :param threshold:
        :return:
        """
        ys = self.data_model.get_water_head()
        ys, zs, fs = self.data_model.fix_data(ys, threshold, self._range_tool.selection)
        self.auto_results = [AutoResult(*fi) for fi in fs]
        self._plot_adj_head(ys)

    def fix_depth_to_water_data(self, threshold):
        ys = self.data_model.depth_to_water_y
        ys, _, _ = self.data_model.fix_data(ys, threshold, self._depth_to_water_range_tool.selection)
        self._set_dtw(ys)

    def match_timeseries(self):
        # ys = self.data_model.get_depth_to_water()
        plot = self._plots[DEPTH_TO_WATER]
        y = plot.data.get_data(DEPTH_Y)
        ey = plot.data.get_data(EXISTING_DEPTH_Y)

        dev = y[0] - ey[-1]
        ny = y - dev
        plot.data.set_data(DEPTH_Y, ny)
        self.data_model.depth_to_water_y = ny
        self.refresh_plot()

    def _plot_adj_head(self, ys):
        self.data_model.set_water_head(ys)
        # plot fixed ranges on raw plot
        # plot = self._plots[WATER_HEAD]
        # plot.auto_fixed_range_overlay.ranges = fs

        # update adjusted head
        self.data_model.adjusted_water_head = ys

        plot = self._plots[ADJ_WATER_HEAD]
        plot.data.set_data('adjusted_water_head_y', ys)
        plot.data.set_data('adjusted_water_head_y', ys)
        self.refresh_plot()

    def fix_upspikes(self, threshold):
        ys = self.data_model.depth_to_water_y
        if ys.any():
            ys = self.data_model.remove_up_spikes(ys, threshold, self._depth_to_water_range_tool.selection)
            #ys = self.data_model.smooth(ys, window, 'hanning', self._depth_to_water_range_tool.selection)
            self._set_dtw(ys)
        self.refresh_plot()

    def _set_dtw(self, ys):
        plot = self._plots[DEPTH_TO_WATER]
        plot_needed = 'depth_y2' not in plot.data.arrays
        plot.data.set_data('depth_y2', ys)
        # plot.data.set_data(DEPTH_Y, ys)
        if plot_needed:
            plot.plot((DEPTH_X, 'depth_y2'), color='purple')
        self.data_model.depth_to_water_y = ys

    def refresh_plot(self):
        self.plot_container.invalidate_and_redraw()

    def smooth_data(self, window, method):
        plot = self._plots[ADJ_WATER_HEAD]

        ys = self.data_model.adjusted_water_head
        sy = self.data_model.smooth(ys, window, method)
        plot_needed = 'sy' not in plot.data.arrays
        plot.data.set_data('sy', sy)
        if plot_needed:
            plot.plot(('x', 'sy'), color='green', line_width=1.5)

        self.refresh_plot()

    def load_file(self, p):
        """
        load data from a file.

        create a new DataModel object and initialize a plot
        :param p:
        :return:
        """
        self.selected_point_id = None
        try:
            data = DataModel(p)
        except ValueError, e:
            warning(None, '{}, is not a valid file.\n Exception={}'.format(p, e))
            return

        self.data_model = data
        self.initialize_plot()

        # get the point id
        pointid = data.pointid
        if pointid is None:
            warning(None, 'Could not extract Point ID from file. Trying Serial Number')
            serial_num = data.serial_number
            if not serial_num:
                warning(None, 'Could not extract Serial number from file')
            else:
                point_ids = [p for p in self.viewer_point_ids if p.serial_num == serial_num]
                if not point_ids:
                    information(None, 'Serial number="{}"  not in database'.format(serial_num))
                else:
                    self.selected_point_id = point_ids[-1]
        else:
            pointid = pointid.lower()
            self.selected_point_id = next((p for p in self.viewer_point_ids if p.name.lower() == pointid), None)

        if self.selected_point_id:
            self.scroll_to_row = self.viewer_point_ids.index(self.selected_point_id)

        self.retrieve_depth_to_water()
        if data.is_acoustic:
            self.calculate_depth_to_water()
        return True
        # else:
        #     warning(None, 'Could not automatically retrieve depth water. Please manually select a Point ID from the '
        #                   '"Site" pane')

    def initialize_plot(self, qc=False):
        self.plot_container = container = self._new_plotcontainer()
        self._plots = {}

        padding = [90, 50, 5, 5]

        if qc:
            funcs = ((DEPTH_TO_WATER, self._add_depth_to_water),)
            # (DEPTH_TO_SENSOR, self._add_depth_to_sensor),
            # (WATER_HEAD, self._add_water_head))
        else:
            if self.data_model.is_acoustic:
                funcs = ((DEPTH_TO_WATER, self._add_depth_to_water),
                         (MANUAL_WATER_LEVEL, self._add_manual_water_depth)
                         )
            else:
                funcs = ((DEPTH_TO_WATER, self._add_depth_to_water),
                         # (DEPTH_TO_SENSOR, self._add_depth_to_sensor),
                         (ADJ_WATER_HEAD, self._add_adjusted_water_head),
                         (MANUAL_WATER_LEVEL, self._add_manual_water_depth),)

        index_range = None
        n = len(funcs)
        for i, (k, f) in enumerate(funcs):
            plot = f(padding, qc)
            if i == 0:
                bottom_axis = PlotAxis(plot, orientation='bottom',  # mapper=xmapper,
                                       tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
                plot.padding_bottom = 50
                plot.x_axis = bottom_axis
                plot.x_axis.title_font = 'modern 14'
                plot.x_axis.tick_label_font = 'modern 14'
                plot.x_axis.title = 'Time'
                t = AxisTool(component=plot.x_axis)
                plot.tools.append(t)

            else:
                plot.resizable = 'h'
                plot.bounds = [1, 200]
                plot.index_range = index_range
                plot.x_axis.visible = False
                if i == n - 1:
                    plot.padding_top = 30

            index_range = plot.index_range
            container.add(plot)
            self._plots[k] = plot

        # if qc:
        #     plot = self._plots[DEPTH_TO_WATER]
        # plot.data.set_data(QC_DEPTH_X, [1, 2, 3])
        # plot.data.set_data(QC_DEPTH_Y, [10, 20, 30])
        # plot.plot((QC_DEPTH_X, QC_DEPTH_Y), linecolor='red')

        # plot = self._plots[QC_ADJ_WATER_HEAD]
        # plot.data.set_data(QC_ADJUSTED_WATER_HEAD_X, [1, 2, 3])
        # plot.data.set_data(QC_ADJUSTED_WATER_HEAD_Y, [30, 20, 10])
        # plot.plot((QC_ADJUSTED_WATER_HEAD_X, QC_ADJUSTED_WATER_HEAD_Y), linecolor='red')

        # plot = self._add_water_depth(padding)
        # plot.index_range = index_range
        # container.add(plot)
        #
        # plot = self._add_depth_to_water(padding)
        # plot.index_range = index_range
        # container.add(plot)
        #
        # plot = self._add_depth_to_sensor(padding)
        # plot.index_range = index_range
        # container.add(plot)

        self.refresh_plot()

    # private
    def _apply_qc(self):
        # _, data = self._gather_data(with_qc=True)

        pid = self.selected_qc_point_id
        if YES == confirm(None, 'Are you sure you want to save QC status for {} to the database?'.format(pid.name)):
            # pid = self.selected_point_id.name

            self.db.apply_qc(pid.name, pid.is_acoustic, self._qc_limits)
            information(None, 'QC status for {} saved to database'.format(pid.name))

    def _save_db(self, with_qc=False):
        _, data, is_acoustic = self._gather_data(with_qc=with_qc)
        if YES == confirm(None, 'Are you sure you want to save to the database?'):
            pid = self.selected_point_id.name
            with_update = True
            if confirm(None, 'Is this new data or an update? Yes=New, No=Update') == YES:
                with_update = False

            e, i = self.db.insert_continuous_water_levels(pid, data, with_update=with_update, is_acoustic=is_acoustic)
            information(None, 'There were {} existing records for {}. {} records inserted'.format(e, pid, i - e))

    def _save_path(self, ext):
        dlg = FileDialog(action='save as')
        if dlg.open():
            p = dlg.path
            if p:
                if not p.endswith(ext):
                    p = '{}{}'.format(p, ext)
                return p

    def _save_depth_to_water(self, plot, ext, **render):
        otop = None
        if self.selected_point_id:
            plot._title.text = self.selected_point_id.name
            plot._title.visible = True
            otop = plot.padding_top
            plot.padding_top = 30

        p = self._save_path(ext)
        if p:
            gc = PdfPlotGraphicsContext(filename=p)
            for lines in plot.plots.itervalues():
                for line in lines:
                    for o in line.overlays:
                        if isinstance(o, DataToolOverlay):
                            ovisible = o.visible
                            o.visible = False

            plot.invalidate_and_redraw()
            gc.render_component(plot, **render)
            gc.save()

            plot._title.visible = False

            if otop is not None:
                plot.padding_top = otop

            for lines in plot.plots.itervalues():
                for line in lines:
                    for o in line.overlays:
                        if isinstance(o, DataToolOverlay):
                            o.visible = ovisible

    def _gather_data(self, with_qc=False, use_isoformat=False, use_excel_format=False):
        model = self.data_model
        x = model.x
        depth_to_water = model.depth_to_water_y
        if model.is_acoustic:
            args = (x, model.temp_air, depth_to_water, model.raw_depth_to_water_y)
            keys = ('timestamp', 'temp_air', 'depth_to_water', 'raw_depth_to_water')
        else:
            ah = model.adjusted_water_head
            h = model.water_head
            water_temp = model.water_temp
            cond = model.cond

            if use_isoformat:
                x = [datetime.fromtimestamp(xi).isoformat() for xi in x]
            elif use_excel_format:
                x = [datetime.fromtimestamp(xi).strftime('%m/%d/%Y %H:%M') for xi in x]

            args = (x, h, ah, depth_to_water, water_temp, cond)
            keys = ('date/time', 'head (ft)', 'adjusted head (ft)', 'Depth to water (ft bgs)', 'water_temp (C)',
                    'cond (mS/cm)')
        if with_qc:
            args = args + (ones_like(x),)
            keys = keys + ('qc',)

        header = ','.join(keys)

        data = array(args).T
        return header, data, model.is_acoustic

    def _add_depth_to_water(self, padding, *args, **kw):
        pd = self._plot_data((DEPTH_X, []),
                             (DEPTH_Y, []))
        pd.set_data(MANUAL_WATER_DEPTH_X, [])
        pd.set_data(MANUAL_WATER_DEPTH_Y, [])
        pd.set_data(EXISTING_DEPTH_X, [])
        pd.set_data(EXISTING_DEPTH_Y, [])

        pd.set_data(QC_DEPTH_X, [])
        pd.set_data(QC_DEPTH_Y, [])

        plot = self._plot_factory(pd, padding=padding, origin='top left')
        plot.y_axis.title = DEPTH_TO_WATER_TITLE

        line = plot.plot((DEPTH_X, DEPTH_Y), color='green')[0]
        line2 = plot.plot((EXISTING_DEPTH_X, EXISTING_DEPTH_Y), color='red')[0]
        line3 = plot.plot((QC_DEPTH_X, QC_DEPTH_Y), color='black')[0]

        dt = DataTool(plot=line, component=plot, normalize_time=False, use_date_str=True)
        dto = DataToolOverlay(component=line, tool=dt)
        line.tools.append(dt)
        line.overlays.append(dto)

        z = ZoomTool(component=line,
                     enable_wheel=True,
                     alpha=0.3,
                     axis='index',
                     always_on=False, tool_mode='range',
                     max_zoom_out_factor=1,
                     max_zoom_in_factor=10000)

        line.overlays.append(z)

        tool = RangeSelection(line, left_button_selects=True)
        line.overlays.append(RangeSelectionOverlay(component=line))
        self._depth_to_water_range_tool = tool

        line.active_tool = tool = LassoSelection(component=line, selection_datasource=line.index)
        line.overlays.append(LassoOverlay(component=line, lasso_selection=tool))

        self._depth_to_water_rect_tool = tool
        # plot manual measurements
        plot.plot((MANUAL_WATER_DEPTH_X, MANUAL_WATER_DEPTH_Y),
                  marker='circle', marker_size=MARKER_SIZE,
                  type='scatter', color='yellow')
        return plot

    # def _add_depth_to_sensor(self, padding, *args, **kw):
    #     pd = self._plot_data((DEPTH_SENSOR_X, []),
    #                          (DEPTH_SENSOR_Y, []))
    #
    #     plot = Plot(data=pd, padding=padding, origin='top left')
    #     plot.y_axis.title = SENSOR_TITLE
    #
    #     plot.plot((DEPTH_SENSOR_X, DEPTH_SENSOR_Y))[0]
    #
    #     return plot

    # def _add_water_head(self, padding, *args, **kw):
    #
    #     data = self.data_model
    #     pd = self._plot_data((WATER_HEAD_X, data.x),
    #                          (WATER_HEAD_Y, data.water_head))
    #
    #     plot = Plot(data=pd, padding=padding)
    #     plot.y_axis.title = HEAD_TITLE
    #
    #     plot.plot((WATER_HEAD_X, WATER_HEAD_Y))[0]
    #     # plot.x_axis.visible = False
    #     # add overlays
    #     o = RangeOverlay(plot=plot)
    #     plot.auto_fixed_range_overlay = o
    #     plot.overlays.append(o)
    #     # self._plots[WATER_HEAD] = plot
    #     return plot

    def _add_adjusted_water_head(self, padding, *args, **kw):
        data = self.data_model
        if data:
            x = data.x
            y = data.adjusted_water_head
        else:
            x, y = [], []

        pd = self._plot_data((ADJUSTED_WATER_HEAD_X, x),
                             (ADJUSTED_WATER_HEAD_Y, y))

        plot = self._plot_factory(pd, padding=padding)

        plot.y_axis.title = ADJUSTED_HEAD_TITLE
        lineplot = plot.plot((ADJUSTED_WATER_HEAD_X, ADJUSTED_WATER_HEAD_Y))[0]

        lineplot.active_tool = tool = RangeSelection(lineplot, left_button_selects=True)
        lineplot.overlays.append(RangeSelectionOverlay(component=lineplot))

        self._range_tool = tool
        # self._plots[ADJ_WATER_HEAD] = plot
        return plot

    def _plot_factory(self, pd, *args, **kw):
        plot = Plot(data=pd, bgcolor='lightyellow', *args, **kw)

        plot.y_axis.title_font = 'modern 14'
        plot.y_axis.tick_label_font = 'modern 14'

        t = AxisTool(component=plot.y_axis)
        plot.tools.append(t)
        return plot

    def _add_manual_water_depth(self, padding, *args, **kw):
        if self.data_model:
            x = self.data_model.manual_water_depth_x
            y = self.data_model.manual_water_depth_y
        else:
            x, y = [], []

        # plot, line, scatter = self._add_line_scatter('', 'Manual BGS', padding, x=x)
        pd = self._plot_data((MANUAL_WATER_DEPTH_X, x),
                             (MANUAL_WATER_DEPTH_Y, y))
        plot = self._plot_factory(pd, padding=padding, origin='top left')

        plot.y_axis.title = MANUAL_WATER_DEPTH_TITLE
        plot.plot((MANUAL_WATER_DEPTH_X, MANUAL_WATER_DEPTH_Y))

        p = plot.plot((MANUAL_WATER_DEPTH_X, MANUAL_WATER_DEPTH_Y), type='scatter',
                      marker='circle', marker_size=MARKER_SIZE)[0]

        tool = RangeSelection(p, left_button_selects=True)
        p.tools.append(tool)
        p.overlays.append(RangeSelectionOverlay(component=p))

        return plot

    def _plot_data(self, x, y):
        pd = ArrayPlotData()
        pd.set_data(x[0], x[1])
        pd.set_data(y[0], y[1])
        return pd

    def _new_plotcontainer(self):
        pc = VPlotContainer()
        pc.bgcolor = 'lightblue'
        return pc

    def _use_daily_mins_changed(self, new):
        plot = self._plots[ADJ_WATER_HEAD]
        data =self.data_model
        x = data.x
        y = data.adjusted_water_head
        if new:
            records = zip(x,y)
            xs, ys = [], []
            ds = 24 * 3600
            for day, records in groupby(records, key=lambda x: int(x[0] / ds)):
                records = list(records)
                # ri = records[0]
                # x = time.mktime(ri[0].timetuple())
                vs = [r[1] for r in records]
                y = min(vs)
                idx = vs.index(y)
                x = [r[0] for r in records][idx]
                xs.append(x)
                ys.append(y)

        else:
            xs,ys = x, y

        plot.data.set_data(ADJUSTED_WATER_HEAD_X, xs)
        plot.data.set_data(ADJUSTED_WATER_HEAD_Y, ys)
        plot.invalidate_and_redraw()

    def _plot_container_default(self):
        pc = self._new_plotcontainer()
        return pc

    # property get/set
    def _get_is_pressure(self):
        return not self.data_model.is_acoustic
        
    def _get_filtered_point_ids(self):
        return fuzzyfinder(self.point_id_entry, self.viewer_point_ids, ('name', 'serial_num'))

    def _get_filename(self):
        return os.path.basename(self.path)
        # ============= EOF =============================================
        # def _add_line_scatter(self, key, title, padding, x=None):
        #     data = self.data_model
        #     pd = ArrayPlotData()
        #     xkey, ykey = 'x', 'y'
        #     if key:
        #         ykey = key
        #         # xkey = '{}_x'.format(key)
        #         # ykey = '{}_y'.format(key)
        #         # if x is None:
        #         # else:
        #         #     setattr(pd, xkey, getattr(data, xkey))
        #         pd.x = data.x
        #         setattr(pd, ykey, getattr(data, ykey))
        #
        #     plot = Plot(data=pd, padding=padding)
        #     plot.y_axis.title = title
        #     print xkey, xkey
        #
        #     line = plot.plot((xkey, ykey))[0]
        #     scatter = plot.plot((xkey, ykey), marker_size=1.5, type='scatter')
        #
        #     dt = DataTool(plot=line, component=plot, normalize_time=False, use_date_str=True)
        #     dto = DataToolOverlay(component=line, tool=dt)
        #     line.tools.append(dt)
        #     line.overlays.append(dto)
        #
        #     zoom = ZoomTool(plot,
        #                     # tool_mode="range",
        #                     axis='index',
        #                     color=(0, 1, 0, 0.5),
        #                     enable_wheel=False,
        #                     always_on=False)
        #     plot.overlays.append(zoom)
        #     return plot, line, scatter
