py boost.add_trivial_printer("List_Obj", lambda v: v['_val'])
py boost.add_trivial_printer("SList_Obj", lambda v: v['_val'])
py boost.add_trivial_printer("Set_Obj", lambda v: v['_val'])
info pretty-print global boost
info pretty-print global trivial
b done
r
p bh1_list_0
p bh1_list_1
p $at(bh1_list_1, 0)
p $at(bh1_list_1, 1)
p bh2_list_0
p bh2_list_1
p mh1_list_0
p mh1_list_1
p mh2_list_0
p mh2_list_1
p good_tvt_list_0
p good_tvt_list_1
##### the next call would fail
#p bad_tvt_list_0
py boost.static_method[('TVT_Bad_List_Node_Traits', 'get_next')] = lambda n: n['_next_2']
p bad_tvt_list_0
p bad_tvt_list_1
p list_it_0
p list_it_1
p bh1_slist_0
p bh1_slist_1
p bh2_slist_0
p bh2_slist_1
p mh1_slist_0
p mh1_slist_1
p mh2_slist_0
p mh2_slist_1
p good_tvt_slist_0
p good_tvt_slist_1
##### the next call would fail
#p bad_tvt_slist_0
py boost.static_method[('TVT_Bad_SList_Node_Traits', 'get_next')] = lambda n: n['_next_2']
p bad_tvt_slist_0
p bad_tvt_slist_1
p slist_it_0
p slist_it_1
p bh1_set_0
p bh1_set_1
p bh2_set_0
p bh2_set_1
p $at(bh2_set_1, 0)
p $at(bh2_set_1, 1)
p $at(bh2_set_1, 2)
p $at(bh2_set_1, 3)
p $at(bh2_set_1, 4)
p mh1_set_0
p mh1_set_1
p mh2_set_0
p mh2_set_1
p good_tvt_set_0
p good_tvt_set_1
##### the next call would fail
#p bad_tvt_set_0
py boost.static_method[('TVT_Bad_Set_Node_Traits', 'get_parent')] = lambda n: n['_parent_2']
py boost.static_method[('TVT_Bad_Set_Node_Traits', 'get_left')] = lambda n: n['_left_2']
py boost.static_method[('TVT_Bad_Set_Node_Traits', 'get_right')] = lambda n: n['_right_2']
p bad_tvt_set_0
p bad_tvt_set_1
p set_it_0
p set_it_1
q
