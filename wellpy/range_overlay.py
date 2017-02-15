# ===============================================================================
# Copyright 2017 ross
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
from chaco.abstract_mapper import AbstractMapper
from chaco.abstract_overlay import AbstractOverlay
from chaco.grid_mapper import GridMapper
from chaco.tools.range_selection_overlay import RangeSelectionOverlay
from enable.colors import ColorTrait
from enable.enable_traits import LineStyle
from traits.api import Float, Instance, cached_property, List, Property, Enum
from numpy import array


class RangeOverlay(AbstractOverlay):
    axis = Enum("index", "value")

    # The color of the selection border line.
    border_color = ColorTrait("dodgerblue")
    # The width, in pixels, of the selection border line.
    border_width = Float(1.0)
    # The line style of the selection border line.
    border_style = LineStyle("solid")
    # The color to fill the selection region.
    fill_color = ColorTrait("lightskyblue")
    # The transparency of the fill color.
    alpha = Float(0.3)

    mapper = Instance(AbstractMapper)

    ranges = List
    axis_index = Property

    def overlay(self, component, gc, view_bounds=None, mode="normal"):
        """ Draws this component overlaid on another component.

        Overrides AbstractOverlay.
        """
        axis_ndx = self.axis_index
        lower_left = [0, 0]
        upper_right = [0, 0]
        # Draw the selection
        coords = self._get_selection_screencoords()

        for coord in coords:
            start, end = coord
            lower_left[axis_ndx] = start
            lower_left[1 - axis_ndx] = component.position[1 - axis_ndx]
            upper_right[axis_ndx] = end - start
            upper_right[1 - axis_ndx] = component.bounds[1 - axis_ndx]

            with gc:
                gc.clip_to_rect(component.x, component.y, component.width, component.height)
                gc.set_alpha(self.alpha)
                gc.set_fill_color(self.fill_color_)
                gc.set_stroke_color(self.border_color_)
                gc.set_line_width(self.border_width)
                gc.set_line_dash(self.border_style_)
                gc.draw_rect((lower_left[0], lower_left[1],
                              upper_right[0], upper_right[1]))

    def _get_selection_screencoords(self):
        coords = []
        i = 0
        for _, _, _, s, e in self.ranges:
            s, e = self.mapper.map_screen(array((s, e)))
            if coords:
                if coords[i - 1][1] == s:
                    coords[i - 1] = (coords[i - 1][0], e)
                    continue

            coords.append((s, e))
            i += 1
        return coords

    def _determine_axis(self):
        """ Determines which element of an (x,y) coordinate tuple corresponds
        to the tool's axis of interest.

        This method is only called if self._axis_index hasn't been set (or is
        None).
        """
        if self.axis == "index":
            if self.plot.orientation == "h":
                return 0
            else:
                return 1
        else:  # self.axis == "value"
            if self.plot.orientation == "h":
                return 1
            else:
                return 0

    def _mapper_default(self):
        # If the plot's mapper is a GridMapper, return either its
        # x mapper or y mapper

        mapper = getattr(self.plot, self.axis + "_mapper")

        if isinstance(mapper, GridMapper):
            if self.axis == 'index':
                return mapper._xmapper
            else:
                return mapper._ymapper
        else:
            return mapper

    @cached_property
    def _get_axis_index(self):
        return self._determine_axis()

# ============= EOF =============================================
