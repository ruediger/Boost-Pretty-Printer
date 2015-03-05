#
# all.py
#
# Import all .py files in the package containing printers.
#

import importlib
import glob
import os

from boost import *

_files = [os.path.basename(_m) for _m in glob.glob(os.path.dirname(__file__) + "/*.py")]
_modules = [_f[:-3] for _f in _files if _f not in non_printer_files]
for _m in _modules:
    importlib.import_module('.' + _m, pkg_name)
