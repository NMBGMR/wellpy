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
from traits.api import Button, Float, Property
from traitsui.api import View, UItem, TabularEditor, Item, HGroup, VGroup, spring
from traitsui.tabular_adapter import TabularAdapter

from globals import FILE_DEBUG


class PointIDAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class WellCentralPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('object.model.plot_container',
                       style='custom', editor=ComponentEditor()))
        return v


class ToolboxPane(TraitsDockPane):
    id = 'wellpy.toolbox.pane'
    name = 'Toolbox'
    fix_data_button = Button('Fix Data')
    constant_offset = Float
    threshold = Float(1)

    def _constant_offset_changed(self, new):
        self.model.apply_constant_offset(new)

    def _fix_data_button_fired(self):
        self.model.fix_data(self.threshold)

    def traits_view(self):
        manual_grp = VGroup(Item('pane.constant_offset', label='Constant Offset'),
                            show_border=True, label='Manual')
        auto_grp = VGroup(Item('pane.threshold', label='Threshold'),
                          UItem('pane.fix_data_button'),
                          show_border=True, label='Auto')

        v = View(VGroup(manual_grp, auto_grp))
        return v


class AutoResultsTabularAdapter(TabularAdapter):
    columns = [('Start', 'start'),
               ('End','end'),
               ('Offset', 'offset')]

    # start_text = Property
    # def _get_start_text(self):
    #     return self.item.start.isoformat()


class AutoResultsPane(TraitsDockPane):
    id = 'wellpy.autoresults.pane'
    name='AutoResults'

    def traits_view(self):
        v = View(UItem('auto_results', editor=TabularEditor(adapter=AutoResultsTabularAdapter())))
        return v


class WellPane(TraitsDockPane):
    id = 'wellpy.well.pane'
    name = 'Well'
    open_file_button = Button('Open')
    retrieve_manual_button = Button('Retrieve')

    def _retrieve_manual_button_fired(self):
        self.model.retrieve_manual()

    def _open_file_button_fired(self):

        if FILE_DEBUG:
            self.model.path = FILE_DEBUG
            self.model.load_file(FILE_DEBUG)
        else:
            dlg = FileDialog(action='open', default_directory=os.path.expanduser('~'))

            if dlg.open() == OK:
                if os.path.isfile(dlg.path):
                    self.model.path = dlg.path
                    self.model.load_file(dlg.path)

    def traits_view(self):
        site_grp = VGroup(UItem('point_id_entry'),
                          UItem('filtered_point_ids',
                                editor=TabularEditor(selected='selected_point_id',
                                                     editable=False,
                                                     adapter=PointIDAdapter())),
                          UItem('pane.retrieve_manual_button',
                                enabled_when='selected_point_id'),
                          show_border=True,
                          label='Site')
        df_grp = HGroup(UItem('filename', style='readonly'),
                        spring,
                        UItem('pane.open_file_button'),
                        show_border=True,
                        label='Diver File')

        metadata_grp = VGroup(show_border=True, label='Metadata')

        v = View(VGroup(df_grp, site_grp, metadata_grp))

        return v

# ============= EOF =============================================
