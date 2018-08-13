import random

from datetime import date as _date, time as _time
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from temba_expressions import conversions
from temba_expressions.utils import decimal_pow, decimal_round


E = Decimal('2.718281828459045235360287471')


# =============================== Text ===============================

def char(ctx, number):
    """
    Returns the character specified by a number
    """
    return chr(conversions.to_integer(number, ctx))


def clean(ctx, text):
    """
    Removes all non-printable characters from a text string
    """
    text = conversions.to_string(text, ctx)
    return ''.join([c for c in text if ord(c) >= 32])


def code(ctx, text):
    """
    Returns a numeric code for the first character in a text string
    """
    return _unicode(ctx, text)  # everything is unicode


def concatenate(ctx, *text):
    """
    Joins text strings into one text string
    """
    result = ''
    for arg in text:
        result += conversions.to_string(arg, ctx)
    return result


def fixed(ctx, number, decimals=2, no_commas=False):
    """
    Formats the given number in decimal format using a period and commas
    """
    value = _round(ctx, number, decimals)
    format_str = '{:f}' if no_commas else '{:,f}'
    return format_str.format(value)


def left(ctx, text, num_chars):
    """
    Returns the first characters in a text string
    """
    num_chars = conversions.to_integer(num_chars, ctx)
    if num_chars < 0:
        raise ValueError("Number of chars can't be negative")
    return conversions.to_string(text, ctx)[0:num_chars]


def _len(ctx, text):
    """
    Returns the number of characters in a text string
    """
    return len(conversions.to_string(text, ctx))


def lower(ctx, text):
    """
    Converts a text string to lowercase
    """
    return conversions.to_string(text, ctx).lower()


def proper(ctx, text):
    """
    Capitalizes the first letter of every word in a text string
    """
    return conversions.to_string(text, ctx).title()


def rept(ctx, text, number_times):
    """
    Repeats text a given number of times
    """
    if number_times < 0:
        raise ValueError("Number of times can't be negative")
    return conversions.to_string(text, ctx) * conversions.to_integer(number_times, ctx)


def right(ctx, text, num_chars):
    """
    Returns the last characters in a text string
    """
    num_chars = conversions.to_integer(num_chars, ctx)
    if num_chars < 0:
        raise ValueError("Number of chars can't be negative")
    elif num_chars == 0:
        return ''
    else:
        return conversions.to_string(text, ctx)[-num_chars:]


def substitute(ctx, text, old_text, new_text, instance_num=-1):
    """
    Substitutes new_text for old_text in a text string
    """
    text = conversions.to_string(text, ctx)
    old_text = conversions.to_string(old_text, ctx)
    new_text = conversions.to_string(new_text, ctx)

    if instance_num < 0:
        return text.replace(old_text, new_text)
    else:
        splits = text.split(old_text)
        output = splits[0]
        instance = 1
        for split in splits[1:]:
            sep = new_text if instance == instance_num else old_text
            output += sep + split
            instance += 1
        return output


def unichar(ctx, number):
    """
    Returns the unicode character specified by a number
    """
    return chr(conversions.to_integer(number, ctx))


def _unicode(ctx, text):
    """
    Returns a numeric code for the first character in a text string
    """
    text = conversions.to_string(text, ctx)
    if len(text) == 0:
        raise ValueError("Text can't be empty")
    return ord(text[0])


def upper(ctx, text):
    """
    Converts a text string to uppercase
    """
    return conversions.to_string(text, ctx).upper()


# =============================== Date and time ===============================


def date(ctx, year, month, day):
    """
    Defines a date value
    """
    return _date(conversions.to_integer(year, ctx), conversions.to_integer(month, ctx), conversions.to_integer(day, ctx))


def datedif(ctx, start_date, end_date, unit):
    """
    Calculates the number of days, months, or years between two dates.
    """
    start_date = conversions.to_date(start_date, ctx)
    end_date = conversions.to_date(end_date, ctx)
    unit = conversions.to_string(unit, ctx).lower()

    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")

    if unit == 'y':
        return relativedelta(end_date, start_date).years
    elif unit == 'm':
        delta = relativedelta(end_date, start_date)
        return 12 * delta.years + delta.months
    elif unit == 'd':
        return (end_date - start_date).days
    elif unit == 'md':
        return relativedelta(end_date, start_date).days
    elif unit == 'ym':
        return relativedelta(end_date, start_date).months
    elif unit == 'yd':
        return (end_date - start_date.replace(year=end_date.year)).days

    raise ValueError("Invalid unit value: %s" % unit)


def datevalue(ctx, text):
    """
    Converts date stored in text to an actual date
    """
    return conversions.to_date(text, ctx)


def day(ctx, date):
    """
    Returns only the day of the month of a date (1 to 31)
    """
    return conversions.to_date_or_datetime(date, ctx).day


def days(ctx, end_date, start_date):
    """
    Returns the number of days between two dates.
    """
    return datedif(ctx, start_date, end_date, 'd')


def edate(ctx, date, months):
    """
    Moves a date by the given number of months
    """
    return conversions.to_date_or_datetime(date, ctx) + relativedelta(months=conversions.to_integer(months, ctx))


def hour(ctx, datetime):
    """
    Returns only the hour of a datetime (0 to 23)
    """
    return conversions.to_datetime(datetime, ctx).hour


def minute(ctx, datetime):
    """
    Returns only the minute of a datetime (0 to 59)
    """
    return conversions.to_datetime(datetime, ctx).minute


