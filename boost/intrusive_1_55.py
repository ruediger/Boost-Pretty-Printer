# coding: utf-8

########################################
# Intrusive containers 1.55
########################################

from .utils import *


@add_printer
class Hook_Printer:
    """Pretty Printer for boost::intrusive::*_(base|member)_hook"""
    printer_name = 'boost::intrusive::hook'
    min_supported_version = (1, 55, 0)
    max_supported_version = (1, 69, 0)
    template_name = ['boost::intrusive::avl_set_base_hook', 'boost::intrusive::avl_set_member_hook',
                     'boost::intrusive::bs_set_base_hook', 'boost::intrusive::bs_set_member_hook',
                     'boost::intrusive::list_base_hook', 'boost::intrusive::list_member_hook',
                     'boost::intrusive::slist_base_hook', 'boost::intrusive::slist_member_hook',
                     'boost::intrusive::set_base_hook', 'boost::intrusive::set_member_hook',
                     'boost::intrusive::splay_set_base_hook', 'boost::intrusive::splay_set_member_hook',
                     'boost::intrusive::unordered_set_base_hook', 'boost::intrusive::unordered_set_member_hook']

    def __init__(self, value):
        self.val = value

    def to_string(self):
        return '<content hidden>' if options.get('hide_intrusive_hooks', False) else None

    def children(self):
        if not options.get('hide_intrusive_hooks', False):
            for field in self.val.type.fields():
                field_name_str = field.name if field.name is not None else '<anonymous>'
                yield field_name_str, self.val[field]


# resolve bhtraits::node_traits
#   node_traits is the 2nd template argument
#
#@add_to_dict(inner_type, ('boost::intrusive::bhtraits', 'node_traits'))
def f(vtt):
    return vtt.template_argument(1)

# resolve mhtraits::node_traits
#   hook is 2nd template parameter (e.g. "list_member_hook")
#   generic_hook is 1st subclass of hook
#   1.55:
#     the 1st template parameter of generic_hook is get_node_algo
#     we hard-code node_traits as a function of get_node_algo
#   1.57:
#     the 1st template arg of generic_hook is the node_algo type
#     the 1st template arg of node_algo type is node_traits
#
#@add_to_dict(inner_type, ('boost::intrusive::mhtraits', 'node_traits'))
def f(vtt):
    gen_hook_t = vtt.template_argument(1).fields()[0].type
    template_arg_t = gen_hook_t.template_argument(0)
    if template_name(template_arg_t).startswith('boost::intrusive::get_'):
        # in 1.55, template_arg_t is of the form "get_*_node_algo"
        voidptr_t = template_arg_t.template_argument(0)
        for case in switch(template_name(template_arg_t)):
            if case('boost::intrusive::get_list_node_algo'):
                return lookup_type('boost::intrusive::list_node_traits<' + str(voidptr_t) + '>')
            if case('boost::intrusive::get_slist_node_algo'):
                return lookup_type('boost::intrusive::slist_node_traits<' + str(voidptr_t) + '>')
            if case('boost::intrusive::get_set_node_algo'):
                opt_size = template_arg_t.template_argument(1)
                return lookup_type('boost::intrusive::rbtree_node_traits<' + str(voidptr_t) + ',' + str(opt_size) + '>')
            if case('boost::intrusive::get_avl_set_node_algo'):
                opt_size = template_arg_t.template_argument(1)
                return lookup_type('boost::intrusive::avltree_node_traits<' + str(voidptr_t) + ',' + str(opt_size) + '>')
            if case('boost::intrusive::get_bs_set_node_algo'):
                return lookup_type('boost::intrusive::tree_node_traits<' + str(voidptr_t) + '>')
    else:
        # in 1.57, temlpate_arg_t is the node_algo type itself
        # its first template argument node_traits
        return template_arg_t.template_argument(0)
    assert False, 'could not determine node_traits'

# resolve trivial_value_traits::node_traits
#   node_traits is the 1st template argument
#
#@add_to_dict(inner_type, ('boost::intrusive::trivial_value_traits', 'node_traits'))
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
    def get_hook_type(value_t, tag_t):
        """Get a base hook type of a type value_t corresponding to a type tag_t"""
        value_base_types = (field.type for field in value_t.fields() if field.is_base_class)
        for value_base_type in value_base_types:
            # Checking if base_type is a hook
            for field in value_base_type.fields():
                if field.is_base_class and template_name(field.type) == 'boost::intrusive::generic_hook':
                    # Check if tag is appropriate
                    hooktags_struct = get_inner_type(field.type, 'hooktags')
                    hook_tag = get_inner_type(hooktags_struct, 'tag')
                    if get_basic_type(hook_tag) == get_basic_type(tag_t):
                        return value_base_type
        assert False, 'no subclass hook with tag: ' + str(tag_t.strip_typedefs())

    value_type = vtt.template_argument(0)
    tag_type = vtt.template_argument(3)
    hook_type = get_hook_type(value_type, tag_type)
    hook_ptr = node_rptr.cast(hook_type.pointer())
    value_ptr = hook_ptr.cast(value_type.pointer())
    return value_ptr

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


