set python print-stack full
python import sys
python sys.path.insert(0, '../boost/')
python import boost
python boost.register_printers()
break main
run
