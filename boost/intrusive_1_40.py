# coding: utf-8

##################################################
# boost::intrusive::set                          #
##################################################

from .utils import *

def get_named_template_argument(gdb_type, arg_name):
    n = 0
    while True:
        try:
            arg = gdb_type.strip_typedefs().template_argument(n)
            if (str(arg).startswith(arg_name)):
                return arg
            n += 1
        except RuntimeError:
            return None

def intrusive_container_has_size_member(intrusive_container_type):
    constant_size_arg = get_named_template_argument(intrusive_container_type, "boost::intrusive::constant_time_size")
    if not constant_size_arg:
        return True
    if str(constant_size_arg.template_argument(0)) == 'false':
        return False
    return True

def intrusive_iterator_to_string(iterator_value):
    opttype = iterator_value.type.template_argument(0).template_argument(0)

    base_hook_traits = get_named_template_argument(opttype, "boost::intrusive::detail::base_hook_traits")
    if base_hook_traits:
        value_type = base_hook_traits.template_argument(0)
        return iterator_value["members_"]["nodeptr_"].cast(value_type.pointer()).dereference()

    member_hook_traits = get_named_template_argument(opttype, "boost::intrusive::detail::member_hook_traits")
    if member_hook_traits:
        value_type = member_hook_traits.template_argument(0)
        member_offset = member_hook_traits.template_argument(2).cast(lookup_type("size_t"))
        current_element_address = iterator_value["members_"]["nodeptr_"].cast(lookup_type("size_t")) - member_offset
        return current_element_address.cast(value_type.pointer()).dereference()

    return iterator_value["members_"]["nodeptr_"]

@add_printer
class BoostIntrusiveSet:
    "Pretty Printer for boost::intrusive::set (Boost.Intrusive)"
    printer_name = 'boost::intrusive::set'
    min_supported_version = (1, 40, 0)
    max_supported_version = (1, 54, 0)
    template_name = 'boost::intrusive::set'

    class Iterator:
        def __init__(self, rb_tree_header, element_pointer_type, member_offset=0):
            self.header = rb_tree_header
            self.member_offset = member_offset
            if member_offset == 0:
                self.node_type = element_pointer_type
            else:
                self.node_type = lookup_type("boost::intrusive::rbtree_node<void*>").pointer();
                self.element_pointer_type = element_pointer_type

            if rb_tree_header['parent_']:
                self.node = rb_tree_header['left_'].cast(self.node_type)
            else:
                self.node = 0

            self.count = 0

        def __iter__(self):
            return self

        def get_element_pointer_from_node_pointer(self):
            if self.member_offset == 0:
                return self.node
            else:
                current_element_address = self.node.cast(lookup_type("size_t")) - self.member_offset
                return current_element_address.cast(self.element_pointer_type)

        def __next__(self):
            # empty set or reached rightmost leaf
            if not self.node:
                raise StopIteration
            item = self.get_element_pointer_from_node_pointer().dereference()
            if self.node != self.header["right_"].cast(self.node_type):
                # Compute the next node.
                node = self.node
                if node.dereference()['right_']:
                    node = node.dereference()['right_']
                    while node.dereference()['left_']:
                        node = node.dereference()['left_']
                else:
                    parent = node.dereference()['parent_']
                    while node == parent.dereference()['right_']:
                        node = parent
                        parent = parent.dereference()['parent_']
                    if node.dereference()['right_'] != parent:
                        node = parent
                self.node = node.cast(self.node_type)
            else:
                self.node = 0
            result = ('[%d]' % self.count, item)
            self.count = self.count + 1
            return result

        def next(self):
            return self.__next__()

    def __init__(self, value):
        self.typename = value.type_name
        self.val = value
        self.element_type = self.val.type.strip_typedefs().template_argument(0)

    def get_header(self):
        return self.val["tree_"]["data_"]["node_plus_pred_"]["header_plus_size_"]["header_"]

    def get_size(self):
        return self.val["tree_"]["data_"]["node_plus_pred_"]["header_plus_size_"]["size_"]

    def has_elements(self):
        header = self.get_header()
        first_element = header["parent_"]
        if first_element:
            return True
        else:
            return False

    def to_string (self):
        if (intrusive_container_has_size_member(self.val.type)):
            return "boost::intrusive::set<%s> with %d elements" % (self.element_type, self.get_size())
        elif (self.has_elements()):
            return "non-empty boost::intrusive::set<%s>" % self.element_type
        else:
            return "empty boost::intrusive::set<%s>" % self.element_type

    def children (self):
        element_pointer_type = self.element_type.pointer()
        member_hook = get_named_template_argument(self.val.type, "boost::intrusive::member_hook")
        if member_hook:
            member_offset = member_hook.template_argument(2).cast(lookup_type("size_t"))
            return self.Iterator(self.get_header(), element_pointer_type, member_offset)
        else:
            return self.Iterator(self.get_header(), element_pointer_type)


