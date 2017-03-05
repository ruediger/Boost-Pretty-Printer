# To use a specific gdb executable, set the GDB variable on the command line.
# E.g.:
#   make GDB=/tmp/gdb-7.9/gdb/gdb
#
# To use a specific (header-only) boost version, set the CPPFLAGS
# to point to the boost include folder you want. E.g.:
#   make CPPFLAGS="-isystem /tmp/boost_1_57_0/include"
#
# For non-header-only libraries, you should also specify LDFLAGS.

GDB ?= gdb
BIN = test
SRC = test.cpp
TESTSUITE = test.py

.PHONY: check interactive clean

check: ${BIN}
	PYTHONPATH="$$PWD/.." ${GDB} --nx --batch -x ${TESTSUITE} ${BIN}

interactive: ${BIN}
	PYTHONPATH="$$PWD/.." ${GDB} --nx ${BIN}

${BIN}: ${SRC}
	$(CXX) -o $@ -std=c++11 -O0 -g3 -ggdb -fno-eliminate-unused-debug-types -Wall -Wextra -Wno-unused-label -Wno-unused-variable -Wno-unused-but-set-variable -pedantic $(CPPFLAGS) $(CXXFLAGS) $(LDFLAGS) $^

clean:
	rm -f ${BIN}
