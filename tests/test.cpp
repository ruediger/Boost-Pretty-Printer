#include <string>
#include <tuple>

#include <boost/version.hpp>
#include <boost/range/iterator_range.hpp>
#include <boost/optional.hpp>
#include <boost/ref.hpp>
#include <boost/logic/tribool.hpp>

#include <boost/smart_ptr.hpp>
#if BOOST_VERSION >= 105500
#include <boost/smart_ptr/intrusive_ref_counter.hpp>
#endif

#include <boost/circular_buffer.hpp>

#include <boost/array.hpp>
#include <boost/variant.hpp>
#include <boost/uuid/uuid.hpp>

#include <boost/container/flat_set.hpp>
#include <boost/container/flat_map.hpp>

#include <boost/intrusive/set.hpp>
#include <boost/intrusive/list.hpp>
#include <boost/date_time/gregorian/gregorian.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

unsigned const boost_version = BOOST_VERSION;

void test_iterator_range()
{
	char const text[] = "hello dolly!";
	boost::iterator_range<char const*> empty_range;
	boost::iterator_range<char const*> char_range(std::begin(text), std::end(text));
break_here:
	;
}

void test_optional()
{
	boost::optional<int> not_initialized;
	boost::optional<int> ten(10);
	// Something is wrong?!
	//char const text[] = "hello dolly!";
	//boost::optional<char const*> dolly(text);
break_here:
	;
}

void test_reference_wrapper()
{
	int x = 42;
	boost::reference_wrapper<int> int_wrapper(x);
break_here:
	;
}

void test_tribool()
{
	boost::logic::tribool val_false;
	boost::logic::tribool val_true(true);
	boost::logic::tribool val_indeterminate(boost::logic::indeterminate);
break_here:
	;
}

void test_scoped_ptr()
{
	boost::scoped_ptr<int> scoped_ptr_empty;
	boost::scoped_ptr<int> scoped_ptr(new int(42));

	boost::scoped_array<int> scoped_array_empty;
	boost::scoped_array<int> scoped_array(new int[1]);
	scoped_array[0] = 42;
break_here:
	;
}

void test_intrusive_ptr()
{
#if BOOST_VERSION >= 105500
	struct S: public boost::intrusive_ref_counter<S>
	{
		int i;
	};

	boost::intrusive_ptr<S> intrusive_empty;
	boost::intrusive_ptr<S> intrusive(new S);
	intrusive->i = 42;
#endif
break_here:
	;
}


void test_shared_ptr()
{
	boost::shared_ptr<int> empty_shared_ptr;
	boost::shared_ptr<int> shared_ptr(new int(9));
	boost::weak_ptr<int> weak_ptr(shared_ptr);

	boost::shared_array<int> empty_shared_array;
	boost::shared_array<int> shared_array(new int[1]);
break_here:
	;
}

void test_circular_buffer()
{
	boost::circular_buffer<int> empty(3);

	auto single_element = empty;
	single_element.push_back(1);

	auto full = single_element;
	full.push_back(2);
	full.push_back(3);

	auto overwrite = full;
	overwrite.push_back(4);

	auto reduced_size = overwrite;
	reduced_size.pop_front();
break_here:
	;
}

void test_array()
{
	boost::array<int, 0> empty;
	boost::array<int, 3> three_elements = { 10, 20, 30 };
break_here:
	;
}

void test_variant()
{
	boost::variant<int, bool> variant_int(42);
	boost::variant<int, bool> variant_bool(true);
break_here:
	;
}

void test_uuid()
{
	boost::uuids::uuid uuid = {
		0x01 ,0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
		0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef };
break_here:
	;
}

void test_date_time()
{
	using namespace boost::gregorian;
	using namespace boost::posix_time;
	date uninitialized_date;
	date einstein(1879, Mar, 14);

	ptime uninitialized_time;
	ptime pos_infin_time = pos_infin;
	ptime neg_infin_time = neg_infin;
	ptime unix_epoch(date(1970, 1, 1));
	ptime einstein_time(einstein);
	ptime ligo(date(2016, Feb, 11), hours(9) + minutes(50) + seconds(45));
break_here:
	;
}

void test_flat_set()
{
	using FlatSetOfInt = boost::container::flat_set<int>;

	FlatSetOfInt empty_set;
	FlatSetOfInt::iterator uninitialized_iter;
	FlatSetOfInt::const_iterator uninitialized_const_iter;

	FlatSetOfInt fset;
	fset.insert(1);
	fset.insert(2);
	auto itr = fset.find(2);
break_here:
	;
}

void test_flat_map()
{
	using FlatMapOfInt = boost::container::flat_map<int, int>;
	FlatMapOfInt empty_map;
break_here:
	;
}

void test_intrusive_set()
{
break_here:
	;
}

void test_intrusive_list()
{
break_here:
	;
}

int main()
{
	test_iterator_range();
	test_optional();
	test_reference_wrapper();
	test_tribool();
	test_scoped_ptr();
	test_intrusive_ptr();
	test_shared_ptr();
	test_circular_buffer();
	test_array();
	test_variant();
	test_uuid();
	test_date_time();
	test_flat_set();
	test_flat_map();
	test_intrusive_set();
	test_intrusive_list();

	return EXIT_SUCCESS;
}
