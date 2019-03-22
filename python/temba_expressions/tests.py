import codecs
import json
import pytz
import regex
import sys
import unittest

from datetime import datetime, date, time
from decimal import Decimal
from six.moves import filter
from time import clock
from . import conversions, EvaluationError
from .dates import DateParser, DateStyle
from .evaluator import Evaluator, EvaluationContext, EvaluationStrategy, DEFAULT_FUNCTION_MANAGER
from .functions import FunctionManager, excel, custom
from .utils import urlquote, decimal_pow, tokenize, format_json_date, parse_json_date


class DateParserTest(unittest.TestCase):

    def test_auto(self):
        tz = pytz.timezone('Africa/Kigali')
        parser = DateParser(date(2015, 8, 12), tz, DateStyle.DAY_FIRST)

        tests = (
            (None, None),
            ("", None),
            ("x", None),
            ("12", None),
            ("31-02-99", None),
            ("1/2/34", date(2034, 2, 1)),
            ("1-2-34", date(2034, 2, 1)),
            ("01 02 34", date(2034, 2, 1)),
            ("1 Feb 34", date(2034, 2, 1)),
            ("1. 2 '34", date(2034, 2, 1)),
            ("my birthday is on 01/02/34", date(2034, 2, 1)),
            ("1st february 2034", date(2034, 2, 1)),
            ("1er février 2034", date(2034, 2, 1)),
            ("2/25-70", date(1970, 2, 25)),  # date style should be ignored when it doesn't make sense
            ("1 feb", date(2015, 2, 1)),  # year can be omitted
            ("Feb 1st", date(2015, 2, 1)),
            ("1 feb 9999999", date(2015, 2, 1)),  # ignore invalid values
            ("1/2/34 14:55", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("1-2-34 2:55PM", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("01 02 34 1455", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("1 Feb 34 02:55 PM", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("1. 2 '34 02:55pm", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("1st february 2034 14.55", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),
            ("1er février 2034 1455h", tz.localize(datetime(2034, 2, 1, 14, 55, 0, 0))),

            # these results differ from Java version because python datetime only support microsecond accuracy
            ("2034-02-01T14:55:41.060422", tz.localize(datetime(2034, 2, 1, 14, 55, 41, 60422))),
            ("2034-02-01T14:55:41.060Z", datetime(2034, 2, 1, 14, 55, 41, 60000, pytz.UTC)),
            ("2034-02-01T14:55:41.060422Z", datetime(2034, 2, 1, 14, 55, 41, 60422, pytz.UTC)),
            ("2034-02-01T14:55:41.060422123Z", datetime(2034, 2, 1, 14, 55, 41, 60422, pytz.UTC)),

            # with timezone (we retain the timezone)
            ("2034-02-01T14:55:41.060422123+02:00", datetime(2034, 2, 1, 14, 55, 41, 60422, pytz.FixedOffset(120)))
        )
        for test in tests:
            parsed = parser.auto(test[0])
            self.assertEqual(parsed, test[1], "error parsing: %s  %s != %s" % (test[0], parsed, test[1]))

    def test_time(self):
        tz = pytz.timezone('Africa/Kigali')
        parser = DateParser(date(2015, 8, 12), tz, DateStyle.DAY_FIRST)

        tests = (
            (None, None),
            ("", None),
            ("x", None),
            ("12", None),
            ("2:55", time(2, 55, 0)),
            ("2:55 AM", time(2, 55, 0)),
            ("14:55", time(14, 55, 0)),
            ("2:55PM", time(14, 55, 0)),
            ("1455", time(14, 55, 0)),
            ("02:55 PM", time(14, 55, 0)),
            ("02:55pm", time(14, 55, 0)),
            ("14.55", time(14, 55, 0)),
            ("1455h", time(14, 55, 0)),
            ("14:55:30", time(14, 55, 30)),
            ("14:55.30PM", time(14, 55, 30)),
            ("12:30 AM", time(0, 30, 0)),
            ("12:30 PM", time(12, 30, 0)),
            ("11:30 AM", time(11, 30, 0)),
            ("11:30 PM", time(23, 30, 0)),
        )
        for test in tests:
            self.assertEqual(parser.time(test[0]), test[1], "Parser error for %s" % test[0])

    def test_year_from_2digits(self):
        self.assertEqual(DateParser._year_from_2digits(1, 2015), 2001)
        self.assertEqual(DateParser._year_from_2digits(64, 2015), 2064)
        self.assertEqual(DateParser._year_from_2digits(65, 2015), 1965)
        self.assertEqual(DateParser._year_from_2digits(99, 2015), 1999)

        self.assertEqual(DateParser._year_from_2digits(1, 1990), 2001)
        self.assertEqual(DateParser._year_from_2digits(40, 1990), 2040)
        self.assertEqual(DateParser._year_from_2digits(41, 1990), 1941)
        self.assertEqual(DateParser._year_from_2digits(99, 1990), 1999)


class ConversionsTest(unittest.TestCase):

    def setUp(self):
        self.tz = pytz.timezone("Africa/Kigali")
        self.context = EvaluationContext({}, timezone=self.tz)

    def test_to_boolean(self):
        self.assertEqual(conversions.to_boolean(True, self.context), True)
        self.assertEqual(conversions.to_boolean(False, self.context), False)

        self.assertEqual(conversions.to_boolean(1, self.context), True)
        self.assertEqual(conversions.to_boolean(0, self.context), False)
        self.assertEqual(conversions.to_boolean(-1, self.context), True)

        self.assertEqual(conversions.to_boolean(Decimal(0.5), self.context), True)
        self.assertEqual(conversions.to_boolean(Decimal(0.0), self.context), False)
        self.assertEqual(conversions.to_boolean(Decimal(-0.5), self.context), True)

        self.assertEqual(conversions.to_boolean("trUE", self.context), True)
        self.assertEqual(conversions.to_boolean("faLSE", self.context), False)
        self.assertEqual(conversions.to_boolean("faLSE", self.context), False)

        self.assertEqual(conversions.to_boolean(date(2012, 3, 4), self.context), True)
        self.assertEqual(conversions.to_boolean(time(12, 34, 0), self.context), True)
        self.assertEqual(conversions.to_boolean(datetime(2012, 3, 4, 5, 6, 7, 8, pytz.UTC), self.context), True)

        self.assertRaises(EvaluationError, conversions.to_boolean, 'x', self.context)

    def test_to_integer(self):
        self.assertEqual(conversions.to_integer(True, self.context), 1)
        self.assertEqual(conversions.to_integer(False, self.context), 0)

        self.assertEqual(conversions.to_integer(1234567890, self.context), 1234567890)

        self.assertEqual(conversions.to_integer(Decimal("1234"), self.context), 1234)
        self.assertEqual(conversions.to_integer(Decimal("1234.5678"), self.context), 1235)
        self.assertEqual(conversions.to_integer(Decimal("0.001"), self.context), 0)

        self.assertEqual(conversions.to_integer("1234", self.context), 1234)

        self.assertRaises(EvaluationError, conversions.to_integer, 'x', self.context)

    def test_to_decimal(self):
        self.assertEqual(conversions.to_decimal(True, self.context), Decimal(1))
        self.assertEqual(conversions.to_decimal(False, self.context), Decimal(0))

        self.assertEqual(conversions.to_decimal(123, self.context), Decimal(123))
        self.assertEqual(conversions.to_decimal(-123, self.context), Decimal(-123))

        self.assertEqual(conversions.to_decimal(Decimal("1234.5678"), self.context), Decimal("1234.5678"))

        self.assertEqual(conversions.to_decimal("1234.5678", self.context), Decimal("1234.5678"))

        self.assertRaises(EvaluationError, conversions.to_decimal, 'x', self.context)

    def test_to_string(self):
        self.assertEqual(conversions.to_string(True, self.context), "TRUE")
        self.assertEqual(conversions.to_string(False, self.context), "FALSE")

        self.assertEqual(conversions.to_string(-1, self.context), "-1")
        self.assertEqual(conversions.to_string(1234567890, self.context), "1234567890")

        self.assertEqual(conversions.to_string(Decimal("2.0"), self.context), "2")
        self.assertEqual(conversions.to_string(Decimal("1234000"), self.context), "1234000")
        self.assertEqual(conversions.to_string(Decimal("0.4440000"), self.context), "0.444")
        self.assertEqual(conversions.to_string(Decimal("1234567890.50"), self.context), "1234567890.5")
        self.assertEqual(conversions.to_string(Decimal("33.333333333333"), self.context), "33.333333333333")
        self.assertEqual(conversions.to_string(Decimal("66.666666666666"), self.context), "66.666666666666")

        self.assertEqual(conversions.to_string("hello", self.context), "hello")

        self.assertEqual(conversions.to_string(date(2012, 3, 4), self.context), "04-03-2012")
        self.assertEqual(conversions.to_string(time(12, 34, 0), self.context), "12:34")
        self.assertEqual(conversions.to_string(self.tz.localize(datetime(2012, 3, 4, 5, 6, 7, 8)), self.context), "2012-03-04T05:06:07.000008+02:00")

        self.context.date_style = DateStyle.MONTH_FIRST

        self.assertEqual(conversions.to_string(date(2012, 3, 4), self.context), "03-04-2012")
        self.assertEqual(conversions.to_string(self.tz.localize(datetime(2012, 3, 4, 5, 6, 7, 8)), self.context), "2012-03-04T05:06:07.000008+02:00")

    def test_to_date(self):
        self.assertEqual(conversions.to_date("14th Aug 2015", self.context), date(2015, 8, 14))
        self.assertEqual(conversions.to_date("14/8/15", self.context), date(2015, 8, 14))

        self.assertEqual(conversions.to_date(date(2015, 8, 14), self.context), date(2015, 8, 14))

        self.assertEqual(conversions.to_date(self.tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)), self.context), date(2015, 8, 14))

        self.context.date_style = DateStyle.MONTH_FIRST

        self.assertEqual(conversions.to_date("12/8/15", self.context), date(2015, 12, 8))
        self.assertEqual(conversions.to_date("14/8/15", self.context), date(2015, 8, 14))  # ignored because doesn't make sense

    def test_to_datetime(self):
        tz = pytz.timezone("Africa/Kigali")

        self.assertEqual(conversions.to_datetime("14th Aug 2015 09:12", self.context), tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)))

        self.assertEqual(conversions.to_datetime("2034-02-01T14:55:41.123456+03:00", self.context),
                         tz.localize(datetime(2034, 2, 1, 13, 55, 41, 123456)))

        self.assertEqual(conversions.to_datetime(date(2015, 8, 14), self.context), tz.localize(datetime(2015, 8, 14, 0, 0, 0, 0)))

        self.assertEqual(conversions.to_datetime(tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)), self.context), tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)))

    def test_to_time(self):
        self.assertEqual(conversions.to_time("9:12", self.context), time(9, 12, 0))
        self.assertEqual(conversions.to_time("0912", self.context), time(9, 12, 0))
        self.assertEqual(conversions.to_time("09.12am", self.context), time(9, 12, 0))

        self.assertEqual(conversions.to_time(time(9, 12, 0), self.context), time(9, 12, 0))

        self.assertEqual(conversions.to_time(self.tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)), self.context), time(9, 12, 0))

    def test_to_repr(self):
        self.assertEqual(conversions.to_repr(False, self.context), 'FALSE')
        self.assertEqual(conversions.to_repr(True, self.context), 'TRUE')

        self.assertEqual(conversions.to_repr(Decimal("123.45"), self.context), '123.45')

        self.assertEqual(conversions.to_repr('x"y', self.context), '"x""y"')

        self.assertEqual(conversions.to_repr(time(9, 12, 0), self.context), '"09:12"')

        self.assertEqual(conversions.to_repr(self.tz.localize(datetime(2015, 8, 14, 9, 12, 0, 0)), self.context), '"2015-08-14T09:12:00+02:00"')


