#include <iostream>
#include <string>
#include <tuple>
#include <boost/intrusive/list.hpp>
#include <boost/intrusive/slist.hpp>
#include <boost/intrusive/set.hpp>
#include <boost/intrusive/trivial_value_traits.hpp>

namespace bi = boost::intrusive;

struct alternate_tag {};

/**
 * Objects to be placed in containers.
 */
struct List_Obj
    : public bi::list_base_hook<>, // base hook, "default_tag"
      public bi::list_base_hook< bi::tag< alternate_tag > > // base hook, "alternate_tag"
{
    int _val;

    // member hooks
    bi::list_member_hook<> _mh1;
    bi::list_member_hook<> _mh2;

    // trivial value traits hook with good node_traits
    List_Obj* _prev_1;
    List_Obj* _next_1;

    // trivial value traits hook with bad node_traits
    List_Obj* _prev_2;
    List_Obj* _next_2;

    List_Obj(int val = 0) : _val(val) {}

    friend std::ostream& operator << (std::ostream& os, const List_Obj& rhs)
    {
        os << rhs._val;
        return os;
    }
};

struct SList_Obj
    : public bi::slist_base_hook<>, // base hook, "default_tag"
      public bi::slist_base_hook< bi::tag< alternate_tag > > // base hook, "alternate_tag"
{
    int _val;

    // member hooks
    bi::slist_member_hook<> _mh1;
    bi::slist_member_hook<> _mh2;

    // trivial value traits hook with good node_traits
    SList_Obj* _next_1;

    // trivial value traits hook with bad node_traits
    SList_Obj* _next_2;

    SList_Obj(int val = 0) : _val(val) {}

    friend std::ostream& operator << (std::ostream& os, const SList_Obj& rhs)
    {
        os << rhs._val;
        return os;
    }
};

struct Set_Obj
    : public bi::set_base_hook<>, // base hook, "default_tag"
      public bi::set_base_hook< bi::tag< alternate_tag > > // base hook, "alternate_tag"
{
    int _val;

    // member hooks
    bi::set_member_hook<> _mh1;
    bi::set_member_hook<> _mh2;

    // trivial value traits hook with good node_traits
    Set_Obj* _parent_1;
    Set_Obj* _left_1;
    Set_Obj* _right_1;
    int      _color_1;

    // trivial value traits hook with bad node_traits
    Set_Obj* _parent_2;
    Set_Obj* _left_2;
    Set_Obj* _right_2;
    int      _color_2;

    Set_Obj(int val = 0) : _val(val) {}

    friend std::ostream& operator << (std::ostream& os, const Set_Obj& rhs)
    {
        os << rhs._val;
        return os;
    }

    friend bool operator < (const Set_Obj& lhs, const Set_Obj& rhs)
    {
        return lhs._val < rhs._val;
    }
};

/**
 * Node Traits structs.
 */
struct TVT_Good_List_Node_Traits
{
    typedef List_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;

    static node_ptr get_next(const_node_ptr n)              { return n->_next_1; }
    static void     set_next(node_ptr n, node_ptr next)     { n->_next_1 = next; }
    static node_ptr get_previous(const_node_ptr n)          { return n->_prev_1; }
    static void     set_previous(node_ptr n, node_ptr prev) { n->_prev_1 = prev; }
};

struct TVT_Bad_List_Node_Traits
{
    typedef List_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;

    static node_ptr get_next(const const_node_ptr& n)                     { return n->_next_2; }
    static void     set_next(const node_ptr& n, const node_ptr& next)     { n->_next_2 = next; }
    static node_ptr get_previous(const const_node_ptr& n)                 { return n->_prev_2; }
    static void     set_previous(const node_ptr& n, const node_ptr& prev) { n->_prev_2 = prev; }
};

struct TVT_Good_SList_Node_Traits
{
    typedef SList_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;

    static node_ptr get_next(const_node_ptr n)              { return n->_next_1; }
    static void     set_next(node_ptr n, node_ptr next)     { n->_next_1 = next; }
};

struct TVT_Bad_SList_Node_Traits
{
    typedef SList_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;

    static node_ptr get_next(const const_node_ptr& n)                     { return n->_next_2; }
    static void     set_next(const node_ptr& n, const node_ptr& next)     { n->_next_2 = next; }
};

