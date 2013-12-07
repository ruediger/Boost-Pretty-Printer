#include <boost/multi_index_container.hpp>
#include <boost/multi_index/ordered_index.hpp>
#include <boost/multi_index/hashed_index.hpp>
#include <boost/multi_index/sequenced_index.hpp>
#include <boost/multi_index/random_access_index.hpp>
#include <boost/multi_index/member.hpp>
#include <tuple>


typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >,
        boost::multi_index::hashed_unique<
            boost::multi_index::identity< int >
            >
        >
    > Int_Set_0;

typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >,
        boost::multi_index::hashed_non_unique<
            boost::multi_index::identity< int >
            >
        >
    > Int_Set_1;

typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >,
        boost::multi_index::sequenced<>
        >
    > Int_Set_2;

typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >,
        boost::multi_index::random_access<>
        >
    > Int_Set_3;

typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::random_access<>,
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >
        >
    > Int_Set_4;

typedef boost::multi_index_container<
    int,
    boost::multi_index::indexed_by<
        boost::multi_index::sequenced<>,
        boost::multi_index::ordered_unique<
            boost::multi_index::identity< int >
            >
        >
    > Int_Set_5;



int main()
{
    std::tuple<int, std::tuple<int,int>> t(1, std::make_tuple(6, 8));
        
    Int_Set_0 s_0;
    Int_Set_1 s_1;
    Int_Set_2 s_2;
    Int_Set_3 s_3;
    Int_Set_4 s_4;
    Int_Set_5 s_5;

    s_0.insert(6);
    s_1.insert(5);
    s_2.insert(17);
    s_3.insert(4);
    boost::multi_index::get<1>(s_4).insert(14);
    boost::multi_index::get<1>(s_5).insert(3);
    s_0.insert(9);
    s_1.insert(3);

    // Break here
    int r = 0;
    for (Int_Set_0::iterator it = s_0.begin(); it != s_0.end(); ++it)
    {
        r += *it;
    }
    return r % 2;
}