class EvaluationContextTest(unittest.TestCase):

    def test_resolve_variable(self):
        contact = {
            "*": "Bob",
            "name": "Bob",
            "age": 33,
            "join_date_1": "28-08-2015 13:06",
            "isnull": None,
            "isbool": True,
            "isfloat": float(1.5),
            "isint": 9223372036854775807,
            "isdict": {'a': 123}
        }

        context = EvaluationContext()
        context.put_variable("foo", 123)
        context.put_variable("contact", contact)

        self.assertEqual(context.resolve_variable("foo"), 123)
        self.assertEqual(context.resolve_variable("FOO"), 123)
        self.assertEqual(context.resolve_variable("contact"), "Bob")
        self.assertEqual(context.resolve_variable("Contact.name"), "Bob")
        self.assertEqual(context.resolve_variable("contact.AGE"), 33)
        self.assertEqual(context.resolve_variable("contact.join_date_1"), "28-08-2015 13:06")
        self.assertEqual(context.resolve_variable("contact.isnull"), "")
        self.assertEqual(context.resolve_variable("contact.isbool"), True)
        self.assertTrue(type(context.resolve_variable("contact.isbool")) == bool)
        self.assertEqual(context.resolve_variable("contact.isfloat"), Decimal('1.5'))
        self.assertEqual(context.resolve_variable("contact.isint"), Decimal('9223372036854775807'))
        self.assertEqual(context.resolve_variable("contact.isdict"), '{"a":123}')

        # no such item
        self.assertRaises(EvaluationError, context.resolve_variable, "bar")

        context.put_variable("zed", ['x', 4])

        # container which is not a dict
        self.assertRaises(EvaluationError, context.resolve_variable, "zed.something")


