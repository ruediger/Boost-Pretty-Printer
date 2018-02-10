# encoding: utf-8

# Pretty-printers for Boost (http://www.boost.org)

# Copyright (C) 2009 Rüdiger Sonderfeld <ruediger@c-plusplus.de>
# Copyright (C) 2014 Matei David <matei@cs.toronto.edu>

# Boost Software License - Version 1.0 - August 17th, 2003

# Permission is hereby granted, free of charge, to any person or organization
# obtaining a copy of the software and accompanying documentation covered by
# this license (the "Software") to use, reproduce, display, distribute,
# execute, and transmit the Software, and to prepare derivative works of the
# Software, and to permit third-parties to whom the Software is furnished to
# do so, all subject to the following:

# The copyright notices in the Software and this entire statement, including
# the above license grant, this restriction and the following disclaimer,
# must be included in all copies of the Software, in whole or in part, and
# all derivative works of the Software, unless such copies or derivative
# works are solely in the form of machine-executable object code generated by
# a source language processor.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

#
# Inspired _but not copied_ from libstdc++'s pretty printers
#

from __future__ import print_function
import re
from .utils import *


#
# Individual Printers follow.
#
# Relevant fields:
#
# - 'printer_name' : Subprinter name used by gdb. (Required.) If it contains
# regex operators, they must be escaped when refering to it from gdb.
# - 'min_supported_version' and 'max_supported_version' : 3-tuples containing min
# and max versions of boost supported by the printer. Required.
# - 'supports(GDB_Value_Wrapper)' classmethod : If it exists, it is used to
# determine if the Printer supports the given object.
# - 'template_name' : string or list of strings. Only objects with this
# template name will attempt to use this printer.
# (Either supports() or template_name is required.)
# - '__init__' : Its only argument is a GDB_Value_Wrapper.
#

@add_printer
class BoostIteratorRange:
    "Pretty Printer for boost::iterator_range (Boost.Range)"
    printer_name = 'boost::iterator_range'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::iterator_range'

    class _iterator:
        def __init__(self, begin, end):
            self.item = begin
            self.end = end
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.item == self.end:
                raise StopIteration
            count = self.count
            self.count = self.count + 1
            elem = self.item.dereference()
            self.item = self.item + 1
            return ('[%d]' % count, elem)

        def next(self):
            return self.__next__()

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def children(self):
        return self._iterator(self.value['m_Begin'], self.value['m_End'])

    def to_string(self):
        begin = self.value['m_Begin']
        end = self.value['m_End']
        return '%s of length %d' % (self.typename, int(end - begin))

    def display_hint(self):
        return 'array'


@add_printer
class BoostOptional:
    "Pretty Printer for boost::optional (Boost.Optional)"
    printer_name = 'boost::optional'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::optional'

    def __init__(self, value):
        self.value = value

    def children(self):
        initialized = self.value['m_initialized']
        if initialized:
            stored_type = get_basic_type(self.value.basic_type.template_argument(0))
            m_storage = self.value['m_storage']
            stored_value = m_storage \
                if get_basic_type(m_storage.type) == stored_type \
                else reinterpret_cast(m_storage['dummy_']['data'], stored_type)
            yield 'value', stored_value

    def to_string(self):
        initialized = self.value['m_initialized']
        if initialized:
            return '{} is initialized'.format(self.value.type_name)
        else:
            return '{} is not initialized'.format(self.value.type_name)


@add_printer
class BoostReferenceWrapper:
    "Pretty Printer for boost::reference_wrapper (Boost.Ref)"
    printer_name = 'boost::reference_wrapper'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::reference_wrapper'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        return '(%s) %s' % (self.typename, self.value['t_'].dereference())


@add_printer
class BoostTribool:
    "Pretty Printer for boost::logic::tribool (Boost.Tribool)"
    printer_name = 'boost::logic::tribool'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::logic::tribool'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        state = self.value['value']
        s = 'indeterminate'
        if(state == 0):
            s = 'false'
        elif(state == 1):
            s = 'true'
        return '(%s) %s' % (self.typename, s)


@add_printer
class BoostScopedPtr:
    "Pretty Printer for boost::scoped_ptr and boost::intrusive_ptr (Boost.SmartPtr)"
    printer_name = 'boost::scoped/intrusive_ptr'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = ['boost::intrusive_ptr', 'boost::scoped_ptr']

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return 'uninitialized' if self.value['px'] == 0 else str(self.value['px'])

    def children(self):
        if self.value['px'] != 0:
            yield 'value', self.value['px'].dereference()


