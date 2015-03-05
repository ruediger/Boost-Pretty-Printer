SHELL = /bin/bash

GDB = gdb

GDB_VERSION = $(shell ${GDB} --version | head -n1 | awk '{print $$4}')
PYTHON_VERSION = $(shell ${GDB} -n -q -ex 'py print(sys.version)' -ex q | head -n1 | awk '{print $$1}')

TAG = default
TESTS = test-container test-intrusive test-multi-index test-other
TARGETS = $(foreach f,${TESTS},${f}.${TAG}.out)


.PHONY: all clean list
.SECONDARY:
.DELETE_ON_ERROR:

all: ${TARGETS}

list:
	@echo GDB_VERSION=${GDB_VERSION}
	@echo PYTHON_VERSION=${PYTHON_VERSION}
	@echo TESTS=${TESTS}
	@echo TARGETS=${TARGETS}

clean:
	rm -rf ${TARGETS} ${TESTS}

define add_gdb_run
$1.${TAG}.out: $1 $1.gdb
	{ \
	echo "GDB_VERSION=$${GDB_VERSION}"; \
	echo "PYTHON_VERSION=$${PYTHON_VERSION}"; \
	${GDB} -n -q $1 \
	  -ex 'set pagination off' \
	  -ex 'set auto-load safe-path /' \
	  -ex 'set trace-commands on' \
	  -ex 'py sys.path.insert(0, "..")' \
	  -ex 'py import boost' \
	  -ex 'py boost.register_printers()' \
	  -x $1.gdb | \
	egrep '^(\+|\$$$$)'; \
	} >$$@
endef
$(foreach f,${TESTS},$(eval $(call add_gdb_run,$f)))

define add_gcc_run
$1: $1.cpp
	g++ -O0 -g3 -ggdb -std=c++11 -Wall -Wextra -pedantic -o $$@ $$<
endef
$(foreach f,${TESTS},$(eval $(call add_gcc_run,$f)))
