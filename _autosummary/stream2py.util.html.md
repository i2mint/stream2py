# stream2py.util

Util functions. Functions that are used by, or can be used with, stream2py objects
(but do not depend on stream2py objects themselves)

### Functions

| `forward_to_instance_enter`(obj)                             |                           |
|--------------------------------------------------------------|---------------------------|
| `forward_to_instance_exit`(obj, \*exception_info)            |                           |
| [`identity`](#stream2py.util.identity)(x) | Returns the input, as is. |
| `null_enter_func`(obj)                                       |                           |
| `null_exit_func`(obj, \*exception_info)                      |                           |

### Classes

| [`ContextualizeCall`](#stream2py.util.ContextualizeCall)(func[, enter_func, exit_func])   | Wraps a callable so that it also becomes a context manager.                            |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`Timer`](#stream2py.util.Timer)([egress])                                    | A simple timer that can be used as a context manager, or started and stopped manually. |

### Exceptions

| [`EnterFunctionValidation`](#stream2py.util.EnterFunctionValidation)   | Raised if an function isn't a valid (context manager) \_\_enter_\_ function   |
|----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`ExitFunctionValidation`](#stream2py.util.ExitFunctionValidation)    | Raised if an function isn't a valid (context manager) \_\_exit_\_ function    |
| [`TypeValidationError`](#stream2py.util.TypeValidationError)       | Raised if an object is not valid                                              |

### *class* stream2py.util.ContextualizeCall(func, enter_func=<function null_enter_func>, exit_func=<function null_exit_func>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Wraps a callable so that it also becomes a context manager.

Both enter and exit functions can be specified.

This can be used, for instance, when the proper use of a function depends on some
objects being “in context” (i.e. calling the enter/exit of some objects).

This happens, for instance, when we want to use a method that depends on its
instance being in context. For convenience, this use case is implemented by the
`contextualize_with_instance` function of this module.

Below is a simple doctest, but check out more significant tests in the tests folder.
You can also check out:

This issue: [https://github.com/i2mint/stream2py/issues/18](https://github.com/i2mint/stream2py/issues/18)

This wiki: [https://github.com/i2mint/stream2py/wiki/Forwarding-context-management](https://github.com/i2mint/stream2py/wiki/Forwarding-context-management)

```pycon
>>> f = lambda x: x + 1
>>> hasattr(f, '__enter__') and hasattr(f, '__exit__')
False
>>> g = ContextualizeCall(f)
>>> hasattr(g, '__enter__') and hasattr(g, '__exit__')
True
>>> with g:
...     print(g(2))
3
```

In the example above we get the default null enter and exit functions.
They do nothing.
Let’s specify some that do something:

```pycon
>>> h = ContextualizeCall(f,
...     enter_func=lambda self: print('entering...'),
...     exit_func=lambda self, *errs: print('exiting...'),
... )
>>> with h:
...     print(h(2))
entering...
3
exiting...
```

#### NOTE
A `ContextualizeCall` instance will delegate all other attributes to the
wrapped `func` except for special methods. If a user needs to also delegate these
special methods, they’ll have to wrap `func` themselves.

### *exception* stream2py.util.EnterFunctionValidation

Bases: [`TypeValidationError`](#stream2py.util.TypeValidationError)

Raised if an function isn’t a valid (context manager) \_\_enter_\_ function

#### *static* is_valid(obj)

Returns True if and only if obj is considered valid

### *exception* stream2py.util.ExitFunctionValidation

Bases: [`TypeValidationError`](#stream2py.util.TypeValidationError)

Raised if an function isn’t a valid (context manager) \_\_exit_\_ function

#### *static* is_valid(obj)

Returns True if and only if obj is considered valid

### *class* stream2py.util.Timer(egress=<function identity>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A simple timer that can be used as a context manager, or started and stopped
manually.

```pycon
>>> from time import sleep
>>> timer = Timer()
>>> timer.start()
>>> sleep(0.01)
>>> timer.elapsed()
0.010056478977203369
>>> timer.stop()
```

You can also use a context block, and specify an `egress` function that will be
called on the elapsed seconds:

```pycon
>>> with Timer(lambda x: print(f"{int(x / (60 * 60 * 24))} days elapsed")) as timer:
...     sleep(0.01)
...     timer.elapsed()
0 days elapsed
```

The same timer instance can be reused across context blocks:

```pycon
>>> timer = Timer(lambda x: int(x / 3600))
>>> with timer:
...     sleep(0.01)
...     t = timer.elapsed()
>>> t
0
>>> with timer:
...     sleep(0.01)
```

Asking for the elapsed time of a timer that isn’t running tells you so, instead of
failing obscurely:

```pycon
>>> Timer().elapsed()
Traceback (most recent call last):
  ...
ValueError: The timer is not running....
```

Note that elapsed time is measured with `time.perf_counter`, a monotonic clock, so
it is unaffected by system clock adjustments. This also means `start_time` is not a
wall-clock timestamp; it is only meaningful as a reference point for a difference.

#### elapsed()

The (egress-transformed) seconds since the timer was started.

Raises `ValueError` if the timer is not running.

### *exception* stream2py.util.TypeValidationError

Bases: [`TypeError`](https://docs.python.org/3/builtins/exceptions.html#TypeError)

Raised if an object is not valid

#### *abstractmethod static* is_valid(obj)

Returns True if and only if obj is considered valid

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### stream2py.util.identity(x)

Returns the input, as is.
