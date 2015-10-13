from __future__ import absolute_import, unicode_literals

import datetime
import pkg_resources
import pytz
import regex

from collections import OrderedDict
from enum import Enum


class DateStyle(Enum):
    DAY_FIRST = 1
    MONTH_FIRST = 2


class Component(Enum):
    YEAR = 0  # 99 or 1999
    MONTH = 1  # 1 or Jan
    DAY = 2
    HOUR = 3
    MINUTE = 4
    HOUR_AND_MINUTE = 5  # e.g. 1400
    SECOND = 6
    NANO = 7
    AM_PM = 8
    OFFSET = 9


class Mode(Enum):
    DATE = 1
    DATETIME = 2
    TIME = 3
    AUTO = 4


class DateLexer(object):
    """
    Lexer used by DateParser. Tokenizes input into sequences of digits or letters.
    """
    class State(Enum):
        IGNORED = 0
        NUMERIC_TOKEN = 1
        ALPHABETIC_TOKEN = 2

    def tokenize(self, text):
        length = len(text)
        if length == 0:
            return []

        state = DateLexer.State.IGNORED
        current_token_type = None
        current_token_start = -1
        tokens = []

        for pos, ch in enumerate(text):
            prev_state = state

            if ch.isalpha():
                state = DateLexer.State.ALPHABETIC_TOKEN
            elif ch.isdigit():
                state = DateLexer.State.NUMERIC_TOKEN
            else:
                state = DateLexer.State.IGNORED

            if prev_state != state:
                # ending a token
                if prev_state != DateLexer.State.IGNORED:
                    tokens.append(DateLexer.Token(current_token_type, text[current_token_start:pos], current_token_start, pos))

                # beginning a new token
                if state != DateLexer.State.IGNORED:
                    current_token_type = DateLexer.Token.Type.NUMERIC if state == DateLexer.State.NUMERIC_TOKEN else DateLexer.Token.Type.ALPHABETIC
                    current_token_start = pos

        if state != DateLexer.State.IGNORED:
            tokens.append(DateLexer.Token(current_token_type, text[current_token_start:length], current_token_start, length))

        return tokens

    class Token(object):
        """
        A lexer token
        """
        class Type(Enum):
            NUMERIC = 1,    # a sequence of digits
            ALPHABETIC = 2  # a sequence of letters

        def __init__(self, _type, text, start, end):
            self.type = _type
            self.text = text
            self.start = start
            self.end = end

        def __eq__(self, other):
            return self.type == other.type and self.text == other.text and self.start == other.start and self.end == other.end


