# coding: utf-8

from __future__ import print_function, unicode_literals, absolute_import, division
import sys
import os
import re
import inspect
import unittest
import datetime
import gdb
import boost
import boost.detect_version
from boost.variant import strip_qualifiers, apply_qualifiers

# Avoiding module 'six' because it might be unavailable
if sys.version_info.major > 2:
    text_type = str
    string_types = str
else:
    text_type = unicode
    string_types = basestring


def execute_cpp_function(function_name):
    """Run until the end of a specified C++ function (assuming the function has a label 'break_here' at the end)

    :param function_name: C++ function name (str)
    :return: None
    """
    breakpoint_location = '{}:break_here'.format(function_name)
    bp = gdb.Breakpoint(breakpoint_location, internal=True)
    bp.silent = True
    gdb.execute('run')
    assert bp.hit_count == 1
    bp.delete()


def to_python_value(value):
    """Convert a gdb.Value to its python equivalent"""
    if not isinstance(value, gdb.Value):
        return value

    type = value.type
    is_string = type.code in (gdb.TYPE_CODE_ARRAY, gdb.TYPE_CODE_PTR) \
        and type.target().code == gdb.TYPE_CODE_INT and type.target().sizeof == 1
    if is_string:
        return value.string('utf-8')
    if type.code == gdb.TYPE_CODE_INT:
        return int(value)
    if type.code == gdb.TYPE_CODE_FLT:
        return float(value)
    if type.code == gdb.TYPE_CODE_BOOL:
        return bool(value)
    if type.code == gdb.TYPE_CODE_REF:
        return to_python_value(value.referenced_value())
    if type.code == gdb.TYPE_CODE_ARRAY:
        return [to_python_value(value[idx]) for idx in range(*type.range())]
    if type.code == gdb.TYPE_CODE_STRUCT:
        return {name: to_python_value(value[field]) for name, field in gdb.types.deep_items(type) if not field.is_base_class}
    return value


def as_struct(children_values):
    """Convert children values conforming to gdb pretty-printer 'struct' protocol to a dict"""
    return {text: to_python_value(value) for text, value in children_values}


def as_array(children_values, convert_func=to_python_value):
    """Convert children values conforming to gdb pretty-printer 'array' protocol to a list"""
    return [convert_func(value) for text, value in children_values]


def as_map(children_values, key_func=to_python_value, value_func=to_python_value):
    """Convert children values conforming to gdb pretty-printer 'map' protocol to a dict"""
    assert len(children_values) % 2 == 0
    it = iter(children_values)
    return [(key_func(key), value_func(value)) for ((key_text, key), (value_text, value)) in zip(it, it)]

class PrettyPrinterTest(unittest.TestCase):
    """Base class for all printer tests"""
    def get_printer_result(self, c_variable_name):
        """Get pretty-printer output for C variable with a specified name

        :param c_variable_name: Name of a C variable
        :return: (string, [children], display_hint)
        """
        value = gdb.parse_and_eval(c_variable_name)
        pretty_printer = gdb.default_visualizer(value)
        self.assertIsNotNone(pretty_printer, 'Pretty printer was not registred')

        string = pretty_printer.to_string()
        if string is not None:
            string = text_type(string)

        if hasattr(pretty_printer, 'children'):
            children = list(pretty_printer.children())
            for child_text, _ in children:
                self.assertIsInstance(child_text, string_types)
        else:
            children = None

        if hasattr(pretty_printer, 'display_hint'):
            self.assertIsInstance(pretty_printer.display_hint(), string_types)
            display_hint = text_type(pretty_printer.display_hint())
        else:
            display_hint = None

        return string, children, display_hint

    def __str__(self):
        return '{}.{}'.format(self.__class__.__name__, self._testMethodName)


