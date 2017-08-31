SHELL := /bin/bash

#
# Determine the versions of gdb, python, and boost.
#
# To use a specific gdb executable, set the GDB variable on the command line.
# E.g.:
#   make GDB=/tmp/gdb-7.9/gdb/gdb
#
# To use a specific (header-only) boost version, set the CPPFLAGS
# to point to the boost include folder you want. E.g.:
#   make CPPFLAGS="-isystem /tmp/boost_1_57_0/include"
#
# For non-header-only libraries, you should also specify LDFLAGS and/or LDLIBS.
# However, the names of the libraries vary from system to system, so some
# tweaking of the rules below might be needed. A better way to find the proper
# libraries would be to use cmake/autotools.
#
GDB = gdb
GDB_VERSION := $(shell ${GDB} --version | head -n1 | awk '{print $$NF}' | tr '.' '_')
PYTHON_VERSION := $(shell ${GDB} -n -q -ex 'py print(sys.version)' -ex q | head -n1 | awk '{print $$1}' | tr '.' '_')
BOOST_VERSION := $(shell echo '\#include <boost/version.hpp>' | $(CXX) $(CPPFLAGS) -E -dM - | awk '$$2=="BOOST_LIB_VERSION" {print $$3}' | tr -d '"')

TAG = gdb-${GDB_VERSION}.python-${PYTHON_VERSION}.boost-${BOOST_VERSION}

#
# List of tests to be run. It can also be specified on the command line. E.g.,
#   make TESTS=test-other
#
TESTS = test-container test-intrusive test-multi-index test-other test-intrusive-advanced

executable_name = ${1}.boost-${BOOST_VERSION}
output_name = ${1}.${TAG}.out
EXECUTABLES := $(foreach f,${TESTS},$(call executable_name,${f}))
OUTPUTS := $(foreach f,${TESTS},$(call output_name,${f}))

.PHONY: all version list clean cleanall
.SECONDARY:
.DELETE_ON_ERROR:

all: ${EXECUTABLES} ${OUTPUTS}

version:
	@echo GDB_VERSION=${GDB_VERSION}
	@echo PYTHON_VERSION=${PYTHON_VERSION}
	@echo BOOST_VERSION=${BOOST_VERSION}

list:
	@echo TESTS=${TESTS}
	@echo EXECUTABLES=${EXECUTABLES}
	@echo OUTPUTS=${OUTPUTS}

clean:
	rm -rf ${OUTPUTS}

cleanall: clean
	rm -rf ${EXECUTABLES}

#
# Generator of gdb run rules.
#
# Note: We don't use a generic rule because the executable prerequisite doesn't
# necessarily exist.
#
define add_gdb_run
$(call output_name,$1): $(call executable_name,$1) $1.gdb
	@echo "GDB_VERSION=$${GDB_VERSION}" >$$@
	@echo "PYTHON_VERSION=$${PYTHON_VERSION}" >>$$@
	@echo "BOOST_VERSION=$${BOOST_VERSION}" >>$$@
	${GDB} -n -q $$< \
	  -ex 'set pagination off' \
	  -ex 'set auto-load safe-path /' \
	  -ex 'set trace-commands on' \
	  -ex 'py sys.path.insert(0, "..")' \
	  -ex 'py import boost.latest' \
	  -ex 'py boost.register_printers()' \
	  -x $1.gdb | \
	egrep '^(\+|\$$$$)' >>$$@
endef
$(foreach f,${TESTS},$(eval $(call add_gdb_run,$f)))

#
# Generic compilation rule for executables.
#
# Note: To add a test run for a non-header-only library that needs specific
# libraries to be linked, a non-generic compilation rule could be used, and it
# would override the generic one.
#
%.boost-${BOOST_VERSION}: %.cpp
	$(CXX) -o $@ -std=c++11 -O0 -g3 -ggdb -fno-eliminate-unused-debug-types -Wall -Wextra -pedantic $(CPPFLAGS) $(CXXFLAGS) $(LDFLAGS) $^ $(LOADLIBES) $(LDLIBS)
