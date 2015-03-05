########################################
# Intrusive containers 1.55
########################################

from boost import *

def short_ns(tag):
    if tag.startswith('boost::intrusive::'):
        return 'bi::' + tag[18:]
    else:
        return tag

@add_type_recognizer
class Generic_Hook_Type_Recognizer:
    "Type Recognizer for boost::intrusive::generic_hook"
    name = 'boost::intrusive::generic_hook-1.55'
    version = '1.55'
    enabled = True
    target_re = re.compile('^boost::intrusive::generic_hook<.*>$')

    def recognize(self, t):
        if not t.tag or self.target_re.search(t.tag) == None:
            return None
        # hook_tag: default (base) or member
        hook_tag = str(t.template_argument(1).strip_typedefs())
        # link mode
        link_mode = str(t.template_argument(2)).split('::')[2]
        # node_type: first subclass, or the first subclass of the first subclass
        node_t = t.fields()[0].type
        if str(node_t.strip_typedefs()).startswith('boost::intrusive::node_holder'):
            node_t = node_t.fields()[0].type
        node_tag = str(node_t.strip_typedefs())
        return ('bi::generic_hook<' + short_ns(node_tag) + ', '
                + short_ns(hook_tag) + ', ' + link_mode + '>')

@add_printer
class Generic_Hook_Printer:
    "Pretty Printer for boost::intrusive::generic_hook"
    printer_name = 'boost::intrusive::generic_hook'
    version = '1.55'
    type_name_re = '^boost::intrusive::generic_hook<.*>$'
    enabled = True

    def __init__(self, value):
        self.value = value

    def to_string(self):
        # the actual node is either the first subclass,
        # or the first subclass of the first subclass
        node = self.value.cast(self.value.type.fields()[0].type)
        if str(node.type.strip_typedefs()).startswith('boost::intrusive::node_holder'):
            node = node.cast(node.type.fields()[0].type)
        return str(node)

@add_type_recognizer
class Hook_Type_Recognizer:
    "Type Recognizer for boost::intrusive::*_(base|member)_hook"
    name = 'boost::intrusive::hook-1.55'
    enabled = True
    target_re = re.compile('^boost::intrusive::(avl_set|bs_set|list|set|slist|splay_set|unordered_set)_(base|member)_hook<.*>$')

    def recognize(self, t):
        if not t.tag or not self.target_re.search(t.tag):
            return None
        # just print the underlying generic hook
        generic_hook_t = t.fields()[0].type
        return Generic_Hook_Type_Recognizer().recognize(generic_hook_t)

@add_printer
class Hook_Printer:
    "Pretty Printer for boost::intrusive::*_(base|member)_hook"
    printer_name = 'boost::intrusive::hook'
    version = '1.55'
    type_name_re = '^boost::intrusive::(avl_set|bs_set|list|set|slist|splay_set|unordered_set)_(base|member)_hook<.*>$'
    enabled = True

    def __init__(self, value):
        self.val = value

    def to_string(self):
        # cast to and print underlying generic hook
        generic_hook_t = self.val.type.fields()[0].type
        generic_hook = self.val.cast(generic_hook_t)
        return str(generic_hook)

# resolve bhtraits::node_traits
#   node_traits is the 2nd template argument
#
@add_to_dict(inner_type, ('boost::intrusive::bhtraits', 'node_traits'))
def f(vtt):
    return vtt.template_argument(1)

