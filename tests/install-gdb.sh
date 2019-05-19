#!/bin/bash
set -ev

sudo apt-get update -qq

if [[ "$1" ==  yes ]]
then
    sudo dpkg --install --force-depends "$TRAVIS_BUILD_DIR/tests/gdb-python2_7.11.1-2_bpo8+1_amd64.deb"
    sudo apt-get -f -qq install
else
    sudo apt-get -qq install gdb
fi
