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
import pymssql
import time

from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Str, UUID, Float


class MockConnection:
    def cursor(self):
        return MockCursor()

    def close(self):
        pass


class MockCursor:
    def execute(self, *args, **kw):
        pass

    def fetchall(self):
        return []

    def fetchone(self):
        pass


class SessionCTX:
    def __init__(self, h, u, p, n, *args, **kw):
        try:
            conn = pymssql.connect(h, u, p, n, *args, **kw)
        except pymssql.InterfaceError:
            conn = MockConnection()
            pass

        self._conn = conn

    def __enter__(self):
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()


class PointIDRecord(HasTraits):
    name = Str
    install_date = None
    serial_num = Str

    def __init__(self, name, install_date, serial_num):
        self.name = name
        self.install_date = install_date
        self.serial_num = serial_num or ''


class WaterDepthRecord(HasTraits):
    uuid = Str
    point_id = Str
    # measurement_date = None
    level_status = None
    # depth = Float

    def __init__(self, uuid, point_id, measurement_date, depth, level_status, *args, **kw):
        super(WaterDepthRecord, self).__init__(*args, **kw)
        # self.depth = depth
        self.uuid = str(uuid)
        self.point_id = point_id
        # self.measurement_date = measurement_date
        self.level_status = level_status
        print measurement_date, depth
        self.measurement = (time.mktime(measurement_date.timetuple()), depth)


class DatabaseConnector(HasTraits):
    _host = Str
    _user = Str
    _dbname = Str
    _password = Str

    def __init__(self, bind=True, *args, **kw):
        super(DatabaseConnector, self).__init__(*args, **kw)

        pref_id = 'wellpy.database'
        if bind:
            bind_preference(self, '_host', '{}.host'.format(pref_id))
            bind_preference(self, '_user', '{}.username'.format(pref_id))
            bind_preference(self, '_password', '{}.password'.format(pref_id))
            bind_preference(self, '_dbname', '{}.name'.format(pref_id))

    def get_point_ids(self):
        with self._get_cursor() as cursor:
            cursor.execute('GetPointIDsPython')
            return [PointIDRecord(*r) for r in cursor.fetchall()]

    def get_depth_to_water(self, point_id):
        with self._get_cursor() as cursor:
            cursor.execute('GetWaterLevelsPython %s', (point_id,))
            return [WaterDepthRecord(*r) for r in cursor.fetchall()]

    def get_continuous_water_levels(self, point_id, low=None, high=None, qced=None):
        with self._get_cursor() as cursor:
            cmd, args = 'GetWaterLevelsContinuousPython %s', (point_id,)

            if low or high or qced is not None:
                args = (point_id, low, high, qced)
                cmd = '{}, %s, %s, %d'.format(cmd)
            print '-------------', cmd, args
            cursor.execute(cmd, args)
            return cursor.fetchall()

    def _get_cursor(self):
        return SessionCTX(self._host, self._user, self._password, self._dbname)


if __name__ == '__main__':
    d = DatabaseConnector()
    import os

    d._host = os.getenv('NM_AQUIFER_HOST')
    d._user = os.getenv('NM_AQUIFER_USER')
    d._password = os.getenv('NM_AQUIFER_PASSWORD')
    d._dbname = 'NM_Aquifer'
    # for pi in d.get_point_ids():
    #     print pi.name, len(d.get_depth_to_water(pi.name)), len(d.get_continuous_water_levels(pi.name))
    name = 'TV-121'
    print d.get_point_ids()

    # print name, len(d.get_depth_to_water(name)), len(d.get_continuous_water_levels(name))
    # for p in d.get_continuous_water_levels(name, low='2016-01-01T00:00:00.000',
    #                                        high='2016-01-01T00:00:00.000',
    #                                        qced=1)[:10]:
    #     print p
    r = d.get_continuous_water_levels(name, qced=None)
    print 'qced=None', len(r)

    r = d.get_continuous_water_levels(name, qced=1)
    print 'qced=1',len(r)

    r = d.get_continuous_water_levels(name, qced=0)
    print 'qced=0',len(r)

    # r = d.get_continuous_water_levels(name, low='2014-01-01T00:00:00.000',
    #                                        high='2016-01-01T00:00:00.000',
    #                                        qced=1)
    # print len(r)
# ============= EOF =============================================
