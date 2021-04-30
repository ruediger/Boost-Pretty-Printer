# encoding: utf-8
from __future__ import print_function, absolute_import, division
import gdb
from .utils import *

#
# Boost TypeErasure

@add_printer
class BoostTypeErasure:
    "Pretty Printer for boost::type_erasure::any (Boost.TypeErasure)"
    printer_name = 'boost::type_erasure::any'
    min_supported_version = (1, 54, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::type_erasure::any'

    def __init__(self, value):
        self.value = value

    def to_string(self):
        stored_value = self.value['_boost_type_erasure_data']['data']
        return '(boost::type_erasure::any<...> data = {})'.format(stored_value)
