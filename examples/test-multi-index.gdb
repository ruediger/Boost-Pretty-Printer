b done
r
p s
py if sys.version_info[0] == 3: long = int
py v = gdb.parse_and_eval('s')
py boost.multi_index_selector[long(v.address)] = 1
p s
py boost.multi_index_selector[long(v.address)] = 2
p s
py boost.multi_index_selector[long(v.address)] = 3
p s
py boost.multi_index_selector[long(v.address)] = 4
p s
q
