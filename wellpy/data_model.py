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
import os

import time

from datetime import datetime
from numpy import empty, polyfit, polyval, array
from openpyxl import load_workbook


class Channel:
    identification = None
    reference_level = None
    value_range = None


class DataModel:
    def __init__(self, path):
        self._path = path
        if os.path.isfile(path):
            self._load(path)

    def apply_linear(self, attr, s, e, mask):
        v = getattr(self, attr)
        ys = v[mask]
        xs = self.x[mask]

        fxs = (xs[0], xs[-1])
        fys = (ys[0], ys[-1])
        coeffs = polyfit(fxs, fys, 1)
        v[mask] = polyval(coeffs, xs)

    def apply_offset(self, attr, offset, mask):
        v = getattr(self, attr)
        v[mask] += offset

    def _load(self, p):
        if p.endswith('.csv'):
            self._load_csv(p)
        else:
            self._load_xls(p)

    def _load_csv(self, p):
        delimiter = ','
        x = []
        ws = []
        with open(p, 'r') as rfile:
            for i, line in enumerate(rfile):
                if i < 53:
                    continue
                line = line.strip()
                try:
                    date, water_head, temp = line.split(delimiter)
                except ValueError:
                    if line.startswith('END OF DATA'):
                        break
                    continue

                try:
                    water_head = float(water_head)
                except TypeError:
                    continue

                date = datetime.strptime(date, '%Y/%m/%d %H:%M:%S')
                x.append(time.mktime(date.timetuple()))
                ws.append(water_head)

        self.x = array(x)

        ws = array(ws)
        self.water_head = ws
        self.adjusted_water_head = ws[:]

    def _load_xls(self, p):
        wb = load_workbook(p, data_only=True)
        sheet = wb[wb.sheetnames[0]]

        # set_location(data, sheet)
        def extract_cell_value(idx):
            rv = sheet[idx].value
            v = rv.split('=')[1]
            return v

        for attr, idx, func in (('location', 'A16', None),
                                ('sample_period', 'A17', None),
                                ('sample_method', 'A18', None)):
            v = extract_cell_value(idx)
            if func:
                v = func(v)
            setattr(self, attr, v)

        # read in channels
        # right now just hard code in two channels

        ch1 = Channel()
        ch1.identification = extract_cell_value('A21')
        ch1.reference_level = extract_cell_value('A22')
        ch1.value_range = extract_cell_value('A23')

        ch2 = Channel()
        ch2.identification = extract_cell_value('A27')
        ch2.reference_level = extract_cell_value('A28')
        ch2.value_range = extract_cell_value('A29')

        self.channels = (ch1, ch2)

        # load the time series
        n = sheet.max_row - 52
        x = empty(n)
        t = empty(n)
        wh = empty(n)
        awh = empty(n)
        wle = empty(n)

        arrs = (x, t, wh, awh, wle)
        for i, row in enumerate(sheet.iter_rows(min_row=53)):
            for j, arr in enumerate(arrs):
                v = row[j].value
                if j == 0:
                    v = time.mktime(v.timetuple())
                arr[i] = v

        self.x = x
        self.temp = t
        self.water_head = wh
        self.adjusted_water_head = awh
        self.water_level_elevation = wle

# ============= EOF =============================================
