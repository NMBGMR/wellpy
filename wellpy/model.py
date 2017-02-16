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
from chaco.tools.range_selection import RangeSelection
from chaco.tools.range_selection_overlay import RangeSelectionOverlay
from datetime import datetime
from traits.api import HasTraits, Instance, Float, List, Property, Str, Button
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from numpy import array, diff, where

from globals import DATABSE_DEBUG
from wellpy.config import config
from wellpy.data_model import DataModel
from wellpy.database_connector import DatabaseConnector
from wellpy.nm_well_database import NMWellDatabase
from wellpy.range_overlay import RangeOverlay
from wellpy.tools import DataTool, DataToolOverlay


class NoSelectionError(BaseException):
    pass


WATER_HEAD = 'water_head'
ADJ_WATER_HEAD = 'adjusted_water_head'
MANUAL_MEASUREMENTS = 'manual'
MANUAL_MEASUREMENTS_SCATTER = 'manual_scatter'


class PointIDRecord(HasTraits):
    name = Str


class AutoResult(HasTraits):
    start = None
    end = None
    offset = Float

    def __init__(self, offset, sidx, eidx, s, e):
        self.offset = offset
        self.start = datetime.fromtimestamp(s)
        self.end = datetime.fromtimestamp(e)


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

    auto_results = List
    db = Instance(DatabaseConnector, ())

    def activated(self):
        pids = self.db.get_point_ids()
        if DATABSE_DEBUG:
            pids = ['A', 'B', 'C']

        self.point_ids = [PointIDRecord(name=p) for p in pids]

    def retrieve_manual(self):
        """
        retrieve the manual measurements from database for selected_pointID
        :return:
        """

        pid = self.selected_point_id
        ms = self.db.get_manual_measurements(pid)

        def factory(mm):
            pass

        xs, ys = array([factory(mi) for mi in ms]).T
        plot = self._plots[MANUAL_MEASUREMENTS]

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

        self.plot_container.invalidate_and_redraw()

    def smooth_data(self, window, method):
        plot = self._plots[ADJ_WATER_HEAD]

        ys = self.data_model.adjusted_water_head
        sy = self.data_model.smooth(ys, window, method)

        plot_needed = 'sy' not in plot.data.arrays
        plot.data.set_data('sy', sy)
        if plot_needed:
            plot.plot(('x', 'sy'), color='green')

        self.plot_container.invalidate_and_redraw()

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

        # index, rr = None, None
        # for i, (a, title) in enumerate((('adjusted_water_head', 'Adj. Head'),
        #                                 ('water_head', 'Head'),
        #                                 # ('temp', 'Temp.'),
        #                                 # ('water_level_elevation', 'Elev.')
        #                                 )):
        #     plot = Plot(data=ArrayPlotData(**{'x': data.x, a: getattr(data, a)}),
        #                 padding=[70, 10, 10, 10])
        #
        #     if index is None:
        #         index = plot.index_mapper
        #         rr = plot.index_range
        #     else:
        #         plot.index_mapper = index
        #         plot.index_range = rr
        #
        #     series = plot.plot(('x', a))[0]
        #     plot.plot(('x', a),
        #               marker_size=1.5,
        #               type='scatter')
        #
        #     dt = DataTool(plot=series, component=plot,
        #                   normalize_time=False,
        #                   use_date_str=True)
        #     dto = DataToolOverlay(
        #         component=series,
        #         tool=dt)
        #     series.tools.append(dt)
        #     series.overlays.append(dto)
        #
        #     plot.y_axis.title = title
        #     if i != 0:
        #         plot.x_axis.visible = False
        #     else:
        #
        #         zoom = ZoomTool(plot, tool_mode="range",
        #                         axis='index',
        #                         color=(0, 1, 0, 0.5),
        #                         enable_wheel=False,
        #                         always_on=False)
        #         plot.overlays.append(zoom)
        #
        #         # tool = RangeSelection(series, left_button_selects=True,
        #         #                       listeners=[self])
        #         # self._tool = tool
        #         #
        #         # series.tools.append(tool)
        #         # series.active_tool = tool
        #         # plot.x_axis.title = 'Time'
        #         bottom_axis = PlotAxis(plot, orientation="bottom",  # mapper=xmapper,
        #                                tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
        #         plot.x_axis = bottom_axis
        #
        #         plot.padding_bottom = 50
        #
        #     series.overlays.append(RangeSelectionOverlay(component=series))
        #     container.add(plot)
        #     self._series.append(series)
        #     self._plots[a] = plot


        container.invalidate_and_redraw()

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
        return [p for p in self.point_ids if p.name.startswith(self.point_id_entry)]

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
