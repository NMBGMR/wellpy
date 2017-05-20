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
from StringIO import StringIO
from pprint import pprint

from datetime import datetime
from lxml import etree

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
            conn = pymssql.connect(h, u, p, n, login_timeout=5, *args, **kw)
        except (pymssql.InterfaceError, pymssql.OperationalError):
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

    def get_schema(self):
        """
       
        :return: 
        """
        with self._get_cursor() as cursor:
            cursor.execute('GetWLCPressureXSDSchema')
            schematxt = cursor.fetchone()[0]

            xmlschema_doc = etree.XML(bytes(schematxt))

            print '-----------------'
            print etree.tostring(xmlschema_doc, pretty_print=True)
            print '-----------------'

            schema = etree.XMLSchema(xmlschema_doc)
            return schema

    def insert_continuous_water_levels(self, pointid, rows):
        """
        InsertWLCPressurePython
        @PointID nvarchar(50),
        @DateMeasured datetime,
        @TemperatureWater real,
        @WaterHead real,
        @WaterHeadAdjusted real,
        @DepthToWaterBGS real,
        @notes nvarchar(100)

        :param pointid:
        :param rows:
        :return:
        """

        with self._get_cursor() as cursor:
            cmd = 'InsertWLCPressurePython %s'
            note = 'testnote'
            for x, a, ah, bgs, temp in rows:
                datemeasured = datetime.fromtimestamp(x).strftime('%m/%d/%Y %I:%M:%S %p')
                args = (pointid, datemeasured, temp, a, ah, bgs, note)
                cursor.execute(cmd, args)

        results = self.get_continuous_water_levels(pointid)
        print 'asdfasdfasdf', len(results)

    def insert_continuous_water_levels_xml(self, pointid, rows):

        # schema = self.get_schema()

        container = etree.Element('WaterLevelsContinuous_Pressure_Test')
        TAGS = 'TemperatureWater', 'WaterHead', 'WaterHeadAdjusted', 'DepthToWaterBGS',
        for x, a, ah, bgs, temp in rows[:5]:
            elem = etree.Element('row')

            pid = etree.Element('PointID')
            pid.text = pointid
            elem.append(pid)

            pid = etree.Element('DateMeasured')
            pid.text = datetime.fromtimestamp(x).strftime('%m/%d/%Y %I:%M:%S %p')
            # pid.text = datetime.fromtimestamp(x).isoformat()
            elem.append(pid)

            for tag, v in zip(TAGS, (temp, a, ah, bgs)):
                item = etree.Element(tag)
                item.text = unicode(v)
                elem.append(item)

            # print etree.tostring(elem, pretty_print=True)
            # schema.assertValid(elem)
            # print 'ada',x, schema.validate(elem)
            note = etree.Element('Notes')
            note.text = 'testnote'
            elem.append(note)
            container.append(elem)

        # xmldata.append(container)
        #
        # print(etree.tostring(cont, pretty_print=True, xml_declaration=True, standalone='yes'))
        # print(etree.tostring(container, pretty_print=True, xml_declaration=True, standalone='yes'))
        # schema.assertValid(cont)
        # schema.assertValid(container)
        # if schema.validate(container):

        with self._get_cursor() as cursor:

            txt = etree.tostring(container,
                                 # encoding='UTF-16',
                                 xml_declaration=True,
                                 standalone='yes',
                                 # pretty_print=True
                                 )
            # print txt

            # cmd, args = 'InsertWLCPressureXMLPython %s', (txt,)
            # cmd, args = 'InsertWLCPressureXMLPython %s', (txt,)
            cmd, args = 'InsertWLCPressureXMLPython_NEW_wUpdate %s', (txt,)
            cursor.execute(cmd, args)
            print cursor.fetchall()

        results = self.get_continuous_water_levels(pointid)
        print 'asdfasdfasdf', len(results)
        # else:
        #     print 'failed to valid'

    def get_continuous_water_levels(self, point_id, low=None, high=None, qced=None):
        with self._get_cursor() as cursor:
            cmd, args = 'GetWLCPressurePython %s', (point_id,)
            # cmd, args = 'GetWaterLevelsContinuousAcousticPython %s', (point_id,)

            if low or high or qced is not None:
                args = (point_id, low, high, qced)
                cmd = '{}, %s, %s, %d'.format(cmd)
            print '-------------', cmd, args
            cursor.execute(cmd, args)
            return cursor.fetchall()

    def _get_cursor(self):
        return SessionCTX(self._host, self._user, self._password, self._dbname)


if __name__ == '__main__':
    d = DatabaseConnector(bind=False)
    import os

    d._host = os.getenv('NM_AQUIFER_HOST')
    d._user = os.getenv('NM_AQUIFER_USER')
    d._password = os.getenv('NM_AQUIFER_PASSWORD')
    d._dbname = 'NM_Aquifer'
    # for pi in d.get_point_ids():
    #     print pi.name, len(d.get_depth_to_water(pi.name)), len(d.get_continuous_water_levels(pi.name))
    name = 'MG-030'
    print d.get_point_ids()

    # print name, len(d.get_depth_to_water(name)), len(d.get_continuous_water_levels(name))
    # for p in d.get_continuous_water_levels(name, low='2016-01-01T00:00:00.000',
    #                                        high='2016-01-01T00:00:00.000',
    #                                        qced=1)[:10]:
    #     print p
    r = d.get_continuous_water_levels(name, qced=None)
    print 'qced=None', len(r)

    r = d.get_continuous_water_levels(name, qced=1)
    print 'qced=1', len(r)

    r = d.get_continuous_water_levels(name, qced=0)
    print 'qced=0', len(r)

    d.get_schema()

    # r = d.get_continuous_water_levels(name, low='2014-01-01T00:00:00.000',
    #                                        high='2016-01-01T00:00:00.000',
    #                                        qced=1)
    # print len(r)
# ============= EOF =============================================
