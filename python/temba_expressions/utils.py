import datetime
import math
import pytz
import regex

from decimal import Decimal, ROUND_HALF_UP
from six.moves.urllib.parse import quote

JSON_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# treats sequences of letters/numbers/_/' as tokens, and symbols as individual tokens
WORD_TOKEN_REGEX = regex.compile(r"[\p{M}\p{L}\p{N}_']+|\pS", flags=regex.UNICODE | regex.V0)


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
    return WORD_TOKEN_REGEX.findall(text)


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

