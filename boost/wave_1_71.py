# coding: utf-8

########################################
# Wave 1.71
########################################

# Authors: Jeff Trull and Mikhail Balabin

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
        return storage

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
class BoostWaveCowString:
    printer_name = 'boost::wave::util::CowString'
    min_supported_version = (1, 71, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::wave::util::CowString'

    def __init__(self, val):
        self.val = val

    def display_hint(self):
        return 'string'

    def to_string(self):
        # following c_str() implementation
        # cast internal buffer to first template argument
        storage_type = self.val.type.template_argument(0)
        buf = cast_array_to_pointer(self.val['buf_'])
        storage_ptr = buf.cast(storage_type.pointer())
        # emulate Data().c_str() + 1
        (rstart, rend) = get_char_range(storage_ptr.dereference())
        if rstart == rend:
            return '<Invalid String>'
        return (rstart + 1).string(length = (rend - rstart - 1))

#
# utility functions
#

def cast_array_to_pointer(val):
    """Cast array to pointer to the first element"""
    assert val.type.code == gdb.TYPE_CODE_ARRAY
    element_type = val.type.target()
    return val.address.cast(element_type.pointer())

# AllocatorStringStorage::c_str() is more of a "get memory data"
# method than a string extractor - # plus it has side effects.
# This returns a range as a pair of pointers, instead.
def get_char_range(val):
    """Extract byte array from storage type"""
    assert template_name(val.type) in [
        'boost::wave::util::AllocatorStringStorage'
    ]
    data = val['pData_'].dereference()
    str_begin = cast_array_to_pointer(data['buffer_'])
    str_end = data['pEnd_']
    return (str_begin, str_end)
