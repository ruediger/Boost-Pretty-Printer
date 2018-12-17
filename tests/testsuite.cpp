#include <string>
#include <tuple>

#include <boost/version.hpp>

#include <boost/range/iterator_range.hpp>
#include <boost/circular_buffer.hpp>
#include <boost/array.hpp>
#if BOOST_VERSION >= 104800
#include <boost/container/flat_set.hpp>
#include <boost/container/flat_map.hpp>
#endif
#include <boost/intrusive/set.hpp>
#include <boost/intrusive/list.hpp>
#include <boost/intrusive/slist.hpp>
#include <boost/intrusive/avl_set.hpp>
#include <boost/intrusive/splay_set.hpp>
#include <boost/intrusive/sg_set.hpp>
#include <boost/unordered_map.hpp>
#include <boost/unordered_set.hpp>
#if BOOST_VERSION >= 105800
#include <boost/container/small_vector.hpp>
#endif
#if BOOST_VERSION >= 105400
#include <boost/container/static_vector.hpp>
#endif
#include <boost/dynamic_bitset.hpp>

#include <boost/smart_ptr.hpp>
#if BOOST_VERSION >= 105500
#include <boost/smart_ptr/intrusive_ref_counter.hpp>
#endif

#include <boost/variant.hpp>
#include <boost/optional.hpp>
#include <boost/ref.hpp>
#if BOOST_VERSION >= 104200
#include <boost/uuid/uuid.hpp>
#endif
#include <boost/date_time/gregorian/gregorian.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/logic/tribool.hpp>

#include <boost/multi_index_container.hpp>
#include <boost/multi_index/sequenced_index.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include <boost/multi_index/hashed_index.hpp>
#include <boost/multi_index/identity.hpp>
#include <boost/multi_index/member.hpp>

unsigned const boost_version = BOOST_VERSION;

namespace bi = boost::intrusive;

void dummy_function()
{
}

void test_iterator_range()
{
	char const text[] = "hello dolly!";
	boost::iterator_range<char const*> empty_range;
	boost::iterator_range<char const*> char_range(std::begin(text), std::end(text));
break_here:
	dummy_function();
}

void test_optional()
{
	boost::optional<int> not_initialized;
	boost::optional<int> ten(10);
	// Something is wrong?!
	//char const text[] = "hello dolly!";
	//boost::optional<char const*> dolly(text);
break_here:
	dummy_function();
}

void test_reference_wrapper()
{
	int x = 42;
	boost::reference_wrapper<int> int_wrapper(x);
break_here:
	dummy_function();
}

void test_tribool()
{
	boost::logic::tribool val_false;
	boost::logic::tribool val_true(true);
	boost::logic::tribool val_indeterminate(boost::logic::indeterminate);
break_here:
	dummy_function();
}

void test_scoped_ptr()
{
	boost::scoped_ptr<int> scoped_ptr_empty;
	boost::scoped_ptr<int> scoped_ptr(new int(42));

	boost::scoped_array<int> scoped_array_empty;
	boost::scoped_array<int> scoped_array(new int[1]);
	scoped_array[0] = 42;
break_here:
	dummy_function();
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
	dummy_function();
}


void test_shared_ptr()
{
	boost::shared_ptr<int> empty_shared_ptr;
	boost::shared_ptr<int> shared_ptr(new int(9));
	boost::weak_ptr<int> weak_ptr(shared_ptr);

	boost::shared_array<int> empty_shared_array;
	boost::shared_array<int> shared_array(new int[1]);
break_here:
	dummy_function();
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
	dummy_function();
}

void test_array()
{
	boost::array<int, 0> empty;
	boost::array<int, 3> three_elements = { 10, 20, 30 };
break_here:
	dummy_function();
}

struct VariantA
{
    int a_;
};
struct VariantB
{
    int b_;
};
template < typename T >
struct VariantT
{
    T t_;
};
template < typename T, typename, typename >
struct VariantTs
{
    T t_;
};
struct VariantChar
{
    char const* t_;
};

