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
from traits.api import HasTraits, Instance, Float, List, Property, Str, Button, Int, Any

from wellpy.data_model import DataModel
from wellpy.database_connector import DatabaseConnector, PointIDRecord
from wellpy.fuzzyfinder import fuzzyfinder
from wellpy.tools import DataTool, DataToolOverlay

from globals import DATABSE_DEBUG, FILE_DEBUG, QC_DEBUG, DEBUG

MARKER_SIZE = 4

DEPTH_TO_WATER_TITLE = 'Depth To Water'
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

QC_DEPTH_Y = 'depth_y'
QC_DEPTH_X = 'depth_x'

WATER_HEAD = 'water_head'
ADJ_WATER_HEAD = 'adjusted_water_head'
QC_ADJ_WATER_HEAD = 'qc_adjusted_water_head'
DEPTH_TO_SENSOR = 'depth_to_sensor'
DEPTH_TO_WATER = 'depth_to_water'
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


class WellpyModel(HasTraits):
    plot_container = Instance(VPlotContainer)
    _tool = None
    _series = None
    _plots = None
    data_model = Instance(DataModel)

    point_id_entry = Str
    point_ids = List
    selected_point_id = Instance(PointIDRecord)
    filtered_point_ids = Property(depends_on='point_id_entry')

    qc_point_ids = List
    selected_qc_point_id = Instance(PointIDRecord)
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

    def activated(self):
        if DATABSE_DEBUG:
            pids = ['A', 'B', 'C']
            self.point_ids = [PointIDRecord(p, '', '') for p in pids]
        else:
            try:
                pids = self.db.get_point_ids()
                self.point_ids = pids
            except BaseException:
                pass

        if self.point_ids:
            self.selected_point_id = self.point_ids[0]

        if FILE_DEBUG:
            self.path = FILE_DEBUG
            if self.load_file(FILE_DEBUG):
                self.fix_adj_head_data(0.25)
                # self.calculate_depth_to_water()
                # self.save_db()

        if DEBUG:
            self.point_id_entry = 'TC-316'

        self.load_qc()

    def apply_qc(self):
        self._save_db(with_qc=True)

    def load_qc_data(self):
        pid = self.selected_qc_point_id
        if pid is None:
            return

        records = self.db.get_continuous_water_levels(pid.name, qced=0)
        if records:
            self.initialize_plot(qc=True)

            """
            PointID, Timestamp, 'temp', 'head', 'adjusted_head', 'depth_to_water'', note
            """
            n = len(records)

            xs = zeros(n)
            hs = zeros(n)
            ahs = zeros(n)
            ds = zeros(n)
            wts = zeros(n)
            for i, ri in enumerate(sorted(records, key=lambda x: x[1])):
                x = time.mktime(ri[1].timetuple())
                xs[i] = x
                wts[i] = float(ri[2])
                hs[i] = float(ri[3])
                ahs[i] = float(ri[4])
                ds[i] = float(ri[5])

            plot = self._plots[DEPTH_TO_WATER]
            plot.data.set_data(DEPTH_X, xs)
            plot.data.set_data(DEPTH_Y, ds)

            xs, ys, ss = self.get_manual_measurements(pid.name)

            plot.data.set_data(QC_MANUAL_X, xs)
            plot.data.set_data(QC_MANUAL_Y, ys)
            plot.plot((QC_MANUAL_X, QC_MANUAL_Y),
                      marker='circle', marker_size=2.5,
                      type='scatter', color='yellow')

            self.refresh_plot()
        else:
            information(None, 'No records required QC for this point id: "{}"'.format(self.selected_qc_point_id.name))

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

    def omit_selection(self):
        pt = self._plots[MANUAL_WATER_LEVEL]
        scatterplot = pt.plots['plot1'][0]

        mask = self.get_selection()
        if mask is not None:
            xs = scatterplot.index.get_data()
            ys = scatterplot.value.get_data()
            scatterplot.index.set_data(delete(xs, mask))
            scatterplot.value.set_data(delete(ys, mask))
            scatterplot.index.metadata['selections'] = []

            # x, y = self.data_model.manual_water_depth_x, self.data_model.manual_water_depth_y
            # self.data_model.manual_water_depth_x = delete(x, mask)
            # self.data_model.manual_water_depth_y = delete(y, mask)

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
            keys, data = self._gather_data(use_isoformat=True)
            header = ','.join(keys)
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
            self.plot_manual_measurements(pid.name)

    def get_manual_measurements(self, name):
        ms = self.db.get_depth_to_water(name)

        xs, ys, ss = array(sorted([mi.measurement for mi in ms],
                                  # reverse=True,
                                  key=lambda x: x[0])).T
        xs = asarray(xs, dtype=float)
        ys = asarray(ys, dtype=float)
        ss = asarray(ss, dtype=bool)
        return xs, ys, ss

    def plot_manual_measurements(self, name):

        xs, ys, ss = self.get_manual_measurements(name)

        max_x = self.data_model.x[-1]
        idx = where(xs <= max_x)[0]
        idx = hstack((idx, idx[-1] + 1))

        xs = xs[idx]
        ys = ys[idx]
        ss = ss[idx]

        plot = self._plots[MANUAL_WATER_LEVEL]
        self.data_model.manual_water_depth_x = xs
        self.data_model.manual_water_depth_y = ys
        self.data_model.water_depth_status = ss

        plot.data.set_data(MANUAL_WATER_DEPTH_X, xs)
        plot.data.set_data(MANUAL_WATER_DEPTH_Y, ys)

        ss = where(asarray(ss, dtype=bool))[0]
        plot.default_index.metadata['selection'] = ss

        self.refresh_plot()

    def snap(self):

        sel = self.get_selection()
        if sel:
            idx = sel[0]

            mxs = self.data_model.manual_water_depth_x
            mys = self.data_model.manual_water_depth_y
            ah = self.data_model.adjusted_water_head

            xs = self.data_model.x
            v = mys[idx]

            x = mxs[idx]
            l, h = x - (3600 * 12), x + (3600 * 12)
            mask = where(logical_and(xs >= l, xs < h))[0]
            dev = ah[mask].mean()-ah

            self.calculate_depth_to_water(value=v+dev)

    def calculate_depth_to_water(self, value=None, correct_drift=False):
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

            dtw = l - h
            return dtw

        ah = self.data_model.adjusted_water_head
        xs = self.data_model.x

        mxs = self.data_model.manual_water_depth_x
        mys = self.data_model.manual_water_depth_y

        mss = self.data_model.omissions

        ds = column_stack((delete(mxs, mss), delete(mys, mss)))

        if value is not None:
            dtw = value
        else:
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

        plot.data.set_data(MANUAL_WATER_DEPTH_X, mxs)
        plot.data.set_data(MANUAL_WATER_DEPTH_Y, mys)
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

    def _plot_adj_head(self, ys):
        self.data_model.set_water_head(ys)
        # plot fixed ranges on raw plot
        # plot = self._plots[WATER_HEAD]
        # plot.auto_fixed_range_overlay.ranges = fs

        # update adjusted head
        self.data_model.adjusted_water_head = ys

        plot = self._plots[ADJ_WATER_HEAD]
        plot.data.set_data('adjusted_water_head_y', ys)
        self.refresh_plot()

    def fix_depth_to_water_data(self, threshold):
        ys = self.data_model.depth_to_water_y
        if ys.any():
            ys, zs, fs = self.data_model.fix_data(ys, threshold)
            plot = self._plots[DEPTH_TO_WATER]
            plot_needed = 'sy' not in plot.data.arrays
            plot.data.set_data('depth_y2', ys)
            # plot.data.set_data(DEPTH_Y, ys)
            if plot_needed:
                plot.plot((DEPTH_X, 'depth_y2'), color='green')

        self.refresh_plot()

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
                point_ids = [p for p in self.point_ids if p.serial_num == serial_num]
                if not point_ids:
                    information(None, 'Serial number="{}"  not in database'.format(serial_num))
                else:
                    self.selected_point_id = point_ids[-1]
        else:
            self.selected_point_id = next((p for p in self.point_ids if p.name == pointid), None)

        if self.selected_point_id:
            self.scroll_to_row = self.point_ids.index(self.selected_point_id)

        self.retrieve_depth_to_water()
        return True
        # else:
        #     warning(None, 'Could not automatically retrieve depth water. Please manually select a Point ID from the '
        #                   '"Site" pane')

    def initialize_plot(self, qc=False):
        self.plot_container = container = self._new_plotcontainer()
        self._plots = {}

        padding = [70, 10, 5, 5]

        if qc:
            funcs = ((DEPTH_TO_WATER, self._add_depth_to_water),)
            # (DEPTH_TO_SENSOR, self._add_depth_to_sensor),
            # (WATER_HEAD, self._add_water_head))
        else:
            funcs = ((DEPTH_TO_WATER, self._add_depth_to_water),
                     # (DEPTH_TO_SENSOR, self._add_depth_to_sensor),
                     (ADJ_WATER_HEAD, self._add_adjusted_water_head),
                     (MANUAL_WATER_LEVEL, self._add_manual_water_depth),)

        index_range = None
        for i, (k, f) in enumerate(funcs):
            plot = f(padding, qc)
            if i == 0:
                bottom_axis = PlotAxis(plot, orientation='bottom',  # mapper=xmapper,
                                       tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
                plot.padding_bottom = 50
                plot.x_axis = bottom_axis
            else:
                plot.index_range = index_range
                plot.x_axis.visible = False

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

    def _save_db(self, with_qc=False):
        keys, data = self._gather_data(with_qc=with_qc)
        if YES == confirm(None, 'Are you sure you want to save to the database?'):
            pid = self.selected_point_id.name
            e, i = self.db.insert_continuous_water_levels(pid, data)
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
            for lines in plot.plots.itervalues():
                for line in lines:
                    for o in line.overlays:
                        if isinstance(o, DataToolOverlay):
                            o.visible = ovisible

    def _gather_data(self, with_qc=False, use_isoformat=False):
        model = self.data_model
        x = model.x
        depth_to_water = model.depth_to_water_y
        ah = model.adjusted_water_head
        h = model.water_head
        water_temp = model.water_temp

        if use_isoformat:
            x = [datetime.fromtimestamp(xi).isoformat() for xi in x]
        args = (x, h, ah, depth_to_water, water_temp)
        keys = ('time', 'head', 'adjusted_head', 'depth_to_water', 'water_temp')
        if with_qc:
            args = args + (ones_like(x),)
            keys = keys + ('qc',)

        data = array(args).T
        return keys, data

    def _add_depth_to_water(self, padding, *args, **kw):
        pd = self._plot_data((DEPTH_X, []),
                             (DEPTH_Y, []))
        pd.set_data(MANUAL_WATER_DEPTH_X, [])
        pd.set_data(MANUAL_WATER_DEPTH_Y, [])

        plot = self._plot_factory(pd, padding=padding, origin='top left')
        plot.y_axis.title = DEPTH_TO_WATER_TITLE

        line = plot.plot((DEPTH_X, DEPTH_Y))[0]

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

    def _plot_container_default(self):
        pc = self._new_plotcontainer()
        return pc

    # property get/set
    def _get_filtered_point_ids(self):
        return fuzzyfinder(self.point_id_entry, self.point_ids, ('name', 'serial_num'))

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