@add_printer
class BoostIntrusiveTreeIterator:
    "Pretty Printer for boost::intrusive::set<*>::iterator (Boost.Intrusive)"
    printer_name = 'boost::intrusive::tree_iterator'
    min_supported_version = (1, 40, 0)
    max_supported_version = (1, 54, 0)
    template_name = 'boost::intrusive::tree_iterator'

    def __init__(self, value):
        self.val = value
        self.typename = value.type_name

    def to_string(self):
        return intrusive_iterator_to_string(self.val)


##################################################
# boost::intrusive::list                         #
##################################################

@add_printer
class BoostIntrusiveList:
    "Pretty Printer for boost::intrusive::list (Boost.Intrusive)"
    printer_name = 'boost::intrusive::list'
    min_supported_version = (1, 40, 0)
    max_supported_version = (1, 54, 0)
    template_name = 'boost::intrusive::list'

    class Iterator:
        def __init__(self, list_header, element_pointer_type, member_offset=0):
            self.header = list_header

            self.member_offset = member_offset
            if member_offset == 0:
                self.node_type = element_pointer_type
            else:
                self.node_type = lookup_type("boost::intrusive::list_node<void*>").pointer();
                self.element_pointer_type = element_pointer_type

            next_node = list_header['next_']
            if next_node != list_header.address:
                self.node = next_node.cast(self.node_type)
            else:
                self.node = 0

            self.count = 0

        def __iter__(self):
            return self

        def get_element_pointer_from_node_pointer(self):
            if self.member_offset == 0:
                return self.node
            else:
                current_element_address = self.node.cast(lookup_type("size_t")) - self.member_offset
                return current_element_address.cast(self.element_pointer_type)

        def __next__(self):
            # empty list or reached end
            if not self.node:
                raise StopIteration
            item = self.get_element_pointer_from_node_pointer().dereference()
            next_node = self.node['next_']
            if next_node != self.header.address:
                self.node = next_node.cast(self.node_type)
            else:
                self.node = 0
            result = ('[%d]' % self.count, item)
            self.count = self.count + 1
            return result

        def next(self):
            return self.__next__()

    def __init__(self, value):
        self.typename = value.type_name
        self.val = value
        self.element_type = self.val.type.strip_typedefs().template_argument(0)

    def get_header(self):
        return self.val["data_"]["root_plus_size_"]["root_"]

    def get_size(self):
        return self.val["data_"]["root_plus_size_"]["size_"]

    def has_elements(self):
        header = self.get_header()
        first_element = header["next_"]
        root_element = header.address
        if first_element != root_element:
            return True
        else:
            return False

    def to_string(self):
        if (intrusive_container_has_size_member(self.val.type)):
            return "boost::intrusive::list<%s> with %d elements" % (self.element_type, self.get_size())
        elif (self.has_elements()):
            return "non-empty boost::intrusive::list<%s>" % self.element_type
        else:
            return "empty boost::intrusive::list<%s>" % self.element_type

    def children(self):
        element_pointer_type = self.element_type.pointer()
        member_hook = get_named_template_argument(self.val.type, "boost::intrusive::member_hook")
        if member_hook:
            member_offset = member_hook.template_argument(2).cast(lookup_type("size_t"))
            return self.Iterator(self.get_header(), element_pointer_type, member_offset)
        else:
            return self.Iterator(self.get_header(), element_pointer_type)

@add_printer
class BoostIntrusiveListIterator:
    "Pretty Printer for boost::intrusive::list<*>::iterator (Boost.Intrusive)"
    printer_name = 'boost::intrusive::list_iterator'
    min_supported_version = (1, 40, 0)
    max_supported_version = (1, 54, 0)
    template_name = '^boost::intrusive::list_iterator'

    def __init__(self, value):
        self.val = value

    def to_string(self):
        return intrusive_iterator_to_string(self.val)
