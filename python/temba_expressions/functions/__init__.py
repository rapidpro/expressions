from __future__ import absolute_import, unicode_literals

import inspect
import six


class FunctionManager(object):

    def __init__(self):
        self._functions = {}

    def add_library(self, library):
        """
        Adds functions from a library module
        :param library: the library module
        :return:
        """
        for fn in six.itervalues(library.__dict__.copy()):
            # ignore imported methods and anything beginning __
            if inspect.isfunction(fn) and inspect.getmodule(fn) == library and not fn.__name__.startswith('__'):
                name = fn.__name__.lower()

                # strip preceding _ chars used to avoid conflicts with Java keywords
                if name.startswith('_'):
                    name = name[1:]

                self._functions[name] = fn

    def get_function(self, name):
        return self._functions.get(name.lower(), None)

    def invoke_function(self, ctx, name, arguments):
        """
        Invokes the given function
        :param ctx: the evaluation context
        :param name: the function name (case insensitive)
        :param arguments: the arguments to be passed to the function
        :return: the function return value
        """
        from temba_expressions import EvaluationError, conversions

        # find function with given name
        func = self.get_function(name)
        if func is None:
            raise EvaluationError("Undefined function: %s" % name)

        args, varargs, defaults = self._get_arg_spec(func)

        call_args = []
        passed_args = list(arguments)

        for arg in args:
            if arg == 'ctx':
                call_args.append(ctx)
            elif passed_args:
                call_args.append(passed_args.pop(0))
            elif arg in defaults:
                call_args.append(defaults[arg])
            else:
                raise EvaluationError("Too few arguments provided for function %s" % name)

        if varargs is not None:
            call_args.extend(passed_args)
            passed_args = []

        # any unused arguments?
        if passed_args:
            raise EvaluationError("Too many arguments provided for function %s" % name)

        try:
            return func(*call_args)
        except Exception as e:
            pretty_args = []
            for arg in arguments:
                if isinstance(arg, six.string_types):
                    pretty = '"%s"' % arg
                else:
                    try:
                        pretty = conversions.to_string(arg, ctx)
                    except EvaluationError:
                        pretty = six.text_type(arg)
                pretty_args.append(pretty)

            raise EvaluationError("Error calling function %s with arguments %s" % (name, ', '.join(pretty_args)), e)

    def build_listing(self):
        """
        Builds a listing of all functions sorted A-Z, with their names and descriptions
        """
        def func_entry(name, func):
            args, varargs, defaults = self._get_arg_spec(func)

            # add regular arguments
            params = [{'name': six.text_type(a), 'optional': a in defaults, 'vararg': False} for a in args if a != 'ctx']

            # add possible variable argument
            if varargs:
                params += [{'name': six.text_type(varargs), 'optional': False, 'vararg': True}]

            return {'name': six.text_type(name.upper()),
                    'description': six.text_type(func.__doc__).strip(),
                    'params': params}

        listing = [func_entry(f_name, f) for f_name, f in six.iteritems(self._functions)]
        return sorted(listing, key=lambda l: l['name'])

    @staticmethod
    def _get_arg_spec(func):
        """
        Gets the argument spec of the given function, returning defaults as a dict of param names to values
        """
        args, varargs, keywords, defaults = inspect.getargspec(func)

        # build a mapping from argument names to their default values, if any:
        if defaults is None:
            defaults = {}
        else:
            defaulted_args = args[-len(defaults):]
            defaults = {name: val for name, val in zip(defaulted_args, defaults)}

        return args, varargs, defaults
