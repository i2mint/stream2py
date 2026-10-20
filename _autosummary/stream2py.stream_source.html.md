# stream2py.stream_source

A BufferReader gives data access to any number of consumers and provides methods to seek data such
as next(), range(), head(), tail().  Each BufferReader instance has it’s own cursor keeping track of
what data was last seen.

### Functions

| [`defaulted_values`](#stream2py.stream_source.defaulted_values)(source_dict, defaults)   | Returns a the values of source_dict where None values are replaced with the corresponding `default_dict` values.   |
|--------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|

### Classes

| [`StreamSource`](#stream2py.stream_source.StreamSource)(\*[, reader_cls])   | Abstract parent class for reading from a source into a StreamBuffer.   |
|-----------------------------------------------------------------------------------|------------------------------------------------------------------------|

### *class* stream2py.stream_source.StreamSource(\*, reader_cls=<class 'stream2py.buffer_reader.BufferReader'>)

Bases: [`Source`](stream2py.protocols.html.md#stream2py.protocols.Source)

Abstract parent class for reading from a source into a StreamBuffer.

Provides interfaces for configuring the StreamBuffer and instantiating BufferReaders.

The open method will be called when creating a reader with open_reader().
The close method will be called when all open readers have been closed().
This will also stop the StreamBuffer. A closed source can be reopened by opening another reader.

```pycon
>>> from stream2py.examples.stream_source import SimpleCounterString
>>> source = SimpleCounterString(start=0, stop=10)
>>> with source.open_reader() as reader:
...     # the source will close when exiting the context
...     reader.read()
...     reader.read()
...     reader.read()
's0'
's1'
's2'
>>> reader2 = source.open_reader()
>>> reader2.read()
's0'
>>> reader2.close()  # closing the reader manually
```

#### configure_buffer(, maxlen=None, sleep_time_on_read_none_s=None, auto_drop=True)

Sets custom buffer parameters.

#### *classmethod* get_timestamp()

Get timestamp of now as int microseconds

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
* **Returns:**
  timestamp in UTC microseconds

#### open_reader(read_size=1, strict_n=False, ignore_no_item_found=False)

Instantiates a reader.

* **Parameters:**
  * **read_size** – number of items to return by default when reading.
    Is also used as the “chunk size” when iterating.
  * **strict_n** – if True, by default a ValueError witll be raised if the
    exact number of requested items are not available when reading.
  * **ignore_no_item_found** – if True, by default return None when no next item
    instead of raising exception during a read

#### set_sleep_time_on_iter_none(sleep_time_s=0.1)

Set the sleep time of the iter yield loop when next data item is not yet available.

* **Parameters:**
  **sleep_time_s** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`float`](https://docs.python.org/3/builtins/functions.html#float)]) – seconds to sleep

#### *property* sleep_time_on_read_none_s *: [Union](https://docs.python.org/3/library/typing.html#typing.Union)[[int](https://docs.python.org/3/builtins/functions.html#int), [float](https://docs.python.org/3/builtins/functions.html#float), [None](https://docs.python.org/3/builtins/constants.html#None)]*

Sets default sleep time for StreamBuffer when it reads None from SourceReader.
Useful when you know the period between data points.

For example if data only comes once every 10 seconds,
it would be inefficient to try and read again every 0.1 seconds and get None up to 100 times
but every 10 seconds or even 1 second would be much more reasonable depending on the use
case. Not necessary if read is a blocking function that always returns a data point.

Default is None which delegates the sleep time to StreamBuffer’s default.

* **Returns:**
  Optional[Union[int, float]] number of seconds to sleep

### stream2py.stream_source.defaulted_values(source_dict, defaults)

Returns a the values of source_dict where None values are replaced with the
corresponding `default_dict` values.

```pycon
>>> defaults = {'a': 1, 'b': 2, 'c': 3}
>>> tuple(defaulted_values({'a': None, 'b': 22, 'c': None}, defaults))
(1, 22, 3)
>>> tuple(defaulted_values({'a': False, 'b': True, 'c': None}, defaults))
(False, True, 3)
```
