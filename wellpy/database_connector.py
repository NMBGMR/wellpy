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


class DatabaseConnector:
    _host = ''
    _user = ''
    _dbname = ''
    _password = ''

    def get_point_ids(self):
        with self._get_cursor() as cursor:
            cursor.execute('GetPointIDsPython')
            return [r[0] for r in cursor.fetchall()]

    def get_manual_measurements(self, point_id):
        with self._get_cursor() as cursor:
            pass

    def get_date_range(self, point_id, low, high):
        with self._get_cursor() as cursor:
            pass

    def _get_cursor(self):
        return SessionCTX(self._host, self._user, self._password, self._dbname)


if __name__ == '__main__':
    d = DatabaseConnector()
    import os

    d._host = os.getenv('NM_AQUIFER_HOST')
    d._user = os.getenv('NM_AQUIFER_USER')
    d._password = os.getenv('NM_AQUIFER_PASSWORD')
    d._dbname = 'NM_Aquifer'
    for pi in d.get_point_ids():
        print pi
# ============= EOF =============================================