struct TVT_Good_Set_Node_Traits
{
    typedef Set_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;
    typedef int color;

    static node_ptr get_parent(const_node_ptr n)              { return n->_parent_1; }
    static void     set_parent(node_ptr n, node_ptr p)        { n->_parent_1 = p; }
    static node_ptr get_left  (const_node_ptr n)              { return n->_left_1; }
    static void     set_left  (node_ptr n, node_ptr p)        { n->_left_1 = p; }
    static node_ptr get_right (const_node_ptr n)              { return n->_right_1; }
    static void     set_right (node_ptr n, node_ptr p)        { n->_right_1 = p; }
    static color    get_color (const_node_ptr n)              { return n->_color_1; }
    static void     set_color (node_ptr n, int c)             { n->_color_1 = c; }
    static color    black     ()                              { return 0; }
    static color    red       ()                              { return 1; }
};

struct TVT_Bad_Set_Node_Traits
{
    typedef Set_Obj node;
    typedef node* node_ptr;
    typedef const node* const_node_ptr;
    typedef int color;

    static node_ptr get_parent(const const_node_ptr& n)              { return n->_parent_2; }
    static void     set_parent(const node_ptr& n, const node_ptr& p) { n->_parent_2 = p; }
    static node_ptr get_left  (const const_node_ptr& n)              { return n->_left_2; }
    static void     set_left  (const node_ptr& n, const node_ptr& p) { n->_left_2 = p; }
    static node_ptr get_right (const const_node_ptr& n)              { return n->_right_2; }
    static void     set_right (const node_ptr& n, const node_ptr& p) { n->_right_2 = p; }
    static color    get_color (const const_node_ptr& n)              { return n->_color_2; }
    static void     set_color (const node_ptr& n, int c)             { n->_color_2 = c; }
    static color    black     ()                                     { return 0; }
    static color    red       ()                                     { return 1; }
};

/**
 * Intrusive container types.
 */
typedef bi::list< List_Obj > bh1_list_t;
typedef bi::list< List_Obj, bi::base_hook< bi::list_base_hook< bi::tag< alternate_tag > > > > bh2_list_t;
typedef bi::list< List_Obj, bi::member_hook< List_Obj, bi::list_member_hook<>, &List_Obj::_mh1> > mh1_list_t;
typedef bi::list< List_Obj, bi::member_hook< List_Obj, bi::list_member_hook<>, &List_Obj::_mh2> > mh2_list_t;
typedef bi::trivial_value_traits< TVT_Good_List_Node_Traits > Good_List_TVT;
typedef bi::trivial_value_traits< TVT_Bad_List_Node_Traits > Bad_List_TVT;
typedef bi::list< List_Obj, bi::value_traits< Good_List_TVT > > good_tvt_list_t;
typedef bi::list< List_Obj, bi::value_traits< Bad_List_TVT > > bad_tvt_list_t;

typedef bi::slist< SList_Obj > bh1_slist_t;
typedef bi::slist< SList_Obj, bi::base_hook< bi::slist_base_hook< bi::tag< alternate_tag > > > > bh2_slist_t;
typedef bi::slist< SList_Obj, bi::member_hook< SList_Obj, bi::slist_member_hook<>, &SList_Obj::_mh1> > mh1_slist_t;
typedef bi::slist< SList_Obj, bi::member_hook< SList_Obj, bi::slist_member_hook<>, &SList_Obj::_mh2> > mh2_slist_t;
typedef bi::trivial_value_traits< TVT_Good_SList_Node_Traits > Good_SList_TVT;
typedef bi::trivial_value_traits< TVT_Bad_SList_Node_Traits > Bad_SList_TVT;
typedef bi::slist< SList_Obj, bi::value_traits< Good_SList_TVT > > good_tvt_slist_t;
typedef bi::slist< SList_Obj, bi::value_traits< Bad_SList_TVT > > bad_tvt_slist_t;

