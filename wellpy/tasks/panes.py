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
import os

from enable.component_editor import ComponentEditor
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traits.api import Button
from traitsui.api import View, UItem, TabularEditor, Item, HGroup
from traitsui.tabular_adapter import TabularAdapter


class PointIDAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class WellCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('object.model.plot_container',
                       style='custom', editor=ComponentEditor()))
        return v


class WellPane(TraitsDockPane):
    id = 'wellpy.well.pane'
    name = 'Point IDs'
    open_file_button = Button('Open')

    def _open_file_button_fired(self):
        dlg = FileDialog(action='open')
        if dlg.open() == OK:
            if os.path.isfile(dlg.path):
                self.model.path = dlg.path
                self.model.model.load_file(dlg.path)

    def traits_view(self):
        v = View(HGroup(UItem('filename', style='readonly'), UItem('pane.open_file_button')),
                 UItem('point_id_entry'),
                 UItem('filtered_point_ids',
                       editor=TabularEditor(adapter=PointIDAdapter())))
        return v

# ============= EOF =============================================
