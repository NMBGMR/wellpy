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
from envisage.ui.tasks.tasks_application import TasksApplication
from pyface.tasks.task_window_layout import TaskWindowLayout


class WellpyApplication(TasksApplication):
    always_use_default_layout = True

    def _default_layout_default(self):
        return [TaskWindowLayout('wellpy.task',
                                 size=(800, 600))]

        # active_task = self.preferences_helper.default_task
        # tasks = [factory.id for factory in self.task_factories]
        # return [TaskWindowLayout(*tasks,
        #                          active_task=active_task,
        #                          size=(800, 600))]

    def get_task(self, tid, activate=True):
        for win in self.windows:
            if win.active_task:
                if win.active_task.id == tid:
                    if activate and win.control:
                        win.activate()
                    break
        else:
            w = TaskWindowLayout(tid)
            win = self.create_window(w)
            if activate:
                win.open()

        if win:
            if win.active_task:
                win.active_task.window = win

            return win.active_task

    def open_task(self, tid, **kw):
        return self.get_task(tid, True, **kw)

# ============= EOF =============================================
