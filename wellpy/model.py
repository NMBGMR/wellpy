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

from chaco.axis import PlotAxis
from chaco.plot_containers import VPlotContainer
from chaco.tools.api import ZoomTool
from chaco.array_plot_data import ArrayPlotData
from chaco.plot import Plot
from chaco.tools.range_selection import RangeSelection
from chaco.tools.range_selection_overlay import RangeSelectionOverlay
from traits.api import HasTraits, Instance
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator

from wellpy.config import config
from wellpy.data_model import DataModel
from wellpy.nm_well_database import NMWellDatabase
from wellpy.tools import DataTool, DataToolOverlay


class NoSelectionError(BaseException):
    pass


class WellpyModel(HasTraits):
    plot_container = Instance(VPlotContainer)
    _tool = None
    _series = None
    _plots = None
    data_model = Instance(DataModel)

    def import_db(self):
        db = NMWellDatabase()
        if db.connect(config.db_host,
                      config.db_user,
                      config.db_password,
                      config.db_name,
                      config.db_login_timeout):

            # do database import here
            record = self._gather_db_record()
            db.add_record(record)

            return True, db.url
        else:
            return False, db.url

    def apply_offset(self, v):
        mask = self._series[0].index.metadata['selection_masks'][0]
        self.data_model.apply_offset('water_head', v, mask)
        self.plot_container.invalidate_and_redraw()
        self._plots['water_head'].data.set_data('water_head', self.data_model.water_head)
        # self._series[0].index.metadata['selection_masks'][0] = []
        self._tool.deselect()

    def load_file(self, p):
        data = DataModel(p)
        self.data_model = data
        self.initialize_plot()

    def initialize_plot(self):
        data = self.data_model

        container = self.plot_container
        self._series = []
        self._plots = {}
        index, rr = None, None
        for i, (a, title) in enumerate((('water_head', 'Head'),
                                        ('adjusted_water_head', 'Adj. Head'),

                                        ('temp', 'Temp.'),
                                        ('water_level_elevation', 'Elev.'))):
            plot = Plot(data=ArrayPlotData(**{'x': data.x, a: getattr(data, a)}),
                        padding=[70, 10, 10, 10],
                        resizable='h',
                        bounds=(1, 125))

            if index is None:
                index = plot.index_mapper
                rr = plot.index_range
            else:
                plot.index_mapper = index
                plot.index_range = rr

            series = plot.plot(('x', a))[0]
            plot.plot(('x', a),
                      marker_size=1.5,
                      type='scatter')

            dt = DataTool(plot=series, component=plot,
                          normalize_time=False,
                          use_date_str=True)
            dto = DataToolOverlay(
                component=series,
                tool=dt)
            series.tools.append(dt)
            series.overlays.append(dto)

            plot.y_axis.title = title
            if i != 0:
                plot.x_axis.visible = False
            else:

                zoom = ZoomTool(plot, tool_mode="range",
                                axis='index',
                                color=(0, 1, 0, 0.5),

                                always_on=False)
                plot.overlays.append(zoom)

                tool = RangeSelection(series, left_button_selects=True,
                                      listeners=[self])
                self._tool = tool

                series.tools.append(tool)
                # series.active_tool = tool
                # plot.x_axis.title = 'Time'
                bottom_axis = PlotAxis(plot, orientation="bottom",  # mapper=xmapper,
                                       tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
                plot.x_axis = bottom_axis

                plot.padding_bottom = 50

            series.overlays.append(RangeSelectionOverlay(component=series))
            container.add(plot)
            self._series.append(series)
            self._plots[a] = plot

        container.invalidate_and_redraw()

    def set_value_selection(self, v):
        for s in self._series:
            s.index.metadata['selections'] = v

    def has_selection(self):
        return bool(self._tool.selection)

    # private
    def _gather_db_record(self):
        raise NotImplementedError

    def _add_range_selection(self, series, listeners=None):
        series.active_tool = tool = RangeSelection(series, left_button_selects=True)
        if listeners:
            tool.listeners = listeners

        series.overlays.append(RangeSelectionOverlay(component=series))
        return tool

    def _plot_container_default(self):
        pc = VPlotContainer()
        return pc

# ============= EOF =============================================
