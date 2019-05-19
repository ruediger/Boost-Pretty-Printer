from __future__ import print_function

import gdb
import gdb.types
import gdb.printing
from gdb import lookup_type
import sys
import collections

from .detect_version import detect_boost_version

#
# Indicators for python2 and python3
#
have_python_2 = (sys.version_info[0] == 2)
have_python_3 = (sys.version_info[0] == 3)

#
# Workarounds
#
if have_python_3:
    xrange = range
    intptr = int
elif have_python_2:
    intptr = long

#
# Replacement for switch statement.
#
class switch(object):
    """
    Replacement for switch statement.
    http://code.activestate.com/recipes/410692/
    """
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:
            self.fall = True
            return True
        else:
            return False

#
# Rudimentary logging facility.
#
def message(s):
    """
    Print string argument to stderr, prefixed by the package name. Ok for both Py2 & Py3.
    """
    print('*** boost printers: ' + s, file=sys.stderr)

#
# Print long error message only once.
#
class _Long_Message(object):
    counts = dict()
def long_message(tag, msg):
    if tag not in _Long_Message.counts:
        _Long_Message.counts[tag] = 1
        message(msg)

#
# get_basic_type(): imported from gdb.types, or workaround from libstdcxx
#
try:
    from gdb.types import get_basic_type
except ImportError:
    # from libstdcxx printers
    def get_basic_type(type):
        # If it points to a reference, get the reference.
        if type.code == gdb.TYPE_CODE_REF:
            type = type.target()
        # Get the unqualified type, stripped of typedefs.
        type = type.unqualified().strip_typedefs()
        return type

#
# parse_and_eval(): imported from gdb, or workaround
#
try:
    from gdb import parse_and_eval
except ImportError:
    # from http://stackoverflow.com/a/2290941/717706
    def parse_and_eval(exp):
        if gdb.VERSION.startswith("6.8.50.2009"):
            return gdb.parse_and_eval(exp)
        # Work around non-existing gdb.parse_and_eval as in released 7.0
        gdb.execute("set logging redirect on")
        gdb.execute("set logging on")
        gdb.execute("print %s" % exp)
        gdb.execute("set logging off")
        return gdb.history(0)


def get_type_qualifiers(t):
    """
    Get string containing the qualifiers of a gdb.Type: const, volatile, and reference.
    """
    assert isinstance(t, gdb.Type)
    t = t.strip_typedefs()
    qualifiers = ''
    if t.code == gdb.TYPE_CODE_REF:
        qualifiers = '&' + qualifiers
        t = t.target()
    if t == t.unqualified():
        pass
    elif t == t.unqualified().const():
        qualifiers = 'c' + qualifiers
    elif t == t.unqualified().volatile():
        qualifiers = 'v' + qualifiers
    elif t == t.unqualified().const().volatile():
        qualifiers = 'cv' + qualifiers
    else:
        assert False, 'could not determine type qualifiers'
    return qualifiers


def template_name(t):
    """
    Get template name of gdb.Type. Only for struct/union/enum.
    """
    assert isinstance(t, gdb.Type)
    bt = get_basic_type(t)
    if bt.code in [gdb.TYPE_CODE_STRUCT, gdb.TYPE_CODE_UNION, gdb.TYPE_CODE_ENUM]:
        return str(bt).split('<')[0]
    else:
        return ''


class _aux_save_value_as_variable(gdb.Function):
    def __init__(self, v):
        super(_aux_save_value_as_variable, self).__init__('_aux_save_value_as_variable')
        self.value = v

    def invoke(self):
        return self.value


def save_value_as_variable(v, s):
    """
    Save gdb.Value `v` as gdb variable `s`.
    """
    assert isinstance(v, gdb.Value)
    assert isinstance(s, str)
    _aux_save_value_as_variable(v)
    gdb.execute('set var ' + s + ' = $_aux_save_value_as_variable()', False, True)


def to_eval(val, var_name=None):
    """
    Return string that, when evaluated, returns the given gdb.Value.

    If <val> has an adddress, the string returned will be of the form:
    "(*(<val.type> *)(<val.address>))".

    If <val> has no address, it is first saved as variable <var_name>,
    then the string returned is "<var_name>".
    """
    assert isinstance(val, gdb.Value)
    if val.address:
        return '(*(' + str(val.type) + ' *)(' + hex(intptr(val.address)) + '))'
    else:
        assert isinstance(var_name, str)
        save_value_as_variable(val, var_name)
        return var_name


