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
from chaco.plot_containers import VPlotContainer
from pyface.tasks.action.schema import SMenu, SMenuBar
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import PaneItem, TaskLayout
from traits.api import List, Str, HasTraits, Instance, Property
from pyface.tasks.task import Task
from traitsui.menu import Action

from globals import DATABSE_DEBUG
from wellpy.database_connector import DatabaseConnector
from wellpy.model import WellpyModel
from wellpy.tasks.panes import WellPane, WellCentralPane


class PointIDRecord(HasTraits):
    name = Str


class WellpyTask(Task):
    id = 'wellpy.task'
    point_id_entry = Str
    point_ids = List
    filtered_point_ids = Property(depends_on='point_id_entry')

    selected_point_id = Instance(PointIDRecord)
    menu_bar = SMenuBar(SMenu(TaskAction(name='Open...', method='open',
                                         accelerator='Ctrl+O'),
                              TaskAction(name='Save', method='save',
                                         accelerator='Ctrl+S'),
                              id='File', name='&File'))
    model = Instance(WellpyModel, ())
    db = Instance(DatabaseConnector, ())

    # def __init__(self, *args, **kw):
    #     super(WellpyTask, self).__init__(*args, **kw)
    #     self._db = DatabaseConnector()

    def activated(self):

        pids = self.db.get_point_ids()
        if DATABSE_DEBUG:
            pids = ['A', 'B', 'C']

        self.point_ids = [PointIDRecord(name=p) for p in pids]

    def create_central_pane(self):
        return WellCentralPane(model=self)

    def create_dock_panes(self):
        return [WellPane(model=self)]

    def _get_filtered_point_ids(self):
        return [p for p in self.point_ids if p.name.startswith(self.point_id_entry)]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('wellpy.well.pane'))

# ============= EOF =============================================
