b done
r
p s
python if sys.version_info[0] == 3: long = int
python import boost.printers
python v = boost.printers.parse_and_eval('s')
python boost.printers.multi_index_selector[long(v.address)] = 1
p s
python boost.printers.multi_index_selector[long(v.address)] = 2
p s
python boost.printers.multi_index_selector[long(v.address)] = 3
p s
python boost.printers.multi_index_selector[long(v.address)] = 4
p s
q
