# coding: utf-8

from __future__ import print_function, unicode_literals, absolute_import, division
import subprocess
import os
from io import open
import stat
import tempfile
import shlex
import shutil

cpp_template = u"""
#include <boost/version.hpp>
#include <iostream>
int main()
{
    unsigned const boost_version = BOOST_VERSION;
    std::cout << boost_version;
    return 0;
}
"""


def unpack_boost_version(boost_version):
    """Split boost version into major, minor and patchlevel components

    :param boost_version: BOOST_VERSION macro from boost/version.hpp
    """
    major = boost_version // 100000
    minor = boost_version // 100 % 1000
    patchlevel = boost_version % 100
    return major, minor, patchlevel


def detect_boost_version():
    """Try to compile simple boost program to automatically detect boost version"""
    dir = tempfile.mkdtemp(prefix='boost-printer-autodetect')
    try:
        src = os.path.join(dir, 'version.cpp')
        bin = os.path.join(dir, 'a.out')

        with open(src, 'w', encoding='utf-8') as src_file:
            print(cpp_template, file=src_file)

        cxx = os.environ.get('CXX', 'c++')
        cppflags = os.environ.get('CPPFLAGS', "")
        cxx_command_line = [cxx] + shlex.split(cppflags) + ['-o', bin, src]
        subprocess.check_call(cxx_command_line)

        os.chmod(bin, stat.S_IXUSR)
        boost_version_raw = int(subprocess.check_output([bin]))
        return unpack_boost_version(boost_version_raw)
    finally:
        shutil.rmtree(dir, ignore_errors=True)
