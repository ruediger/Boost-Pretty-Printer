set python print-stack full
python import boost
python boost.register_printers(boost_version=(${boost_major}, ${boost_minor}, ${boost_patchlevel}))
break main
run
