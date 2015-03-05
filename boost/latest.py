#
# latest.py
#
# Import only the latest printers.
#

import importlib

from boost import *

_modules = [_f[:-3] for _f in latest_printer_files]
for _m in _modules:
    importlib.import_module('.' + _m, pkg_name)