class EvaluatorTest(unittest.TestCase):

    def setUp(self):
        self.evaluator = Evaluator()

    def test_evaluate_template(self):
        output, errors = self.evaluator.evaluate_template("Answer is @(2 + 3)", EvaluationContext())
        self.assertEqual(output, "Answer is 5")
        self.assertEqual(errors, [])

        # with unbalanced expression
        output, errors = self.evaluator.evaluate_template("Answer is @(2 + 3", EvaluationContext())
        self.assertEqual(output, "Answer is @(2 + 3")
        self.assertEqual(errors, [])

        # with illegal char
        output, errors = self.evaluator.evaluate_template("@('x')", EvaluationContext())
        self.assertEqual(output, "@('x')")
        self.assertEqual(errors, ["Expression error at: '"])

    def test_evaluate_template_with_resolve_available_strategy(self):
        context = EvaluationContext()
        context.put_variable("foo", 5)
        context.put_variable("bar", "x")

        output, errors = self.evaluator.evaluate_template("@(1 + 2)", context, False, EvaluationStrategy.RESOLVE_AVAILABLE)
        self.assertEqual(output, "3")

        output, errors = self.evaluator.evaluate_template("Hi @contact.name", context, False, EvaluationStrategy.RESOLVE_AVAILABLE)
        self.assertEqual(output, "Hi @contact.name")

        output, errors = self.evaluator.evaluate_template("@(foo + contact.name + bar)", context, False, EvaluationStrategy.RESOLVE_AVAILABLE)
        self.assertEqual(output, "@(5+contact.name+\"x\")")

    def test_evaluate_expression(self):
        context = EvaluationContext()
        context.put_variable("foo", 5)
        context.put_variable("bar", 3)
        context.put_variable("now", "17-02-2017 15:10")
        context.put_variable("today", "17-02-2017")

        self.assertEqual(self.evaluator.evaluate_expression("true", context), True)
        self.assertEqual(self.evaluator.evaluate_expression("FALSE", context), False)

        self.assertEqual(self.evaluator.evaluate_expression("10", context), Decimal(10))
        self.assertEqual(self.evaluator.evaluate_expression("1234.5678", context), Decimal("1234.5678"))

        self.assertEqual(self.evaluator.evaluate_expression("\"\"", context), "")
        self.assertEqual(self.evaluator.evaluate_expression("\"سلام\"", context), "سلام")
        self.assertEqual(self.evaluator.evaluate_expression("\"He said \"\"hi\"\" \"", context), "He said \"hi\" ")

        self.assertEqual(self.evaluator.evaluate_expression("-10", context), Decimal(-10))
        self.assertEqual(self.evaluator.evaluate_expression("1 + 2", context), Decimal(3))
        self.assertEqual(self.evaluator.evaluate_expression("1.3 + 2.2", context), Decimal("3.5"))
        self.assertEqual(self.evaluator.evaluate_expression("1.3 - 2.2", context), Decimal("-0.9"))
        self.assertEqual(self.evaluator.evaluate_expression("4 * 2", context), Decimal(8))
        self.assertEqual(self.evaluator.evaluate_expression("4 / 2", context), Decimal("2.0000000000"))
        self.assertEqual(self.evaluator.evaluate_expression("4 ^ 2", context), Decimal(16))
        self.assertEqual(self.evaluator.evaluate_expression("4 ^ 0.5", context), Decimal(2))
        self.assertEqual(self.evaluator.evaluate_expression("4 ^ -1", context), Decimal("0.25"))

        self.assertEqual(self.evaluator.evaluate_expression("\"foo\" & \"bar\"", context), "foobar")
        self.assertEqual(self.evaluator.evaluate_expression("2 & 3 & 4", context), "234")

        # check precedence
        self.assertEqual(self.evaluator.evaluate_expression("2 + 3 / 4 - 5 * 6", context), Decimal("-27.2500000000"))
        self.assertEqual(self.evaluator.evaluate_expression("2 & 3 + 4 & 5", context), "275")

        # check associativity
        self.assertEqual(self.evaluator.evaluate_expression("2 - -2 + 7", context), Decimal(11))
        self.assertEqual(self.evaluator.evaluate_expression("2 ^ 3 ^ 4", context), Decimal(4096))

        self.assertEqual(self.evaluator.evaluate_expression("FOO", context), 5)
        self.assertEqual(self.evaluator.evaluate_expression("foo + bar", context), Decimal(8))

        self.assertEqual(self.evaluator.evaluate_expression("len(\"abc\")", context), 3)
        self.assertEqual(self.evaluator.evaluate_expression("SUM(1, 2, 3)", context), Decimal(6))

        self.assertEqual(self.evaluator.evaluate_expression("FIXED(1234.5678)", context), "1,234.57")
        self.assertEqual(self.evaluator.evaluate_expression("FIXED(1234.5678, 1)", context), "1,234.6")
        self.assertEqual(self.evaluator.evaluate_expression("FIXED(1234.5678, 1, True)", context), "1234.6")

        # check comparisons
        self.assertEqual(self.evaluator.evaluate_expression("foo > bar", context), True)
        self.assertEqual(self.evaluator.evaluate_expression("foo < bar", context), False)
        self.assertEqual(self.evaluator.evaluate_expression("now > (today - 1)", context), True)
        self.assertEqual(self.evaluator.evaluate_expression("now < (today - 1)", context), False)

        