class DateParser(object):
    """
    Flexible date parser for human written dates
    """
    LEXER = DateLexer()

    AM = 0
    PM = 1

    DATE_SEQUENCES_DAY_FIRST = [
        [Component.DAY, Component.MONTH, Component.YEAR],
        [Component.MONTH, Component.DAY, Component.YEAR],
        [Component.YEAR, Component.MONTH, Component.DAY],
        [Component.DAY, Component.MONTH],
        [Component.MONTH, Component.DAY],
        [Component.MONTH, Component.YEAR],
    ]

    DATE_SEQUENCES_MONTH_FIRST = [
        [Component.MONTH, Component.DAY, Component.YEAR],
        [Component.DAY, Component.MONTH, Component.YEAR],
        [Component.YEAR, Component.MONTH, Component.DAY],
        [Component.MONTH, Component.DAY],
        [Component.DAY, Component.MONTH],
        [Component.MONTH, Component.YEAR],
    ]

    TIME_SEQUENCES = [
        [Component.HOUR_AND_MINUTE],
        [Component.HOUR, Component.MINUTE],
        [Component.HOUR, Component.MINUTE, Component.AM_PM],
        [Component.HOUR, Component.MINUTE, Component.SECOND],
        [Component.HOUR, Component.MINUTE, Component.SECOND, Component.AM_PM],
        [Component.HOUR, Component.MINUTE, Component.SECOND, Component.NANO],
        [Component.HOUR, Component.MINUTE, Component.SECOND, Component.NANO, Component.OFFSET],
    ]

    def __init__(self, now, timezone, date_style):
        """
        Creates a new date parser
        :param now: the now which parsing happens relative to
        :param timezone: the timezone in which times are interpreted if input doesn't include an offset
        :param date_style: whether dates are usually entered day first or month first
        """
        self._now = now
        self._timezone = timezone
        self._date_style = date_style

    def auto(self, text):
        """
        Returns a date or datetime depending on what information is available
        :param text: the text to parse
        :return: the parsed date or datetime
        """
        result = self._parse(text, Mode.AUTO)
        return result.value if result else None

    def auto_with_location(self, text):
        """
        Returns a date or datetime depending on what information is available, along with location information
        :param text: the text to parse
        :return: the result including the date or datetime and location
        """
        return self._parse(text, Mode.AUTO)

    def time(self, text):
        """
        Tries to parse a time value from the given text
        :param text: the text to parse
        :return: the parsed time
        """
        result = self._parse(text, Mode.TIME)
        return result.value if result else None

    def _parse(self, text, mode):
        """
        Returns a date, datetime or time depending on what information is available
        """
        if not text.strip():
            return None

        # split the text into numerical and alphabetical tokens
        tokens = self.LEXER.tokenize(text)

        start_pos = -1
        end_pos = -1

        # get the possibilities for each token
        token_possibilities = []
        for token in tokens:
            possibilities = self._get_token_possibilities(token, mode)
            if len(possibilities) > 0:
                token_possibilities.append(possibilities)

                # keep track of min start and max end positions of tokens with possibilities
                if start_pos < 0:
                    start_pos = token.start
                if token.end > end_pos:
                    end_pos = token.end

        # see what valid sequences we can make
        sequences = self._get_possible_sequences(mode, len(token_possibilities), self._date_style)

        for sequence in sequences:
            match = OrderedDict()

            for c in range(len(sequence)):
                component = sequence[c]
                value = token_possibilities[c].get(component, None)
                match[component] = value

                if value is None:
                    break
            else:
                # try to form a valid date or time and return it if successful
                obj = self._make_result(match, self._now, self._timezone)
                if obj is not None:
                    return DateParser.Result(obj, start_pos, end_pos)

        return None

    @classmethod
    def _get_possible_sequences(cls, mode, length, date_style):
        """
        Gets possible component sequences in the given mode
        :param mode: the mode
        :param length: the length (only returns sequences of this length)
        :param date_style: whether dates are usually entered day first or month first
        :return:
        """
        sequences = []
        date_sequences = cls.DATE_SEQUENCES_DAY_FIRST if date_style == DateStyle.DAY_FIRST else cls.DATE_SEQUENCES_MONTH_FIRST

        if mode == Mode.DATE or mode == Mode.AUTO:
            for seq in date_sequences:
                if len(seq) == length:
                    sequences.append(seq)

        elif mode == Mode.TIME:
            for seq in cls.TIME_SEQUENCES:
                if len(seq) == length:
                    sequences.append(seq)

        if mode == Mode.DATETIME or mode == Mode.AUTO:
            for date_seq in date_sequences:
                for time_seq in cls.TIME_SEQUENCES:
                    if len(date_seq) + len(time_seq) == length:
                        sequences.append(date_seq + time_seq)

        return sequences

    @classmethod
    def _get_token_possibilities(cls, token, mode):
        """
        Returns all possible component types of a token without regard to its context. For example "26" could be year,
        date or minute, but can't be a month or an hour.
        :param token: the token to classify
        :param mode: the parse mode
        :return: the dict of possible types and values if token was of that type
        """
        possibilities = {}
        text = token.text.lower()

        if token.type == DateLexer.Token.Type.NUMERIC:
            as_int = int(text)

            if mode != Mode.TIME:
                if 1 <= as_int <= 9999 and (len(text) == 2 or len(text) == 4):
                    possibilities[Component.YEAR] = as_int
                if 1 <= as_int <= 12:
                    possibilities[Component.MONTH] = as_int
                if 1 <= as_int <= 31:
                    possibilities[Component.DAY] = as_int

            if mode != Mode.DATE:
                if 0 <= as_int <= 23:
                    possibilities[Component.HOUR] = as_int
                if 0 <= as_int <= 59:
                    possibilities[Component.MINUTE] = as_int
                if 0 <= as_int <= 59:
                    possibilities[Component.SECOND] = as_int
                if len(text) == 3 or len(text) == 6 or len(text) == 9:
                    nano = 0
                    if len(text) == 3:  # millisecond precision
                        nano = as_int * 1000000
                    elif len(text) == 6:  # microsecond precision
                        nano = as_int * 1000
                    elif len(text) == 9:
                        nano = as_int
                    possibilities[Component.NANO] = nano
                if len(text) == 4:
                    hour = as_int / 100
                    minute = as_int - (hour * 100)
                    if 1 <= hour <= 24 and 1 <= minute <= 59:
                        possibilities[Component.HOUR_AND_MINUTE] = as_int

        elif token.type == DateLexer.Token.Type.ALPHABETIC:
            if mode != Mode.TIME:
                # could it be a month alias?
                month = MONTHS_BY_ALIAS.get(text, None)
                if month is not None:
                    possibilities[Component.MONTH] = month

            if mode != Mode.DATE:
                # could it be an AM/PM marker?
                is_am_marker = text == "am"
                is_pm_marker = text == "pm"
                if is_am_marker or is_pm_marker:
                    possibilities[Component.AM_PM] = cls.AM if is_am_marker else cls.PM

                # offset parsing is limited to Z meaning UTC for now
                if text == "z":
                    possibilities[Component.OFFSET] = 0

        return possibilities

    @classmethod
    def _make_result(cls, values, now, timezone):
        """
        Makes a date or datetime or time object from a map of component values
        :param values: the component values
        :param now: the current now
        :param timezone: the current timezone
        :return: the date, datetime, time or none if values are invalid
        """
        date = None
        time = None

        if Component.MONTH in values:
            year = cls._year_from_2digits(values.get(Component.YEAR, now.year), now.year)
            month = values[Component.MONTH]
            day = values.get(Component.DAY, 1)
            try:
                date = datetime.date(year, month, day)
            except ValueError:
                return None  # not a valid date

        if (Component.HOUR in values and Component.MINUTE in values) or Component.HOUR_AND_MINUTE in values:
            if Component.HOUR_AND_MINUTE in values:
                combined = values[Component.HOUR_AND_MINUTE]
                hour = combined / 100
                minute = combined - (hour * 100)
                second = 0
                nano = 0
            else:
                hour = values[Component.HOUR]
                minute = values[Component.MINUTE]
                second = values.get(Component.SECOND, 0)
                nano = values.get(Component.NANO, 0)

                if hour <= 12 and values.get(Component.AM_PM, cls.AM) == cls.PM:
                    hour += 12

            try:
                time = datetime.time(hour, minute, second, microsecond=(nano / 1000))
            except ValueError:
                return None  # not a valid time

        if Component.OFFSET in values:
            timezone = pytz.FixedOffset(values[Component.OFFSET] / 60)

        if date is not None and time is not None:
            return timezone.localize(datetime.datetime.combine(date, time))
        elif date is not None:
            return date
        elif time is not None:
            return time
        else:
            return None

    @staticmethod
    def _year_from_2digits(short_year, current_year):
        """
        Converts a relative 2-digit year to an absolute 4-digit year
        :param short_year: the relative year
        :param current_year: the current year
        :return: the absolute year
        """
        if short_year < 100:
            short_year += current_year - (current_year % 100)
            if abs(short_year - current_year) >= 50:
                if short_year < current_year:
                    return short_year + 100
                else:
                    return short_year - 100
        return short_year

    class Result(object):
        """
        A complete parse result
        """
        def __init__(self, value, start, end):
            self.value = value
            self.start = start
            self.end = end


def load_month_aliases(filename):
    alias_file = pkg_resources.resource_string(__name__, filename).decode('UTF-8', 'replace')
    aliases = {}
    month = 1
    for line in alias_file.split('\n'):
        for alias in line.split(','):
            aliases[alias] = month
        month += 1
    return aliases


MONTHS_BY_ALIAS = load_month_aliases('month.aliases')
