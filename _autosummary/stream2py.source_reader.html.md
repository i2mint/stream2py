# stream2py.source_reader

A SourceReader defines how to get data with the methods: open(), read(), and close(), and also how
the data is ordered with the key() method and an info property describing the instance.

### Classes

| [`SourceReader`](#stream2py.source_reader.SourceReader)(\*args, \*\*kwargs)   | (deprecated) Abstract class interface to be used by StreamBuffer.   |
|-------------------------------------------------------------------------------------|---------------------------------------------------------------------|

### *class* stream2py.source_reader.SourceReader(\*args, \*\*kwargs)

Bases: [`Source`](stream2py.protocols.html.md#stream2py.protocols.Source)

(deprecated) Abstract class interface to be used by StreamBuffer.

```pycon
>>> from stream2py import SourceReader
>>>
>>> class SimpleCounterString(SourceReader):
...     '''Count in range returning a string formatted as f"s{count}"'''
...     def __init__(self, start, stop):
...         assert start < stop
...         self.start = start
...         self.stop = stop
...         self.range_iterator = None
...         self.open_count = 0
...
...     def open(self):
...         self.open_count += 1
...         self.range_iterator = iter(range(self.start, self.stop))
...         self._closed = False
...
...     def read(self):
...         value = next(self.range_iterator, None)
...         if value is not None:
...             return f's{value}'
...         else:
...             return None
...
...     def close(self):
...         del self.range_iterator
...         self.range_iterator = None
...         self._closed = True
...
...     @property
...     def info(self):
...         return dict(start=self.start, stop=self.stop, open_count=self.open_count)
...
...     def key(self, data):
...         return int(data[1:])
...
>>> source_reader = SimpleCounterString(start=0, stop=10)
>>> source_reader.closed
True
>>> source_reader.open()
>>> source_reader.closed
False
>>> source_reader.info
{'start': 0, 'stop': 10, 'open_count': 1}
>>> source_reader.read()
's0'
>>> source_reader.close()
>>> source_reader.closed
True
>>> with source_reader:
...     source_reader.info
...     source_reader.read()
...     source_reader.read()
...     source_reader.read()
{'start': 0, 'stop': 10, 'open_count': 2}
's0'
's1'
's2'
```

#### *abstractmethod* close()

Close and clean up source reader.
Will be called when StreamBuffer stops or if an exception is raised during read and append
loop.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### *property* closed *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

True if the source reader is closed, False if it’s open.

Similar to io.IOBase.closed property.

* **Returns:**
  bool indicating whether the source is closed

#### *classmethod* get_timestamp()

Get timestamp of now as int microseconds

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
* **Returns:**
  timestamp in UTC microseconds

#### *property* info *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

A dict with important source info. Default can be init_kwargs and open timestamp.

This info will be available in BufferReader after SourceReader has opened but any changes
made between open and close are not guaranteed to be visible. Any continuous status updates
should be included with read data instead.

* **Returns:**
  dict

#### join_items(items)

(Optional) Join consecutive data items into one data item.

Implement together with `slice_item` to let `BufferReader.range(...,
join=True)` return the exact span asked for, as a single item (e.g. several
waveform chunks concatenated). Not abstract: sources whose items can’t be
joined just don’t override it.

* **Parameters:**
  **items** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – non-empty list of data items, in key order
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
* **Returns:**
  one data item

#### *abstractmethod* key(data)

Converts data into a comparable value to sort by

* **Parameters:**
  **data** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – the return value of the ‘read’ method
* **Return type:**
  [`ComparableType`](stream2py.utility.typing_hints.html.md#stream2py.utility.typing_hints.ComparableType)
* **Returns:**
  ComparableType

#### *abstractmethod* open()

Set up source to be read and set some source info affected by open time like the time of
open. Will be called in StreamBuffer immediately before first read.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### set_sleep_time_on_iter_none(sleep_time_s=0.001)

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

#### slice_item(item, start=None, stop=None)

(Optional) The part of `item` whose keys fall within `[start, stop]`.

`None` for a bound means unbounded on that side; an item that needs no
trimming can be returned as is. See `join_items`. Must be pure (items in the
buffer are shared, never mutate them) and keyed on absolute keys: it is applied
once per bound, so a lone item is sliced twice (`start` then `stop`).

* **Parameters:**
  **item** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – a data item as returned by `read`
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
* **Returns:**
  a data item of the same kind, possibly shorter
