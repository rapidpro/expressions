from __future__ import absolute_import, unicode_literals

import datetime
import math
import pytz
import regex
import urllib

from decimal import Decimal, ROUND_HALF_UP

JSON_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def decimal_pow(number, power):
    """
    Pow for two decimals
    """
    return Decimal(math.pow(number, power))


def decimal_round(number, num_digits, rounding=ROUND_HALF_UP):
    """
    Rounding for decimals with support for negative digits
    """
    exp = Decimal(10) ** -num_digits

    if num_digits >= 0:
        return number.quantize(exp, rounding)
    else:
        return exp * (number / exp).to_integral_value(rounding)


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


def render_dict(value):
    """
    Converts a dict to a string. If dict has a default value, that is returned, otherwise we generate a se of name value
    pairs separated by new lines.
    """
    if '*' in value:
        return unicode(value['*'])
    elif '__default__' in value:
        return unicode(value['__default__'])

    pairs = []

    for item_key, item_val in value.items():
        # flatten nested dict
        if isinstance(item_val, dict):
            if '*' in item_val:
                item_val = item_val['*']
            elif '__default__' in item_val:
                item_val = item_val['__default__']
            else:
                item_val = '[...]'

        pairs.append('%s: %s' % (item_key, unicode(item_val)))

    return '\n'.join(sorted(pairs))