def run_printer_tests(module_contents):
    """Scan through module_contents (Iterable[Any]) and run unit tests from all PrettyPrinterTest subclasses
        matching to environment variable TEST_REGEX"""
    test_re_str = os.environ.get('TEST_REGEX', '.*')
    test_re = re.compile(test_re_str)
    test_cases = [obj for obj in module_contents
                  if inspect.isclass(obj)
                  and issubclass(obj, PrettyPrinterTest)
                  and obj is not PrettyPrinterTest
                  and test_re.search(obj.__name__)]
    test_cases.sort(key=lambda case: case.__name__)
    test_suite = unittest.TestSuite(unittest.TestLoader().loadTestsFromTestCase(test_case) for test_case in test_cases)
    return unittest.TextTestRunner(verbosity=2).run(test_suite)


# Boost version defined in test.cpp
boost_version = boost.detect_version.unpack_boost_version(int(gdb.parse_and_eval('boost_version')))


class IteratorRangeTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_iterator_range')

    def test_empty_range(self):
        string, children, display_hint = self.get_printer_result('empty_range')
        self.assertTrue(string.endswith('of length 0'))
        self.assertEqual(display_hint, 'array')
        self.assertEqual(children, [])

    def test_char_range(self):
        string, children, display_hint = self.get_printer_result('char_range')
        self.assertTrue(string.endswith('of length 13'))
        self.assertEqual(display_hint, 'array')
        self.assertEqual(as_array(children, lambda v: chr(int(v))),
                         ['h', 'e', 'l', 'l', 'o', ' ', 'd', 'o', 'l', 'l', 'y', '!', '\0'])


class OptionalTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_optional')

    def test_not_initialized(self):
        string, children, display_hint = self.get_printer_result('not_initialized')
        self.assertTrue(string.endswith('is not initialized'))
        self.assertEqual(children, [])
        self.assertIsNone(display_hint)

    def test_initialized(self):
        string, children, display_hint = self.get_printer_result('ten')
        self.assertTrue(string.endswith('is initialized'))
        self.assertEqual(as_struct(children), {'value': 10})
        self.assertIsNone(display_hint, None)


class ReferenceWrapperTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_reference_wrapper')

    def test_int_wrapper(self):
        string, children, display_hint = self.get_printer_result('int_wrapper')
        self.assertEqual(string, '(boost::reference_wrapper<int>) 42')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)


class TriboolTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_tribool')

    def test_tribool_false(self):
        string, children, display_hint = self.get_printer_result('val_false')
        self.assertTrue(string.endswith('false'))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_tribool_true(self):
        string, children, display_hint = self.get_printer_result('val_true')
        self.assertTrue(string.endswith('true'))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_tribool_indeterminate(self):
        string, children, display_hint = self.get_printer_result('val_indeterminate')
        self.assertTrue(string.endswith('indeterminate'))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)


class ScopedPtrTest(PrettyPrinterTest):
    """Test for scoped_ptr and scoped_array"""
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_scoped_ptr')

    def test_scoped_ptr_empty(self):
        string, children, display_hint = self.get_printer_result('scoped_ptr_empty')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertIsNone(display_hint)

    def test_scoped_ptr(self):
        string, children, display_hint = self.get_printer_result('scoped_ptr')
        self.assertNotEqual(string, 'uninitialized')
        self.assertEqual(as_struct(children), {'value': 42})
        self.assertIsNone(display_hint)

    def test_scoped_array_empty(self):
        string, children, display_hint = self.get_printer_result('scoped_array_empty')
        self.assertEqual(string, 'uninitialized')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_scoped_array(self):
        string, children, display_hint = self.get_printer_result('scoped_array')
        self.assertNotEqual(string, 'uninitialized')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)


@unittest.skipIf(boost_version < (1, 55), 'implemented in boost 1.55 and later')
class IntrusivePtrTest(PrettyPrinterTest):
    """Test for intrusive_ptr"""
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_ptr')

    def test_intrusive_empty(self):
        string, children, display_hint = self.get_printer_result('intrusive_empty')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertIsNone(display_hint)

    def test_intrusive(self):
        string, children, display_hint = self.get_printer_result('intrusive')
        self.assertNotEqual(string, 'uninitialized')
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['i'], 42)
        self.assertIsNone(display_hint)