class FunctionsTest(unittest.TestCase):
    
    def setUp(self):
        self.tz = pytz.timezone("Africa/Kigali")
        self.now = self.tz.localize(datetime(2015, 8, 14, 10, 38, 30, 123456))
        self.context = EvaluationContext({}, self.tz, DateStyle.DAY_FIRST, self.now)

    def test_invoke_function(self):
        manager = FunctionManager()
        manager.add_library(sys.modules[__name__])
        
        self.assertEqual(manager.invoke_function(self.context, "foo", [12]), 24)
        self.assertEqual(manager.invoke_function(self.context, "FOO", [12]), 24)
        self.assertEqual(manager.invoke_function(self.context, "bar", [12, 5]), 17)
        self.assertEqual(manager.invoke_function(self.context, "bar", [12]), 14)
        self.assertEqual(manager.invoke_function(self.context, "doh", [12, 1, 2, 3]), 36)

        # can't invoke a "private" function
        self.assertRaises(EvaluationError, manager.invoke_function, self.context, "zed", [12])

        # can't pass an unrecognized data type
        self.assertRaises(EvaluationError, manager.invoke_function, self.context, "foo", [self])

    def test_build_listing(self):
        listing = DEFAULT_FUNCTION_MANAGER.build_listing()

        def by_name(name):
            return next(filter(lambda f: f['name'] == name, listing), None)

        # check function with no params
        self.assertEqual(by_name('NOW'), {'name': 'NOW',
                                          'description': "Returns the current date and time",
                                          'params': []})

        # check function with no defaults
        self.assertEqual(by_name('ABS'), {'name': 'ABS',
                                          'description': "Returns the absolute value of a number",
                                          'params': [{'name': 'number', 'optional': False, 'vararg': False}]})

        # check function with defaults
        self.assertEqual(by_name('WORD_COUNT'), {'name': 'WORD_COUNT',
                                                 'description': "Returns the number of words in the given text string",
                                                 'params': [{'name': 'text', 'optional': False, 'vararg': False},
                                                            {'name': 'by_spaces', 'optional': True, 'vararg': False}]})

        # check function with varargs
        self.assertEqual(by_name('SUM'), {'name': 'SUM',
                                          'description': "Returns the sum of all arguments",
                                          'params': [{'name': 'number', 'optional': False, 'vararg': True}]})
    
    def test_excel(self):
        # text functions
        self.assertEqual(excel.char(self.context, 9), '\t')
        self.assertEqual(excel.char(self.context, 10), '\n')
        self.assertEqual(excel.char(self.context, 13), '\r')
        self.assertEqual(excel.char(self.context, 32), ' ')
        self.assertEqual(excel.char(self.context, 65), 'A')

        self.assertEqual(excel.clean(self.context, 'Hello \nwo\trl\rd'), 'Hello world')

        self.assertEqual(excel.code(self.context, '\t'), 9)
        self.assertEqual(excel.code(self.context, '\n'), 10)

        self.assertEqual(excel.concatenate(self.context, 'Hello', 4, '\n'), 'Hello4\n')
        self.assertEqual(excel.concatenate(self.context, 'واحد', ' ', 'إثنان', ' ', 'ثلاثة'), 'واحد إثنان ثلاثة')

        self.assertEqual(excel.fixed(self.context, Decimal('1234.5678')), '1,234.57')  # default is 2 decimal places w/ comma
        self.assertEqual(excel.fixed(self.context, '1234.5678', 1), '1,234.6')
        self.assertEqual(excel.fixed(self.context, '1234.5678', 2), '1,234.57')
        self.assertEqual(excel.fixed(self.context, '1234.5678', 3), '1,234.568')
        self.assertEqual(excel.fixed(self.context, '1234.5678', 4), '1,234.5678')
        self.assertEqual(excel.fixed(self.context, '1234.5678', 0), '1,235')
        self.assertEqual(excel.fixed(self.context, '1234.5678', -1), '1,230')
        self.assertEqual(excel.fixed(self.context, '1234.5678', -2), '1,200')
        self.assertEqual(excel.fixed(self.context, '1234.5678', -3), '1,000')
        self.assertEqual(excel.fixed(self.context, '1234.5678', -4), '0')
        self.assertEqual(excel.fixed(self.context, '1234.5678', 3, True), '1234.568')
        self.assertEqual(excel.fixed(self.context, '1234.5678', -2, True), '1200')

        self.assertEqual(excel.left(self.context, 'abcdef', 0), '')
        self.assertEqual(excel.left(self.context, 'abcdef', 2), 'ab')
        self.assertEqual(excel.left(self.context, 'واحد', 2), 'وا')
        self.assertRaises(ValueError, excel.left, self.context, 'abcd', -1)  # exception for negative char count

        self.assertEqual(excel._len(self.context, ''), 0)
        self.assertEqual(excel._len(self.context, 'abc'), 3)
        self.assertEqual(excel._len(self.context, 'واحد'), 4)

        self.assertEqual(excel.lower(self.context, 'aBcD'), 'abcd')
        self.assertEqual(excel.lower(self.context, 'A واحد'), 'a واحد')

        self.assertEqual(excel.proper(self.context, 'first-second third'), 'First-Second Third')
        self.assertEqual(excel.proper(self.context, 'واحد abc ثلاثة'), 'واحد Abc ثلاثة')

        self.assertEqual(excel.rept(self.context, 'abc', 3), 'abcabcabc')
        self.assertEqual(excel.rept(self.context, 'واحد', 3), 'واحدواحدواحد')

        self.assertEqual(excel.right(self.context, 'abcdef', 0), '')
        self.assertEqual(excel.right(self.context, 'abcdef', 2), 'ef')
        self.assertEqual(excel.right(self.context, 'واحد', 2), 'حد')
        self.assertRaises(ValueError, excel.right, self.context, 'abcd', -1)  # exception for negative char count

        self.assertEqual(excel.substitute(self.context, 'hello Hello world', 'hello', 'bonjour'), 'bonjour Hello world')  # case-sensitive
        self.assertEqual(excel.substitute(self.context, 'hello hello world', 'hello', 'bonjour'), 'bonjour bonjour world')  # all instances
        self.assertEqual(excel.substitute(self.context, 'hello hello world', 'hello', 'bonjour', 2), 'hello bonjour world')  # specific instance
        self.assertEqual(excel.substitute(self.context, 'واحد إثنان ثلاثة', 'واحد', 'إثنان'), 'إثنان إثنان ثلاثة')

        self.assertEqual(excel.unichar(self.context, 65), 'A')
        self.assertEqual(excel.unichar(self.context, 1575), 'ا')

        self.assertEqual(excel._unicode(self.context, '\t'), 9)
        self.assertEqual(excel._unicode(self.context, '\u04d2'), 1234)
        self.assertEqual(excel._unicode(self.context, 'ا'), 1575)
        self.assertRaises(ValueError, excel._unicode, self.context, '')  # exception for empty string

        self.assertEqual(excel.upper(self.context, 'aBcD'), 'ABCD')
        self.assertEqual(excel.upper(self.context, 'a واحد'), 'A واحد')

        # date functions
        self.assertEqual(excel.date(self.context, 2012, "3", Decimal(2.0)), date(2012, 3, 2))

        self.assertEqual(excel.datedif(self.context, "28/5/81", "23-11-15", "y"), 34)
        self.assertEqual(excel.datedif(self.context, date(2011, 1, 1), date(2012, 12, 31), "y"), 1)
        self.assertEqual(excel.datedif(self.context, "20/9/14", "23/11/15", "m"), 14)
        self.assertEqual(excel.datedif(self.context, "1/6/2001", "15/8/2002", "d"), 440)
        self.assertEqual(excel.datedif(self.context, "1/6/2001", "15/8/2002", "YD"), 75)
        self.assertEqual(excel.datedif(self.context, "1/6/2001", "15/8/2002", "YM"), 2)
        self.assertEqual(excel.datedif(self.context, "1/6/2001", "15/8/2002", "mD"), 14)
        self.assertEqual(excel.datedif(self.context, "16/6/2001", "15/8/2002", "mD"), 30)

        self.assertEqual(excel.datevalue(self.context, "2-3-13"), date(2013, 3, 2))

        self.assertEqual(excel.day(self.context, date(2012, 3, 2)), 2)

        self.assertEqual(excel.days(self.context, "15/3/11", "1/2/11"), 42)
        self.assertEqual(excel.days(self.context, self.tz.localize(datetime(2011, 12, 31, 10, 38, 30, 123456)), date(2011, 1, 1)), 364)

        self.assertEqual(excel.edate(self.context, date(2013, 3, 2), 1), date(2013, 4, 2))
        self.assertEqual(excel.edate(self.context, '01-02-2014', -2), date(2013, 12, 1))

        self.assertEqual(excel.hour(self.context, '01-02-2014 03:55'), 3)

        self.assertEqual(excel.minute(self.context, '01-02-2014 03:55'), 55)

        self.assertEqual(excel.now(self.context), self.tz.localize(datetime(2015, 8, 14, 10, 38, 30, 123456)))

        self.assertEqual(excel.second(self.context, '01-02-2014 03:55:30'), 30)

        self.assertEqual(excel.time(self.context, 1, 30, 15), time(1, 30, 15))

        self.assertEqual(excel.timevalue(self.context, '1:30:15'), time(1, 30, 15))

        self.assertEqual(excel.today(self.context), date(2015, 8, 14))

        self.assertEqual(excel.weekday(self.context, date(2015, 8, 15)), 7)  # Sat = 7
        self.assertEqual(excel.weekday(self.context, "16th Aug 2015"), 1)  # Sun = 1

        self.assertEqual(excel.year(self.context, date(2012, 3, 2)), 2012)

        # math functions
        self.assertEqual(excel.average(self.context, 1), 1)
        self.assertEqual(excel.average(self.context, 1, "2", 3), 2)
        self.assertEqual(excel.average(self.context, -1, -2), Decimal('-1.5'))

        self.assertRaises(ValueError, excel.average, self.context)  # no args

        self.assertEqual(excel._abs(self.context, 1), 1)
        self.assertEqual(excel._abs(self.context, -1), 1)

        self.assertEqual(excel.exp(self.context, 1), Decimal('2.718281828459045090795598298427648842334747314453125'))
        self.assertEqual(excel.exp(self.context, '2.0'), Decimal('7.38905609893064951876340273884125053882598876953125'))

        self.assertEqual(excel._int(self.context, '8.9'), 8)
        self.assertEqual(excel._int(self.context, '-8.9'), -9)
        self.assertEqual(excel._int(self.context, '1234.5678'), 1234)

        self.assertEqual(excel._max(self.context, 1), 1)
        self.assertEqual(excel._max(self.context, 1, 3, 2, -5), 3)
        self.assertEqual(excel._max(self.context, -2, -5), -2)

        self.assertRaises(ValueError, excel._max, self.context)  # no args

        self.assertEqual(excel._min(self.context, 1), 1)
        self.assertEqual(excel._min(self.context, -1, -3, -2, 5), -3)
        self.assertEqual(excel._min(self.context, -2, -5), -5)

        self.assertRaises(ValueError, excel._min, self.context)  # no args

        self.assertEqual(excel.mod(self.context, Decimal(3), 2), 1)
        self.assertEqual(excel.mod(self.context, Decimal(-3), Decimal(2)), 1)
        self.assertEqual(excel.mod(self.context, Decimal(3), Decimal(-2)), -1)
        self.assertEqual(excel.mod(self.context, Decimal(-3), Decimal(-2)), -1)

        self.assertEqual(excel._power(self.context, '4', '2'), Decimal('16'))
        self.assertEqual(excel._power(self.context, '4', '0.5'), Decimal('2'))

        self.assertEqual(excel._round(self.context, '2.15', 1), Decimal('2.2'))
        self.assertEqual(excel._round(self.context, '2.149', 1), Decimal('2.1'))
        self.assertEqual(excel._round(self.context, '-1.475', 2), Decimal('-1.48'))
        self.assertEqual(excel._round(self.context, '21.5', '-1'), Decimal(20))
        self.assertEqual(excel._round(self.context, '626.3', '-3'), Decimal(1000))
        self.assertEqual(excel._round(self.context, '1.98', '-1'), Decimal(0))
        self.assertEqual(excel._round(self.context, '-50.55', '-2'), Decimal(-100))

        self.assertEqual(excel.rounddown(self.context, '3.2', 0), Decimal('3'))
        self.assertEqual(excel.rounddown(self.context, '76.9', 0), Decimal('76'))
        self.assertEqual(excel.rounddown(self.context, '3.14159', 3), Decimal('3.141'))
        self.assertEqual(excel.rounddown(self.context, '-3.14159', '1'), Decimal('-3.1'))
        self.assertEqual(excel.rounddown(self.context, '31415.92654', '-2'), Decimal(31400))
        self.assertEqual(excel.rounddown(self.context, '31499', '-2'), Decimal(31400))

        self.assertEqual(excel.roundup(self.context, '3.2', 0), Decimal('4'))
        self.assertEqual(excel.roundup(self.context, '76.9', 0), Decimal('77'))
        self.assertEqual(excel.roundup(self.context, '3.14159', 3), Decimal('3.142'))
        self.assertEqual(excel.roundup(self.context, '-3.14159', '1'), Decimal('-3.2'))
        self.assertEqual(excel.roundup(self.context, '31415.92654', '-2'), Decimal(31500))
        self.assertEqual(excel.roundup(self.context, '31499', '-2'), Decimal(31500))

        self.assertEqual(excel._sum(self.context, 1), 1)
        self.assertEqual(excel._sum(self.context, 1, 2, 3), 6)

        self.assertRaises(ValueError, excel._sum, self.context)  # no args

        self.assertEqual(excel.trunc(self.context, '8.9'), 8)
        self.assertEqual(excel.trunc(self.context, '-8.9'), -8)
        self.assertEqual(excel.trunc(self.context, '0.45'), 0)
        self.assertEqual(excel.trunc(self.context, '1234.5678'), 1234)

        # logical functions
        self.assertEqual(excel._and(self.context, False), False)
        self.assertEqual(excel._and(self.context, True), True)
        self.assertEqual(excel._and(self.context, 1, True, "true"), True)
        self.assertEqual(excel._and(self.context, 1, True, "true", 0), False)

        self.assertEqual(excel.false(), False)

        self.assertEqual(excel._if(self.context, True), 0)
        self.assertEqual(excel._if(self.context, True, 'x', 'y'), 'x')
        self.assertEqual(excel._if(self.context, 'true', 'x', 'y'), 'x')
        self.assertEqual(excel._if(self.context, False), False)
        self.assertEqual(excel._if(self.context, False, 'x', 'y'), 'y')
        self.assertEqual(excel._if(self.context, 0, 'x', 'y'), 'y')

        self.assertEqual(excel._or(self.context, False), False)
        self.assertEqual(excel._or(self.context, True), True)
        self.assertEqual(excel._or(self.context, 1, False, "false"), True)
        self.assertEqual(excel._or(self.context, 0, True, "false"), True)

        self.assertEqual(excel.true(), True)

    def test_custom(self):
        self.assertEqual(custom.field(self.context, '15+M+Seattle', 1, '+'), '15')
        self.assertEqual(custom.field(self.context, '15 M Seattle', 1), '15')
        self.assertEqual(custom.field(self.context, '15+M+Seattle', 2, '+'), 'M')
        self.assertEqual(custom.field(self.context, '15+M+Seattle', 3, '+'), 'Seattle')
        self.assertEqual(custom.field(self.context, '15+M+Seattle', 4, '+'), '')
        self.assertEqual(custom.field(self.context, '15    M  Seattle', 2), 'M')
        self.assertEqual(custom.field(self.context, ' واحد إثنان-ثلاثة ', 1), 'واحد')
        self.assertRaises(ValueError, custom.field, self.context, '15+M+Seattle', 0)

        self.assertEqual('', custom.first_word(self.context, '  '))
        self.assertEqual('abc', custom.first_word(self.context, ' abc '))
        self.assertEqual('abc', custom.first_word(self.context, ' abc '))
        self.assertEqual('abc', custom.first_word(self.context, ' abc def ghi'))
        self.assertEqual('واحد', custom.first_word(self.context, ' واحد '))
        self.assertEqual('واحد', custom.first_word(self.context, ' واحد إثنان ثلاثة '))

        self.assertEqual('25%', custom.percent(self.context, '0.25321'))
        self.assertEqual('33%', custom.percent(self.context, Decimal('0.33')))

        self.assertEqual('1 2 3 4 , 5 6 7 8 , 9 0 1 2 , 3 4 5 6', custom.read_digits(self.context, '1234567890123456'))  # credit card
        self.assertEqual('1 2 3 , 4 5 6 , 7 8 9 , 0 1 2', custom.read_digits(self.context, '+123456789012'))  # phone number
        self.assertEqual('1 2 3 , 4 5 6', custom.read_digits(self.context, '123456'))  # triplets
        self.assertEqual('1 2 3 , 4 5 , 6 7 8 9', custom.read_digits(self.context, '123456789'))  # soc security
        self.assertEqual('1,2,3,4,5', custom.read_digits(self.context, '12345'))  # regular number, street address, etc
        self.assertEqual('1,2,3', custom.read_digits(self.context, '123'))  # regular number, street address, etc
        self.assertEqual('', custom.read_digits(self.context, ''))  # empty

        self.assertEqual('', custom.remove_first_word(self.context, 'abc'))
        self.assertEqual('', custom.remove_first_word(self.context, ' abc '))
        self.assertEqual('def-ghi ', custom.remove_first_word(self.context, ' abc def-ghi '))  # should preserve remainder of text
        self.assertEqual('', custom.remove_first_word(self.context, ' واحد '))
        self.assertEqual('إثنان ثلاثة ', custom.remove_first_word(self.context, ' واحد إثنان ثلاثة '))

        self.assertEqual('abc', custom.word(self.context, ' abc def ghi', 1))
        self.assertEqual('ghi', custom.word(self.context, 'abc-def  ghi  jkl', 3))
        self.assertEqual('jkl', custom.word(self.context, 'abc-def  ghi  jkl', 3, True))
        self.assertEqual('jkl', custom.word(self.context, 'abc-def  ghi  jkl', '3', 'TRUE'))  # string args only
        self.assertEqual('jkl', custom.word(self.context, 'abc-def  ghi  jkl', -1))  # negative index
        self.assertEqual('', custom.word(self.context, ' abc def   ghi', 6))  # out of range
        self.assertEqual('', custom.word(self.context, '', 1))
        self.assertEqual('واحد', custom.word(self.context, ' واحد إثنان ثلاثة ', 1))
        self.assertEqual('ثلاثة', custom.word(self.context, ' واحد إثنان ثلاثة ', -1))
        self.assertRaises(ValueError, custom.word, self.context, '', 0)  # number cannot be zero

        self.assertEqual(0, custom.word_count(self.context, ''))
        self.assertEqual(4, custom.word_count(self.context, ' abc-def  ghi  jkl'))
        self.assertEqual(4, custom.word_count(self.context, ' abc-def  ghi  jkl', False))
        self.assertEqual(3, custom.word_count(self.context, ' abc-def  ghi  jkl', True))
        self.assertEqual(3, custom.word_count(self.context, ' واحد إثنان-ثلاثة ', False))
        self.assertEqual(2, custom.word_count(self.context, ' واحد إثنان-ثلاثة ', True))

        self.assertEqual('abc def', custom.word_slice(self.context, ' abc  def ghi-jkl ', 1, 3))
        self.assertEqual('ghi jkl', custom.word_slice(self.context, ' abc  def ghi-jkl ', 3, 0))
        self.assertEqual('ghi-jkl', custom.word_slice(self.context, ' abc  def ghi-jkl ', 3, 0, True))
        self.assertEqual('ghi jkl', custom.word_slice(self.context, ' abc  def ghi-jkl ', '3', '0', 'false'))  # string args only
        self.assertEqual('ghi jkl', custom.word_slice(self.context, ' abc  def ghi-jkl ', 3))
        self.assertEqual('def ghi', custom.word_slice(self.context, ' abc  def ghi-jkl ', 2, -1))
        self.assertEqual('jkl', custom.word_slice(self.context, ' abc  def ghi-jkl ', -1))
        self.assertEqual('def', custom.word_slice(self.context, ' abc  def ghi-jkl ', 2, -1, True))
        self.assertEqual('واحد إثنان', custom.word_slice(self.context, ' واحد إثنان ثلاثة ', 1, 3))
        self.assertRaises(ValueError, custom.word_slice, self.context, ' abc  def ghi-jkl ', 0)  # start can't be zero

        self.assertEqual("01-02-2034 16:55", custom.format_date(self.context, "2034-02-01T14:55:41.060422123Z"))
        self.assertEqual("01-02-2034 16:55", custom.format_date(self.context, "01-02-2034 16:55"))
        self.assertRaises(EvaluationError, custom.format_date, self.context, 'not date')

        self.assertEqual("Kimihurura", custom.format_location(self.context, "Rwanda > Kigali > Kimihurura"))
        self.assertEqual("Kigali", custom.format_location(self.context, "Rwanda > Kigali"))
        self.assertEqual("Rwanda", custom.format_location(self.context, "Rwanda"))

        self.assertEqual("Isaac Newton", custom.regex_group(self.context, "Isaac Newton", '(\w+) (\w+)', 0))
        self.assertEqual("Isaac", custom.regex_group(self.context, "Isaac Newton", '(\w+) (\w+)', 1))
        self.assertEqual("Newton", custom.regex_group(self.context, "Isaac Newton", '(\w+) (\w+)', "2"))
        self.assertRaises(ValueError, custom.regex_group, self.context, "Isaac Newton", '(\w+) (\w+)', 5)


