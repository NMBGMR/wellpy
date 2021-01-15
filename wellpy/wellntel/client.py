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
from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter
import requests

from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, HasTraits, Button, Instance
from traitsui.api import View, Item, UItem, HGroup


DT_FMT = '%Y-%m-%d %H:%M:%S'
POINTID_MAP = {'Gaume Well': 'WL-0036', 'Eileen Dodds Well': 'SA-0240', 'Moss Farms Well': 'EB-165'}


class WellntelClient(HasTraits):
    db = Instance('wellpy.database_connector.DatabaseConnector')
    api_key = Str
    output_root = Str
    start_datetime = Str('2020-09-29 09:14:00')
    get_readings_button = Button('Get Readings')
    get_start_datetime_from_db_button = Button('Get Start Date')

    def bind_preferences(self):
        bind_preference(self, 'api_key', 'wellpy.wellntel.api_key')
        bind_preference(self, 'output_root', 'wellpy.wellntel.output_root')

    def readings(self):
        dt = datetime.strptime(self.start_datetime, DT_FMT)

        records = []
        self._get_readings(dt, records, None)
        print('total {}'.format(len(records)))
        for pid, records in groupby(sorted(records, key=itemgetter('pointid')), key=itemgetter('pointid')):
            self._make_output(pid, records)

    def upload_outputs(self, paths):
        for p in paths:
            pid, ext = os.path.splitext(os.path.basename(p))
            if self.db:
                records = self._get_records_from_file(p)
                self.db.insert_wellntel_water_levels(pid, records)

    # private
    def _get_readings(self, dt, records, prev):
        r = list(self._get_endpoint('readings', dt))
        records.extend(r)

        ndt = r[-1]['timestamp']
        # if len(r) == 1000 and prev != ndt:
        if prev != ndt:
            self._get_readings(ndt, records, dt)

    def _get_records_from_file(self, p):
        with open(p, 'r') as rfile:
            header = next(rfile).strip().split(',')

            def factory(row):
                row = row.strip().split(',')
                r = dict(zip(header, row))
                r['timestamp'] = datetime.strptime(r['timestamp'], DT_FMT)

            return [factory(line) for line in rfile]

    def _make_output(self, pid, records):
        with open(os.path.join(self.output_root, '{}.csv'.format(pid)), 'w') as wfile:
            wfile.write('timestamp,temperature_C,temperature_raw,depth\n')
            for r in records:
                keys = ('timestamp_raw', 'temperature_C', 'temperature_raw', 'depth')
                row = ','.join((str(r[k]) for k in keys))
                row = '{}\n'.format(row)
                wfile.write(row)

    def _get_start_datetime_from_db_button_fired(self):
        if self.db:
            dt = self.db.get_last_acoustic_record()
            self.start_datetime = dt.strftime(DT_FMT)
            print('start datetime', self.start_datetime)

    def _get_readings_button_fired(self):
        self.readings()

    def _get_endpoint(self, ep, dt):
        headers = {'accept': 'application/json',
                   'Authorization': 'Key {}'.format(self.api_key)}

        root = 'https://connect.wellntel.com/analytics-api'
        url = '{}/{}?count=1000&start={}&order=ascending'.format(root, ep, dt.strftime(DT_FMT))
        print('fetching from {}'.format(url))
        resp = requests.get(url, headers=headers)

        def toc(t):
            f = t/10.
            c = (f-32)*5/9.
            return c

        if resp.status_code == 200:
            for record in resp.json():
                pid = record['wellname']
                timestamp = record['timestamp']
                temperature = record['temperature']
                wlrecord = {'pointid': POINTID_MAP.get(pid, pid),
                            'timestamp': datetime.strptime(timestamp, DT_FMT),
                            'depth': record['depth'],
                            'temperature_C': toc(temperature),
                            'temperature_raw': temperature,
                            'timestamp_raw': timestamp,
                            }
                yield wlrecord

    def traits_view(self):
        v = View(HGroup(Item('start_datetime'), UItem('get_start_datetime_from_db_button')),
                 UItem('get_readings_button'),
                 resizable=True)
        return v


if __name__ == '__main__':
    clt = WellntelClient()
    clt.api_key = ''
    clt.output_root = 'data'
    clt.configure_traits()
# ============= EOF =============================================