void test_variant()
{
    using Variant = boost::variant<
		VariantA,
		VariantB,
		VariantT<int>,
		VariantTs<int, int, int>,
		VariantChar>;
    Variant variant_a(VariantA{42});
    Variant variant_b(VariantB{24});
    Variant variant_t(VariantT<int>{53});
    Variant variant_ts(VariantTs<int, int, int>{35});
    Variant variant_char(VariantChar{"hello variant!"});
    
    double const ** const var_type_1{};
    const double * * const var_type_2{};
    const double ** const& var_type_3 = var_type_1;
        
break_here:
	dummy_function();
}

void test_uuid()
{
#if BOOST_VERSION >= 104200
	boost::uuids::uuid uuid = {
		0x01 ,0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
		0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef };
#endif
break_here:
	dummy_function();
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
	dummy_function();
}

void test_flat_set()
{
#if BOOST_VERSION >= 104800
	using FlatSetOfInt = boost::container::flat_set<int>;

	FlatSetOfInt empty_set;
	FlatSetOfInt::iterator uninitialized_iter;
	FlatSetOfInt::const_iterator uninitialized_const_iter;

	FlatSetOfInt fset;
	fset.reserve(4);
	fset.insert(1);
	fset.insert(2);
	auto itr = fset.find(2);
#endif
break_here:
	dummy_function();
}

void test_flat_map()
{
#if BOOST_VERSION >= 104800
	using FlatMapOfInt = boost::container::flat_map<int, int>;
	FlatMapOfInt empty_map;
	FlatMapOfInt::iterator uninitialized_iter;
	FlatMapOfInt::const_iterator uninitialized_const_iter;

	FlatMapOfInt fmap;
	fmap.reserve(4);
	fmap[1] = 10;
	fmap[2] = 20;
	auto itr = fmap.find(2);
#endif
break_here:
	dummy_function();
}

// Intrusive set: red-black tree, base hook
void test_intrusive_set_base()
{
    namespace bi = boost::intrusive;
    struct Tag1
    {
    };
    struct Tag2
    {
    };
    using Hook1 = bi::set_base_hook<bi::tag<Tag1>>;
    using Hook2 = bi::set_base_hook<bi::tag<Tag2>>;
	struct IntSetElement
	    : public Hook1
	    , public Hook2
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using BaseSet1 = boost::intrusive::set<IntSetElement, bi::base_hook<Hook1>>;
	using BaseSet2 = boost::intrusive::set<IntSetElement, bi::base_hook<Hook2>>;

	BaseSet1 empty_base_set;

	BaseSet1 bset_1;
	bset_1.insert(elem3);
	bset_1.insert(elem2);
	bset_1.insert(elem1);

	BaseSet2 bset_2;
	bset_2.insert(elem3);
	bset_2.insert(elem2);

	auto iter_1 = std::next(bset_1.begin());
	auto iter_2 = std::next(bset_2.begin());
break_here:
	bset_1.clear();
	bset_2.clear();
}

/* It is possible to write a single template function for all intrusive tree types, but gcc optimizes out
some types in that case. I was unable to make compiler stop doing it (@mbalabin).

template<template<class E, class H> class SetType, class HookType>
void test_intrusive_member_set()
{
	struct IntSetElement
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
		HookType member_hook_1;
		HookType member_hook_2;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using MemberSet1 = SetType<
	    IntSetElement,
	    bi::member_hook<IntSetElement, HookType, &IntSetElement::member_hook_1>>;
    using MemberSet2 = SetType<
        IntSetElement,
        bi::member_hook<IntSetElement, HookType, &IntSetElement::member_hook_2>>;

	MemberSet1 empty_member_set;

	MemberSet1 member_set_1;
	member_set_1.insert(elem3);
	member_set_1.insert(elem2);
	member_set_1.insert(elem1);

	MemberSet2 member_set_2;
	member_set_2.insert(elem3);
	member_set_2.insert(elem2);

	auto iter1 = member_set_1.begin();
	auto iter2 = member_set_2.begin();

break_here:
	member_set_1.clear();
	member_set_2.clear();
}
*/

