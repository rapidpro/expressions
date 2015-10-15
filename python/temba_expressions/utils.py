from __future__ import absolute_import, unicode_literals

import datetime
import math
import pytz
import regex
import urllib

from decimal import Decimal

JSON_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def decimal_pow(number, power):
    """
    Pow for two decimals
    """
    return Decimal(math.pow(number, power))


def urlquote(text):
    """
    Encodes text for inclusion in a URL query string. Should be equivalent to Django's urlquote function.
    :param text: the text to encode
    :return: the encoded text
    """
    return urllib.quote(text.encode('utf-8'))


def tokenize(text):
    """
    Tokenizes a string by splitting on non-word characters.
    """
    splits = regex.split(r"\W+", text, flags=regex.UNICODE | regex.V0)
    return [split for split in splits if split]   # return only non-empty


def parse_json_date(value):
    """
    Parses an ISO8601 formatted datetime from a string value
    """
    if not value:
        return None

    return datetime.datetime.strptime(value, JSON_DATETIME_FORMAT).replace(tzinfo=pytz.UTC)


def format_json_date(value):
    """
    Formats a datetime as ISO8601 in UTC with millisecond precision, e.g. "2014-10-03T09:41:12.790Z"
    """
    if not value:
        return None

    # %f will include 6 microsecond digits
    micro_precision = value.astimezone(pytz.UTC).strftime(JSON_DATETIME_FORMAT)

    # only keep the milliseconds portion of the second fraction
    return micro_precision[:-4] + 'Z'