class TemplateTest(unittest.TestCase):

    def test_templates(self):
        evaluator = Evaluator(allowed_top_levels=("channel", "contact", "date", "extra", "flow", "step"))

        with codecs.open('test_files/template_tests.json', 'r', 'utf-8') as tests_file:
            tests_json = json_strip_comments(tests_file.read())
            tests_json = json.loads(tests_json, parse_float=Decimal)
            tests = []
            for test_json in tests_json:
                tests.append(TemplateTest.TestDefinition(test_json))

        failures = []
        start = int(round(clock() * 1000))

        for test in tests:
            try:
                if not test.run(evaluator):
                    failures.append(test)
            except Exception as e:
                print("Exception whilst evaluating: %s" % test.template)
                raise e

        duration = int(round(clock() * 1000)) - start

        print("Completed %d template tests in %dms (failures=%d)" % (len(tests), duration, len(failures)))

        if failures:
            print("Failed tests:")

            for test in failures:
                print("========================================\n")
                print("Template: " + test.template)
                if test.expected_output is not None:
                    print("Expected output: " + test.expected_output)
                else:
                    print("Expected output regex: " + test.expected_output_regex)
                print("Actual output: " + test.actual_output)
                print("Expected errors: " + ', '.join(test.expected_errors))
                print("Actual errors: " + ', '.join(test.actual_errors))

            self.fail("There were failures in the template tests")  # fail unit test if there were any errors

    class TestDefinition(object):

        def __init__(self, json_obj):
            self.template = json_obj['template']
            self.context = EvaluationContext.from_json(json_obj['context'])
            self.url_encode = json_obj['url_encode']
            self.expected_output = json_obj.get('output', None)
            self.expected_output_regex = json_obj.get('output_regex', None)
            self.expected_errors = json_obj['errors']

            self.actual_output = None
            self.actual_errors = None

        def run(self, evaluator):
            output, errors = evaluator.evaluate_template(self.template, self.context, self.url_encode)
            self.actual_output = output
            self.actual_errors = errors

            if self.expected_output is not None:
                if self.expected_output != self.actual_output:
                    return False
            else:
                if not regex.compile(self.expected_output_regex).fullmatch(self.actual_output):
                    return False

            return self.expected_errors == self.actual_errors


