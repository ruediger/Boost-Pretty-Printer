#!/bin/bash
set -ev

sudo apt-get update -qq

if [[ "$1" ==  yes ]]
then
    # https://packages.debian.org/jessie-backports/gdb-python2
    curl -o gdb-python2.deb 'http://http.us.debian.org/debian/pool/main/g/gdb/gdb-python2_7.11.1-2~bpo8+1_amd64.deb'
    sudo dpkg --install --force-depends gdb-python2.deb
    sudo apt-get -f -qq install
else
    sudo apt-get -qq install gdb
fi