object_method = dict()


def call_object_method(v, f, *args):
    """
    Apply method `f` to object `v`, with arguments `args`.
    """
    assert isinstance(v, gdb.Value)
    assert isinstance(f, str)
    # try the bypass function call first, by type name
    key = str(get_basic_type(v.type)) + '::' + f
    if key in object_method:
        return object_method[key](v, *args)
    # try the bypass function call first, by template name
    key = template_name(v.type) + '::' + f
    if key in object_method:
        return object_method[key](v, *args)
    i = 0
    args_to_eval = list()
    for arg in args:
        assert isinstance(arg, gdb.Value), 'extra argument %s not a gdb.Value' % i + 1
        args_to_eval.append(to_eval(arg, '$_call_object_method_arg_%s' % i + 1))
    try:
        return parse_and_eval(to_eval(v, '$_call_object_method_arg_0') + '.' + f
                              + '(' + ', '.join(args_to_eval) + ')')
    except:
        message('call_object_method: call failed to: ' + key)
        long_message(
            'call_object_method',
            '\n\tgdb might eliminate inline functions\n' +
            '\tto add a python function bypass, use:\n' +
            '\t  py boost.object_method["' + key + '"] = <f>')
        raise gdb.error


static_var_addr = dict()


def get_static_var_addr(s):
    if s in static_var_addr:
        return parse_and_eval('(void**)' + str(static_var_addr[s]))
    return None


#
# Bypass static method calls
#
# key: (str, str)
#   1st argument is the enclosing type/template name, stripped of typedefs.
#   2nd argument is the method name.
# value: python function
#   Call this function instead of calling original static method.
#   If the 1st key is a template name, the function is given one extra
#   parameter, the type name that matched.
#
static_method = dict()


def call_static_method(t, f, *args):
    """Apply static method `t`::`f` to gdb.Value objects in `args`.

    If (str(`t`), `f`) matches a key in `static_method`, interpret
    dictionary value as a python function to call instead,
    passing it arguments `*args`.

    Next, if (template_name(`t`), `f`) matches a key, interpret
    dictionary value as a python function to call instead,
    passing it `t` as first argument, then `*args`.

    Args:
      `t`: a gdb.Type
      `f`: a str
      `args`: gdb.Value objects

    Raises:
      gdb.error, if call fails.
    """
    assert isinstance(t, gdb.Type)
    assert isinstance(f, str)

    # first, try the type name bypass
    if (str(t.strip_typedefs()), f) in static_method:
        f_to_call = static_method[(str(t.strip_typedefs()), f)]
        assert callable(f_to_call), '"f_to_call" not callable'
        return f_to_call(*args)

    # next, try the template name bypass
    if (template_name(t), f) in static_method:
        f_to_call = static_method[(template_name(t), f)]
        assert callable(f_to_call), '"f_to_call" not callable'
        return f_to_call(t, *args)

    # construct argument list
    i = 0
    args_to_eval = list()
    for arg in args:
        assert isinstance(arg, gdb.Value), 'extra argument %s not a gdb.Value' % i
        args_to_eval.append(to_eval(arg, '$_call_static_method_arg_%s' % i))
    # eval in gdb
    cmd = str(t) + '::' + f + '(' + ', '.join(args_to_eval) + ')'
    try:
        return parse_and_eval(cmd)
    except:
        message('call_static_method: call failed: ' + cmd)
        long_message(
            'call_static_method',
            '\n\tto bypass call with a python function <f>, use:\n' +
            '\t  py boost.static_method[("' + str(t.strip_typedefs())
            + '", "' + f + '")] = <f>')
        raise gdb.error


#
# Bypass inner type deduction
#
# key: (str, str, str)
#   1st argument is outter type/template name, stripped of typedefs.
#   2nd argument is inner typedef name to look for.
# value: gdb.Type, str, or python function
#   If value is a gdb.Type or str, return the corresponding type
#   instead of accessing the inner type.
#   If value is a function, call it giving the outter type as argument.
#
inner_type = dict()


