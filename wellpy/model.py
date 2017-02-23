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
from chaco.axis import PlotAxis
from chaco.plot_containers import VPlotContainer
from chaco.tools.api import ZoomTool
from chaco.array_plot_data import ArrayPlotData
from chaco.plot import Plot
from chaco.tools.pan_tool2 import PanTool
from chaco.tools.range_selection import RangeSelection
from chaco.tools.range_selection_overlay import RangeSelectionOverlay
from datetime import datetime
from traits.api import HasTraits, Instance, Float, List, Property, Str, Button
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from numpy import array, diff, where, ones, logical_and, hstack, zeros_like

from globals import DATABSE_DEBUG
from wellpy.config import config
from wellpy.data_model import DataModel
from wellpy.database_connector import DatabaseConnector, PointIDRecord
from wellpy.fuzzyfinder import fuzzyfinder
from wellpy.nm_well_database import NMWellDatabase
from wellpy.range_overlay import RangeOverlay
from wellpy.tools import DataTool, DataToolOverlay


class NoSelectionError(BaseException):
    pass


WATER_HEAD = 'water_head'
ADJ_WATER_HEAD = 'adjusted_water_head'
DEPTH_TO_SENSOR = 'depth_to_sensor'
DEPTH_TO_SENSOR_SCATTER = 'depth_to_sensor_scatter'
DEPTH_TO_WATER = 'depth_to_water'





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
    filtered_point_ids = Property(depends_on='point_id_entry')
    selected_point_id = Instance(PointIDRecord)
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

    def activated(self):
        if DATABSE_DEBUG:
            pids = ['A', 'B', 'C']
            self.point_ids = [PointIDRecord(p, '', '') for p in pids]
        else:
            pids = self.db.get_point_ids()
            self.point_ids = pids

    def retrieve_depth_to_sensor(self):
        """
        retrieve the depth to sensor measurements from database for selected_pointID
        :return:
        """

        pid = self.selected_point_id
        ms = self.db.get_manual_measurements(pid)

        def factory(mm):
            pass

        xs, ys = array([factory(mi) for mi in ms]).T
        plot = self._plots[DEPTH_TO_SENSOR]

    def calculate_depth_to_water(self, correct_drift=True):
        """
        calculate depth to water
        ------------------------------------------------------
        |           |   |
        |           |   |
        |           |   |
        |           |   |    depth_to_water == d
        |           |   |                                     manual_measurement
        |           |   |
        |           |   |
        ~~~~~~~~~~~ | -------
        |           |
        |           |        adjusted_water_head
        |           |
        |-----------| ------- --------------------------------


        w/o drift
        d(t) = manual_measurement - adjusted_water_head

        w/drift
        d(t) = (manual_measurement_1 - m(t-t_0)) - adjusted_water_head
        where m = dL/dt == (manual_measurement_1 - manual_measurement_0) / (t_1 - t_0)


        :return:
        """

        def calculated_dtw_bin(l1, l0, x, h):
            l = l1 * ones(h.shape[0])
            if correct_drift:
                to = x[0]
                m = (l1 - l0) / (x[-1] - to)
                l = [l1 - m * (t - to) for t in x]

            dtw = l - h
            return dtw

        ah = self.data_model.adjusted_water_head
        xs = self.data_model.x
        ds = self.data_model.depth_to_sensor

        # ds needs to be reverse sorted
        # eg. (t1, t0)
        dd = zeros_like(ah)

        for i in xrange(len(ds)):
            m1, m0 = ds[i], ds[i + 1]

            mask = where(logical_and(xs <= m1[0], xs >= m0[0]))[0]

            dd[mask] = calculated_dtw_bin(m1[1], m0[1], xs[mask], ah[mask])

        self.data_model.depth_to_water = dd

        plot = self._plot[DEPTH_TO_WATER]
        plot.data.set_data('y', dd)
        self.refresh_plot()

    def fix_data(self, threshold):
        """
        automatically remove offsets and zeros
        :param threshold:
        :return:
        """
        ys = self.data_model.get_water_head()
        ys, zs, fs = self.data_model.fix_data(ys, threshold)
        self.auto_results = [AutoResult(*fi) for fi in fs]

        # plot fixed ranges on raw plot
        plot = self._plots[WATER_HEAD]
        plot.auto_fixed_range_overlay.ranges = fs

        # update adjusted head
        self.data_model.adjusted_water_head = ys
        plot = self._plots[ADJ_WATER_HEAD]
        plot.data.set_data('y', ys)

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
        data = DataModel(p)
        self.data_model = data
        self.initialize_plot()

    def initialize_plot(self):
        container = self.plot_container
        self._plots = {}

        padding = [70, 10, 10, 10]

        plot = self._add_adjusted_water_head(padding)
        container.add(plot)

        plot = self._add_water_head(padding)
        container.add(plot)

        self._add_water_level(padding)

        self.refresh_plot()

    def _add_water_head(self, padding):
        plot, line, scatter = self._add_line_scatter('water_head', 'Water Head', padding)
        plot.x_axis.visible = False
        # add overlays
        o = RangeOverlay(plot=plot)
        plot.auto_fixed_range_overlay = o
        plot.overlays.append(o)
        self._plots[WATER_HEAD] = plot
        return plot

    def _add_adjusted_water_head(self, padding):
        plot, line, scatter = self._add_line_scatter('adjusted_water_head', 'Adj. Water Head', padding)
        bottom_axis = PlotAxis(plot, orientation="bottom",  # mapper=xmapper,
                               tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
        plot.x_axis = bottom_axis
        plot.padding_bottom = 50

        pt = PanTool(component=plot)
        plot.tools.append(pt)

        self._plots[ADJ_WATER_HEAD] = plot
        return plot

    def _add_water_level(self, padding):
        pass

    def _add_line_scatter(self, key, title, padding):
        data = self.data_model
        pd = ArrayPlotData(x=data.x, y=getattr(data, key))
        plot = Plot(data=pd, padding=padding)
        plot.y_axis.title = title

        line = plot.plot(('x', 'y'))[0]
        scatter = plot.plot(('x', 'y'), marker_size=1.5, type='scatter')

        dt = DataTool(plot=line, component=plot, normalize_time=False, use_date_str=True)
        dto = DataToolOverlay(component=line, tool=dt)
        line.tools.append(dt)
        line.overlays.append(dto)

        zoom = ZoomTool(plot,
                        # tool_mode="range",
                        axis='index',
                        color=(0, 1, 0, 0.5),
                        enable_wheel=False,
                        always_on=False)
        plot.overlays.append(zoom)
        return plot, line, scatter

    def _plot_container_default(self):
        pc = VPlotContainer()
        return pc

    # property get/set
    def _get_filtered_point_ids(self):

        return fuzzyfinder(self.point_id_entry, self.point_ids, 'name')
        # return [p for p in self.point_ids if p.name.startswith(self.point_id_entry)]

    def _get_filename(self):
        return os.path.basename(self.path)
        # ============= EOF =============================================
        # def apply_constant_offset(self, v):
        #     self.fix_data()
        #
        #     if self._apply_constant_offset(v):
        #         self.plot_container.invalidate_and_redraw()
        #         self._plots[ADJ_WATER_HEAD].data.set_data(ADJ_WATER_HEAD, self.data_model.adjusted_water_head)
        #         self._tool.deselect()
        #     # self._series[0].index.metadata['selection_masks'] = None
        # def set_value_selection(self, v):
        #     if v is None:
        #         v = array([])

        # for s in self._series:
        #     s.index.metadata['selections'] = v

        # def has_selection(self):
        #     if isinstance(self._tool.selection, tuple):
        #         return bool(self._tool.selection)
        #     else:
        #         return self._tool.selection.any()
        #         # return self._tool.selection and self._tool.selection.any()
        #
        # private
        # def _apply_constant_offset(self, v):
        #     try:
        #         mask = self._series[0].index.metadata['selection_masks'][0]
        #         self.data_model.apply_offset(ADJ_WATER_HEAD, v, mask)
        #         return True
        #     except KeyError:
        #         pass
        #
        # def _apply_linear_interpolation(self):
        #
        #     mask = self._series[0].index.metadata['selection_masks'][0]
        #     s,e = self._series[0].index.metadata['selections']
        #
        #     self.data_model.apply_linear(ADJ_WATER_HEAD, s, e, mask)
        #
        # def _gather_db_record(self):
        #     raise NotImplementedError
        #
        # def _add_range_selection(self, series, listeners=None):
        #     series.active_tool = tool = RangeSelection(series, left_button_selects=True)
        #     if listeners:
        #         tool.listeners = listeners
        #
        #     series.overlays.append(RangeSelectionOverlay(component=series))
        #     return tool

        # def import_db(self):
        #     db = NMWellDatabase()
        #     if db.connect(config.db_host,
        #                   config.db_user,
        #                   config.db_password,
        #                   config.db_name,
        #                   config.db_login_timeout):
        #
        #         # do database import here
        #         record = self._gather_db_record()
        #         db.add_record(record)
        #
        #         return True, db.url
        #     else:
        #         return False, db.url
        #
        # def apply_offset(self, kind, v):
        #     if kind.lower() == 'constant':
        #         self._apply_constant_offset(v)
        #     else:
        #         self._apply_linear_interpolation()
        #
        #     self.plot_container.invalidate_and_redraw()
        #     self._plots[ADJ_WATER_HEAD].data.set_data(ADJ_WATER_HEAD, self.data_model.adjusted_water_head)
        #     self._tool.deselect()
        #     self._series[0].index.metadata['selection_masks'] = None