def month(ctx, date):
    """
    Returns only the month of a date (1 to 12)
    """
    return conversions.to_date_or_datetime(date, ctx).month


def now(ctx):
    """
    Returns the current date and time
    """
    return ctx.now.astimezone(ctx.timezone)


def second(ctx, datetime):
    """
    Returns only the second of a datetime (0 to 59)
    """
    return conversions.to_datetime(datetime, ctx).second


def time(ctx, hours, minutes, seconds):
    """
    Defines a time value
    """
    return _time(conversions.to_integer(hours, ctx), conversions.to_integer(minutes, ctx), conversions.to_integer(seconds, ctx))


def timevalue(ctx, text):
    """
    Converts time stored in text to an actual time
    """
    return conversions.to_time(text, ctx)


def today(ctx):
    """
    Returns the current date
    """
    return ctx.now.astimezone(ctx.timezone).date()


def weekday(ctx, date):
    """
    Returns the day of the week of a date (1 for Sunday to 7 for Saturday)
    """
    return ((conversions.to_date_or_datetime(date, ctx).weekday() + 1) % 7) + 1


def year(ctx, date):
    """
    Returns only the year of a date
    """
    return conversions.to_date_or_datetime(date, ctx).year


# =============================== Math ===============================


def _abs(ctx, number):
    """
    Returns the absolute value of a number
    """
    return conversions.to_decimal(abs(conversions.to_decimal(number, ctx)), ctx)


def average(ctx, *number):
    """
    Returns the average (arithmetic mean) of the arguments
    """
    return _sum(ctx, *number) / len(number)


def exp(ctx, number):
    """
    Returns e raised to the power of number
    """
    return decimal_pow(E, conversions.to_decimal(number, ctx))


def _int(ctx, number):
    """
    Rounds a number down to the nearest integer
    """
    return conversions.to_integer(conversions.to_decimal(number, ctx).to_integral_value(ROUND_FLOOR), ctx)


def _max(ctx, *number):
    """
    Returns the maximum value of all arguments
    """
    if len(number) == 0:
        raise ValueError("Wrong number of arguments")

    result = conversions.to_decimal(number[0], ctx)
    for arg in number[1:]:
        arg = conversions.to_decimal(arg, ctx)
        if arg > result:
            result = arg
    return result


def _min(ctx, *number):
    """
    Returns the minimum value of all arguments
    """
    if len(number) == 0:
        raise ValueError("Wrong number of arguments")

    result = conversions.to_decimal(number[0], ctx)
    for arg in number[1:]:
        arg = conversions.to_decimal(arg, ctx)
        if arg < result:
            result = arg
    return result


def mod(ctx, number, divisor):
    """
    Returns the remainder after number is divided by divisor
    """
    number = conversions.to_decimal(number, ctx)
    divisor = conversions.to_decimal(divisor, ctx)
    return number - divisor * _int(ctx, number / divisor)


def _power(ctx, number, power):
    """
    Returns the result of a number raised to a power
    """
    return decimal_pow(conversions.to_decimal(number, ctx), conversions.to_decimal(power, ctx))


def rand():
    """
    Returns an evenly distributed random real number greater than or equal to 0 and less than 1
    """
    return Decimal(str(random.random()))


def randbetween(ctx, bottom, top):
    """
    Returns a random integer number between the numbers you specify
    """
    bottom = conversions.to_integer(bottom, ctx)
    top = conversions.to_integer(top, ctx)
    return random.randint(bottom, top)


def _round(ctx, number, num_digits):
    """
    Rounds a number to a specified number of digits
    """
    number = conversions.to_decimal(number, ctx)
    num_digits = conversions.to_integer(num_digits, ctx)

    return decimal_round(number, num_digits, ROUND_HALF_UP)


def rounddown(ctx, number, num_digits):
    """
    Rounds a number down, toward zero
    """
    number = conversions.to_decimal(number, ctx)
    num_digits = conversions.to_integer(num_digits, ctx)

    return decimal_round(number, num_digits, ROUND_DOWN)


def roundup(ctx, number, num_digits):
    """
    Rounds a number up, away from zero
    """
    number = conversions.to_decimal(number, ctx)
    num_digits = conversions.to_integer(num_digits, ctx)

    return decimal_round(number, num_digits, ROUND_UP)


def _sum(ctx, *number):
    """
    Returns the sum of all arguments
    """
    if len(number) == 0:
        raise ValueError("Wrong number of arguments")

    result = Decimal(0)
    for arg in number:
        result += conversions.to_decimal(arg, ctx)
    return result


def trunc(ctx, number):
    """
    Truncates a number to an integer by removing the fractional part of the number
    """
    return conversions.to_integer(conversions.to_decimal(number, ctx).to_integral_value(ROUND_DOWN), ctx)


# =============================== Logical ===============================

def _and(ctx, *logical):
    """
    Returns TRUE if and only if all its arguments evaluate to TRUE
    """
    for arg in logical:
        if not conversions.to_boolean(arg, ctx):
            return False
    return True


def false():
    """
    Returns the logical value FALSE
    """
    return False


def _if(ctx, logical_test, value_if_true=0, value_if_false=False):
    """
    Returns one value if the condition evaluates to TRUE, and another value if it evaluates to FALSE
    """
    return value_if_true if conversions.to_boolean(logical_test, ctx) else value_if_false


def _or(ctx, *logical):
    """
    Returns TRUE if any argument is TRUE
    """
    for arg in logical:
        if conversions.to_boolean(arg, ctx):
            return True
    return False


def true():
    """
    Returns the logical value TRUE
    """
    return True
