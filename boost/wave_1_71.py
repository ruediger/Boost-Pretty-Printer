# coding: utf-8

########################################
# Wave 1.71
########################################

# Authors: Jeff Trull and Mikhail Balabin

import itertools
import sys
from .utils import *

@add_printer
class BoostWaveFlexString:
    """Pretty Printer for Boost.Wave internal string"""
    printer_name = 'boost::wave::util::flex_string'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::util::flex_string'

    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'string'

    def to_string(self):
        storage_type = self.val.type.template_argument(3)
        storage = self.val.cast(storage_type)
        printer = gdb.default_visualizer(storage)
        if printer is None:
            return storage
        # This will fail for wide strings
        b = bytearray(int(ch) for _, ch in printer.children())
        s = b.decode(encoding=sys.getdefaultencoding(), errors='replace')
        return s


@add_printer
class BoostWaveFilePosition:
    """Pretty Printer for Boost.Wave File Position"""
    printer_name = 'boost::wave::util::file_position'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::util::file_position'

    def __init__(self, val):
        self.val = val

    def to_string(self):
        return "({} {}:{})".format(
            self.val["file"], self.val["line"], self.val["column"])


@add_printer
class BoostWaveToken:
    """Pretty Printer for Boost.Wave CppLexer Token"""
    printer_name = 'boost::wave::cpplexer::lex_token'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::cpplexer::lex_token'

    def __init__(self, val):
        self.val = val

    def to_string(self):
        return "{} : {} {}".format(
            self.val["data"]["id"], self.val["data"]["value"], self.val["data"]["pos"])

#
# internal types, unlikely to be directly printed, that support flex_string
#

@add_printer
class BoostWaveAllocatorStringStorage:
    printer_name = 'boost::wave::util::AllocatorStringStorage'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::util::AllocatorStringStorage'

    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'array'
        
    def children(self):
        data = self.val['pData_'].dereference()

        str_begin = cast_array_to_pointer(data['buffer_'])
        str_end = data['pEnd_']
        str_length = str_end - str_begin
        for idx in range(str_length):
            yield '[{}]'.format(idx), (str_begin + idx).dereference()


@add_printer
class BoostWaveCowString:
    printer_name = 'boost::wave::util::CowString'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::util::CowString'

    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'array'

    def children(self):
        storage_type = self.val.type.template_argument(0)
        storage = reinterpret_cast(self.val['buf_'], storage_type)
        printer = gdb.default_visualizer(storage)       
        if printer is None:
            # Unknown underlying storage
            return
        chars = itertools.islice(printer.children(), 1, None)
        for idx, (_, ch) in enumerate(chars):
            yield '[{}]'.format(idx), ch

#
# utility functions
#

def cast_array_to_pointer(val):
    """Cast array to pointer to the first element"""
    assert val.type.code == gdb.TYPE_CODE_ARRAY
    element_type = val.type.target()
    return val.address.cast(element_type.pointer())

