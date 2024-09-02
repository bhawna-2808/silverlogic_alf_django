import datetime
import re

from django.utils import six

STRFDATETIME = re.compile("([dgGhHis])")
STRFDATETIME_REPL = lambda x: "%%(%s)s" % x.group()


def timedelta_nice_repr(timedelta, display="long", sep=", "):
    """
    Turns a datetime.timedelta object into a nice string repr.
    from (as of ALF-2241): https://github.com/sookasa/django-timedelta-field/blob/master/timedelta/helpers.py
    """
    assert isinstance(timedelta, datetime.timedelta), "First argument must be a timedelta."

    result = []

    weeks = int(timedelta.days / 7)
    days = timedelta.days % 7
    hours = int(timedelta.seconds / 3600)
    minutes = int((timedelta.seconds % 3600) / 60)
    seconds = timedelta.seconds % 60

    if display == "sql":
        days += weeks * 7
        return "%i %02i:%02i:%02i" % (days, hours, minutes, seconds)
    elif display == "minimal":
        words = ["w", "d", "h", "m", "s"]
    elif display == "short":
        words = [" wks", " days", " hrs", " min", " sec"]
    elif display == "long":
        words = [" weeks", " days", " hours", " minutes", " seconds"]
    else:
        # Use django template-style formatting.
        # Valid values are:
        # d,g,G,h,H,i,s
        return STRFDATETIME.sub(STRFDATETIME_REPL, display) % {
            "d": days,
            "g": hours,
            "G": hours if hours > 9 else "0%s" % hours,
            "h": hours,
            "H": hours if hours > 9 else "0%s" % hours,
            "i": minutes if minutes > 9 else "0%s" % minutes,
            "s": seconds if seconds > 9 else "0%s" % seconds,
        }

    values = [weeks, days, hours, minutes, seconds]

    for i, value in enumerate(values):
        if value == 1 and len(words[i]) > 1:
            result.append("%i%s" % (value, words[i].rstrip("s")))
        else:
            result.append("%i%s" % (value, words[i]))

    # values with less than one second, which are considered zeroes
    if len(result) == 0:
        # display as 0 of the smallest unit
        result.append("0%s" % (words[-1]))

    return sep.join(result)


def parse_string_to_timedelta(string):
    """
    Parse a string into a timedelta object.
    from: https://bitbucket.org/schinckel/django-timedelta-field/src/229cd5a9ae15b6611c6689ce3a074333fdc7daf2/timedelta/helpers.py#lines-160
    """
    string = string.strip()

    if string == "":
        raise TypeError("'%s' is not a valid time interval" % string)
    # This is the format we get from sometimes Postgres, sqlite,
    # and from serialization
    d = re.match(
        r"^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):"
        r"(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$",
        six.text_type(string),
    )
    if d:
        d = d.groupdict(0)
        if d["sign"] == "-":
            for k in "hours", "minutes", "seconds":
                d[k] = "-" + d[k]
        d.pop("sign", None)
    else:
        # This is the more flexible format
        d = re.match(
            r"^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?"
            r"((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?"
            r"((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?"
            r"((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?"
            r"((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$",
            six.text_type(string),
        )
        if not d:
            raise TypeError("'%s' is not a valid time interval" % string)
        d = d.groupdict(0)

    return datetime.timedelta(**dict(((k, float(v)) for k, v in d.items())))