def get_inner_type(t, s):
    """
    Fetch inner typedef `t`::`s`.

    If either (str(`t`), `s`) or (template_name(`t`), `s`) is a key in `inner_type`:
    if value is gdb.Value, return that instead;
    if value is a str, lookup the corresponding type and return it;
    if value is a function, call it with argument `t`, and return its value.

    Args:
      `t`: a gdb.Type
      `s`: a string

    Returns:
      A gdb.Type object corresponding to the inner type.

    Raises:
      gdb.error, if inner type is not found.
    """
    assert isinstance(t, gdb.Type)
    assert isinstance(s, str)

    v = None
    # first, try the type name bypass
    if (str(t.strip_typedefs()), s) in inner_type:
        v = inner_type[(str(t.strip_typedefs()), s)]
    # next, try the template name bypass
    elif (template_name(t), s) in inner_type:
        v = inner_type[(template_name(t), s)]

    if isinstance(v, gdb.Type):
        return v
    elif isinstance(v, str):
        return lookup_type(v)
    elif callable(v):
        return v(t)

    # finally, try plain inner type access
    inner_type_name = str(get_basic_type(t)) + '::' + s
    try:
        return lookup_type(inner_type_name).strip_typedefs()
    except gdb.error:
        message('get_inner_type: failed to find type: ' + inner_type_name)
        long_message(
            'get_inner_type',
            '\n\tBy default, gcc eliminates unused typedefs from object files, which can\n' +
            '\tcause gdb not to find them at runtime. To elimiate this behaviour, use the\n' +
            '\tflag `-fno-eliminate-unused-debug-types`. NOTE: clang (3.5) seems to be\n' +
            '\tsilently ignoring this flag.\n' +
            '\tAlternatively, to bypass this failure, add the result manually with:\n' +
            '\t  py boost.inner_type[("' +
            str(get_basic_type(t)) + '", "' + s + '")] = <type>')
        raise


#
# Raw pointer transformation
#
# key: str
#   The type/template name of pointer-like type.
# value: function
#   Python function to call to obtain a raw pointer.
#
raw_ptr = dict()


def get_raw_ptr(p):
    """
    Cast pointer-like object `p` into a raw pointer.

    If `p` is a pointer, it is returned unchanged.

    If the type or template name of `p` is a key in `raw_ptr`, the associated value
    is interpreted as a function to call to produce the raw pointer.

    If no corresponding entry is found in `raw_ptr`,
    an attempt is made to call `p.operator->()`.
    """
    assert isinstance(p, gdb.Value)

    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return p

    f = None
    if str(p.type.strip_typedefs()) in raw_ptr:
        f = raw_ptr[str(p.type.strip_typedefs())]
        assert callable(f)
    elif template_name(p.type) in raw_ptr:
        f = raw_ptr[template_name(p.type)]
        assert callable(f)

    if f:
        return f(p)

    p_str = to_eval(p, '$_get_raw_ptr_p')
    #save_value_as_variable(p, '$_p')
    try:
        return parse_and_eval(p_str + '.operator->()')
    except gdb.error:
        message('get_raw_ptr: call to operator->() failed on type: ' + str(p.type.strip_typedefs()))
        long_message(
            'get_raw_ptr',
            '\n\tto bypass this with python function <f>, add:\n' +
            '\t  py boost.raw_ptr["' + str(p.type.strip_typedefs()) + '"] = <f>')
        raise gdb.error


def print_ptr(p):
    """
    If `p` is a pointer, print it in hex. Otherwise, invoke pretty printer.
    """
    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return hex(intptr(p))
    else:
        return str(p)


#
# Null value checker
#
# key: str
#   Type or template name, stripped of typedefs, of pointer-like type.
# value: function
#   Call function with argument a value of pointer-like type to determine if
#   value represents null.
#
null_dict = dict()


def is_null(p):
    """
    Check if `p` is null.

    If `p` is a pointer, check if it is 0 or not.

    If the type or template name of `p` appear in `null_dict`, call the corresponding
    value with argument `p`.
    """
    assert isinstance(p, gdb.Value)

    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return intptr(p) == 0

    f = None
    if str(p.type.strip_typedefs()) in null_dict:
        f = null_dict[str(p.type.strip_typedefs())]
        assert callable(f)
    elif template_name(p.type) in null_dict:
        f = null_dict[template_name(p.type)]
        assert callable(f)

    if f:
        return f(p)

    message('is_null: cannot run is_null() on type: ' + str(p.type.strip_typedefs()))
    long_message(
        'is_null',
        '\n\tto bypass this with python function <f>, add:\n' +
        '\t  py boost.null_dict["' + str(p.type.strip_typedefs()) + '"] = <f>')
    raise gdb.error