@add_printer
class BoostScopedArray:
    "Pretty Printer for boost::scoped_array (Boost.SmartPtr)"
    printer_name = 'boost::scoped_array'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = ['boost::scoped_array']

    def __init__(self, value):
        self.value = value

    def to_string(self):
        # Array elements can not be displayed because size of the array is not known
        return 'uninitialized' if self.value['px'] == 0 else 'array start {}'.format(self.value['px'])


def read_atomic_counter(counter):
    """Read atomic counter used in control blocks of boost::shared_ptr and boost::shared_array"""
    # If std library is not libstdc++ or implementation of std::atomic changes, this method will break.
    # Unfortunately, libstdc++ does not provide a printer for std::atomic.
    type = get_basic_type(counter.type)
    if type.code == gdb.TYPE_CODE_INT:
        return int(counter)
    if type.code == gdb.TYPE_CODE_STRUCT and gdb.types.has_field(type, '_M_i'):
        return int(counter['_M_i'])
    return '?'


@add_printer
class BoostSharedPtr:
    """Pretty Printer for boost::shared_ptr and boost::weak_ptr (Boost.SmartPtr)"""
    printer_name = 'boost::shared/weak_ptr'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = ['boost::shared_ptr', 'boost::weak_ptr']

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        if self.value['px'] == 0x0:
            return 'uninitialized'
        countobj = self.value['pn']['pi_'].dereference()
        refcount = read_atomic_counter(countobj['use_count_'])
        weakcount = read_atomic_counter(countobj['weak_count_'])
        return 'count {}, weak count {}'.format(refcount, weakcount)

    def children(self):
        if self.value['px'] != 0:
            yield 'value', self.value['px'].dereference()


@add_printer
class BoostSharedArray:
    """Pretty Printer for boost::shared_array and boost::weak_array (Boost.SmartPtr)"""
    printer_name = 'boost::shared/weak_array'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = ['boost::shared_array', 'boost::weak_array']

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        if self.value['px'] == 0x0:
            return 'uninitialized'

        # Array elements can not be displayed because size of the array is not known
        countobj = self.value['pn']['pi_'].dereference()
        refcount = read_atomic_counter(countobj['use_count_'])
        weakcount = read_atomic_counter(countobj['weak_count_'])
        return 'count {}, weak count {}, array start {}'.format(refcount, weakcount, self.value['px'])


@add_printer
class BoostCircular:
    "Pretty Printer for boost::circular_buffer (Boost.Circular)"
    printer_name = 'boost::circular_buffer'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::circular_buffer'

    class _iterator:
        def __init__(self, first, last, buff, end, size):
            self.item = first  # virtual beginning of the circular buffer
            self.last = last   # virtual end of the circular buffer (one behind the last element).
            self.buff = buff   # internal buffer used for storing elements in the circular buffer
            self.end = end     # internal buffer's end (end of the storage space).
            self.size = size
            self.capa = int(end - buff)
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.count == self.size:
                raise StopIteration
            count = self.count
            crt = self.buff + (count + self.item - self.buff) % self.capa
            elem = crt.dereference()
            self.count = self.count + 1
            return ('[%d]' % count, elem)

        def next(self):
            return self.__next__()

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def children(self):
        return self._iterator(self.value['m_first'],
                              self.value['m_last'],
                              self.value['m_buff'],
                              self.value['m_end'],
                              self.value['m_size'])

    def to_string(self):
        buff = self.value['m_buff']
        end = self.value['m_end']
        size = self.value['m_size']
        return '%s of length %d/%d' % (self.typename, int(size), int(end - buff))

    def display_hint(self):
        return 'array'


@add_printer
class BoostArray:
    "Pretty Printer for boost::array (Boost.Array)"
    printer_name = 'boost::array'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::array'

    def __init__(self, value):
        self.value = value
        self.size = int(value.type.template_argument(1))

    def to_string(self):
        return None

    def children(self):
        for idx in range(self.size):
            yield '[{}]'.format(idx), self.value['elems'][idx]

    def display_hint(self):
        return 'array'
 

@add_printer
class BoostUuid:
    "Pretty Printer for boost::uuids::uuid (Boost.Uuid)"
    printer_name = 'boost::uuids::uuid'
    min_supported_version = (1, 42, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::uuids::uuid'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        u = (int(self.value['data'][i]) for i in xrange(16))
        s = 'xxxx-xx-xx-xx-xxxxxx'.replace('x', '%02x') % tuple(u)
        return '(%s) %s' % (self.typename, s)
