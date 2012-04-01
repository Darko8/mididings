# -*- coding: utf-8 -*-
#
# mididings
#
# Copyright (C) 2008-2012  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import mididings.misc as misc

import inspect
import sys
import collections
import functools
if sys.version_info < (2, 6):
    functools.reduce = reduce

import decorator


def accept(*constraints, **kwargs):
    """
    A decorator that applies type checks and other constraints to the arguments
    of the decorated function.

    Constraints must be given in the order of the function's positional
    arguments, one constraint per argument. If the function accepts variable
    arguments, one additional constraint must be specified, and will be applied
    to each of those arguments.

    If the optional keyword argument with_rest is True, all variable arguments
    are instead combined with the last regular positional argument into a
    single list. This list is then passed to the original function as a single
    argument.
    """
    with_rest = kwargs['with_rest'] if 'with_rest' in kwargs else False

    @decorator.decorator
    def constrain_arguments(f, *args, **kwargs):
        argspec = inspect.getargspec(f)
        arg_names = argspec[0]
        have_varargs = (argspec[1] is not None) and not with_rest

        mod_args = []

        assert ((len(constraints) == len(arg_names) and not have_varargs)
             or (len(constraints) == len(arg_names) + 1 and have_varargs))
        assert len(kwargs) == 0

        for constraint, arg_name, arg in zip(constraints, arg_names, args):
            if with_rest and arg_name == arg_names[-1]:
                # with_rest is True and this is the last argument: combine with varargs
                index = len(arg_names)
                arg = (arg,) + args[index:]
            try:
                a = _apply_constraint(constraint, arg)
                mod_args.append(a)
            except TypeError:
                ex = sys.exc_info()[1]
                message = "invalid type for parameter '%s' of %s(): %s" % (arg_name, f.__name__, str(ex))
                raise TypeError(message)
            except ValueError:
                ex = sys.exc_info()[1]
                message = "invalid value for parameter '%s' of %s(): %s" % (arg_name, f.__name__, str(ex))
                raise ValueError(message)

        if have_varargs:
            index = len(arg_names)
            constraint = constraints[index]

            for arg in args[index:]:
                try:
                    a = _apply_constraint(constraint, arg)
                    mod_args.append(a)
                except TypeError:
                    ex = sys.exc_info()[1]
                    message = "invalid type in varargs of %s(): %s" % (f.__name__, str(ex))
                    raise TypeError(message)
                except ValueError:
                    ex = sys.exc_info()[1]
                    message = "invalid value in varargs of %s(): %s" % (f.__name__, str(ex))
                    raise ValueError(message)

        return f(*mod_args)

    return constrain_arguments


def _apply_constraint(constraint, value):
    if inspect.isclass(constraint):
        # single type, check if instance
        if not isinstance(value, constraint):
            message = "should be %s, got %s" % (constraint.__name__, type(value).__name__)
            raise TypeError(message)
        return value
    elif misc.issequence(constraint) and all(inspect.isclass(c) for c in constraint):
        # multiple types, check if instance
        if not isinstance(value, constraint):
            types = ", ".join(c.__name__ for c in constraint)
            message = "should be one of (%s), got %s" % (types, type(value).__name__)
            raise TypeError(message)
        return value
    elif misc.issequence(constraint):
        # multiple values, check if value is in sequence
        if value not in constraint:
            values = ", ".join(repr(c) for c in constraint)
            message = "should be one of (%s), got %r" % (values, value)
            raise ValueError(message)
        return value
    elif isinstance(constraint, collections.Callable):
        # callable
        return constraint(value)
    else:
        assert False


class sequenceof(object):
    """
    Checks that the argument is a sequence, and applies a constraint to each
    element in that sequence.
    """
    def __init__(self, what):
        self.what = what

    def __call__(self, arg):
        if not misc.issequence(arg):
            raise TypeError("not a sequence")
        try:
            return [_apply_constraint(self.what, value) for value in arg]
        except (TypeError, ValueError):
            ex = sys.exc_info()[1]
            message = "illegal item in sequence: %s" % str(ex)
            raise type(ex)(message)


class flatten_sequenceof(object):
    """
    Flattens all arguments into a single list, and applies a constraint to
    each element in that list.
    """
    def __init__(self, what):
        self.what = what

    def __call__(self, arg):
        try:
            return [_apply_constraint(self.what, value) for value in misc.flatten(arg)]
        except (TypeError, ValueError):
            ex = sys.exc_info()[1]
            message = "illegal item in sequence: %s" % str(ex)
            raise type(ex)(message)


class either(object):
    """
    Accepts the argument if any of the given constraints can be applied.
    """
    def __init__(self, *alternatives):
        self.alternatives = alternatives

    def __call__(self, arg):
        errors = []
        for n, child in enumerate(self.alternatives):
            try:
                return _apply_constraint(child, arg)
            except (TypeError, ValueError):
                ex = sys.exc_info()[1]
                errors.append("error %d: %s: %s" % (n + 1, type(ex).__name__, str(ex)))
        message = "none of the alternatives matched:\n" + '\n'.join(errors)
        raise TypeError(message)


class reduce_bitmask(object):
    """
    Flattens all arguments and reduces them to a single bitmask.
    """
    def __init__(self, what):
        self.what = what

    def __call__(self, arg):
        seq = _apply_constraint(self.what, misc.flatten(arg))
        return functools.reduce(lambda x, y: x | y, seq)