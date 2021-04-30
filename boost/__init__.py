# encoding: utf-8

# Pretty-printers for Boost (http://www.boost.org)

# Copyright (C) 2009 Rüdiger Sonderfeld <ruediger@c-plusplus.de>
# Copyright (C) 2014 Matei David <matei@cs.toronto.edu>

# Boost Software License - Version 1.0 - August 17th, 2003

# Permission is hereby granted, free of charge, to any person or organization
# obtaining a copy of the software and accompanying documentation covered by
# this license (the "Software") to use, reproduce, display, distribute,
# execute, and transmit the Software, and to prepare derivative works of the
# Software, and to permit third-parties to whom the Software is furnished to
# do so, all subject to the following:

# The copyright notices in the Software and this entire statement, including
# the above license grant, this restriction and the following disclaimer,
# must be included in all copies of the Software, in whole or in part, and
# all derivative works of the Software, unless such copies or derivative
# works are solely in the form of machine-executable object code generated by
# a source language processor.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

#
# Inspired _but not copied_ from libstdc++'s pretty printers
#

from __future__ import print_function, unicode_literals, absolute_import, division
from . import printers
from . import flat_containers
from . import unordered_containers
from . import intrusive_1_55
from . import intrusive_1_40
from . import multi_index_1_42
from . import type_erasure
from .utils import register_printers, add_trivial_printer, options, last_supported_boost_version
from . import datetime
from . import variant
from . import wave_1_71
