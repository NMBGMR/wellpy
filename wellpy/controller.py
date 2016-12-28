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

# ============= enthought library imports =======================
import os

from enable.component_editor import ComponentEditor
from pyface.action.menu_bar_manager import MenuBarManager
from pyface.action.menu_manager import MenuManager
from pyface.action.tool_bar_manager import ToolBarManager
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.file_dialog import FileDialog
from pyface.message_dialog import warning
from traits.api import Instance, Button, Float, Str
from traitsui.api import Controller, View, UItem, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action

from wellpy.config import config
from wellpy.model import WellpyModel


class WellpyController(Controller):
    model = Instance(WellpyModel)
    apply_offset = Button
    offset = Float
    title = Str

    def open_csv(self, info):
        self.model.load_file('/Users/ross/Programming/github/wellpy/data/AR0209_AztecMW.xlsx')
        # dlg = FileDialog(action='open', default_directory=config.default_data_dir)
        # if dlg.open() == 'OK':
        #     if os.path.isfile(dlg.path):
        #         self.model.load_file(dlg.path)

    def apply_offset(self, info):
        if not self.model.has_selection():
            ret = confirm(None, 'No Range selected? Apply to entire dataset')
            if ret != YES:
                return

        v = View(Item('controller.offset'),
                 title='Set Offset',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        info = self.edit_traits(view=v)
        if info.result:
            self.model.apply_offset(self.offset)

    def traits_view(self):
        actions = [Action(name='Open CSV...', action='open_csv')]
        menu = MenuManager(*actions, name='File')
        menubar = MenuBarManager(menu)

        actions = [Action(name='Open CSV', action='open_csv'),
                   Action(name='Apply Offset', action='apply_offset')]
        toolbar = ToolBarManager(*actions)

        v = View(UItem('plot_container', style='custom', editor=ComponentEditor()),
                 menubar=menubar, resizable=True,
                 toolbar=toolbar,
                 title = self.title,
                 width=800,
                 height=650)
        return v

# ============= EOF =============================================
