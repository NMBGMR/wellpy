# ===============================================================================
# Copyright 2016 ross
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


class CommitCTX:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        cur = self._conn.cursor()
        return cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.commit()


class NMWellDatabase:
    url = ''
    _connection = None

    def connect(self, host, user, pwd, name, login_timeout=5):
        self.url = '{}@{}/{}'.format(user, host, name)
        print login_timeout
        try:
            self._connection = pymssql.connect(host, user, pwd, name,
                                               login_timeout=login_timeout)
            return True
        except BaseException:
            return False

    def add(self):
        sql = ''
        with CommitCTX(self._connection) as cursor:
            cursor.execute(sql)

# ============= EOF =============================================
