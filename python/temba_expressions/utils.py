from __future__ import absolute_import, unicode_literals

import datetime
import math
import pytz
import sys
import regex

from decimal import Decimal, ROUND_HALF_UP
from six.moves.urllib.parse import quote

JSON_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

WORD_TOKEN_REGEX = r"\w+"  # any word characters
WORD_TOKEN_REGEX += r"|[\u20A0-\u20CF]"  # Currency symbols
WORD_TOKEN_REGEX += r"|[\u2600-\u27BF]"  # Miscellaneous symbols

if sys.maxunicode > 65535:
    WORD_TOKEN_REGEX += r"|[\U0001F300-\U0001F5FF]"  # Miscellaneous Symbols and Pictographs
    WORD_TOKEN_REGEX += r"|[\U0001F600-\U0001F64F]"  # Emoticons
    WORD_TOKEN_REGEX += r"|[\U0001F680-\U0001F6FF]"  # Transport and Map Symbols
    WORD_TOKEN_REGEX += r"|[\U0001F900-\U0001F9FF]"  # Supplemental Symbols and Pictographs

else:
    WORD_TOKEN_REGEX += r"|\uD83C[\uDF00-\uDFFF]"  # Miscellaneous Symbols and Pictographs, Emoticons
    WORD_TOKEN_REGEX += r"|\uD83D[\uDC00-\uDE4F]"  # Miscellaneous Symbols and Pictographs, Emoticons
    WORD_TOKEN_REGEX += r"|\uD83D[\uDE80-\uDEFF]"  # Transport and Map Symbols
    WORD_TOKEN_REGEX += r"|\uD83E[\uDD00-\uDDFF]"  # Supplemental Symbols and Pictographs


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
    return quote(text.encode('utf-8'))


def tokenize(text):
    """
    Tokenizes a string by splitting on non-word characters.
    """
    return regex.findall(WORD_TOKEN_REGEX, text, flags=regex.UNICODE | regex.V0)


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