typedef bi::set< Set_Obj > bh1_set_t;
typedef bi::set< Set_Obj, bi::base_hook< bi::set_base_hook< bi::tag< alternate_tag > > > > bh2_set_t;
typedef bi::set< Set_Obj, bi::member_hook< Set_Obj, bi::set_member_hook<>, &Set_Obj::_mh1> > mh1_set_t;
typedef bi::set< Set_Obj, bi::member_hook< Set_Obj, bi::set_member_hook<>, &Set_Obj::_mh2> > mh2_set_t;
typedef bi::trivial_value_traits< TVT_Good_Set_Node_Traits > Good_Set_TVT;
typedef bi::trivial_value_traits< TVT_Bad_Set_Node_Traits > Bad_Set_TVT;
typedef bi::set< Set_Obj, bi::value_traits< Good_Set_TVT > > good_tvt_set_t;
typedef bi::set< Set_Obj, bi::value_traits< Bad_Set_TVT > > bad_tvt_set_t;

/**
 * Intrusive containers.
 */
std::vector< List_Obj > v_list = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
bh1_list_t bh1_list_0;
bh1_list_t bh1_list_1;
bh2_list_t bh2_list_0;
bh2_list_t bh2_list_1;
mh1_list_t mh1_list_0;
mh1_list_t mh1_list_1;
mh2_list_t mh2_list_0;
mh2_list_t mh2_list_1;
good_tvt_list_t good_tvt_list_0;
good_tvt_list_t good_tvt_list_1;
bad_tvt_list_t bad_tvt_list_0;
bad_tvt_list_t bad_tvt_list_1;
bh1_list_t::iterator list_it_0;
bh1_list_t::iterator list_it_1;

std::vector< SList_Obj > v_slist = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
bh1_slist_t bh1_slist_0;
bh1_slist_t bh1_slist_1;
bh2_slist_t bh2_slist_0;
bh2_slist_t bh2_slist_1;
mh1_slist_t mh1_slist_0;
mh1_slist_t mh1_slist_1;
mh2_slist_t mh2_slist_0;
mh2_slist_t mh2_slist_1;
good_tvt_slist_t good_tvt_slist_0;
good_tvt_slist_t good_tvt_slist_1;
bad_tvt_slist_t bad_tvt_slist_0;
bad_tvt_slist_t bad_tvt_slist_1;
bh1_slist_t::iterator slist_it_0;
bh1_slist_t::iterator slist_it_1;

std::vector< Set_Obj > v_set = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
bh1_set_t bh1_set_0;
bh1_set_t bh1_set_1;
bh2_set_t bh2_set_0;
bh2_set_t bh2_set_1;
mh1_set_t mh1_set_0;
mh1_set_t mh1_set_1;
mh2_set_t mh2_set_0;
mh2_set_t mh2_set_1;
good_tvt_set_t good_tvt_set_0;
good_tvt_set_t good_tvt_set_1;
bad_tvt_set_t bad_tvt_set_0;
bad_tvt_set_t bad_tvt_set_1;
bh1_set_t::iterator set_it_0;
bh1_set_t::iterator set_it_1;

void done() {}

template < typename Cont >
std::ostream& print_cont(std::ostream& os, const Cont& l)
{
    bool first = true;
    for (const auto& e : l)
    {
        if (not first)
        {
            os << ", ";
        }
        os << e;
        first = false;
    }
    return os;
}

