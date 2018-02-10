#
# Boost Variant
#

from .utils import *

def strip_qualifiers(typename):
    """remove const/volatile qualifiers, references, and pointers of a type"""

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
    """apply the given sequence of const/volatile qualifiers, references, and pointers to a gdb.Type"""

    for q in qs:
        if q == '*':
            t = t.pointer()
        elif q == '&':
            t = t.reference()
        elif q == 'const':
            t = t.const()
        elif q == 'volatile':
            t = t.volatile()
    return t


def split_parameter_pack(typename):
    """
    Split a string represending a comma-separated c++ parameter pack
    into a list of stings of element types.
    This is a workaround to issues likely related to
    https://sourceware.org/bugzilla/show_bug.cgi?id=17311.
    """

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
        self.typename = value.type_name
        self.value = value
        # Due to some mysterious reason, self.value.type.template_name(which) does not work unless variadic templates
        # are disabled using BOOST_VARIANT_DO_NOT_USE_VARIADIC_TEMPLATES.
        # It might be https://sourceware.org/bugzilla/show_bug.cgi?id=17311
        m = BoostVariant.regex.search(self.typename)
        self.types = list(split_parameter_pack(m.group(1)))

    def to_string(self):
        which = intptr(self.value['which_'])
        assert which >= 0, 'Heap backup is not supported'
        type = self.types[which]
        return '(boost::variant<...>) type = {}'.format(type)

    def children(self):
        which = intptr(self.value['which_'])
        assert which >= 0, 'Heap backup is not supported'
        type,qps = strip_qualifiers(self.types[which])
        ptrtype = apply_qualifiers(lookup_type(type), qps).pointer()
        dataptr = self.value['storage_']['data_']['buf'].address.cast(ptrtype)
        yield str(type), dataptr.dereference()