class SharedPtrTest(PrettyPrinterTest):
    """Test for shared_ptr, shared_array and weak_ptr"""
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_shared_ptr')

    def test_empty_shared_ptr(self):
        string, children, display_hint = self.get_printer_result('empty_shared_ptr')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertIsNone(display_hint)

    def test_shared_ptr(self):
        string, children, display_hint = self.get_printer_result('shared_ptr')
        self.assertEqual(string, 'count 1, weak count 2')
        self.assertEqual(as_struct(children), {'value': 9})
        self.assertIsNone(display_hint)

    def test_weak_ptr(self):
        string, children, display_hint = self.get_printer_result('weak_ptr')
        self.assertEqual(string, 'count 1, weak count 2')
        self.assertEqual(as_struct(children), {'value': 9})
        self.assertIsNone(display_hint)

    def test_empty_shared_array(self):
        string, children, display_hint = self.get_printer_result('empty_shared_array')
        self.assertEqual(string, 'uninitialized')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_shared_array(self):
        string, children, display_hint = self.get_printer_result('shared_array')
        self.assertTrue(string.startswith('count 1, weak count 1'))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)


class CircularBufferTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_circular_buffer')

    def test_empty(self):
        string, children, display_hint = self.get_printer_result('empty')
        self.assertTrue(string.endswith('of length 0/3'))
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_single_element(self):
        string, children, display_hint = self.get_printer_result('single_element')
        self.assertTrue(string.endswith('of length 1/3'))
        self.assertEqual(as_array(children), [1])
        self.assertEqual(display_hint, 'array')

    def test_full(self):
        string, children, display_hint = self.get_printer_result('full')
        self.assertTrue(string.endswith('of length 3/3'))
        self.assertEqual(as_array(children), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_overwrite(self):
        string, children, display_hint = self.get_printer_result('overwrite')
        self.assertTrue(string.endswith('of length 3/3'))
        self.assertEqual(as_array(children), [2, 3, 4])
        self.assertEqual(display_hint, 'array')

    def test_reduced_size(self):
        string, children, display_hint = self.get_printer_result('reduced_size')
        self.assertTrue(string.endswith('of length 2/3'))
        self.assertEqual(as_array(children), [3, 4])
        self.assertEqual(display_hint, 'array')


class ArrayTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_array')

    def test_empty(self):
        string, children, display_hint = self.get_printer_result('empty')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_three_elements(self):
        string, children, display_hint = self.get_printer_result('three_elements')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children), [10, 20, 30])
        self.assertEqual(display_hint, 'array')


@unittest.skipIf(boost_version < (1, 58), 'implemented in boost 1.58 and later')
class SmallVectorTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_small_vector')

    def test_small_vector_1(self):
        string, children, display_hint = self.get_printer_result('small_vector_1')
        self.assertEqual(string, 'size=2 capacity=3')
        self.assertEqual(as_array(children), [1, 2])
        self.assertEqual(display_hint, 'array')

    def test_small_vector_2(self):
        string, children, display_hint = self.get_printer_result('small_vector_2')
        self.assertEqual(string, 'size=5 capacity=5')
        self.assertEqual(as_array(children), [1, 2, 3, 4, 5])
        self.assertEqual(display_hint, 'array')

    def test_small_vector_base(self):
        string, children, display_hint = self.get_printer_result('as_base_vector')
        self.assertEqual(string, 'size=2')
        self.assertEqual(as_array(children), [1, 2])
        self.assertEqual(display_hint, 'array')

    def test_empty_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        self.assertEqual(as_struct(children), {'value': 1})
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 58), 'Printer was implemented for boost 1.58 and later versions')
class StaticVectorTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_static_vector')

    def test_zero_size_vector(self):
        string, children, display_hint = self.get_printer_result('zero_size_vector')
        self.assertEqual(string, 'size=0')
        self.assertEqual(as_array(children), [])
        self.assertEqual(display_hint, 'array')

    def test_static_vector(self):
        string, children, display_hint = self.get_printer_result('static_vector')
        self.assertEqual(string, 'size=2')
        self.assertEqual(as_array(children), [1, 2])
        self.assertEqual(display_hint, 'array')

    def test_empty_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        self.assertEqual(as_struct(children), {'value': 1})
        self.assertEqual(display_hint, None)


class DynamicBitsetTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_dynamic_bitset')

    def test_empty_bitset(self):
        string, children, display_hint = self.get_printer_result('empty_bitset')
        self.assertEqual(string, 'size=0')
        self.assertEqual(as_array(children), [])
        self.assertEqual(display_hint, 'array')

    def test_big_bitset(self):
        string, children, display_hint = self.get_printer_result('bitset')
        self.assertEqual(string, 'size=130')
        expected = [0] * 130
        expected[0] = 1
        expected[2] = 1
        expected[129] = 1
        self.assertEqual(as_array(children), expected)
        self.assertEqual(display_hint, 'array')


class VariantTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_variant')

    def check_type(self, var_name):
        """Check that variable type is restored from string correctly"""
        var = gdb.parse_and_eval(var_name)
        base_type_name, qualifiers = strip_qualifiers(str(var.type))
        recovered_type = apply_qualifiers(gdb.lookup_type(base_type_name), qualifiers)
        self.assertEqual(var.type.name, recovered_type.name)

    def test_variant_a(self):
        string, children, display_hint = self.get_printer_result('variant_a')
        self.assertEqual(string, '(boost::variant<...>) type = VariantA')
        self.assertEqual(as_struct(children), {'VariantA': {'a_': 42}})
        self.assertIsNone(display_hint)

    def test_variant_b(self):
        string, children, display_hint = self.get_printer_result('variant_b')
        self.assertEqual(string, '(boost::variant<...>) type = VariantB')
        self.assertEqual(as_struct(children), {'VariantB': {'b_': 24}})
        self.assertIsNone(display_hint)

    def test_variant_t(self):
        string, children, display_hint = self.get_printer_result('variant_t')
        self.assertEqual(string, '(boost::variant<...>) type = VariantT<int>')
        self.assertEqual(as_struct(children), {'VariantT<int>': {'t_': 53}})
        self.assertIsNone(display_hint)

    def test_variant_ts(self):
        string, children, display_hint = self.get_printer_result('variant_ts')
        self.assertEqual(string, '(boost::variant<...>) type = VariantTs<int, int, int>')
        self.assertEqual(as_struct(children), {'VariantTs<int, int, int>': {'t_': 35}})
        self.assertIsNone(display_hint)

    def test_variant_char(self):
        string, children, display_hint = self.get_printer_result('variant_char')
        self.assertEqual(string, '(boost::variant<...>) type = VariantChar')
        self.assertEqual(as_struct(children), {'VariantChar': {'t_': 'hello variant!'}})
        self.assertIsNone(display_hint)

    def test_type1(self):
        self.check_type('var_type_1')

    def test_type2(self):
        self.check_type('var_type_2')

    def test_type3(self):
        self.check_type('var_type_3')


@unittest.skipIf(boost_version < (1, 42, 0), 'implemented in boost 1.42 and later')
class UuidTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_uuid')

    def test_uuid(self):
        string, children, display_hint = self.get_printer_result('uuid')
        self.assertEqual(string, '(boost::uuids::uuid) 01234567-89ab-cdef-0123-456789abcdef')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)


class DateTimeTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_date_time')

    def test_uninitialized_date(self):
        string, children, display_hint = self.get_printer_result('uninitialized_date')
        self.assertEqual(string, '(boost::gregorian::date) uninitialized')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_date(self):
        string, children, display_hint = self.get_printer_result('einstein')
        self.assertEqual(string, '(boost::gregorian::date) 1879-03-14')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_uninitialized_time(self):
        string, children, display_hint = self.get_printer_result('uninitialized_time')
        self.assertEqual(string, '(boost::posix_time::ptime) uninitialized')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_posinfin_time(self):
        string, children, display_hint = self.get_printer_result('pos_infin_time')
        self.assertEqual(string, '(boost::posix_time::ptime) positive infinity')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_neginfin_time(self):
        string, children, display_hint = self.get_printer_result('neg_infin_time')
        self.assertEqual(string, '(boost::posix_time::ptime) negative infinity')
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_time_1970_01_01(self):
        string, children, display_hint = self.get_printer_result('unix_epoch')
        dt = datetime.datetime(year=1970, month=1, day=1)
        self.assertEqual(string, '(boost::posix_time::ptime) {}Z'.format(dt))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_time_2016_02_11_09_50_45(self):
        string, children, display_hint = self.get_printer_result('ligo')
        dt = datetime.datetime(year=2016, month=2, day=11, hour=9, minute=50, second=45)
        self.assertEqual(string, '(boost::posix_time::ptime) {}Z'.format(dt))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)

    def test_time_1879_03_14(self):
        string, children, display_hint = self.get_printer_result('einstein_time')
        dt = datetime.datetime(year=1879, month=3, day=14)
        self.assertEqual(string, '(boost::posix_time::ptime) {}Z'.format(dt))
        self.assertIsNone(children)
        self.assertIsNone(display_hint)
        pass


@unittest.skipIf(boost_version < (1, 48, 0), 'implemented in boost 1.48 and later')
class FlatSetTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_flat_set')

    def test_empty_set(self):
        string, children, display_hint = self.get_printer_result('empty_set')
        self.assertEqual(string, 'boost::container::flat_set<int> size=0 capacity=0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_full_set(self):
        string, children, display_hint = self.get_printer_result('fset')
        self.assertEqual(string, 'boost::container::flat_set<int> size=2 capacity=4')
        self.assertEqual(as_array(children), [1, 2])
        self.assertEqual(display_hint, 'array')

    def test_empty_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_empty_const_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_const_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('itr')
        self.assertEqual(string, None)
        self.assertEqual(as_struct(children), {'value': 2})
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 48, 0), 'implemented in boost 1.48 and later')
class FlatMapTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_flat_map')

    def test_empty_map(self):
        string, children, display_hint = self.get_printer_result('empty_map')
        self.assertEqual(string, 'boost::container::flat_map<int, int> size=0 capacity=0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'map')

    def test_map_full(self):
        string, children, display_hint = self.get_printer_result('fmap')
        self.assertEqual(string, 'boost::container::flat_map<int, int> size=2 capacity=4')
        self.assertEqual(as_map(children), [(1, 10), (2, 20)])
        self.assertEqual(display_hint, 'map')

    def test_empty_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_empty_const_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_const_iter')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('itr')
        self.assertEqual(string, None)
        self.assertEqual(as_struct(children), {'value': {'first': 2, 'second': 20}})
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveBaseSetTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_set_base')

    def test_empty_base_set(self):
        string, children, display_hint = self.get_printer_result('empty_base_set')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_base_set_1(self):
        string, children, display_hint = self.get_printer_result('bset_1')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_base_set_2(self):
        string, children, display_hint = self.get_printer_result('bset_2')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [2, 3])
        self.assertEqual(display_hint, 'array')

    def test_base_set_iter_1(self):
        string, children, display_hint = self.get_printer_result('iter_1')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)

    def test_base_set_iter_2(self):
        string, children, display_hint = self.get_printer_result('iter_2')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 3)
        self.assertEqual(display_hint, None)


