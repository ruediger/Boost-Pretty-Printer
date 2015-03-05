#include <boost/intrusive/list.hpp>
#include <boost/intrusive/trivial_value_traits.hpp>
namespace bi = boost::intrusive;

struct A
{
    A(int i = 0) : _val(i) {}

    int _val;
    A* _prev_1;
    A* _next_1;
    A* _prev_2;
    A* _next_2;
};

template<class VoidPointer>
struct NT_1
{
    typedef A node;
    typedef typename bi::pointer_traits<VoidPointer>::template rebind_pointer<node>::type node_ptr;
    typedef typename bi::pointer_traits<VoidPointer>::template rebind_pointer<const node>::type const_node_ptr;

    //static node_ptr get_next(const const_node_ptr& n)            { return n->_next_1; }
    static node_ptr get_next(const_node_ptr n)            { return n->_next_1; }
    static void set_next(node_ptr n, node_ptr next)       { n->_next_1 = next; }
    //static node_ptr get_previous(const const_node_ptr& n)        { return n->_prev_1; }
    static node_ptr get_previous(const_node_ptr n)        { return n->_prev_1; }
    static void set_previous(node_ptr n, node_ptr prev)   { n->_prev_1 = prev; }
};

typedef bi::trivial_value_traits< NT_1<void*>, bi::normal_link > VT_1;
typedef bi::list< A, bi::value_traits< VT_1 > > List_1;

int main()
{
    List_1 l1;
    A a(42);
    l1.push_front(a);

    auto r = l1.get_root_node();
    auto n = List_1::node_traits::get_next(r);
    auto i = l1.begin();
    (void)l1.end();

    (void)n;
    (void)i;

    return 0;
}
