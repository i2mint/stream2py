"""Util functions. Functions that are used by, or can be used with, stream2py objects
(but do not depend on stream2py objects themselves)
"""

from inspect import signature, Parameter
from abc import abstractmethod
from functools import wraps


class TypeValidationError(TypeError):
    """Raised if an object is not valid"""

    @staticmethod
    @abstractmethod
    def is_valid(obj) -> bool:
        """Returns True if and only if obj is considered valid"""

    @classmethod
    def validate(cls, obj, *args, **kwargs):
        if not cls.is_valid(obj):
            raise cls(*args, **kwargs)


def null_enter_func(obj):
    return obj


def null_exit_func(obj, *exception_info):
    return None


def _has_min_num_of_arguments(func, mininum_n_args):
    return len(signature(func).parameters) >= mininum_n_args


def _callable_has_a_variadic_pos(func):
    """True if and only if the function has a variadic positional argument (i.e.
    *args)"""
    return any(
        x.kind == Parameter.VAR_POSITIONAL for x in signature(func).parameters.values()
    )


class EnterFunctionValidation(TypeValidationError):
    """Raised if an function isn't a valid (context manager) __enter__ function"""

    @staticmethod
    def is_valid(obj):
        return callable(obj) and _has_min_num_of_arguments(obj, 1)


class ExitFunctionValidation(TypeValidationError):
    """Raised if an function isn't a valid (context manager) __exit__ function"""

    @staticmethod
    def is_valid(obj):
        return callable(obj) and (
            _callable_has_a_variadic_pos or _has_min_num_of_arguments(obj, 4)
        )


# TODO: If needed:
#  A more general Contextualizer would proxy/delegate all methods (including special
#  ones) to the wrapped
class ContextualizeCall:
    """
    Wraps a callable so that it also becomes a context manager.

    Both enter and exit functions can be specified.

    This can be used, for instance, when the proper use of a function depends on some
    objects being "in context" (i.e. calling the enter/exit of some objects).

    This happens, for instance, when we want to use a method that depends on its
    instance being in context. For convenience, this use case is implemented by the
    ``contextualize_with_instance`` function of this module.

    Below is a simple doctest, but check out more significant tests in the tests folder.
    You can also check out:

    This issue: https://github.com/i2mint/stream2py/issues/18

    This wiki: https://github.com/i2mint/stream2py/wiki/Forwarding-context-management

    >>> f = lambda x: x + 1
    >>> hasattr(f, '__enter__') and hasattr(f, '__exit__')
    False
    >>> g = ContextualizeCall(f)
    >>> hasattr(g, '__enter__') and hasattr(g, '__exit__')
    True
    >>> with g:
    ...     print(g(2))
    3

    In the example above we get the default null enter and exit functions.
    They do nothing.
    Let's specify some that do something:

    >>> h = ContextualizeCall(f,
    ...     enter_func=lambda self: print('entering...'),
    ...     exit_func=lambda self, *errs: print('exiting...'),
    ... )
    >>> with h:
    ...     print(h(2))
    entering...
    3
    exiting...

    Note: A ``ContextualizeCall`` instance will delegate all other attributes to the
    wrapped `func` except for special methods. If a user needs to also delegate these
    special methods, they'll have to wrap `func` themselves.
    """

    def __init__(self, func, enter_func=null_enter_func, exit_func=null_exit_func):
        # validation
        if not callable(func):
            raise TypeError(f'First argument should be a callable, was: {func}')
        EnterFunctionValidation.validate(
            enter_func,
            f'Not a valid enter function (should be a callable with at least one arg): '
            f'{enter_func}',
        )
        ExitFunctionValidation.validate(
            exit_func,
            f'Not a valid exit function (should be a callable with at least one arg or '
            f'varadic args): {exit_func}',
        )
        # assignment
        self.func = func
        self.enter_func = enter_func
        self.exit_func = exit_func
        # wrapping self with attributes of func (signature, name, etc.)
        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __enter__(self):
        #         print(f'{type(self).__name__}.__enter__')
        return self.enter_func(self.func)

    def __exit__(self, exc_type, exc_val, exc_tb):
        #         print(f'{type(self).__name__}.__exit__')
        return self.exit_func(self.func, exc_type, exc_val, exc_tb)

    def __getattr__(self, attrname):
        return getattr(self.func, attrname)


# ---------------------------------------------------------------------------------------
# Using these general objects for the particular case of having bound methods forward
# their context
# management to the instances they're bound to

from functools import partial


def forward_to_instance_enter(obj):
    return obj.__self__.__enter__()


def forward_to_instance_exit(obj, *exception_info):
    return obj.__self__.__exit__(*exception_info)


contextualize_with_instance = partial(
    ContextualizeCall,
    enter_func=forward_to_instance_enter,
    exit_func=forward_to_instance_exit,
)
contextualize_with_instance.__doc__ = (
    'To be applied to a bound method. '
    'Returns a callable that forwards context enters/exits to the bound instance. '
    'See ``tests.test_util.test_contextualize_with_instance`` for and example use.'
)
