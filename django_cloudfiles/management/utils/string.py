"""
Some quick and dirty string-related utilities used by the management commands.
Not suggested for reuse; something better almost certainly exists.
"""

from sys import stdout

def write(str):
    stdout.write(str)
    stdout.flush()        

DECIMAL_ORDERS = (
    (10**(3*4), "TB"),
    (10**(3*3), "GB"),
    (10**(3*2), "MB"),
    (10**(3*1), "KB"),
    (10**(3*0), "B"),
)
def format_bytes(bytes):
    for order, mnemonic in DECIMAL_ORDERS:
        if bytes >= order:
            return "%u %s" % (bytes // order, mnemonic)
    return "%u %s" % (bytes, DECIMAL_ORDERS[-1][1])

SECS_IN_MIN = 60
MINS_IN_HOUR = 60
SECS_IN_HOUR = SECS_IN_MIN * MINS_IN_HOUR
def format_secs(secs):
    if secs < SECS_IN_MIN:
        return "%u %s" % (secs, "seconds")
    if secs < SECS_IN_HOUR:
        return "%u:%u" % (secs // SECS_IN_MIN, secs % SECS_IN_MIN)
    return "%u:%s" % (secs // SECS_IN_HOUR, format_secs(secs % SECS_IN_HOUR))