# resolve mhtraits::node_traits
#   hook is 2nd template parameter (e.g. "list_member_hook")
#   generic_hook is 1st subclass of hook
#   get_node_algo is 1st template parameter of generic_hook
#
#   We hard-code node_traits as a function of get_node_algo.
#
@add_to_dict(inner_type, ('boost::intrusive::mhtraits', 'node_traits'))
def f(vtt):
    gen_hook_t = vtt.template_argument(1).fields()[0].type
    get_node_algo_t = gen_hook_t.template_argument(0)
    voidptr_t = get_node_algo_t.template_argument(0)
    for case in switch(template_name(get_node_algo_t)):
        if case('boost::intrusive::get_list_node_algo'):
            return gdb.lookup_type('boost::intrusive::list_node_traits<'
                                   + str(voidptr_t) + '>')
        if case('boost::intrusive::get_slist_node_algo'):
            return gdb.lookup_type('boost::intrusive::slist_node_traits<'
                                   + str(voidptr_t) + '>')
        if case('boost::intrusive::get_set_node_algo'):
            opt_size = get_node_algo_t.template_argument(1)
            return gdb.lookup_type('boost::intrusive::rbtree_node_traits<'
                                   + str(voidptr_t) + ',' + str(opt_size) + '>')
        if case('boost::intrusive::get_avl_set_node_algo'):
            opt_size = get_node_algo_t.template_argument(1)
            return gdb.lookup_type('boost::intrusive::avltree_node_traits<'
                                   + str(voidptr_t) + ',' + str(opt_size) + '>')
        if case('boost::intrusive::get_bs_set_node_algo'):
            return gdb.lookup_type('boost::intrusive::tree_node_traits<'
                                   + str(voidptr_t) + '>')
    assert False, 'could not determine node_traits'

# resolve trivial_value_traits::node_traits
#   node_traits is the 1st template argument
#
@add_to_dict(inner_type, ('boost::intrusive::trivial_value_traits', 'node_traits'))
def f(vtt):
    return vtt.template_argument(0)

# resolve trivial_value_traits::to_value_ptr
#   node == value
#
@add_to_dict(static_method, ('boost::intrusive::trivial_value_traits', 'to_value_ptr'))
def f(vtt, node_rptr):
    return node_rptr

# resolve bhtraits::to_value_ptr
#   perform a 2-step upcast to accomodate for multiple base hooks
#
@add_to_dict(static_method, ('boost::intrusive::bhtraits', 'to_value_ptr'))
def f(vtt, node_rptr):
    # first, find the tag type
    tag_t = vtt.template_argument(3)
    # find a 'generic_hook' 1st base class of a base class of value type
    # with the appropriate tag
    value_t = vtt.template_argument(0)
    subclass_t = None
    for f in value_t.fields():
        if f.type.code != gdb.TYPE_CODE_STRUCT:
            # the remaining types aren't subclasses
            break
        t1 = f.type
        t2 = t1.fields()[0].type
        if (template_name(t2) == 'boost::intrusive::generic_hook'
            and t2.template_argument(1).strip_typedefs() == tag_t.strip_typedefs()):
            subclass_t = t2
            break
    assert subclass_t, 'no subclass hook with tag: ' + str(tag_t.strip_typedefs())
    # first upcast into generic_hook ptr with correct tag
    subclass_rptr = node_rptr.cast(subclass_t.pointer())
    val_rptr_t = value_t.pointer()
    # second upcast into value
    return subclass_rptr.cast(val_rptr_t)

# resolve mhtraits::to_value_ptr
#   offset is 3rd template argument
#
@add_to_dict(static_method, ('boost::intrusive::mhtraits', 'to_value_ptr'))
def f(vtt, node_rptr):
    offset = vtt.template_argument(2)
    offset_int = parse_and_eval('(size_t)(' + str(offset) + ')')
    node_rptr_int = intptr(node_rptr)
    value_t = vtt.template_argument(0)
    val_rptr_t = value_t.pointer()
    return parse_and_eval('(' + str(val_rptr_t.strip_typedefs()) +
                          ')(' + str(node_rptr_int - offset_int) + ')')

# resolve (s)list_node_traits::get_next
#
@add_to_dict(static_method,
             ('boost::intrusive::list_node_traits', 'get_next'),
             ('boost::intrusive::slist_node_traits', 'get_next'))
def f(ntt, node_rptr):
    return node_rptr['next_']

# resolve (rb|avl)tree_node_traits::get_parent
#
@add_to_dict(static_method,
             ('boost::intrusive::rbtree_node_traits', 'get_parent'),
             ('boost::intrusive::avltree_node_traits', 'get_parent'),
             ('boost::intrusive::tree_node_traits', 'get_parent'))
def f(ntt, node_rptr):
    return node_rptr['parent_']

# resolve (rb|avl)tree_node_traits::get_left
#
@add_to_dict(static_method,
             ('boost::intrusive::rbtree_node_traits', 'get_left'),
             ('boost::intrusive::avltree_node_traits', 'get_left'),
             ('boost::intrusive::tree_node_traits', 'get_left'))
