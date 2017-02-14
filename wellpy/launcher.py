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
import logging

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin

from wellpy.application import WellpyApplication
from wellpy.tasks.plugin import WellpyPlugin


def launch():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    shandler = logging.StreamHandler()
    shandler.setLevel(logging.DEBUG)

    root.addHandler(shandler)

    plugins = [CorePlugin(),
               TasksPlugin(),
               WellpyPlugin()]

    app = WellpyApplication(plugins=plugins)

    app.run()

if __name__ == '__main__':
    launch()
# ============= EOF =============================================
