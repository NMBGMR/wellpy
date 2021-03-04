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
# from pyface.progress_dialog import ProgressDialog
from traits.api import HasTraits, Str, UUID, Float

from wellpy.config import config

testtxt = '''
<?xml version="1.0" encoding="utf-16" standalone="yes"?>
<WaterLevelsContinuous_Pressure_Test>
<row><PointID>TV-121</PointID><DateMeasured>2014-02-07T12:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.53295</WaterHead><WaterHeadAdjusted>6.53295</WaterHeadAdjusted><DepthToWaterBGS>119.957</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:2/7/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-01-25T12:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.33938</WaterHead><WaterHeadAdjusted>6.33938</WaterHeadAdjusted><DepthToWaterBGS>120.1506</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:1/25/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-03-04T12:00:00</DateMeasured><TemperatureWater>12.527</TemperatureWater><WaterHead>6.49905</WaterHead><WaterHeadAdjusted>6.49905</WaterHeadAdjusted><DepthToWaterBGS>119.991</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:3/4/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-12-17T12:00:00</DateMeasured><TemperatureWater>12.547</TemperatureWater><WaterHead>6.35004</WaterHead><WaterHeadAdjusted>6.35004</WaterHeadAdjusted><DepthToWaterBGS>120.14</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:12/17/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-08-08T12:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.22783</WaterHead><WaterHeadAdjusted>6.22783</WaterHeadAdjusted><DepthToWaterBGS>120.2622</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:8/8/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-11-22T12:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.26911</WaterHead><WaterHeadAdjusted>6.26911</WaterHeadAdjusted><DepthToWaterBGS>120.2209</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:11/22/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-12-01T12:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.15128</WaterHead><WaterHeadAdjusted>6.15128</WaterHeadAdjusted><DepthToWaterBGS>120.3387</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:12/1/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-11-18T00:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.13788</WaterHead><WaterHeadAdjusted>6.13788</WaterHeadAdjusted><DepthToWaterBGS>120.3521</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:11/18/2014 12:00:00 AM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-04-04T12:00:00</DateMeasured><TemperatureWater>12.547</TemperatureWater><WaterHead>6.35496</WaterHead><WaterHeadAdjusted>6.35496</WaterHeadAdjusted><DepthToWaterBGS>120.135</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:4/4/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-09-18T12:00:00</DateMeasured><TemperatureWater>12.547</TemperatureWater><WaterHead>6.15866</WaterHead><WaterHeadAdjusted>6.15866</WaterHeadAdjusted><DepthToWaterBGS>120.3313</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:9/18/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-01-09T00:00:00</DateMeasured><TemperatureWater>12.54</TemperatureWater><WaterHead>6.54006</WaterHead><WaterHeadAdjusted>6.54006</WaterHeadAdjusted><DepthToWaterBGS>119.9499</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:1/9/2014 12:00:00 AM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-07-29T00:00:00</DateMeasured><TemperatureWater>12.533</TemperatureWater><WaterHead>6.1726</WaterHead><WaterHeadAdjusted>6.1726</WaterHeadAdjusted><DepthToWaterBGS>120.3174</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:7/29/2014 12:00:00 AM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-12-27T12:00:00</DateMeasured><TemperatureWater>12.56</TemperatureWater><WaterHead>6.27349</WaterHead><WaterHeadAdjusted>6.27349</WaterHeadAdjusted><DepthToWaterBGS>120.2165</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:12/27/2014 12:00:00 PM </Notes></row>
<row><PointID>TV-121</PointID><DateMeasured>2014-09-06T00:00:00</DateMeasured><TemperatureWater>12.547</TemperatureWater><WaterHead>6.05887</WaterHead><WaterHeadAdjusted>6.05887</WaterHeadAdjusted><DepthToWaterBGS>120.4311</DepthToWaterBGS><Notes>my note on pointID: TV-121, dteMeasured:9/6/2014 12:00:00 AM </Notes></row>
</WaterLevelsContinuous_Pressure_Test>
'''