// Intrusive set: red-black tree, member hooks
void test_intrusive_rbtree_set_member()
{
    namespace bi = boost::intrusive;
	struct IntSetElement
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
		bi::set_member_hook<> member_hook_1;
		bi::set_member_hook<> member_hook_2;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using MemberSet1 = bi::set<
	    IntSetElement,
	    bi::member_hook<IntSetElement, bi::set_member_hook<>, &IntSetElement::member_hook_1>>;
    using MemberSet2 = bi::set<
        IntSetElement,
        bi::member_hook<IntSetElement, bi::set_member_hook<>, &IntSetElement::member_hook_2>>;

	MemberSet1 empty_member_set;

	MemberSet1 member_set_1;
	member_set_1.insert(elem3);
	member_set_1.insert(elem2);
	member_set_1.insert(elem1);

	MemberSet2 member_set_2;
	member_set_2.insert(elem3);
	member_set_2.insert(elem2);

	auto iter1 = member_set_1.begin();
	auto iter2 = member_set_2.begin();
break_here:
	member_set_1.clear();
	member_set_2.clear();
}

// Intrusive set: avl tree, member hooks
void test_intrusive_avl_set_member()
{
    namespace bi = boost::intrusive;
	struct IntSetElement
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
		bi::avl_set_member_hook<> member_hook_1;
		bi::avl_set_member_hook<> member_hook_2;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using MemberSet1 = bi::avl_set<
	    IntSetElement,
	    bi::member_hook<IntSetElement, bi::avl_set_member_hook<>, &IntSetElement::member_hook_1>>;
    using MemberSet2 = bi::avl_set<
        IntSetElement,
        bi::member_hook<IntSetElement, bi::avl_set_member_hook<>, &IntSetElement::member_hook_2>>;

	MemberSet1 empty_member_set;

	MemberSet1 member_set_1;
	member_set_1.insert(elem3);
	member_set_1.insert(elem2);
	member_set_1.insert(elem1);

	MemberSet2 member_set_2;
	member_set_2.insert(elem3);
	member_set_2.insert(elem2);

	auto iter1 = member_set_1.begin();
	auto iter2 = member_set_2.begin();
break_here:
	member_set_1.clear();
	member_set_2.clear();
}

// Intrusive set: splay tree, member hooks
void test_intrusive_splay_set_member()
{
    namespace bi = boost::intrusive;
	struct IntSetElement
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
		bi::bs_set_member_hook<> member_hook_1;
		bi::bs_set_member_hook<> member_hook_2;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using MemberSet1 = bi::splay_set<
	    IntSetElement,
	    bi::member_hook<IntSetElement, bi::bs_set_member_hook<>, &IntSetElement::member_hook_1>>;
    using MemberSet2 = bi::splay_set<
        IntSetElement,
        bi::member_hook<IntSetElement, bi::bs_set_member_hook<>, &IntSetElement::member_hook_2>>;

	MemberSet1 empty_member_set;

	MemberSet1 member_set_1;
	member_set_1.insert(elem3);
	member_set_1.insert(elem2);
	member_set_1.insert(elem1);

	MemberSet2 member_set_2;
	member_set_2.insert(elem3);
	member_set_2.insert(elem2);

	auto iter1 = member_set_1.begin();
	auto iter2 = member_set_2.begin();
break_here:
	member_set_1.clear();
	member_set_2.clear();
}

// Intrusive set: scapegoat tree, member hooks
void test_intrusive_sg_set_member()
{
    namespace bi = boost::intrusive;
	struct IntSetElement
	{
		IntSetElement(int i) : int_(i) {}

		bool operator<(IntSetElement const& rhs) const { return int_ < rhs.int_; }
		int int_;
		bi::bs_set_member_hook<> member_hook_1;
		bi::bs_set_member_hook<> member_hook_2;
	};

	IntSetElement elem1(1);
	IntSetElement elem2(2);
	IntSetElement elem3(3);

	using MemberSet1 = bi::sg_set<
	    IntSetElement,
	    bi::member_hook<IntSetElement, bi::bs_set_member_hook<>, &IntSetElement::member_hook_1>>;
    using MemberSet2 = bi::sg_set<
        IntSetElement,
        bi::member_hook<IntSetElement, bi::bs_set_member_hook<>, &IntSetElement::member_hook_2>>;

	MemberSet1 empty_member_set;

	MemberSet1 member_set_1;
	member_set_1.insert(elem3);
	member_set_1.insert(elem2);
	member_set_1.insert(elem1);

	MemberSet2 member_set_2;
	member_set_2.insert(elem3);
	member_set_2.insert(elem2);

	auto iter1 = member_set_1.begin();
	auto iter2 = member_set_2.begin();
break_here:
	member_set_1.clear();
	member_set_2.clear();
}

