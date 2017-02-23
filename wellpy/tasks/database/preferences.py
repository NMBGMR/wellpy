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
from apptools.preferences.preferences_helper import PreferencesHelper
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Password
from traitsui.api import View, Item, VGroup


class DatabasePreferences(PreferencesHelper):
    id = 'wellpy.database.preferences'
    preferences_path = 'wellpy.database'
    name = Str
    host = Str
    password = Password
    username = Str


class DatabasePreferencesPane(PreferencesPane):
    model_factory = DatabasePreferences
    category = 'Database'

    def traits_view(self):
        v = View(VGroup(Item('host'),
                        Item('username'),
                        Item('password'),
                        Item('name'),
                        label='Database Connection',
                        show_border=True),
                 width=500)
        return v

# ============= EOF =============================================