class MockConnection:
    def cursor(self):
        return MockCursor()

    def close(self):
        pass

    def commit(self):
        pass


class MockCursor:
    def execute(self, *args, **kw):
        pass

    def fetchall(self):
        return []

    def fetchone(self):
        pass


def get_connection(h, u, p, n, *args, **kw):
    try:
        conn = pymssql.connect(h, u, p, n, timeout=15, login_timeout=5, *args, **kw)
    except (pymssql.InterfaceError, pymssql.OperationalError):
        conn = MockConnection()

    return conn


class SessionCTX:
    def __init__(self, h, u, p, n, *args, **kw):
        conn = get_connection(h, u, p, n, *args, **kw)
        self._conn = conn

    def __enter__(self):
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.commit()
        self._conn.close()


class PointIDRecord(HasTraits):
    name = Str
    install_date = None
    serial_num = Str

    def __init__(self, name, install_date=None, serial_num=None):
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
        # self.level_status = level_status

        measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d')
        t = measurement_date.timetuple()
        try:
            timestamp = time.mktime(t)
        except (OverflowError, ValueError):
            timestamp = 0

        self.measurement = (timestamp, depth, level_status)


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
            return sorted([PointIDRecord(*r) for r in cursor.fetchall()], key=lambda x: x.name)

    def get_point_ids_simple(self):
        with self._get_cursor() as cursor:
            cmd = '''SELECT DISTINCT PointID FROM dbo.Equipment
            WHERE PointID IS NOT NULL
            AND (EquipmentType = 'Pressure transducer' or EquipmentType='Acoustic sounder')  
            ORDER BY[PointID]'''

            cursor.execute(cmd)

            return [PointIDRecord(*r) for r in cursor.fetchall()]

    def get_qc_point_ids(self, qced=False):
        with self._get_cursor() as cursor:
            cursor.execute('GetPointIDsQCdPython %d', (int(qced),))
            return sorted([PointIDRecord(*r) for r in cursor.fetchall()], key=lambda x: x.name)

    def get_depth_to_water(self, point_id):
        with self._get_cursor() as cursor:
            cursor.execute('GetWaterLevelsPython %s', (point_id.upper(),))
            return [WaterDepthRecord(*r) for r in cursor.fetchall()]

    def get_schema(self):
        """
       
        :return: 
        """
        with self._get_cursor() as cursor:
            cursor.execute('GetWLCPressureXSDSchema')
            schematxt = cursor.fetchone()[0]

            xmlschema_doc = etree.XML(str(schematxt))

            print '-----------------'
            print etree.tostring(xmlschema_doc, pretty_print=True)
            print '-----------------'

            schema = etree.XMLSchema(xmlschema_doc)
            return schema

    def apply_qc(self, pointid, limits, state=True):
        mi, ma = limits
        mi = datetime.fromtimestamp(mi).strftime('%m/%d/%Y %I:%M:%S %p')
        ma = datetime.fromtimestamp(ma).strftime('%m/%d/%Y %I:%M:%S %p')

        with self._get_cursor() as cursor:
            cmd = 'Update dbo.WaterLevelsContinuous_Pressure ' \
                  'Set QCed=%d ' \
                  'Where DateMeasured>=%s and DateMeasured<=%s and PointID=%s'
            args = (int(state), mi, ma, pointid)
            cursor.execute(cmd, args)

    def get_wellid(self, pointid, cursor=None):
        if cursor is None:
            conn = self._get_connection()
            cursor = conn.cursor()
        # retrieve wellid
        cmd = '''Select WellID from dbo.WellData where PointID=%s'''
        print(pointid)
        cursor.execute(cmd, pointid)
        try:
            return cursor.fetchone()[0]
        except TypeError:
            # this "pointid" not in database
            print('PointID={} not in WellData. cannot get WellID')

    def get_last_acoustic_record(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # retrieve wellid
        sql = '''select DateMeasured from WaterLevelsContinuous_Acoustic
        where DataSource='S'
        order by DateMeasured desc 
        '''
        cursor.execute(sql)
        return cursor.fetchone()[0]

    def insert_chunk(self, conn, cursor, rows, cmd, chunker):
        n = len(rows)
        chunk_len = 300
        ntries = 2
        cn = n / chunk_len + 1
        for i in xrange(0, n, chunk_len):
            print 'Insert chunk:  {}/{}'.format(i, n)
            # pd.change_message('Insert chunk:  {}/{}'.format(i, cn))
            # pd.update(i)
            chunk = rows[i:i + chunk_len]

            for j in xrange(ntries):
                try:
                    cursor.executemany(cmd, chunker(chunk))
                except:
                    print 'need to retry', j + 1
                    time.sleep(2)
                    continue

                break
            conn.commit()
        conn.close()

    def insert_wellntel_water_levels(self, pointid, rows):
        conn = self._get_connection()
        cursor = conn.cursor()
        wellid = self.get_wellid(pointid, cursor)
        if wellid:
            cmd = '''INSERT into dbo.WaterLevelsContinuous_Acoustic
                                 (WellID, PointID, 
                                 DateMeasured,TemperatureAir,DepthToWaterBGS,
                                 MeasurementMethod,DataSource,MeasuringAgency)
                                 VALUES (%s, %s,
                                  %s, %s, %s, 
                                  %s, %s, %s)'''

            def chunker(chunk):
                return [(wellid, pointid,
                         row['timestamp'].strftime('%m/%d/%Y %I:%M:%S %p'),
                         float(row['temperature']),
                         float(row['depth']),
                         'K', 'S', 'NMBGMR'
                         ) for row in chunk]

            self.insert_chunk(conn, cursor, rows, cmd, chunker)

    def insert_continuous_water_levels(self, pointid, rows, with_update=False, is_acoustic=False):
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
        user = config.user

        n = len(rows)
        note = 'testnote'

        conn = self._get_connection()
        cursor = conn.cursor()
        wellid = self.get_wellid(pointid, cursor)

        if is_acoustic:
            existing_nresults = len(self.get_acoustic_water_levels(pointid))
            rows = [{'timestamp': r[0], 'temperature': r[1], 'depth': r[2]} for r in rows]
            self.insert_wellntel_water_levels(pointid, rows)
            inserted_nresults = len(self.get_acoustic_water_levels(pointid))
        else:
            existing_nresults = len(self.get_continuous_water_levels(pointid))
            if with_update:
                with self._get_cursor() as cursor:
                    cmd = 'InsertWLCPressurePython_NEW_wUpdate %s, %s, %d, %d, %d, %d, %s'
                    for i, (x, a, ah, bgs, temp) in enumerate(rows):
                        datemeasured = datetime.fromtimestamp(x).strftime('%m/%d/%Y %I:%M:%S %p')
                        args = (pointid, datemeasured, temp, a, ah, bgs, note)
                        cursor.execute(cmd, args)
            else:
                cmd = '''INSERT into dbo.WaterLevelsContinuous_Pressure
                         (PointID, DateMeasured, TemperatureWater, [CONDDL (mS/cm)], WaterHead, 
                           WaterHeadAdjusted, DepthToWaterBGS, Notes, WellID)
                         VALUES (%s, %s, %d, %d, %d, %d, %d, %s, %s)'''

                def chunker(chunk):
                    return [(pointid, datetime.fromtimestamp(x).strftime('%m/%d/%Y %I:%M:%S %p'),
                             temp, cond, a, ah, bgs, note, wellid)
                            for x, a, ah, bgs, temp, cond in chunk]

                self.insert_chunk(conn, cursor, rows, cmd, chunker)
            inserted_nresults = len(self.get_continuous_water_levels(pointid))

        return existing_nresults, inserted_nresults

    def get_acoustic_water_levels(self, point_id):
        with self._get_cursor() as cursor:
            cmd = '''Select * from dbo.WaterLevelsContinuous_Acoustic where PointID=%s'''
            cursor.execute(cmd, point_id)
            return cursor.fetchall()

    def get_continuous_water_levels(self, point_id, low=None, high=None, qced=None):
        with self._get_cursor() as cursor:
            cmd, args = 'GetWLCPressurePython %s', (point_id.upper(),)
            if low or high or qced is not None:
                args = (point_id, low, high, qced)
                cmd = '{}, %s, %s, %d'.format(cmd)
            cursor.execute(cmd, args)
            return cursor.fetchall()

    def _get_cursor(self):
        return SessionCTX(self._host, self._user, self._password, self._dbname)

    def _get_connection(self):
        return get_connection(self._host, self._user, self._password, self._dbname)


if __name__ == '__main__':
    d = DatabaseConnector(bind=False)
    import os

    d._host = os.getenv('NM_AQUIFER_HOST')
    d._user = os.getenv('NM_AQUIFER_USER')
    d._password = os.getenv('NM_AQUIFER_PASSWORD')
    print d._host, d._user, d._password
    d._dbname = 'NM_Aquifer'
    # for pi in d.get_point_ids():
    #     print pi.name, len(d.get_depth_to_water(pi.name)), len(d.get_continuous_water_levels(pi.name))
    name = 'MG-030'
    # print d.get_point_ids()

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

    # d.get_schema()

    # r = d.get_continuous_water_levels(name, low='2014-01-01T00:00:00.000',
    #                                        high='2016-01-01T00:00:00.000',
    #                                        qced=1)
    # print len(r)
# ============= EOF =============================================
# def insert_continuous_water_levels_xml(self, pointid, rows):
    #
    #     schema = self.get_schema()
    #
    #     container = etree.Element('WaterLevelsContinuous_Pressure_Test')
    #     TAGS = 'TemperatureWater', 'WaterHead', 'WaterHeadAdjusted', 'DepthToWaterBGS',
    #     for x, a, ah, bgs, temp in rows[:5]:
    #         elem = etree.Element('row')
    #
    #         pid = etree.Element('PointID')
    #         pid.text = pointid
    #         elem.append(pid)
    #
    #         pid = etree.Element('DateMeasured')
    #         # pid.text = datetime.fromtimestamp(x).strftime('%m/%d/%Y%I:%M:%S %p')
    #         pid.text = datetime.fromtimestamp(x).isoformat()
    #         elem.append(pid)
    #
    #         for tag, v in zip(TAGS, (temp, a, ah, bgs)):
    #             item = etree.Element(tag)
    #             item.text = unicode(v)
    #             elem.append(item)
    #
    #         # print etree.tostring(elem, pretty_print=True)
    #         # schema.assertValid(elem)
    #         # print 'ada',x, schema.validate(elem)
    #         note = etree.Element('Notes')
    #         note.text = 'testnote'
    #         elem.append(note)
    #         container.append(elem)
    #
    #     # container = etree.XML(testtxt)
    #
    #     # xmldata.append(container)
    #     #
    #     # print(etree.tostring(cont, pretty_print=True, xml_declaration=True, standalone='yes'))
    #     # print(etree.tostring(container, pretty_print=True, xml_declaration=True, standalone='yes'))
    #     # schema.assertValid(cont)
    #     schema.assertValid(container)
    #     # if schema.validate(container):
    #
    #     with self._get_cursor() as cursor:
    #
    #         txt = etree.tostring(container,
    #                              encoding='UTF-8',
    #                              xml_declaration=True,
    #                              standalone='yes',
    #                              pretty_print=True
    #                              )
    #         print txt
    #
    #         # cmd, args = 'InsertWLCPressureXMLPython %s', (txt,)
    #         # print testtxt
    #         # cmd, args = 'InsertWLCPressurePython %s', (testtxt,)
    #         cmd, args = 'InsertWLCPressureXMLPython_NEW_wUpdate %s', (txt,)
    #         cursor.execute(cmd, args)
    #         print cursor.fetchall()
    #
    #     results = self.get_continuous_water_levels(pointid)
    #     print 'asdfasdfasdf', len(results)
    #     # else:
    #     #     print 'failed to valid'