@add_printer
class Iterator_Printer:
    """Pretty Printer for boost::intrusive::(list|slist|tree)_iterator"""
    printer_name = 'boost::intrusive::iterator'
    min_supported_version = (1, 55, 0)
    max_supported_version = (1, 69, 0)
    template_name = ['boost::intrusive::list_iterator',
                     'boost::intrusive::slist_iterator',
                     'boost::intrusive::tree_iterator']

    def __init__(self, value):
        self.val = value

    def to_string(self):
        return None

    def children(self):
        value_traits_t = self.val.type.template_argument(0)
        node_rptr = unwind_references(call_object_method(self.val, 'pointed_node'))
        value_rptr = get_raw_ptr(call_static_method(value_traits_t, 'to_value_ptr', node_rptr))
        yield 'value', value_rptr.dereference()


@add_printer
class List_Printer:
    """Pretty Printer for boost::intrusive list and slist"""
    printer_name = 'boost::intrusive::list'
    min_supported_version = (1, 55, 0)
    max_supported_version = (1, 69, 0)
    template_name = ['boost::intrusive::list', 'boost::intrusive::slist']

    class Iterator:
        def __init__(self, v):
            self.value_traits_t = v.value_traits_t
            self.node_traits_t = v.node_traits_t
            self.root_node_rptr = get_raw_ptr(call_object_method(v, 'get_root_node'))

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
            index_str = '[%d @%s]' % (self.count, print_ptr(val_rptr))
            result = index_str, val_rptr.referenced_value()

            self.count += 1
            self.crt_node_rptr = get_raw_ptr(call_static_method(
                self.node_traits_t, 'get_next', self.crt_node_rptr))
            return result

        def next(self):
            return self.__next__()

    def __init__(self, v):
        self.v = v
        self.v.list_impl_t = get_basic_type(self.v.basic_type.fields()[0].type)
        self.v.value_t = self.v.basic_type.template_argument(0)
        self.v.value_traits_t = self.v.list_impl_t.template_argument(0)
        self.v.node_traits_t = get_inner_type(self.v.list_impl_t, 'node_traits')

    def to_string(self):
        return None

    def children(self):
        return self.Iterator(self.v)

    def display_hint(self):
        return 'array'


@add_printer
class Tree_Printer:
    """Pretty Printer for boost::intrusive ordered sets"""
    printer_name = 'boost::intrusive::set'
    min_supported_version = (1, 55, 0)
    max_supported_version = (1, 69, 0)

    @staticmethod
    def get_bstree_impl_base(t):
        #
        # Given a type `t`, look for a `bstree_impl` base up to 5 levels up the
        # class hierarchy. If found, also retrieve the `value_type` as the first
        # template parameter of either the super class of `bstree_impl` (when
        # this is `bstree`), or the super super (for all other trees).
        #
        t_list = list()
        while (len(t_list) < 5 and isinstance(t, gdb.Type) and t.code == gdb.TYPE_CODE_STRUCT
               and template_name(t) != 'boost::intrusive::bstree_impl'):
            t_list.append(t)
            try:
                t = get_basic_type(t.fields()[0].type)
            except:
                return None
        if isinstance(t, gdb.Type) and template_name(t) == 'boost::intrusive::bstree_impl':
            return t
        else:
            return None

    @staticmethod
    def supports(v):
        return Tree_Printer.get_bstree_impl_base(v.basic_type) != None

    class Iterator:
        def __init__(self, v):
            self.value_traits_t = v.value_traits_t
            self.node_traits_t = v.node_traits_t
            self.optimize_size = False
            if template_name(self.node_traits_t) in ['boost::intrusive::avltree_node_traits',
                                                     'boost::intrusive::rbtree_node_traits']:
                self.optimize_size = bool(self.node_traits_t.template_argument(1))
            self.header_node_rptr = get_raw_ptr(call_object_method(v.cast(v.bstree_impl_t), 'header_ptr'))

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
            index_str = '[%d @%s]' % (self.count, print_ptr(val_rptr))
            result = index_str, val_rptr.referenced_value()
            self.count += 1
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
                    n = get_raw_ptr(call_static_method(self.node_traits_t, 'get_left', self.crt_node_rptr))
                    if is_null(n):
                        break
                    self.crt_node_rptr = n
            else:
                # if right subtree is empty, find first ancestor in whose left subtree we are
                while True:
                    old_n = self.crt_node_rptr
                    self.crt_node_rptr = get_raw_ptr(call_static_method(self.node_traits_t, 'get_parent', self.crt_node_rptr))
                    if self.optimize_size:
                        self.crt_node_rptr = parse_and_eval('(' + str(get_basic_type(self.crt_node_rptr.type)) + ')(((size_t)' + str(self.crt_node_rptr).split()[0] + ') & (~(size_t)3))')
                    if self.crt_node_rptr == self.header_node_rptr:
                        break
                    n = get_raw_ptr(call_static_method(self.node_traits_t, 'get_left', self.crt_node_rptr))
                    if n == old_n:
                        break

    def __init__(self, v):
        self.v = v
        self.v.bstree_impl_t = self.get_bstree_impl_base(v.basic_type)
        self.v.value_t = get_inner_type(self.v.bstree_impl_t, 'value_type')
        self.v.value_traits_t = self.v.bstree_impl_t.template_argument(0)
        self.v.node_traits_t = get_inner_type(self.v.bstree_impl_t, 'node_traits')

    def to_string(self):
        # Print size?
        return None

    def children(self):
        return self.Iterator(self.v)

    def display_hint(self):
        return 'array'