class IntrusiveMemberSetCommon:
    def test_empty_member_set(self):
        string, children, display_hint = self.get_printer_result('empty_member_set')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_member_set_1(self):
        string, children, display_hint = self.get_printer_result('member_set_1')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_member_set_2(self):
        string, children, display_hint = self.get_printer_result('member_set_2')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [2, 3])
        self.assertEqual(display_hint, 'array')

    def test_member_set_iter1(self):
        string, children, display_hint = self.get_printer_result('iter1')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 1)
        self.assertEqual(display_hint, None)

    def test_member_set_iter2(self):
        string, children, display_hint = self.get_printer_result('iter2')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberRbtreeSetTest(PrettyPrinterTest, IntrusiveMemberSetCommon):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_rbtree_set_member')


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberAvlTreeSetTest(PrettyPrinterTest, IntrusiveMemberSetCommon):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_avl_set_member')


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberSplayTreeSetTest(PrettyPrinterTest, IntrusiveMemberSetCommon):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_splay_set_member')


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberSgTreeSetTest(PrettyPrinterTest, IntrusiveMemberSetCommon):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_sg_set_member')


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveBaseListTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_list_base')

    def test_empty_base_list(self):
        string, children, display_hint = self.get_printer_result('empty_base_list')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_base_list_1(self):
        string, children, display_hint = self.get_printer_result('base_list_1')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_base_list_2(self):
        string, children, display_hint = self.get_printer_result('base_list_2')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 3])
        self.assertEqual(display_hint, 'array')

    def test_base_list_iter_1(self):
        string, children, display_hint = self.get_printer_result('iter_1')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)

    def test_base_list_iter_2(self):
        string, children, display_hint = self.get_printer_result('iter_2')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 3)
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveBaseListDefaultTagTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_list_base_default_tag')

    def test_empty_base_list(self):
        string, children, display_hint = self.get_printer_result('empty_base_list')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_base_list(self):
        string, children, display_hint = self.get_printer_result('base_list')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_base_list_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberListTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_list_member')

    def test_empty_member_list(self):
        string, children, display_hint = self.get_printer_result('empty_member_list')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_member_list_1(self):
        string, children, display_hint = self.get_printer_result('member_list_1')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_member_list_2(self):
        string, children, display_hint = self.get_printer_result('member_list_2')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [3, 2, 1])
        self.assertEqual(display_hint, 'array')

    def test_member_list_iter_1(self):
        string, children, display_hint = self.get_printer_result('iter_1')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 1)
        self.assertEqual(display_hint, None)

    def test_member_list_iter_2(self):
        string, children, display_hint = self.get_printer_result('iter_2')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 3)
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveBaseSlistTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_slist_base')

    def test_empty_list(self):
        string, children, display_hint = self.get_printer_result('empty_list')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_list_1(self):
        string, children, display_hint = self.get_printer_result('list_1')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_list_2(self):
        string, children, display_hint = self.get_printer_result('list_2')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [2, 3])
        self.assertEqual(display_hint, 'array')

    def test_iter_1(self):
        string, children, display_hint = self.get_printer_result('iter_1')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)

    def test_iter_2(self):
        string, children, display_hint = self.get_printer_result('iter_2')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 3)
        self.assertEqual(display_hint, None)


