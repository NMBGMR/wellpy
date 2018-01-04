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

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

import yaml

HOME = os.path.expanduser('~')


def write_default(p):
    obj = {'default_data_dir': os.path.expanduser('~')}

    with open(p, 'w') as wfile:
        yaml.dump(obj, wfile, default_flow_style=False)


class Config:
    DEBUG_PATH = '/Users/ross/Programming/github/wellpy/data/AR0209_AztecMW.xlsx'
    DEBUG_PATH = '/Users/ross/Sandbox/wellpydata/1_mg-030_danielson_wel_170118081630_D7259.csv'
    DEBUG = True
    user = 'default'
    _d = None

    def __init__(self):
        root = os.path.join(HOME, '.wellpy')
        if not os.path.isdir(root):
            os.mkdir(root)

        p = self.path
        if not os.path.isfile(p):
            write_default(p)
        self.load()

    @property
    def path(self):
        root = os.path.join(HOME, '.wellpy')
        p = os.path.join(root, 'config.yaml')
        return p

    def load(self):
        with open(self.path, 'r') as rfile:
            self._d = yaml.load(rfile)

    def dump(self):
        with open(self.path, 'w') as wfile:
            yaml.dump(self._d, wfile, default_flow_style=False)

    def set_value(self, key, value):
        self._d[key] = value

    def __getattr__(self, item):
        return self._d.get(item)


config = Config()


# ============= EOF =============================================
