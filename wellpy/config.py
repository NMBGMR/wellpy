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
        yaml.dump(obj, wfile)


class Config:
    def __init__(self):
        root = os.path.join(HOME, '.csvplotter')
        if not os.path.isdir(root):
            os.mkdir(root)

        p = os.path.join(root, 'config.yaml')
        if not os.path.isfile(p) or True:
            write_default(p)

        with open(p, 'r') as rfile:
            self._d = yaml.load(rfile)

    def __getattr__(self, item):
        return self._d.get(item)


config = Config()


# ============= EOF =============================================