@unittest.skipUnless((1, 55, 0) <= boost_version < (1, 70, 0), 'Tests for intrusive containers are not supported for boost < 1.55 or boost >= 1.70')
class IntrusiveMemberSlistTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_intrusive_slist_member')

    def test_empty_member_list(self):
        string, children, display_hint = self.get_printer_result('empty_list')
        self.assertEqual(string, None)
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_member_list(self):
        string, children, display_hint = self.get_printer_result('list')
        self.assertEqual(string, None)
        self.assertEqual(as_array(children, lambda val: int(val['int_'])), [1, 2, 3])
        self.assertEqual(display_hint, 'array')

    def test_member_list_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        children_as_struct = as_struct(children)
        self.assertEqual(set(children_as_struct), {'value'})
        self.assertEqual(children_as_struct['value']['int_'], 2)
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 58), 'Printer was implemented for boost 1.58 and later versions')
class UnorderedMapTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_unordered_map')

    expected_content = [(10, 'ten'), (20, 'twenty'), (30, 'thirty')]

    def test_empty_map(self):
        string, children, display_hint = self.get_printer_result('empty_map')
        self.assertEqual(string, 'boost::unordered::unordered_map<int, const char *> size = 0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'map')

    def test_map(self):
        string, children, display_hint = self.get_printer_result('map')
        self.assertEqual('boost::unordered::unordered_map<int, const char *> size = 3', string)
        self.assertEqual(
            sorted(as_map(children)),
            self.expected_content)
        self.assertEqual('map', display_hint)

    def test_big_map(self):
        string, children, display_hint = self.get_printer_result('big_map')
        self.assertEqual('boost::unordered::unordered_map<int, int> size = 100000', string)
        actual_children = sorted(as_map(children))
        expected_children = [(i, i) for i in range(100000)]
        self.assertEqual(expected_children, actual_children)
        self.assertEqual('map', display_hint)

    def test_uninitialized_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        possible_values = [{'value': {'first': key, 'second': value}} for key, value in self.expected_content]
        self.assertIn(as_struct(children), possible_values)
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 58), 'Printer was implemented for boost 1.58 and later versions')
class UnorderedMultimapTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_unordered_multimap')

    expected_content = [(10, 'dieci'), (10, 'ten'), (20, 'twenty'), (20, 'venti'), (30, 'thirty'), (30, 'trenta')]

    def test_empty_multimap(self):
        string, children, display_hint = self.get_printer_result('empty_map')
        self.assertEqual(string, 'boost::unordered::unordered_multimap<int, const char *> size = 0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'map')

    def test_multimap(self):
        string, children, display_hint = self.get_printer_result('map')
        self.assertEqual('boost::unordered::unordered_multimap<int, const char *> size = 6', string)
        self.assertEqual(
            sorted(as_map(children)),
            self.expected_content)
        self.assertEqual('map', display_hint)

    def test_uninitialized_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        possible_values = [{'value': {'first': key, 'second': value}} for key, value in self.expected_content]
        self.assertIn(as_struct(children), possible_values)
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 58), 'Printer was implemented for boost 1.58 and later versions')
class UnorderedSetTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_unordered_set')

    expected_content = ['Democritus', 'Pythagoras', 'Thales']

    def test_empty_set(self):
        string, children, display_hint = self.get_printer_result('empty_set')
        self.assertEqual(string, 'boost::unordered::unordered_set<const char *> size = 0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_set(self):
        string, children, display_hint = self.get_printer_result('set')
        self.assertEqual('boost::unordered::unordered_set<const char *> size = 3', string)
        self.assertEqual(
            sorted(as_array(children)),
            self.expected_content)
        self.assertEqual('array', display_hint)

    def test_uninitialized_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        possible_values = [{'value': item} for item in self.expected_content]
        self.assertIn(as_struct(children), possible_values)
        self.assertEqual(display_hint, None)


@unittest.skipIf(boost_version < (1, 58), 'Printer was implemented for boost 1.58 and later versions')
class UnorderedMultisetTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_unordered_multiset')

    expected_content = ['Bruegel', 'Bruegel', 'Plinius', 'Plinius']

    def test_empty_multiset(self):
        string, children, display_hint = self.get_printer_result('empty_multiset')
        self.assertEqual(string, 'boost::unordered::unordered_multiset<const char *> size = 0')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, 'array')

    def test_multiset(self):
        string, children, display_hint = self.get_printer_result('multiset')
        self.assertEqual('boost::unordered::unordered_multiset<const char *> size = 4', string)
        self.assertEqual(
            sorted(as_array(children)),
            self.expected_content)
        self.assertEqual('array', display_hint)

    def test_uninitialized_iter(self):
        string, children, display_hint = self.get_printer_result('uninitialized_iter')
        self.assertEqual(string, 'uninitialized')
        self.assertEqual(children, [])
        self.assertEqual(display_hint, None)

    def test_iter(self):
        string, children, display_hint = self.get_printer_result('iter')
        self.assertEqual(string, None)
        possible_values = [{'value': item} for item in self.expected_content]
        self.assertIn(as_struct(children), possible_values)
        self.assertEqual(display_hint, None)

class DurationTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_duration')

    def test_empty(self):
        string, children, display_hint = self.get_printer_result('empty_duration')
        self.assertEqual(string,'(boost::posix_time::time_duration) 0')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

    def test_duration_130(self):
        string, children, display_hint = self.get_printer_result('duration_130')
        self.assertEqual(string,'(boost::posix_time::time_duration) 2m 10s')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

    def test_duration_neg_130(self):
        string, children, display_hint = self.get_printer_result('duration_neg_130')
        self.assertEqual(string,'(boost::posix_time::time_duration) -2m 10s')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

    def test_duration_with_ms(self):
        string, children, display_hint = self.get_printer_result('duration_with_ms')
        self.assertEqual(string,'(boost::posix_time::time_duration) 1m 1.010000s')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

    def test_duration_not_a_time(self):
        string, children, display_hint = self.get_printer_result('duration_not_a_time')
        self.assertEqual(string,'(boost::posix_time::time_duration) not a date time')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

    def test_duration_3600(self):
        string, children, display_hint = self.get_printer_result('duration_3600')
        self.assertEqual(string,'(boost::posix_time::time_duration) 1h')
        self.assertEqual(children, None)
        self.assertEqual(display_hint, None)

@unittest.skipIf(boost_version < (1, 56, 0), 'implemented in boost 1.56 and later')
class MultiIndexTest(PrettyPrinterTest):
    @classmethod
    def setUpClass(cls):
        execute_cpp_function('test_multi_index')

    def test_sequened_first_empty(self):
        string, children, display_hint = self.get_printer_result('sf_empty')
        self.assertTrue(string.startswith('empty'))
        self.assertEqual(as_array(children, int), [])
        self.assertIsNone(display_hint)

    def test_ordered_first_empty(self):
        string, children, display_hint = self.get_printer_result('of_empty')
        self.assertTrue(string.startswith('empty'))
        self.assertEqual(as_array(children, int), [])
        self.assertIsNone(display_hint)

    def test_hashed_first_empty(self):
        string, children, display_hint = self.get_printer_result('hf_empty')
        self.assertTrue(string.startswith('empty'))
        self.assertEqual(as_array(children, int), [])
        self.assertIsNone(display_hint)

    def test_sequened_first(self):
        string, children, display_hint = self.get_printer_result('sf_two')
        self.assertEqual(as_array(children, int), [ 1, 2 ])
        self.assertIsNone(display_hint)

    def test_ordered_first(self):
        string, children, display_hint = self.get_printer_result('of_two')
        self.assertEqual(as_array(children, int), [ 1, 2 ])
        self.assertIsNone(display_hint)

    def test_hashed_first(self):
        string, children, display_hint = self.get_printer_result('hf_two')
        self.assertEqual(sorted(as_array(children, int)), [ 1, 2 ]) # unordered
        self.assertIsNone(display_hint)

    def test_hashed_first_over2_same_value(self):
        string, children, display_hint = self.get_printer_result('hf_over_two_same_value')
        self.assertEqual(sorted(as_array(children, int)), [ 1, 1, 1, 2, 2, 2, 2, 3, 3, 4]) # unordered
        self.assertIsNone(display_hint)


# TODO: More intrusive tests:
# 1. Non-raw pointers
# 2. Custom node traits

# TODO: More printers:
# 1. Pointer containers
# 2. boost 1.65: poly_collection, atomic_shared_ptr, local_shared_ptr
# 3. Boost.Lockfree ?
# 4. Rest of Boost.Containers?

print('*** GDB version:', gdb.VERSION)
print('*** Python version: {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
print('*** Boost version: {}.{}.{}'.format(*boost_version))
boost.register_printers(boost_version=boost_version)
test_result = run_printer_tests(globals().values())
sys.exit(0 if test_result.wasSuccessful() else 1)
