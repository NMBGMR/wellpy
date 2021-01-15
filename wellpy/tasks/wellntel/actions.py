# ===============================================================================
# Copyright 2020 ross
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

from pyface.directory_dialog import DirectoryDialog
from pyface.file_dialog import FileDialog
from traitsui.menu import Action


class AppAction(Action):
    def perform(self, event):
        app = event.task.window.application
        self._perform(event, app)

    def _perform(self, event, app):
        pass


class ClientAction(AppAction):
    def _perform(self, event, app):
        clt = app.get_service('wellpy.wellntel.client.WellntelClient')
        db = app.get_service('wellpy.database_connector.DatabaseConnector')

        clt.bind_preferences()
        clt.db = db
        self._perform_hook(clt)

    def _perform_hook(self, clt):
        pass


class WellntelGetDataAction(ClientAction):
    name = 'Get Readings'

    def _perform_hook(self, clt):
        clt.edit_traits()


class WellntelLoadFromFileAction(ClientAction):
    name = 'Load From File'

    def _perform_hook(self, clt):

        dlg = FileDialog(default_path=os.path.join(os.path.expanduser('~'), 'Documents'),
                         action='open files')
        if dlg.open():
            if dlg.paths:
                clt.upload_outputs(dlg.paths)

# ============= EOF =============================================
