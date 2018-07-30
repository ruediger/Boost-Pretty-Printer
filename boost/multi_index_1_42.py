# coding: utf-8

from .utils import *

#
# Some utility methods.
#

def _paren_split(s, target_paren = '<'):
    "Split the given string at commas (,) at the first paranthesis sublevel of target_paren, ignoring commas within other paranthesized blocks. This can be used to extract template arguments."
    open_parens = '([{<'
    close_parens = ')]}>'
    end_paren = {}
    end_paren['('] = ')'
    end_paren['['] = ']'
    end_paren['{'] = '}'
    end_paren['<'] = '>'
    if target_paren not in open_parens:
        message('error: _paren_split: target_paren [' + target_paren + '] must be one of [' + open_parens + ']')
        return None
    paren_stack = []
    res = []
    st = 0
    for i in xrange(len(s)):
        if s[i] in open_parens:
            if len(paren_stack) == 0 and s[i] == target_paren:
                st = i + 1
            paren_stack.append(s[i])
        elif s[i] in close_parens:
            if len(paren_stack) == 0 or s[i] != end_paren[paren_stack[-1]]:
                # mismatched parens
                return None
            if len(paren_stack) == 1 and paren_stack[0] == target_paren:
                res += [[st, i]]
                st = i + 1
            del paren_stack[-1]
        elif s[i] == ',':
            if len(paren_stack) == 0:
                # comma among primary identifiers
                return None
            if len(paren_stack) == 1 and paren_stack[0] == target_paren:
                res += [[st, i]]
                st = i + 1
    return res

def _strip_inheritance_qual(s):
    if s.startswith('public '):
        return s[7:]
    if s.startswith('private '):
        return s[8:]
    if s.startswith('protected '):
        return s[10:]
    return s

def _boost_multi_index_get_indexes(v):
    "Save the index types of a multi_index_container in v.indexes."
    v.main_args = _paren_split(str(v.basic_type))
    if len(v.main_args) != 3:
        message('error parsing: ' + str(v.basic_type))
        return False
    arg2_str = str(v.basic_type)[v.main_args[1][0]:v.main_args[1][1]] # the 2nd template arg
    arg2_args = _paren_split(arg2_str)
    if len(arg2_args) == 0:
        message('error parsing arg2 of: ' + str(v.basic_type))
        return False
    v.indexes = []
    for r in arg2_args:
        v.indexes.append(arg2_str[r[0]:r[1]].split('<')[0].strip())

# The size in pointers of the index fields for all index types.
_boost_multi_index_index_size = {}
_boost_multi_index_index_size['boost::multi_index::ordered_unique'] = 3
_boost_multi_index_index_size['boost::multi_index::ordered_non_unique'] = 3
_boost_multi_index_index_size['boost::multi_index::hashed_unique'] = 1
_boost_multi_index_index_size['boost::multi_index::hashed_non_unique'] = 1
_boost_multi_index_index_size['boost::multi_index::sequenced'] = 2
_boost_multi_index_index_size['boost::multi_index::random_access'] = 1

#
# The following is an experimental printer for boost::multi_index_container
# using ordered unique/nonunique or sequenced index. This might not always
# work for various reasons.
#
# 1. I did not fully decode the templated construction of these containers.
# For further hacks, here are the assumptions made by the current code:
# - Given the address x of a boost::multi_index_container object, one can find
#   the address of the head node by casting the container into its second
#   subclass, and following the 'member' pointer.
# - Each node is stored in memory as:
#   (Element, index_n-1_fields, ..., index_0_fields)
# - The size of an Element is rounded up to the next multiple of 8.
# - The size of the index fields for various indexes are in
#   _boost_multi_index_index_size (in number of pointers).
# - For ordered & sequenced indexes:
# - The i-th index field pointers (3 for ordered, 2 for sequenced) point to the
#   address of the destination node's i-th index fields pointers (not to the
#   address of the destination node's Element).
# - The head node pointer of the multiindex container points to the head node's
#   Element address.
# - For ordered indexes:
#   - The last bit of parent_ptr is used to store the node color in the tree, so
#     it must be AND-ed to 0 before following the ptr.
#   - Inside the head node, the pointers specify:
#     parent_ptr: root node
#     left_ptr: node with smallest element
#     right_ptr: node with largest element
#   - The elements are stored in a sorted binary tree (probably balanced, but we
#     don't care about that for printing). So, given a node x, all nodes in the
#     left subtree of x appear before x when ordered, and all nodes in the right
#     subtree appear after x.
# - For sequenced indexes:
#   - The index field contains: previous@0 and next@1.
#   - To traverse the container, keep following next pointers until returning
#     back to the head node.
#
# 2. The python framework in gdb is limited. To cast a
# boost::multi_index_container to one of its super classes, I use an awkward
# parse_and_eval() that can be broken by as little as output formatting changes.
#