def f(ntt, node_rptr):
    return node_rptr['left_']

# resolve (rb|avl)tree_node_traits::get_right
#
@add_to_dict(static_method,
             ('boost::intrusive::rbtree_node_traits', 'get_right'),
             ('boost::intrusive::avltree_node_traits', 'get_right'),
             ('boost::intrusive::tree_node_traits', 'get_right'))
def f(ntt, node_rptr):
    return node_rptr['right_']

def apply_pointed_node(it):
    """Apply iterator::pointed_node."""
    assert isinstance(it, gdb.Value)

    # builtin iterators
    #
    if (template_name(it.type) == 'boost::intrusive::list_iterator'
        or template_name(it.type) == 'boost::intrusive::slist_iterator'
        or template_name(it.type) == 'boost::intrusive::tree_iterator'):
        return it['members_']['nodeptr_']

    return call_object_method(it, 'pointed_node')

def value_rptr_from_iiterator(it):
    # value traits is first template argument
    value_traits_t = it.type.template_argument(0)
    # apply pointed_node() to get node_ptr
    node_rptr = get_raw_ptr(apply_pointed_node(it))
    return get_raw_ptr(call_static_method(value_traits_t, 'to_value_ptr', node_rptr))

@add_printer
class Iterator_Printer:
    "Pretty Printer for boost::intrusive::(list|slist|tree)_iterator"
    printer_name = 'boost::intrusive::iterator'
    version = '1.55'
    type_name_re = '^boost::intrusive::(list|slist|tree)_iterator<.*>$'
    enabled = True

    def __init__(self, value):
        self.val = value

    def to_string(self):
        value_rptr = value_rptr_from_iiterator(self.val)
        try:
            value_str = str(value_rptr.dereference())
        except:
            value_str = 'N/A'
        return str(self.val['members_']['nodeptr_']) + ' -> ' + value_str

@add_printer
class List_Printer:
    "Pretty Printer for boost::intrusive list and slist"
    printer_name = 'boost::intrusive::list'
    version = '1.55'
    type_name_re = '^boost::intrusive::s?list<.*>$'
    enabled = True

    class Iterator:
        def __init__(self, l):
            self.value_traits_t = l.type.fields()[0].type.template_argument(0)
            self.node_traits_t = get_inner_type(self.value_traits_t, 'node_traits')
            self.root_node_rptr = get_raw_ptr(call_object_method(l, 'get_root_node'))

        def __iter__(self):
            self.count = 0
            self.crt_node_rptr = get_raw_ptr(call_static_method(
                self.node_traits_t, 'get_next', self.root_node_rptr))
            return self

        def __next__(self):
            if self.crt_node_rptr == self.root_node_rptr or is_null(self.crt_node_rptr):
                raise StopIteration
            val_rptr = get_raw_ptr(call_static_method(
                self.value_traits_t, 'to_value_ptr', self.crt_node_rptr))
            try:
                val_str = str(val_rptr.referenced_value())
            except:
                val_str = 'N/A'
            result = ('[%d @%s]' % (self.count, print_ptr(val_rptr)), val_str)
            self.count = self.count + 1
            self.crt_node_rptr = get_raw_ptr(call_static_method(
                self.node_traits_t, 'get_next', self.crt_node_rptr))
            return result

        def next(self):
            return self.__next__()

    def __init__(self, l):
        self.l = l
        self.value_type = self.l.type.template_argument(0)

    def to_string (self):
        res = ''
        if self.l.qualifiers:
            res += '(' + self.l.qualifiers + ')'
        res += (short_ns(template_name(self.l.type)) +
                '<' + str(self.value_type.strip_typedefs()) + '>')
        return res

    def children (self):
        return self.Iterator(self.l)

#@add_type_recognizer
class List_Type_Recognizer:
    "Type Recognizer for boost::intrusive::list"
    name = 'boost::intrusive::list-1.55'
    enabled = True

    def recognize(self, t):
        qualifiers = get_type_qualifiers(t)
        basic_t = gdb.types.get_basic_type(t)
        if not str(basic_t).startswith('boost::intrusive::list<'):
            return None
        res = '%'
        if qualifiers:
            res += '(' + qualifiers + ')'
        res += 'bi::list<' + str(basic_t.template_argument(0)) + '>'
        return res