// Intrusive double-linked list, base hook
void test_intrusive_list_base()
{
    namespace bi = boost::intrusive;
    struct Tag1
    {
    };
    struct Tag2
    {
    };
    using Hook1 = bi::list_base_hook<bi::tag<Tag1>>;
    using Hook2 = bi::list_base_hook<bi::tag<Tag2>>;

	struct IntListElement
	    : public Hook1
	    , public Hook2
	{
		IntListElement(int i) : int_(i) {}
		int int_;
	};

	IntListElement elem1(1);
	IntListElement elem2(2);
	IntListElement elem3(3);

	using BaseList1 = bi::list<IntListElement, bi::base_hook<Hook1>>;
	using BaseList2 = bi::list<IntListElement, bi::base_hook<Hook2>>;

	BaseList1 empty_base_list;

	BaseList1 base_list_1;
	base_list_1.push_back(elem1);
	base_list_1.push_back(elem2);
	base_list_1.push_back(elem3);

	BaseList2 base_list_2;
	base_list_2.push_back(elem1);
	base_list_2.push_back(elem3);

	// AFAIU, intrusive iterators are not default-initialized to any value. It is not possible
	// to distinguish an uninitialized iterator from an initialized one, and thus it is pointless to test it.
	//BaseList::iterator base_list_null_iter;
	auto iter_1 = std::next(base_list_1.begin());
	auto iter_2 = std::next(base_list_2.begin());
break_here:
	dummy_function();
}

// Intrusive double-linked list, base hook, default tag
void test_intrusive_list_base_default_tag()
{
    namespace bi = boost::intrusive;

	struct IntListElement : public bi::list_base_hook<>
	{
		IntListElement(int i) : int_(i) {}
		int int_;
	};

	IntListElement elem1(1);
	IntListElement elem2(2);
	IntListElement elem3(3);

	using BaseList = bi::list<IntListElement>;

	BaseList empty_base_list;

	BaseList base_list;
	base_list.push_back(elem1);
	base_list.push_back(elem2);
	base_list.push_back(elem3);

	// AFAIU, intrusive iterators are not default-initialized to any value. It is not possible
	// to distinguish an uninitialized iterator from an initialized one, and thus it is pointless to test it.
	//BaseList::iterator base_list_null_iter;
	auto iter = std::next(base_list.begin());
break_here:
	dummy_function();
}

// Intrusive double-linked list, member hooks
void test_intrusive_list_member()
{
	namespace bi = boost::intrusive;
	struct IntListElement
	{
		IntListElement(int i) : int_(i) {}

		int int_;
		bi::list_member_hook<> member_hook_1;
		bi::list_member_hook<> member_hook_2;
	};

	IntListElement elem1(1);
	IntListElement elem2(2);
	IntListElement elem3(3);

	using MemberList1 = bi::list<
		IntListElement,
		bi::member_hook<IntListElement, bi::list_member_hook<>, &IntListElement::member_hook_1>>;
	using MemberList2 = boost::intrusive::list<
		IntListElement,
		bi::member_hook<IntListElement, bi::list_member_hook<>, &IntListElement::member_hook_2>>;

	MemberList1 empty_member_list;

	MemberList1 member_list_1;
	member_list_1.push_back(elem1);
	member_list_1.push_back(elem2);
	member_list_1.push_back(elem3);

	MemberList2 member_list_2;
	member_list_2.push_back(elem3);
	member_list_2.push_back(elem2);
	member_list_2.push_back(elem1);

	auto iter_1 = member_list_1.begin();
	auto iter_2 = member_list_2.begin();
break_here:
	dummy_function();
}

// Intrusive single-linked list, base hooks
void test_intrusive_slist_base()
{
    namespace bi = boost::intrusive;
    struct Tag1
    {
    };
    struct Tag2
    {
    };
    using Hook1 = bi::list_base_hook<bi::tag<Tag1>>;
    using Hook2 = bi::list_base_hook<bi::tag<Tag2>>;

	struct IntListElement
	    : public Hook1
	    , public Hook2
	{
		IntListElement(int i) : int_(i) {}
		int int_;
	};

	IntListElement elem1(1);
	IntListElement elem2(2);
	IntListElement elem3(3);

	using BaseList1 = bi::slist<IntListElement, bi::base_hook<Hook1>>;
	using BaseList2 = bi::slist<IntListElement, bi::base_hook<Hook2>>;

	BaseList1 empty_list;

	BaseList1 list_1;
	list_1.push_front(elem3);
	list_1.push_front(elem2);
	list_1.push_front(elem1);

	BaseList2 list_2;
	list_2.push_front(elem3);
	list_2.push_front(elem2);

	auto iter_1 = std::next(list_1.begin());
	auto iter_2 = std::next(list_2.begin());
break_here:
	dummy_function();
}