def add_to_dict(d, *keys):
    """
    Decorator that adds its argument object to  dict `d` under every key in `*keys`.
    """
    assert isinstance(d, dict)

    def inner_decorator(obj):
        for k in keys:
            d[k] = obj
        return None
    return inner_decorator

#
# Convenience function for printing specific elements in containers.
#
class at_func(gdb.Function):
    def __init__(self):
        super(at_func, self).__init__('at')
    def invoke(self, cont, idx=0):
        assert isinstance(cont, gdb.Value)
        p = gdb.default_visualizer(cont)
        assert p, 'no printer for type [' + str(cont.type) + ']'
        assert hasattr(p, 'children'), 'printer for type [' + str(cont.type) + '] has no children() function'
        it = iter(p.children())
        i = idx
        while i > 0:
            next(it)
            i -= 1
        _, val = next(it)
        return str(val)


_at = at_func()


def unwind_references(value):
    """Convert reference (or reference chain) to actual value"""
    # gdb.TYPE_CODE_RVALUE_REF is also available in recent gdb versions
    while value.type.code == gdb.TYPE_CODE_REF:
        value = value.referenced_value()
    return value


def reinterpret_cast(value, target_type):
    return value.address.cast(target_type.pointer()).dereference()


class GDB_Value_Wrapper(gdb.Value):
    """Wrapper class for gdb.Value"""
    def __init__(self, value):
        # In Python 3 simply deriving from gdb.Value will generate a __dict__ attribute.
        # In Python 2 we add a __dict__ attribute explicitly.
        if have_python_2:
            self.__dict__ = {}
        gdb.Value.__init__(value)
        self.qualifiers = get_type_qualifiers(value.type)
        self.basic_type = get_basic_type(value.type)
        self.type_name = str(self.basic_type)
        self.template_name = template_name(self.basic_type)


class Printer_Gen(object):
    """
    Top-level printer generator.
    """
    class SubPrinter_Gen(object):
        def __init__(self, Printer, tn=str()):
            self.Printer = Printer
            # set printer_name
            assert tn != '' or hasattr(Printer, 'printer_name')
            if tn != '':
                self.name = tn
            elif hasattr(Printer, 'printer_name'):
                self.name = Printer.printer_name
            # set enabled
            if hasattr(Printer, 'enabled'):
                self.enabled = Printer.enabled
            else:
                self.enabled = True

        def __call__(self, v):
            if not self.enabled:
                return None
            if hasattr(self.Printer, 'supports') and not self.Printer.supports(v):
                return None
            if hasattr(self.Printer, 'transform') and callable(self.Printer.transform):
                tv = self.Printer.transform(v)
                if type(tv) == gdb.Value:
                    p = gdb.default_visualizer(tv)
                    if p:
                        return p
                return self.Printer(tv)
            else:
                return self.Printer(v)

    def __init__(self, name):
        self.name = name
        self.enabled = True
        self.subprinters = list()
        self.template_name_dict = collections.defaultdict(list)
        self.no_template_name_list = list()

    def add(self, Printer, tn=str()):
        if not hasattr(Printer, 'supports') and not hasattr(Printer, 'template_name') and tn == '':
            message('cannot import printer [' + Printer.printer_name + ']: neither supports() nor template_name is defined')
            return
        # get list of template names
        if tn != '':
            name_list = [tn]
        elif not hasattr(Printer, 'template_name'):
            name_list = list()
        elif type(Printer.template_name) == str:
            name_list = [Printer.template_name]
        elif type(Printer.template_name) == list:
            name_list = Printer.template_name
        else:
            message('cannot import printer [' + Printer.printer_name + ']: template_name has type=' + str(type(Printer.template_name)))
            return
        # create new printer
        p = Printer_Gen.SubPrinter_Gen(Printer, tn)
        # add it to subprinters
        self.subprinters.append(p)
        # add it to template_name_dict
        if name_list:
            for template_name in name_list:
                self.template_name_dict[template_name].append(p)
        else:
            self.no_template_name_list.append(p)

    def __call__(self, value):
        v = GDB_Value_Wrapper(value)
        subprinter_generators = self.template_name_dict.get(v.template_name, self.no_template_name_list)
        for subprinter_gen in subprinter_generators:
            printer = subprinter_gen(v)
            if printer is not None:
                return printer
        return None


class Type_Printer_Gen:
    """
    Top-level type printer generator.
    """

    def __init__(self, Type_Recognizer):
        self.name = Type_Recognizer.name
        self.enabled = Type_Recognizer.enabled
        self.Type_Recognizer = Type_Recognizer

    def instantiate(self):
        return self.Type_Recognizer()


