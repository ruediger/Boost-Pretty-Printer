#!/bin/bash

if [ $# -eq 0 ]
then
	echo 'Boost source subdirectories must be given as a arguments'
	exit 1
fi

for boost_dir in "$@"
do
	export CPPFLAGS="-isystem $boost_dir"
	make clean
	make
done