int main()
{
    bh1_list_1.push_front(v_list[0]);
    bh1_list_1.push_front(v_list[1]);
    bh2_list_1.push_front(v_list[0]);
    bh2_list_1.push_front(v_list[2]);
    mh1_list_1.push_front(v_list[0]);
    mh1_list_1.push_front(v_list[3]);
    mh2_list_1.push_front(v_list[0]);
    mh2_list_1.push_front(v_list[4]);
    good_tvt_list_1.push_front(v_list[0]);
    good_tvt_list_1.push_front(v_list[5]);
    bad_tvt_list_1.push_front(v_list[0]);
    bad_tvt_list_1.push_front(v_list[6]);
    list_it_1 = bh1_list_1.begin();

    bh1_slist_1.push_front(v_slist[0]);
    bh1_slist_1.push_front(v_slist[1]);
    bh2_slist_1.push_front(v_slist[0]);
    bh2_slist_1.push_front(v_slist[2]);
    mh1_slist_1.push_front(v_slist[0]);
    mh1_slist_1.push_front(v_slist[3]);
    mh2_slist_1.push_front(v_slist[0]);
    mh2_slist_1.push_front(v_slist[4]);
    good_tvt_slist_1.push_front(v_slist[0]);
    good_tvt_slist_1.push_front(v_slist[5]);
    bad_tvt_slist_1.push_front(v_slist[0]);
    bad_tvt_slist_1.push_front(v_slist[6]);
    slist_it_1 = bh1_slist_1.begin();

    bh1_set_1.insert(v_set[0]);
    bh1_set_1.insert(v_set[1]);
    bh1_set_1.insert(v_set[3]);
    bh1_set_1.insert(v_set[5]);
    bh1_set_1.insert(v_set[7]);
    bh1_set_1.insert(v_set[9]);
    bh2_set_1.insert(v_set[0]);
    bh2_set_1.insert(v_set[2]);
    bh2_set_1.insert(v_set[4]);
    bh2_set_1.insert(v_set[6]);
    bh2_set_1.insert(v_set[8]);
    mh1_set_1.insert(v_set[0]);
    mh1_set_1.insert(v_set[3]);
    mh2_set_1.insert(v_set[0]);
    mh2_set_1.insert(v_set[4]);
    good_tvt_set_1.insert(v_set[0]);
    good_tvt_set_1.insert(v_set[5]);
    bad_tvt_set_1.insert(v_set[0]);
    bad_tvt_set_1.insert(v_set[6]);
    set_it_1 = bh1_set_1.begin();

    std::cout << "bh1_list_1: ";
    print_cont(std::cout, bh1_list_1);
    std::cout << "\n";
    std::cout << "bh2_list_1: ";
    print_cont(std::cout, bh2_list_1);
    std::cout << "\n";
    std::cout << "mh1_list_1: ";
    print_cont(std::cout, mh1_list_1);
    std::cout << "\n";
    std::cout << "mh2_list_1: ";
    print_cont(std::cout, mh2_list_1);
    std::cout << "\n";
    std::cout << "good_tvt_list_1: ";
    print_cont(std::cout, good_tvt_list_1);
    std::cout << "\n";
    std::cout << "bad_tvt_list_1: ";
    print_cont(std::cout, bad_tvt_list_1);
    std::cout << "\n";

    std::cout << "bh1_slist_1: ";
    print_cont(std::cout, bh1_slist_1);
    std::cout << "\n";
    std::cout << "bh2_slist_1: ";
    print_cont(std::cout, bh2_slist_1);
    std::cout << "\n";
    std::cout << "mh1_slist_1: ";
    print_cont(std::cout, mh1_slist_1);
    std::cout << "\n";
    std::cout << "mh2_slist_1: ";
    print_cont(std::cout, mh2_slist_1);
    std::cout << "\n";
    std::cout << "good_tvt_slist_1: ";
    print_cont(std::cout, good_tvt_slist_1);
    std::cout << "\n";
    std::cout << "bad_tvt_slist_1: ";
    print_cont(std::cout, bad_tvt_slist_1);
    std::cout << "\n";

    std::cout << "bh1_set_1: ";
    print_cont(std::cout, bh1_set_1);
    std::cout << "\n";
    std::cout << "bh2_set_1: ";
    print_cont(std::cout, bh2_set_1);
    std::cout << "\n";
    std::cout << "mh1_set_1: ";
    print_cont(std::cout, mh1_set_1);
    std::cout << "\n";
    std::cout << "mh2_set_1: ";
    print_cont(std::cout, mh2_set_1);
    std::cout << "\n";
    std::cout << "good_tvt_set_1: ";
    print_cont(std::cout, good_tvt_set_1);
    std::cout << "\n";
    std::cout << "bad_tvt_set_1: ";
    print_cont(std::cout, bad_tvt_set_1);
    std::cout << "\n";

    done();

    bh1_list_1.clear();
    bh2_list_1.clear();
    mh1_list_1.clear();
    mh2_list_1.clear();
    good_tvt_list_1.clear();
    bad_tvt_list_1.clear();

    bh1_slist_1.clear();
    bh2_slist_1.clear();
    mh1_slist_1.clear();
    mh2_slist_1.clear();
    good_tvt_slist_1.clear();
    bad_tvt_slist_1.clear();

    bh1_set_1.clear();
    bh2_set_1.clear();
    mh1_set_1.clear();
    mh2_set_1.clear();
    good_tvt_set_1.clear();
    bad_tvt_set_1.clear();
}
