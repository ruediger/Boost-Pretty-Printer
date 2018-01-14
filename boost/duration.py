from .utils import *
@add_printer
class BoostPosixTimePTime:
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
        ticks = call_object_method(self.value,"ticks")
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
            # return dir(self.value)
            ticks_per_second = 1000000
            num_fractional_digits = 6
            hours = ticks / (3600*ticks_per_second)
            if hours > 0:
                rt += str(hours) + 'h'
            min = (ticks / (60*ticks_per_second)) % 60
            if min > 0:
                rt += str(min) + 'm'
            sec = (ticks / ticks_per_second) % 60
            if sec > 0:
                rt += str(sec)
                if ticks % ticks_per_second > 0:
                    rt += '.%06d' % (ticks % ticks_per_second)
                rt += 's'
            if rt == "":
                rt = "0"
            if neg:
                rt = "-" + rt
        return ('(%s) ' % self.typename) + rt
