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
from pyface.message_dialog import warning, information
from traits.api import Instance, Button, Float, Str, HasTraits, Password, CInt, Enum
from traitsui.api import Controller, View, UItem, Item, VGroup
from traitsui.menu import Action

from wellpy.config import config
from wellpy.model import WellpyModel


class WellpyController(Controller):
    model = Instance(WellpyModel)
    apply_offset = Button
    offset = Float
    title = Str
    offset_kind = Enum('Linear','Constant')

    def configure_db(self, info):
        class Connection(HasTraits):
            name = Str
            user = Str
            host = Str
            password = Password
            login_timeout = CInt

        v = View(VGroup(Item('host', label='Server', tooltip='Database Server IP address e.g., 192.168.0.1'),
                        Item('user', label='Username', tooltip='Username for connecting to database'),
                        Item('password', tooltip='Password for connecting to database'),
                        Item('name', tooltip='Name of database'),
                        Item('login_timeout', tooltip='Login timeout in seconds')),
                 buttons=['OK', 'Cancel'],
                 width=300,
                 kind='livemodal',
                 title='Edit Database Connection')

        c = Connection()
        attrs = ('host', 'user', 'password', 'name')
        for a in attrs:
            setattr(c, a, getattr(config, 'db_{}'.format(a)) or '')

        setattr(c, 'login_timeout', getattr(config, 'db_login_timeout') or 3)

        info = c.edit_traits(view=v)
        if info.result:
            for a in attrs:
                config.set_value('db_{}'.format(a), str(getattr(c, a)))

            config.set_value('db_login_timeout', getattr(c, 'login_timeout'))
            config.dump()
            config.load()

    def import_db(self, info):
        result, url = self.model.import_db()
        if result:
            information(None, 'Added to database.\n\n {}'.format(url))
        else:
            warning(None, 'Unable to connect to database.\n\n {}'.format(url))

    def open_csv(self, info):
        if config.DEBUG:
            self.model.load_file(config.DEBUG_PATH)
        else:
            dlg = FileDialog(action='open', default_directory=config.default_data_dir)
            if dlg.open() == 'OK':
                if os.path.isfile(dlg.path):
                    self.model.load_file(dlg.path)

    def apply_offset(self, info):
        if not self.model.has_selection():
            ret = confirm(None, 'No Range selected? Apply to entire dataset')
            if ret != YES:
                return

        v = View(Item('controller.offset_kind', label='Kind'),
                 Item('controller.offset', enabled_when='kind="Constant"'),
                 title='Set Offset',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        info = self.edit_traits(view=v)
        if info.result:
            self.model.apply_offset(self.offset_kind, self.offset)

    def traits_view(self):
        actions = [Action(name='Open Excel...', action='open_csv')]
        menu = MenuManager(*actions, name='File')
        menubar = MenuBarManager(menu)

        actions = [Action(name='Open Excel', action='open_csv'),
                   Action(name='Apply Offset', action='apply_offset'),
                   Action(name='Configure DB', action='configure_db'),
                   Action(name='Import DB', action='import_db'),
                   ]
        toolbar = ToolBarManager(*actions)

        v = View(UItem('plot_container', style='custom', editor=ComponentEditor()),
                 menubar=menubar, resizable=True,
                 toolbar=toolbar,
                 title='Wellpy',
                 width=800,
                 height=650)
        return v

# ============= EOF =============================================