// Intrusive single-linked list, member hooks
void test_intrusive_slist_member()
{
	struct IntListElement
	{
		IntListElement(int i) : int_(i) {}
		int int_;
		boost::intrusive::slist_member_hook<> member_hook_;
	};

	using ListMemberOption = boost::intrusive::member_hook<
		IntListElement,
		boost::intrusive::slist_member_hook<>,
		&IntListElement::member_hook_>;
	using MemberSlist = boost::intrusive::slist<IntListElement, ListMemberOption>;

	MemberSlist empty_list;

	IntListElement elem1(1);
	IntListElement elem2(2);
	IntListElement elem3(3);

	MemberSlist list;
	list.push_front(elem3);
	list.push_front(elem2);
	list.push_front(elem1);

	auto iter = std::next(list.begin());
break_here:
	dummy_function();
}

// boost::unordered_map and its iterator
void test_unordered_map()
{
	boost::unordered_map<int, char const*> empty_map;
	boost::unordered_map<int, char const*> map = {{30, "thirty"}, {20, "twenty"}, {10, "ten"}};

	boost::unordered_map<int, int> big_map;
	for (int i = 0; i < 100000; ++i)
	{
	    big_map.emplace(i, i);
	}

	boost::unordered_map<int, char const*>::iterator uninitialized_iter;
	auto iter = map.begin();
break_here:
	dummy_function();
}

// boost::unordered_multimap and its iterator
void test_unordered_multimap()
{
	boost::unordered_multimap<int, char const*>
		empty_map,
		map = {{30, "thirty"}, {20, "twenty"}, {10, "ten"}, {10, "dieci"}, {20, "venti"}, {30, "trenta"}};

	boost::unordered_multimap<int, char const*>::iterator uninitialized_iter;
	auto iter = map.begin();
break_here:
	dummy_function();
}

// boost::unordered_set and its iterator
void test_unordered_set()
{
	boost::unordered_set<char const*> empty_set;
	boost::unordered_set<char const*> set = {"Thales", "Pythagoras", "Democritus"};

	boost::unordered_set<char const*>::iterator uninitialized_iter;
	auto iter = set.begin();
break_here:
	dummy_function();
}

// boost::unordered_multiset and its iterator
void test_unordered_multiset()
{
	boost::unordered_multiset<char const*> empty_multiset;
	boost::unordered_multiset<char const*> multiset = {"Plinius", "Plinius", "Bruegel", "Bruegel"};

	boost::unordered_multiset<char const*>::iterator uninitialized_iter;
	auto iter = multiset.begin();
break_here:
	dummy_function();
}

void test_small_vector()
{
#if BOOST_VERSION >= 105800
	boost::container::small_vector<int, 3> small_vector_1 = {1, 2};
	boost::container::small_vector<int, 3> small_vector_2 = {1, 2, 3, 4, 5};
	auto& as_base_vector = static_cast<boost::container::small_vector_base<int>&>(small_vector_1);

	auto iter = small_vector_1.begin();
	decltype(iter) uninitialized_iter;
#endif
break_here:
	dummy_function();
}

void test_static_vector()
{
#if BOOST_VERSION >= 105400
	boost::container::static_vector<int, 0> zero_size_vector;
	boost::container::static_vector<int, 3> static_vector = {1, 2};

	auto iter = static_vector.begin();
	decltype(iter) uninitialized_iter;
#endif
break_here:
	dummy_function();
}

void test_dynamic_bitset()
{
	boost::dynamic_bitset<> empty_bitset;
	boost::dynamic_bitset<> bitset(130);
	bitset[0] = true;
	bitset[2] = true;
	bitset[129] = true;
break_here:
	dummy_function();
}

