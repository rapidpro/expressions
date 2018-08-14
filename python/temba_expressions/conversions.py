import datetime

from decimal import Decimal, ROUND_HALF_UP
from . import EvaluationError


def to_boolean(value, ctx):
    """
    Tries conversion of any value to a boolean
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return value != 0
    elif isinstance(value, Decimal):
        return value != Decimal(0)
    elif isinstance(value, str):
        value = value.lower()
        if value == 'true':
            return True
        elif value == 'false':
            return False
    elif isinstance(value, datetime.date) or isinstance(value, datetime.time):
        return True

    raise EvaluationError("Can't convert '%s' to a boolean" % str(value))


def to_integer(value, ctx):
    """
    Tries conversion of any value to an integer
    """
    if isinstance(value, bool):
        return 1 if value else 0
    elif isinstance(value, int):
        return value
    elif isinstance(value, Decimal):
        try:
            val = int(value.to_integral_exact(ROUND_HALF_UP))
            if isinstance(val, int):
                return val
        except ArithmeticError:
            pass
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            pass

    raise EvaluationError("Can't convert '%s' to an integer" % str(value))


def to_decimal(value, ctx):
    """
    Tries conversion of any value to a decimal
    """
    if isinstance(value, bool):
        return Decimal(1) if value else Decimal(0)
    elif isinstance(value, int):
        return Decimal(value)
    elif isinstance(value, Decimal):
        return value
    elif isinstance(value, str):
        try:
            return Decimal(value)
        except Exception:
            pass

    raise EvaluationError("Can't convert '%s' to a decimal" % str(value))


def to_string(value, ctx):
    """
    Tries conversion of any value to a string
    """
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, Decimal):
        return format_decimal(value)
    elif isinstance(value, str):
        return value
    elif type(value) == datetime.date:
        return value.strftime(ctx.get_date_format(False))
    elif isinstance(value, datetime.time):
        return value.strftime('%H:%M')
    elif isinstance(value, datetime.datetime):
        return value.astimezone(ctx.timezone).isoformat()

    raise EvaluationError("Can't convert '%s' to a string" % str(value))


def to_date(value, ctx):
    """
    Tries conversion of any value to a date
    """
    if isinstance(value, str):
        temporal = ctx.get_date_parser().auto(value)
        if temporal is not None:
            return to_date(temporal, ctx)
    elif type(value) == datetime.date:
        return value
    elif isinstance(value, datetime.datetime):
        return value.date()  # discard time

    raise EvaluationError("Can't convert '%s' to a date" % str(value))


def to_datetime(value, ctx):
    """
    Tries conversion of any value to a datetime
    """
    if isinstance(value, str):
        temporal = ctx.get_date_parser().auto(value)
        if temporal is not None:
            return to_datetime(temporal, ctx)
    elif type(value) == datetime.date:
        return ctx.timezone.localize(datetime.datetime.combine(value, datetime.time(0, 0)))
    elif isinstance(value, datetime.datetime):
        return value.astimezone(ctx.timezone)

    raise EvaluationError("Can't convert '%s' to a datetime" % str(value))


def to_date_or_datetime(value, ctx):
    """
    Tries conversion of any value to a date or datetime
    """
    if isinstance(value, str):
        temporal = ctx.get_date_parser().auto(value)
        if temporal is not None:
            return temporal
    elif type(value) == datetime.date:
        return value
    elif isinstance(value, datetime.datetime):
        return value.astimezone(ctx.timezone)

    raise EvaluationError("Can't convert '%s' to a date or datetime" % str(value))


def to_time(value, ctx):
    """
    Tries conversion of any value to a time
    """
    if isinstance(value, str):
        time = ctx.get_date_parser().time(value)
        if time is not None:
            return time
    elif isinstance(value, datetime.time):
        return value
    elif isinstance(value, datetime.datetime):
        return value.astimezone(ctx.timezone).time()

    raise EvaluationError("Can't convert '%s' to a time" % str(value))


def to_same(value1, value2, ctx):
    """
    Converts a pair of arguments to their most-likely types. This deviates from Excel which doesn't auto convert values
    but is necessary for us to intuitively handle contact fields which don't use the correct value type
    """
    if type(value1) == type(value2):
        return value1, value2

    try:
        # try converting to two decimals
        return to_decimal(value1, ctx), to_decimal(value2, ctx)
    except EvaluationError:
        pass

    try:
        # try converting to two dates
        d1, d2 = to_date_or_datetime(value1, ctx), to_date_or_datetime(value2, ctx)

        # if either one is a datetime, then the other needs to become a datetime
        if type(value1) != type(value2):
            d1, d2 = to_datetime(d1, ctx), to_datetime(d2, ctx)
        return d1, d2
    except EvaluationError:
        pass

    # try converting to two strings
    return to_string(value1, ctx), to_string(value2, ctx)


def to_repr(value, ctx):
    """
    Converts a value back to its representation form, e.g. x -> "x"
    """
    as_string = to_string(value, ctx)

    if isinstance(value, str) or isinstance(value, datetime.date) or isinstance(value, datetime.time):
        as_string = as_string.replace('"', '""')  # escape quotes by doubling
        as_string = '"%s"' % as_string

    return as_string


def format_decimal(decimal):
    """
    Formats a decimal number
    :param decimal: the decimal value
    :return: the formatted string value
    """
    # strip trailing fractional zeros
    normalized = decimal.normalize()
    sign, digits, exponent = normalized.as_tuple()
    if exponent >= 1:
        normalized = normalized.quantize(1)

    return str(normalized)
