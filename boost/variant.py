# encoding: utf-8
from __future__ import print_function, absolute_import, division
import gdb
import re
from .utils import *

#
# Boost Variant
#

def strip_qualifiers(typename):
    """Remove const/volatile qualifiers, references, and pointers of a type"""
    qps = []

    try:
        while True:
            typename = typename.rstrip()
            qual = next(q for q in ['&', '*', 'const', 'volatile'] if typename.endswith(q))
            typename = typename[:-len(qual)]
            qps.append(qual)
    except StopIteration:
        pass

    try:
        while True:
            typename = typename.lstrip()
            qual = next(q for q in ['const', 'volatile'] if typename.startswith(q))
            typename = typename[len(qual):]
            qps.append(qual)
    except StopIteration:
        pass

    return typename, qps[::-1]


def apply_qualifiers(t, qs):
    """Apply the given sequence of references, and pointers to a gdb.Type.
       const and volatile qualifiers are not applied cince they do not affect
       printing. Also it is not possible to make a const+volatile qualified
       type in gdb."""
    for q in qs:
        if q == '*':
            t = t.pointer()
        elif q == '&':
            t = t.reference()
        elif q == 'const':
            t = t.const()
    return t


def split_parameter_pack(typename):
    """Split a string represending a comma-separated c++ parameter pack into a list of stings of element types"""
    unmatched = 0
    length = len(typename)
    b = e = 0
    while e < length:
        c = typename[e]
        if c == ',' and unmatched == 0:
            yield typename[b:e].strip()
            b = e = e + 1
        elif c == '<':
            unmatched += 1
        elif c == '>':
            unmatched -= 1
        e += 1
    yield typename[b:e].strip()


@add_printer
class BoostVariant:
    "Pretty Printer for boost::variant (Boost.Variant)"
    printer_name = 'boost::variant'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::variant'
    regex = re.compile('^boost::variant<(.*)>$')

    def __init__(self, value):
        self.value = value

    def to_string(self):
        stored_type, stored_type_name = self.get_variant_type()
        return '(boost::variant<...>) type = {}'.format(stored_type_name)

    def children(self):
        stored_type, stored_type_name = self.get_variant_type()
        stored_value = reinterpret_cast(self.value['storage_']['data_']['buf'], stored_type)
        yield stored_type_name, stored_value

    def get_variant_type(self):
        """Get a gdb.Type of a template argument"""
        type_index = intptr(self.value['which_'])
        assert type_index >= 0, 'Heap backup is not supported'
        
        # This is a workaround for a GDB issue
        # https://sourceware.org/bugzilla/show_bug.cgi?id=17311. 
        # gdb.Type.template_argument() method does not work unless variadic templates
        # are disabled using BOOST_VARIANT_DO_NOT_USE_VARIADIC_TEMPLATES.
        m = BoostVariant.regex.search(self.value.type_name)
        type_names = list(split_parameter_pack(m.group(1)))
        stored_type_name = type_names[type_index]
        base_type_name, qualifiers = strip_qualifiers(stored_type_name)
        return apply_qualifiers(lookup_type(base_type_name), qualifiers), stored_type_name
