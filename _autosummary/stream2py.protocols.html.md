# stream2py.protocols

Defines protocols for classes to avoid circular imports

### Classes

| [`Source`](#stream2py.protocols.Source)(\*args, \*\*kwargs)   | The interface for the StreamSource class.   |
|-------------------------------------------------------------------------------|---------------------------------------------|

### *class* stream2py.protocols.Source(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

The interface for the StreamSource class.

#### close()

Close the resource.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### *property* info *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

Information about the source.

#### key(data)

Sort key of `data`.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

#### open()

Open the resource.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### read()

Read the next item, or `None` if nothing is ready.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

#### *property* sleep_time_on_read_none_s *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Seconds to wait when `read` returns `None`.