class UtilsTest(unittest.TestCase):

    def test_urlquote(self):
        self.assertEqual(urlquote(""), "")
        self.assertEqual(urlquote("?!=Jow&Flow"), "%3F%21%3DJow%26Flow")

    def test_decimal_pow(self):
        self.assertEqual(decimal_pow(Decimal(4), Decimal(2)), Decimal(16))
        self.assertEqual(decimal_pow(Decimal(4), Decimal('0.5')), Decimal(2))
        self.assertEqual(decimal_pow(Decimal(2), Decimal(-2)), Decimal('0.25'))

    def test_tokenize(self):
        self.assertEqual(tokenize(" one "), ["one"])
        self.assertEqual(tokenize("one   two three"), ["one", "two", "three"])
        self.assertEqual(tokenize("one.two.three"), ["one", "two", "three"])
        self.assertEqual(tokenize("O'Grady can't foo_bar"), ["O'Grady", "can't", "foo_bar"])               # single quotes and underscores don't split tokens
        self.assertEqual(tokenize("öne.βήταa.thé"), ["öne", "βήταa", "thé"])                               # non-latin letters allowed in tokens
        self.assertEqual(tokenize("واحد اثنين ثلاثة"), ["واحد", "اثنين", "ثلاثة"])                           # RTL scripts
        self.assertEqual(tokenize("  \t\none(two!*@three "), ["one", "two", "three"])                      # other punctuation ignored
        self.assertEqual(tokenize("spend$£€₠₣₪"), ["spend", "$", "£", "€", "₠", "₣", "₪"])                 # currency symbols treated as individual tokens
        self.assertEqual(tokenize("math+=×÷√∊"), ["math", "+", "=", "×", "÷", "√", "∊"])                   # math symbols treated as individual tokens
        self.assertEqual(tokenize("emoji😄🏥👪👰😟🧟"), ["emoji", "😄", "🏥", "👪", "👰", "😟", "🧟"])  # emojis treated as individual tokens
        self.assertEqual(tokenize("👍🏿 👨🏼"), ["👍", "🏿", "👨", "🏼"])                                # tone modifiers treated as individual tokens
        self.assertEqual(tokenize("ℹ ℹ️"), ["ℹ", "ℹ️"])                                                # variation selectors ignored
        self.assertEqual(tokenize("ยกเลิก sasa"), ["ยกเลิก", "sasa"])                                       # Thai word means Cancelled
        self.assertEqual(tokenize("বাতিল sasa"), ["বাতিল", "sasa"])                                         # Bangla word means Cancel
        self.assertEqual(tokenize("ထွက်သွား sasa"), ["ထွက်သွား", "sasa"])                                    # Burmese word means exit

    def test_parse_json_date(self):
        val = datetime(2014, 10, 3, 1, 41, 12, 790000, pytz.UTC)

        self.assertEqual(parse_json_date(None), None)
        self.assertEqual(parse_json_date("2014-10-03T01:41:12.790Z"), val)

    def test_format_json_date(self):
        val = datetime(2014, 10, 3, 1, 41, 12, 790000, pytz.UTC)

        self.assertEqual(format_json_date(None), None)
        self.assertEqual(format_json_date(val), "2014-10-03T01:41:12.790Z")


#
# Testing utility methods
#

def json_strip_comments(text):
    """
    Strips /* ... */ style comments from JSON
    """
    pattern = regex.compile(r'/\*[^\*]+\*/', regex.DOTALL|regex.MULTILINE|regex.UNICODE)
    match = pattern.search(text)
    while match:
        text = text[:match.start()] + text[match.end():]
        match = pattern.search(text)
    return text


#
# Custom expression functions accessible when this module is loaded into a function manager as a library
#

def foo(ctx, a):
    return a * 2


def _bar(ctx, a, b=2):
    return a + b


def doh(a, *args):
    return len(args) * a


def __zed(a):
    return a / 2