void test_duration()
{
    boost::posix_time::time_duration empty_duration;
    boost::posix_time::time_duration duration_130 = boost::posix_time::seconds(130);
    boost::posix_time::time_duration duration_3600 = boost::posix_time::seconds(3600);
    boost::posix_time::time_duration duration_neg_130 = boost::posix_time::seconds(-130);
    boost::posix_time::time_duration duration_with_ms = boost::posix_time::seconds(61) + boost::posix_time::millisec(10);
    boost::posix_time::time_duration duration_not_a_time(boost::posix_time::not_a_date_time);
break_here:
    dummy_function();
}

// boost::multi_index

namespace mi = boost::multi_index;

struct mi_tag_sequenced {};
struct mi_tag_ordered {};
struct mi_tag_hashed {};

using sequenced_first =  mi::multi_index_container<
	int,
	mi::indexed_by<
		mi::sequenced<
			mi::tag<mi_tag_sequenced>
		>,
		mi::ordered_unique<
			mi::tag<mi_tag_ordered>,
			mi::identity<int>
		>,
		mi::hashed_unique<
			mi::tag<mi_tag_hashed>,
			mi::identity<int>
		>
	>
>;

using ordered_first = mi::multi_index_container<
	int,
	mi::indexed_by<
		mi::ordered_unique<
			mi::tag<mi_tag_ordered>,
			mi::identity<int>
		>,
		mi::hashed_unique<
			mi::tag<mi_tag_hashed>,
			mi::identity<int>
		>,
		mi::sequenced<
			mi::tag<mi_tag_sequenced>
		>
	>
>;

using hashed_first = mi::multi_index_container<
	int,
	mi::indexed_by<
		mi::hashed_unique<
			mi::tag<mi_tag_hashed>,
			mi::identity<int>
		>,
		mi::sequenced<
			mi::tag<mi_tag_sequenced>
		>,
		mi::ordered_unique<
			mi::tag<mi_tag_ordered>,
			mi::identity<int>
		>
	>
>;

using hashed_first_non_unique = mi::multi_index_container<
	int,
	mi::indexed_by<
		mi::hashed_non_unique<
			mi::tag<mi_tag_hashed>,
			mi::identity<int>
		>,
		mi::sequenced<
			mi::tag<mi_tag_sequenced>
		>,
		mi::ordered_non_unique<
			mi::tag<mi_tag_ordered>,
			mi::identity<int>
		>
	>
>;


void test_multi_index()
{
	sequenced_first sf_empty;
	ordered_first of_empty;
	hashed_first hf_empty;

	sequenced_first sf_two;
	sf_two.push_back(1);
	sf_two.push_back(2);

	ordered_first of_two;
	of_two.insert(1);
	of_two.insert(2);

	hashed_first hf_two;
	hf_two.insert(1);
	hf_two.insert(2);

	hashed_first_non_unique hf_over_two_same_value;
	hf_over_two_same_value.insert(1);
	hf_over_two_same_value.insert(1);
	hf_over_two_same_value.insert(1);
	hf_over_two_same_value.insert(2);
	hf_over_two_same_value.insert(2);
	hf_over_two_same_value.insert(2);
	hf_over_two_same_value.insert(2);
	hf_over_two_same_value.insert(3);
	hf_over_two_same_value.insert(3);
	hf_over_two_same_value.insert(4);

 break_here:
	dummy_function();
}

int main()
{
	test_iterator_range();
	test_circular_buffer();
	test_array();
	test_flat_set();
	test_flat_map();
	test_unordered_map();
	test_unordered_multimap();
	test_unordered_set();
	test_unordered_multiset();
	test_small_vector();
	test_static_vector();
	test_dynamic_bitset();

	test_intrusive_set_base();
	test_intrusive_rbtree_set_member();
	test_intrusive_avl_set_member();
	test_intrusive_splay_set_member();
	test_intrusive_sg_set_member();

	test_intrusive_list_base();
	test_intrusive_list_base_default_tag();
	test_intrusive_list_member();
	test_intrusive_slist_base();
	test_intrusive_slist_member();

	test_scoped_ptr();
	test_intrusive_ptr();
	test_shared_ptr();

	test_variant();
	test_optional();
	test_reference_wrapper();
	test_uuid();
	test_date_time();
	test_tribool();
	test_duration();

	test_multi_index();

	return EXIT_SUCCESS;
}