type_printer_list = []
boost_printer_list = []
trivial_printer_list = []


def register_printers(obj=None, boost_version=None):
    """
    Register top-level printers 'boost' and 'trivial' with objfile `obj`.
    """
    if boost_version is None:
        message('Detecting boost_version... ')
        boost_version = detect_boost_version()
        message('Detected boost version: {}.{}.{}'.format(*boost_version))
    supported_printers = [printer for printer in boost_printer_list
                          if printer.min_supported_version <= boost_version <= printer.max_supported_version]
    if supported_printers:
        boost_printer_gen = Printer_Gen('boost')
        for printer in supported_printers:
            boost_printer_gen.add(printer)
        gdb.printing.register_pretty_printer(obj, boost_printer_gen, replace=True)
    else:
        message('No boost printers are available for boost version {}.{}.{}!'.format(*boost_version))

    trivial_printer_gen = Printer_Gen('trivial')
    for printer in trivial_printer_list:
        trivial_printer_gen.add(printer)
    gdb.printing.register_pretty_printer(obj, trivial_printer_gen, replace=True)

    for tp in type_printer_list:
        gdb.types.register_type_printer(obj, tp)


def add_printer(p):
    """
    Decorator that adds the given printer `p` to the top-level 'boost' printer.
    """
    boost_printer_list.append(p)
    return p


class _cant_add_printer:
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, p):
        message('printer [' + p.printer_name + '] not supported: ' + self.msg)
        return p


def cond_add_printer(cond, msg):
    """
    Decorator-generator that conditionally adds a printer to the top-level 'boost' printer.
    """
    if cond:
        return add_printer
    else:
        return _cant_add_printer(msg)


def add_type_recognizer(r):
    """
    Add a type recognizer.
    """
    type_printer_list.append(Type_Printer_Gen(r))
    return r


class _cant_add_type_recognizer:
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, p):
        message('type recognizer [' + p.printer_name + '] not supported: ' + self.msg)
        return p


def cond_add_type_recognizer(cond, msg):
    """
    Conditionally add a type recognizer.
    """
    if cond:
        return add_type_recognizer
    else:
        return _cant_add_type_recognizer(msg)


def add_trivial_printer(tn, f):
    """
    Add a trivial printer.
    For a value v with template name matching `tn`, print it by invoking `f`(v). Works even from inside gdb. E.g.:

    py boost.add_trivial_printer("List_Obj", lambda v: v['_val'])
        - for every object v of type "List_Obj", simply print v._val


    """
    assert type(tn) == str and tn != ''
    assert callable(f)

    class _Printer:
        printer_name = tn
        template_name = tn
        transform = staticmethod(f)

        def __init__(self, v):
            self.v = v

        def to_string(self):
            return str(self.v)
    trivial_printer_list.append(_Printer)


def add_trivial_type_printer(tn, f, **kwargs):
    """
    Add trivial type printer.

    For a type t with template name matching `tn`, print it by invoking `f`(t).

    NOTE: The function automatically registers the type printer with gdb by invoking
    gdb.types.register_type_printer(). This is necessary because unlike the case of
    value printers, there is no top-level type printer to intermediate the process.
    The optional keyword argument `obj` specifies the object file for which to do
    the registration. (If not specified, the type printer will be global.)
    """
    assert type(tn) == str and tn != ''
    assert callable(f)

    class _Type_Recognizer:
        name = tn
        enabled = True
        transform = staticmethod(f)

        def recognize(self, t):
            _tn = template_name(t)
            if _tn != self.name:
                return None
            return self.transform(t)
    if 'obj' not in kwargs:
        kwargs['obj'] = None
    gdb.types.register_type_printer(kwargs['obj'], Type_Printer_Gen(_Type_Recognizer))


#
# To specify which index to use for printing for a specific container
# (dynamically, inside gdb), add its address here as key, and the desired
# index as value. E.g.:
#
# (gdb) p &s_5
# $2 = (Int_Set_5 *) 0x7fffffffd770
# (gdb) python import boost.printers
# (gdb) python boost.multi_index_selector[0x7fffffffd770] = 1
# (gdb) p s_5
#
multi_index_selector = dict()

#
# If set to true, do not print intrusive container hooks.
#
options = {'hide_intrusive_hooks': True}

# Latest boost currently supported by printers
last_supported_boost_version = (1, 70, 0)