@add_printer
class Boost_Multi_Index:
    "Printer for boost::multi_index_container"
    printer_name = 'boost::multi_index_container'
    min_supported_version = (1, 42, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::multi_index::multi_index_container'

    #
    # Not supported indexes (hashes and random-access) are captured and printed
    # by this subprinter. To disable this, set this to False. This can be set in
    # the source code, in .gdbinit where the printers are loaded, or dynamically
    # from inside gdb.
    #
    print_not_supported = True

    @classmethod
    def supports(self_type, v):
        _boost_multi_index_get_indexes(v)
        #message('address=' + str(intptr(v.address)) + ' multi_index_selector=' + str(multi_index_selector))
        if intptr(v.address) in multi_index_selector:
            v.idx = multi_index_selector[intptr(v.address)]
            #message('address found')
        else:
            v.idx = 0
            #message('address not found')
        if v.idx >= len(v.indexes):
            return False
        return (self_type.print_not_supported
                or v.indexes[v.idx] == 'boost::multi_index::ordered_unique'
                or v.indexes[v.idx] == 'boost::multi_index::ordered_non_unique'
                or v.indexes[v.idx] == 'boost::multi_index::hashed_unique'
                or v.indexes[v.idx] == 'boost::multi_index::hashed_non_unique'
                or v.indexes[v.idx] == 'boost::multi_index::sequenced')

    @staticmethod
    def get_val_ptr(node_ptr, index_offset):
        return node_ptr - index_offset

    def __init__(self, v):
        # clear up the type_name:
        # pick template name
        self.type_name = v.type_name[0:v.main_args[0][0]].strip()[:-1]
        # add 2 args only (omit allocator)
        self.type_name += ('<'
                           + v.type_name[v.main_args[0][0]:v.main_args[0][1]].strip()
                           + ', '
                           + v.type_name[v.main_args[1][0]:v.main_args[1][1]].strip()
                           + '>')
        # remove bulk
        self.type_name = ''.join(self.type_name.split('boost::multi_index::detail::'))
        self.type_name = ''.join(self.type_name.split('boost::multi_index::'))
        self.type_name = ''.join(self.type_name.split('boost::detail::'))
        self.type_name = ''.join(self.type_name.split(', mpl_::na'))
        self.type_name = ''.join(self.type_name.split('mpl_::na'))
        self.type_name = ''.join(self.type_name.split('tag<>'))
        self.type_name = '<>'.join(self.type_name.split('< >'))
        self.type_name = 'boost::' + self.type_name
        # add index specifier
        self.type_name += '[idx=' + str(v.idx) + ']'
        #message('type_name: ' + self.type_name)

        # index type
        self.index_type = v.indexes[v.idx]

        # node count
        self.node_count = int(v['node_count'])

        # first, we need the element type
        self.elem_type = v.basic_type.template_argument(0)
        #message('elem_type: ' + str(self.elem_type))

        # next, we compute the element size and round it up to the pointer size
        ptr_size = gdb.lookup_type('void').pointer().sizeof
        self.elem_size = ((self.elem_type.sizeof - 1) / ptr_size + 1) * ptr_size
        #message('elem_size: ' + str(self.elem_size))

        # next, we cast the object into its 2nd subtype which should be header_holder
        # and retrieve the head node
        #header_holder_subtype = _get_subtype(v.basic_type, 1)
        header_holder_subtype = v.basic_type.fields()[1].type
        if header_holder_subtype == None:
            message('error computing 2nd subtype of ' + str(v.basic_type))
            return None
        if not str(header_holder_subtype).strip().startswith('boost::multi_index::detail::header_holder'):
            message('2nd subtype of multi_index_container is not header_holder')
            return None
        head_node = v.cast(header_holder_subtype)['member'].dereference()
        #message('head_node.type.sizeof: ' + str(head_node.type.sizeof))

        # finally, we compute the offset from the element address
        # to the index field address, as well as the address of the parent_ptr
        # inside the head node
        # to do that, we compute the size of all indexes prior to the current one
        self.index_offset = head_node.type.sizeof
        for i in xrange(v.idx + 1):
            self.index_offset -= _boost_multi_index_index_size[v.indexes[i]] * ptr_size
        #message('index_offset: ' +  str(self.index_offset))

        self.head_index_ptr = intptr(head_node.address) + self.index_offset
        #message('head_index_ptr: ' + hex(self.head_index_ptr))

        # offset for hashed_index
        self.index_offset_for_hash = head_node.type.sizeof - (v.idx + 1) * ptr_size * 2
        self.head_index_ptr_for_hash = intptr(head_node.address) + self.index_offset_for_hash

    def empty_cont(self):
        return self.node_count == 0

    class empty_iterator:
        def __init__(self):
            pass
        def __iter__(self):
            return self
        def __next__(self):
            raise StopIteration
        def next(self):
            return self.__next__()

    class na_iterator:
        def __init__(self, index_type):
            self.saw_msg = False
            self.index_type = index_type
        def __iter__(self):
            return self
        def __next__(self):
            if not self.saw_msg:
                self.saw_msg = True
                return (self.index_type, 'printer not implemented')
            raise StopIteration
        def next(self):
            return self.__next__()

    class ordered_iterator:
        @staticmethod
        def get_parent_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ')')), 16) & (~intptr(1))

        @staticmethod
        def get_left_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ' + 1)')), 16)

        @staticmethod
        def get_right_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ' + 2)')), 16)

        def __init__(self, elem_type, index_offset, first, last):
            self.elem_type = elem_type
            self.index_offset = index_offset
            self.crt = first
            self.last = last
            self.saw_last = False
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.crt == self.last and self.saw_last:
                raise StopIteration
            crt = self.crt
            #message('crt: ' + hex(crt))
            if self.crt == self.last:
                self.saw_last = True
            else:
                if self.get_right_ptr(self.crt) != 0:
                    # next is leftmost node in right subtree
                    #message('next is in right subtree')
                    self.crt = self.get_right_ptr(self.crt)
                    while self.get_left_ptr(self.crt) != 0:
                        self.crt = self.get_left_ptr(self.crt)
                else:
                    # next is first ancestor from which crt is in left subtree
                    #message('next is an ancestor')
                    while True:
                        old_crt = self.crt
                        self.crt = self.get_parent_ptr(self.crt)
                        if self.get_left_ptr(self.crt) == old_crt:
                            break
                #message('next: ' + hex(self.crt))
            count = self.count
            self.count = self.count + 1
            val_ptr = Boost_Multi_Index.get_val_ptr(crt, self.index_offset)
            return ('[%s]' % hex(int(val_ptr)),
                    str(parse_and_eval('*(' + str(self.elem_type) + '*)'
                                       + str(val_ptr))))

        def next(self):
            return self.__next__()

    class hashed_iterator:
        @staticmethod
        def get_prev_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ')')), 16)

        @staticmethod
        def get_next_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ' + 1)')), 16)

        def __init__(self, elem_type, index_offset, begin, end):
            self.elem_type = elem_type
            self.index_offset = index_offset
            self.crt = begin
            self.end = end
            self.count = 0
            self.trace = set()

        def __iter__(self):
            return self

        def __next__(self):
            if self.crt == self.end:
                raise StopIteration
            crt = self.crt
            self.trace.add(crt)
            self.crt = self.get_prev_ptr(self.crt)
            if self.crt in self.trace:
                self.trace.clear()
                self.crt = self.get_prev_ptr(self.crt)
                self.crt = self.get_next_ptr(self.crt)
            count = self.count
            self.count = self.count + 1
            val_ptr = Boost_Multi_Index.get_val_ptr(crt, self.index_offset)
            return ('[%s]' % hex(int(val_ptr)),
                    str(parse_and_eval('*(' + str(self.elem_type) + '*)'
                                       + str(val_ptr))))

        def next(self):
            return self.__next__()

    class sequenced_iterator:
        @staticmethod
        def get_prev_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ')')), 16)

        @staticmethod
        def get_next_ptr(node_ptr):
            return intptr(str(parse_and_eval('*((void**)' + str(node_ptr) + ' + 1)')), 16)

        def __init__(self, elem_type, index_offset, begin, end):
            self.elem_type = elem_type
            self.index_offset = index_offset
            self.crt = begin
            self.end = end
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.crt == self.end:
                raise StopIteration
            crt = self.crt
            self.crt = self.get_next_ptr(self.crt)
            count = self.count
            self.count = self.count + 1
            val_ptr = Boost_Multi_Index.get_val_ptr(crt, self.index_offset)
            return ('[%s]' % hex(int(val_ptr)),
                    str(parse_and_eval('*(' + str(self.elem_type) + '*)'
                                       + str(val_ptr))))

        def next(self):
            return self.__next__()

    def children(self):
        if self.empty_cont():
            return self.empty_iterator()
        if (self.index_type == 'boost::multi_index::ordered_unique'
            or self.index_type == 'boost::multi_index::ordered_non_unique'):
            return self.ordered_iterator(
                self.elem_type,
                self.index_offset,
                self.ordered_iterator.get_left_ptr(self.head_index_ptr),
                self.ordered_iterator.get_right_ptr(self.head_index_ptr))
        elif (self.index_type == 'boost::multi_index::hashed_unique'
            or self.index_type == 'boost::multi_index::hashed_non_unique'):
            return self.hashed_iterator(
                self.elem_type,
                self.index_offset_for_hash,
                self.hashed_iterator.get_prev_ptr(self.head_index_ptr_for_hash),
                self.head_index_ptr_for_hash)
        elif self.index_type == 'boost::multi_index::sequenced':
            return self.sequenced_iterator(
                self.elem_type,
                self.index_offset,
                self.sequenced_iterator.get_next_ptr(self.head_index_ptr),
                self.head_index_ptr)
        return self.na_iterator(self.index_type)

    def to_string(self):
        if self.empty_cont():
            return 'empty %s' % self.type_name
        return '%s' % self.type_name
