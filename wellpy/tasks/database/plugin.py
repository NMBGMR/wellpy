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
from envisage.service_offer import ServiceOffer
from traits.api import List

from wellpy.database_connector import DatabaseConnector
from wellpy.tasks.database.preferences import DatabasePreferencesPane


class DatabasePlugin(Plugin):
    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(contributes_to='envisage.ui.tasks.preferences_panes')

    service_offers = List(contributes_to='envisage.service_offers')

    def _service_offers_default(self):
        so1 = ServiceOffer(protocol='wellpy.database_connector.DatabaseConnector',
                           factory=DatabaseConnector)
        return [so1]

    def _preferences_panes_default(self):
        return [DatabasePreferencesPane]

# ============= EOF =============================================
