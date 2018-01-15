from .utils import *
import math
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
            hours = math.floor(ticks / (3600*ticks_per_second))
            if hours > 0:
                rt += str(hours) + 'h '
            min = math.floor(ticks / (60*ticks_per_second)) % 60
            if min > 0:
                rt += str(min) + 'm '
            sec = math.floor((ticks / ticks_per_second)) % 60
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
