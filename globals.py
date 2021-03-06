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
import os

DATABSE_DEBUG = os.environ.get('DATABASE_DEBUG')
FILE_DEBUG = os.environ.get('FILE_DEBUG')
# FILE_DEBUUG = None
QC_DEBUG = os.environ.get('QC_DEBUG')
DEBUG = os.environ.get('DEBUG')

DEBUG = True if DEBUG == '1' else False
# ============= EOF =============================================
