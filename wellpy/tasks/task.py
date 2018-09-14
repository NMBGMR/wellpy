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

from chaco.plot_containers import VPlotContainer
from envisage.ui.tasks.action.preferences_action import PreferencesAction
from pyface.tasks.action.schema import SMenu, SMenuBar, SGroup
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import PaneItem, TaskLayout, VSplitter, Tabbed
from traits.api import List, Str, HasTraits, Instance, Property, Button
from pyface.tasks.task import Task
from traitsui.menu import Action

from globals import DATABSE_DEBUG
from wellpy.database_connector import DatabaseConnector
from wellpy.model import WellpyModel
from wellpy.tasks.actions import ResetLayoutAction
from wellpy.tasks.panes import WellPane, WellCentralPane, ToolboxPane, AutoResultsPane, QCPane, ViewerPane


class WellpyTask(Task):
    name = 'Wellpy'
    id = 'wellpy.task'
    model = Instance(WellpyModel, ())

    # def __init__(self, *args, **kw):
    #     super(WellpyTask, self).__init__(*args, **kw)
    #     self._db = DatabaseConnector()

    def activated(self):
        self.model.activated()

    def create_central_pane(self):
        return WellCentralPane(model=self)

    def create_dock_panes(self):
        return [WellPane(model=self.model),
                ToolboxPane(model=self.model),
                AutoResultsPane(model=self.model),
                QCPane(model=self.model),
                ViewerPane(model=self.model)]

    def _default_layout_default(self):
        return TaskLayout(left=VSplitter(PaneItem('wellpy.well.pane'),
                                         Tabbed(PaneItem('wellpy.toolbox.pane'),
                                                PaneItem('wellpy.qc.pane'),
                                                PaneItem('wellpy.viewer.pane'))),
                          bottom=PaneItem('wellpy.autoresults.pane'))

    def _menu_bar_factory(self, menus=None):
        if not menus:
            menus = []

        # edit_menu = SMenu(GenericFindAction(),
        #                   id='Edit', name='&Edit')

        # entry_menu = SMenu(
        #     id='entry.menu',
        #     name='&Entry')

        file_menu = SMenu(
            SGroup(id='Open'),
            # SGroup(id='New'),
            # SGroup(
            #     GenericSaveAsAction(),
            #     GenericSaveAction(),
            #     id='Save'),
            # SGroup(),
            PreferencesAction(),
            id='file.menu', name='File')

        window_menu = SMenu(ResetLayoutAction(),
                            id='window.menu', name='Window')
        # tools_menu = SMenu(
        #     CopyPreferencesAction(),
        #     id='tools.menu', name='Tools')
        #
        # window_menu = SMenu(
        #     WindowGroup(),
        #     Group(
        #         CloseAction(),
        #         CloseOthersAction(),
        #         id='Close'),
        #     OpenAdditionalWindow(),
        #     Group(MinimizeAction(),
        #           ResetLayoutAction(),
        #           PositionAction()),
        #
        #     # SplitEditorAction(),
        #     id='window.menu',
        #     name='Window')
        # help_menu = SMenu(
        #     IssueAction(),
        #     NoteAction(),
        #     AboutAction(),
        #     DocumentationAction(),
        #     ChangeLogAction(),
        #     RestartAction(),
        #
        #     # KeyBindingsAction(),
        #     # SwitchUserAction(),
        #
        #     StartupTestsAction(),
        #     # DemoAction(),
        #     id='help.menu',
        #     name='Help')
        #
        # grps = self._view_groups()
        # view_menu = SMenu(*grps, id='view.menu', name='&View')

        mb = SMenuBar(
            file_menu,
            # edit_menu,
            # view_menu,
            # tools_menu,
            window_menu,
            # help_menu
        )
        # if menus:
        #     for mi in reversed(menus):
        #         mb.items.insert(4, mi)

        return mb

    def _menu_bar_default(self):
        return self._menu_bar_factory()

# ============= EOF =============================================