@add_printer
class Tree_Printer:
    "Pretty Printer for boost::intrusive ordered sets"
    printer_name = 'boost::intrusive::set'
    version = '1.55'
    enabled = True

    @staticmethod
    def get_bstree_impl_base(t):
        d = 5
        while (d > 0 and isinstance(t, gdb.Type) and t.code == gdb.TYPE_CODE_STRUCT
               and template_name(t) != 'boost::intrusive::bstree_impl'):
            try:
                t = t.fields()[0].type
            except:
                return None
            d -= 1
        if d > 0 and isinstance(t, gdb.Type) and t.code == gdb.TYPE_CODE_STRUCT:
            return t
        else:
            return None

    @staticmethod
    def supports(v):
        return Tree_Printer.get_bstree_impl_base(v.type) != None

    class Iterator:
        def __init__(self, l):
            self.value_traits_t = l.type.fields()[0].type.template_argument(0)
            self.node_traits_t = get_inner_type(self.value_traits_t, 'node_traits')
            self.header_node_rptr = get_raw_ptr(call_object_method(l, 'header_ptr'))

        def __iter__(self):
            self.count = 0
            self.crt_node_rptr = get_raw_ptr(call_static_method(
                self.node_traits_t, 'get_left', self.header_node_rptr))
            return self

        def __next__(self):
            if self.crt_node_rptr == self.header_node_rptr:
                raise StopIteration
            val_rptr = get_raw_ptr(call_static_method(
                self.value_traits_t, 'to_value_ptr', self.crt_node_rptr))
            try:
                val_str = str(val_rptr.referenced_value())
            except:
                val_str = 'N/A'
            result = ('[%d @%s]' % (self.count, print_ptr(val_rptr)), val_str)
            self.count = self.count + 1
            self.advance()
            return result

        def next(self):
            return self.__next__()

        def advance(self):
            n = get_raw_ptr(call_static_method(
                self.node_traits_t, 'get_right', self.crt_node_rptr))
            if not is_null(n):
                # if right subtree is not empty, find leftmost node in it
                self.crt_node_rptr = n
                while True:
                    n = get_raw_ptr(call_static_method(
                        self.node_traits_t, 'get_left', self.crt_node_rptr))
                    if is_null(n):
                        break
                    self.crt_node_rptr = n
            else:
                # if right subtree is empty, find first ancestor in whose left subtree we are
                while True:
                    old_n = self.crt_node_rptr
                    self.crt_node_rptr = get_raw_ptr(call_static_method(
                        self.node_traits_t, 'get_parent', self.crt_node_rptr))
                    if self.crt_node_rptr == self.header_node_rptr:
                        break
                    n = get_raw_ptr(call_static_method(
                        self.node_traits_t, 'get_left', self.crt_node_rptr))
                    if n == old_n:
                        break

    def __init__(self, l):
        self.l = l

    def to_string (self):
        res = ''
        if self.l.qualifiers:
            res += '(' + self.l.qualifiers + ')'
        if str(self.l.type).startswith('boost::intrusive::'):
            value_type = self.l.type.template_argument(0)
            res += (short_ns(template_name(self.l.type)) +
                    '<' + str(value_type.strip_typedefs()) + '>')
        else:
            res += str(self.l.type)
        return res

    def children (self):
        return self.Iterator(self.l.cast(self.get_bstree_impl_base(self.l.type)))

#@add_type_recognizer
class Tree_Type_Recognizer:
    "Type Recognizer for boost::intrusive::tree"
    name = 'boost::intrusive::tree-1.55'
    enabled = True

    @staticmethod
    def supports(t):
        d = 5
        while (d > 0 and isinstance(t, gdb.Type)
               and template_name(t) != 'boost::intrusive::bstree_impl'):
            try:
                t = t.fields()[0].type
            except:
                return None
            d -= 1
        return d > 0 and isinstance(t, gdb.Type)

    def recognize(self, t):
        qualifiers = get_type_qualifiers(t)
        basic_t = gdb.types.get_basic_type(t)
        if not self.supports(basic_t):
            return None
        res = '%'
        if qualifiers:
            res += '(' + qualifiers + ')'
        res += short_ns(template_name(basic_t)) + '<' + str(basic_t.template_argument(0)) + '>'
        return res
