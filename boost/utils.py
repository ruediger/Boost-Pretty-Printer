from __future__ import print_function

import sys
import re
import gdb
import gdb.types

#
# Indicators for python2 and python3
#
have_python_2 = (sys.version_info[0] == 2)
have_python_3 = (sys.version_info[0] == 3)

#
# Workaround: if python3, typedef long as int
#
if have_python_3:
    long = int
    xrange = range

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
# execute(): imported from gdb
#
from gdb import execute

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
    Get template name of gdb.Type.
    """
    assert isinstance(t, gdb.Type)
    return str(t.strip_typedefs()).split('<')[0]

class _aux_save_value_as_variable(gdb.Function):
    def __init__(self, v):
        super(_aux_save_value_as_variable, self).__init__('_aux_save_value_as_variable')
        self.value = v
    def invoke(self):
        return self.value

def save_value_as_variable(v, s):
    """Save gdb.Value `v` as gdb variable `s`."""
    assert isinstance(v, gdb.Value), 'arg 1 not a gdb.Value'
    assert isinstance(s, str), 'arg 2 not a string'
    _aux_save_value_as_variable(v)
    execute('set var ' + s + ' = $_aux_save_value_as_variable()')

def to_eval(val, var_name = None):
    """
    Return string that, when evaluated, returns the given gdb.Value.

    If <val> has an adddress, the string returned will be of the form:
    "(*(<val.type> *)(<val.address>))".

    If <val> has no address, it is first saved as variable <var_name>,
    then the string returned is "<var_name>".
    """
    assert isinstance(val, gdb.Value)
    if val.address:
        return '(*(' + str(val.type) + ' *)(' + hex(int(val.address)) + '))'
    else:
        assert isinstance(var_name, str)
        save_value_as_variable(val, var_name)
        return var_name

def call_object_method(v, f, *args):
    """Apply method to given object."""
    assert isinstance(v, gdb.Value)
    assert isinstance(f, str)
    i = 0
    args_to_eval = list()
    for arg in args:
        assert isinstance(arg, gdb.Value), 'extra argument %s not a gdb.Value' % i + 1
        args_to_eval.append(to_eval(arg, '$_call_object_method_arg_%s' % i + 1))
    return parse_and_eval(to_eval(v, '$_call_object_method_arg_0') + '.' + f
                          + '(' + ', '.join(args_to_eval) + ')')


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
    assert isinstance(t, gdb.Type), '"t" not a gdb.Type'
    assert isinstance(f, str), '"f" not a string'

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
        print('call_static_method:\n' +
              '\tcall failed: ' + cmd + '\n' +
              '\tto bypass call with a python function <f>, use:\n' +
              '\t  py boost_print.static_method[("' + str(t.strip_typedefs())
              + '", "' + f + '")] = <f>',
              file=sys.stderr)
        raise gdb.error


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
    assert isinstance(t, gdb.Type), 'arg not a gdb.Type'
    assert isinstance(s, str), 's not a str'

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
        return gdb.lookup_type(v)
    elif callable(v):
        return v(t)

    # finally, try plain inner type access
    inner_type_name = str(t.strip_typedefs()) + '::' + s
    try:
        return gdb.lookup_type(inner_type_name)
    except gdb.error:
        print('get_inner_type:\n' +
              '\tfailed to find type: ' + inner_type_name + '\n' +
              '\tto bypass this failure, add the result manually with:\n' +
              '\t  py boost_print.inner_type[("' +
              str(t.strip_typedefs()) + '", "' + s + '")] = <type>',
              file=sys.stderr)
        raise gdb.error


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
    assert isinstance(p, gdb.Value), '"p" not a gdb.Value'

    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return p

    f = None
    if str(p.type.strip_typedefs()) in raw_ptr:
        f = raw_ptr[str(p.type.strip_typedefs())]
        assert callable(f), '"f" not callable'
    elif template_name(p.type) in raw_ptr:
        f = raw_ptr[template_name(p.type)]
        assert callable(f), '"f" not callable'

    if f:
        return f(p)

    p_str = to_eval(p, '$_get_raw_ptr_p')
    #save_value_as_variable(p, '$_p')
    try:
        return parse_and_eval(p_str +'.operator->()')
    except gdb.error:
        print('get_raw_ptr:\n'
              + '\tcall to operator->() failed on type: '
              + str(p.type.strip_typedefs()) + '\n'
              + '\tto bypass this with python function <f>, add:\n'
              + '\t  py boost_print.raw_ptr["' +
              str(p.type.strip_typedefs()) + '"] = <f>',
              file=sys.stderr)
        raise gdb.error

def print_ptr(p):
    """
    If `p` is a pointer, print it in hex. Otherwise, invoke pretty printer.
    """
    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return hex(int(p))
    else:
        return str(p)

# Null value checker
#
# key: str
#   Type or template name, stripped of typedefs, of pointer-like type.
# value: function
#   Call function with argument a value of pointer-like type to determine if
#   value represents null.
null_dict = dict()

def is_null(p):
    """
    Check if `p` is null.

    If `p` is a pointer, check if it is 0 or not.

    If the type or template name of `p` appear in `null_dict`, call the corresponding
    value with argument `p`.
    """
    assert isinstance(p, gdb.Value), '"p" not a gdb.Value'

    if p.type.strip_typedefs().code == gdb.TYPE_CODE_PTR:
        return int(p) == 0

    f = None
    if str(p.type.strip_typedefs()) in null_dict:
        f = null_dict[str(p.type.strip_typedefs())]
        assert callable(f), '"f" not callable'
    elif template_name(p.type) in null_dict:
        f = null_dict[template_name(p.type)]
        assert callable(f), '"f" not callable'

    if f:
        return f(p)

    print('is_null:\n'
          + '\tcannot run is_null() on type: ' + str(p.type.strip_typedefs()) + '\n'
          + '\tto bypass this with python function <f>, add:\n'
          + '\t  py boost_print.null_dict["' + str(p.type.strip_typedefs()) + '"] = <f>',
          file=sys.stderr)
    raise gdb.error

def _add_to_dict(d, *keys):
    """Decorator that adds its argument object to  dict `d` under every key in `*keys`."""
    assert isinstance(d, dict), '"d" not a dict'
    def _aux_decorator(obj):
        for k in keys:
            d[k] = obj
        return None
    return _aux_decorator

# convenience function for printing specific elements in containers
#
class at_func(gdb.Function):
    def __init__(self):
        super(at_func, self).__init__('at')
    def invoke(self, cont, idx=0):
        assert isinstance(cont, gdb.Value), '"cont" not a gdb.Value'
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

#
# GDB_Value_Wrapper: Wrapper class for gdb.Value
#
# Its sole purpose is to provide a __dict__, which allows setting custom attributes.
#
if sys.version_info[0] > 2:
    # for python3, simply deriving from gdb.Value will generate a __dict__ attribute
    class GDB_Value_Wrapper(gdb.Value):
        """
        Wrapper class for gdb.Value.
        Its sole purpose is to provide a __dict__, which allows setting custom attributes.
        """
        pass
else:
    # for python2, we add a __dict__ attribute explicitly
    class GDB_Value_Wrapper(gdb.Value):
        def __init__(self, value):
            super(GDB_Value_Wrapper, self).__init__(value)
            self.__dict__ = {}


###
### Individual value printers appear in various .py files.
###
### Relevant fields:
###
### - 'printer_name' : Subprinter name used by gdb. (Required.) If it contains
###     regex operators, they must be escaped when refering to it from gdb.
### - 'version' : Appended to the subprinter name. (Optional.)
### - 'supports(GDB_Value_Wrapper)' classmethod : If it exists, it is used to
###     determine if the Printer supports the given object.
### - 'type_name_re' : If 'supports(basic_type)' doesn't exist, a default
###     version is used which simply tests whether the type name matches this
###     re. (Either supports() or type_name_re is required.)
### - 'enabled' : If this exists and is set to false, disable printer.
### - '__init__' : Its only argument is a GDB_Value_Wrapper.
###

class Printer_Gen(object):
    """
    Top-level printer generator.
    """
    class SubPrinter_Gen(object):
        def match_re(self, v):
            return self.re.search(str(v.basic_type)) != None

        def __init__(self, Printer):
            self.name = Printer.printer_name
            if hasattr(Printer, 'version'):
                self.name += '-' + Printer.version
            if hasattr(Printer, 'enabled'):
                self.enabled = Printer.enabled
            else:
                self.enabled = True
            if hasattr(Printer, 'supports'):
                self.re = None
                self.supports = Printer.supports
            else:
                self.re = re.compile(Printer.type_name_re)
                self.supports = self.match_re
            self.Printer = Printer

        def __call__(self, v):
            if not self.enabled:
                return None
            if self.supports(v):
                v.type_name = str(v.basic_type)
                return self.Printer(v)
            return None

    def __init__(self, name):
        self.name = name
        self.enabled = True
        self.subprinters = []

    def add(self, Printer):
        self.subprinters.append(Printer_Gen.SubPrinter_Gen(Printer))

    def __call__(self, value):
        qualifiers = get_type_qualifiers(value.type)
        v = GDB_Value_Wrapper(value.cast(get_basic_type(value.type)))
        v.qualifiers = qualifiers
        v.basic_type = v.type
        v.template_name = template_name(v.basic_type)
        for subprinter_gen in self.subprinters:
            printer = subprinter_gen(v)
            if printer != None:
                return printer
        return None

boost_printer_gen = Printer_Gen('boost')
trivial_printer_gen = Printer_Gen('trivial')

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

type_printer_list = list()

#
# This function registers the top-level Printer generator with gdb.
# This should be called from .gdbinit.
#
def register_printers(obj=None):
    """
    Register printers with objfile obj.
    """
    gdb.printing.register_pretty_printer(obj, boost_printer_gen, replace=True)
    gdb.printing.register_pretty_printer(obj, trivial_printer_gen, replace=True)
    for tp in type_printer_list:
        gdb.types.register_type_printer(obj, tp)

# Register value printer with the top-level printer generator.
def _register_printer(Printer):
    "Add a value printer"
    boost_printer_gen.add(Printer)
    return Printer

def _cant_register_printer(Printer):
    print('*** pretty-printer [%s] not supported by this gdb version'
          % Printer.printer_name, file=sys.stderr)
    return Printer

def _cond_register_printer(cond=True):
    "Conditionally add a value printer"
    if cond:
        return _register_printer
    else:
        return _cant_register_printer

def add_type_recognizer(Type_Recognizer):
    "Add a type recognizer"
    type_printer_list.append(Type_Printer_Gen(Type_Recognizer))
    return Type_Recognizer

def _cant_add_type_recognizer(Type_Recognizer):
    print('*** type recognizer [%s] not supported by this gdb version'
          % Type_Recognizer.name, file=sys.stderr)
    return Type_Recognizer

# Register type recognizer with the top-level type printer list.
def cond_add_type_recognizer(cond=True):
    "Conditionally add a type recognizer"
    if cond:
        return add_type_recognizer
    else:
        return _cant_add_type_recognizer

# Add trivial printers, even from inside gdb. E.g.:
#
#   py boost_print.add_trivial_printer("List_Obj", lambda v: v['_val'])
#     - for every object v of type "List_Obj", simply print v._val
#
def add_trivial_printer(type_name, fcn):
    """
    Add a trivial printer.

    For a value v of type matching `type_name`, print it by invoking `fcn`(v).
    """
    class Printer:
        printer_name = type_name
        type_name_re = '^' + type_name + '$'
        f = fcn
        def __init__(self, v):
            self.v = v
        def to_string(self):
            return str(Printer.f(self.v))
    trivial_printer_gen.add(Printer)
