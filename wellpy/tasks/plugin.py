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
from envisage.plugin import Plugin
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu, SMenuBar
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List
from traitsui.menu import Action

from wellpy.tasks.task import WellpyTask


class WellpyPlugin(Plugin):
    name = 'Wellpy'

    tasks = List(contributes_to='envisage.ui.tasks.tasks')

    # service_offers = List(contributes_to='envisage.service_offers')
    # available_task_extensions = List(contributes_to='pychron.available_task_extensions')
    # task_extensions = List(contributes_to='envisage.ui.tasks.task_extensions')
    # my_task_extensions = List(contributes_to='envisage.ui.tasks.task_extensions')

    # def _task_extensions_default(self):
    #     ext=[]
    #     ext.append(TaskExtension(actions=[SchemaAddition(id='Reset Layout',
    #                                                      path='MenuBar/File',
    #                                                      factory=ResetLayoutAction),
    #
    #                                       SchemaAddition(id='File',
    #                                                      path='MenuBar',
    #                                                      factory=lambda: SMenu(id='File',
    #                                                                            name='File'))
    #                                       ]))
    #     print ext
    #         # SchemaAddition(id='Open',
    #         #                factory=OpenWellAction,
    #         #                path='MenuBar/file.menu/Open')]))
    #     return ext

    def _tasks_default(self):
        return [TaskFactory(id='wellpy.task',
                            factory=self._wellpy_factory), ]

    def _wellpy_factory(self):
        wt = WellpyTask()
        db = self.application.get_service('wellpy.database_connector.DatabaseConnector')
        wt.model.db = db

        return wt

# ============= EOF =============================================
