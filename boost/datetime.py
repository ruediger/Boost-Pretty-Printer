from __future__ import print_function, absolute_import, division

import datetime
import math
from .utils import *

@add_printer
class BoostPosixTimeDuration:
    "Pretty Printer for boost::posix_time::time_duration"
    printer_name = 'boost::posix_time::time_duration'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::posix_time::time_duration'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        rt = ""
        neg = False
        ticks = int(self.value['ticks_']['value_'])
        if ticks == 2**63 - 1:
            rt = 'positive infinity'
        elif ticks == -2**63:
            rt = 'negative infinity'
        if ticks == 2**63 - 2:
            rt = 'not a date time'
        else:
            if ticks < 0:
                neg = True
                ticks *= -1
            ticks_per_second = 1000000
            hours = ticks // (3600*ticks_per_second)
            if hours > 0:
                rt += str(hours) + 'h '
            min = (ticks // (60*ticks_per_second)) % 60
            if min > 0:
                rt += str(min) + 'm '
            sec = (ticks // ticks_per_second) % 60
            if sec > 0:
                rt += str(sec)
                if ticks % ticks_per_second > 0:
                    rt += '.%06d' % (ticks % ticks_per_second)
                rt += 's'
            if rt == "":
                rt = "0"
            if neg:
                rt = "-" + rt
        return '(%s) %s' % (self.typename, rt.strip())

@add_printer
class BoostGregorianDate:
    "Pretty Printer for boost::gregorian::date"
    printer_name = 'boost::gregorian::date'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::gregorian::date'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        n = intptr(self.value['days_'])
        date_int_type_bits = self.value['days_'].type.sizeof * 8
        # Compatibility fix for gdb+python2, which erroneously converts big 64-bit unsigned
        # values to negative python ints. It affects various special values and dates in VERY distant future.
        if n < 0:
            n += 2**date_int_type_bits

        # Check for uninitialized case
        if n == 2**date_int_type_bits - 2:
            return '(%s) uninitialized' % self.typename
        # Convert date number to year-month-day
        a = n + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        day = e + 1 - (153 * m + 2) // 5
        month = m + 3 - 12 * (m // 10)
        year = 100 * b + d - 4800 + (m // 10)
        return '(%s) %4d-%02d-%02d' % (self.typename, year, month, day)


@add_printer
class BoostPosixTimePTime:
    "Pretty Printer for boost::posix_time::ptime"
    printer_name = 'boost::posix_time::ptime'
    min_supported_version = (1, 40, 0)
    max_supported_version = last_supported_boost_version
    template_name = 'boost::posix_time::ptime'

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        n = int(self.value['time_']['time_count_']['value_'])
        # Check for uninitialized case
        if n == 2**63 - 2:
            return '(%s) uninitialized' % self.typename
        # Check for boost::posix_time::pos_infin case
        if n == 2**63 - 1:
            return '(%s) positive infinity' % self.typename
        # Check for boost::posix_time::neg_infin case
        if n == -2**63:
            return '(%s) negative infinity' % self.typename
        # Subtract the unix epoch from the timestamp and convert the resulting timestamp into something human readable
        unix_epoch_time = (n - 210866803200000000) / 1000000.0
        time_string = datetime.datetime.utcfromtimestamp(unix_epoch_time).isoformat(' ')
        return '(%s) %sZ' % (self.typename, time_string)
