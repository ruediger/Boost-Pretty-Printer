from __future__ import print_function
from .utils import *

#
# To specify which index to use for printing for a specific container
# (dynamically, inside gdb), add its address here as key, and the desired
# index as value. E.g.:
#
# (gdb) p &s_5
# $2 = (Int_Set_5 *) 0x7fffffffd770
# (gdb) python import boost.printers
# (gdb) python boost.printers.multi_index_selector[0x7fffffffd770] = 1
# (gdb) p s_5
#
multi_index_selector = dict()
