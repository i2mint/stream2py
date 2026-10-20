# stream2py.buffer_reader

A BufferReader gives data access to any number of consumers and provides methods to seek data such
as next(), range(), head(), tail().  Each BufferReader instance has it’s own cursor keeping track of
what data was last seen.

### Classes

| [`BufferReader`](#stream2py.buffer_reader.BufferReader)(buffer, source_reader_info, ...)   | Reader that is constructed from StreamBuffer.mk_reader()   |
|--------------------------------------------------------------------------------------------------|------------------------------------------------------------|

### *class* stream2py.buffer_reader.BufferReader(buffer, source_reader_info, stop_event, , read_size=1, peek=False, strict_n=False, ignore_no_item_found=False)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Reader that is constructed from StreamBuffer.mk_reader()

```pycon
>>> from stream2py import StreamBuffer, BufferReader
>>> from stream2py.examples.source_reader import SimpleCounterString
>>>
>>> source_reader = SimpleCounterString(start=0, stop=100)
>>> stream_buffer = StreamBuffer(source_reader=source_reader, maxlen=100)
>>> stream_buffer.start()
>>>
>>> buffer_reader = stream_buffer.mk_reader()
>>> isinstance(buffer_reader, BufferReader)
True
>>> buffer_reader.is_stopped
False
>>> buffer_reader.last_item == None  # None until value is seen
True
>>> buffer_reader.next() # get first item
's0'
>>> buffer_reader.last_item # check last_item cursor
's0'
>>> # next will not update last_item cursor
>>> buffer_reader.next(peek=True), buffer_reader.last_item
('s1', 's0')
>>> # same as what was peeked but now cursor is updated
>>> buffer_reader.next(), buffer_reader.last_item
('s1', 's1')
>>> buffer_reader.range(start=5, stop=10)
['s5', 's6', 's7', 's8', 's9', 's10']
>>> buffer_reader.last_item
's10'
>>> buffer_reader.range(start=5, stop=10, step=3), buffer_reader.last_item
(['s5', 's8'], 's8')
>>> buffer_reader.range(start=10, stop=15, peek=True)
['s10', 's11', 's12', 's13', 's14', 's15']
>>> buffer_reader.last_item # unchanged with peek
's8'
>>> buffer_reader.last_key # key of last_item
8
>>> # only 9 is greater than last item key
>>> buffer_reader.range(start=0, stop=9, only_new_items=True)
['s9']
>>> buffer_reader.head(), buffer_reader.last_item, buffer_reader.last_key
('s0', 's0', 0)
>>> buffer_reader.tail(), buffer_reader.last_item, buffer_reader.last_key
('s99', 's99', 99)
>>>
>>> stream_buffer.stop()
>>>
>>> buffer_reader.is_stopped
True
```

#### is_same_buffer(other_buffer_reader)

Check if reader is looking at the same buffer

#### *property* is_stopped *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Checks if stop event has been set by StreamBuffer.

* **Returns:**
  bool

#### *property* last_item

last seen item cursor

#### *property* last_key

key to last seen item cursor

#### range(start, stop, step=None, , peek=False, ignore_no_item_found=None, only_new_items=False, start_le=False, stop_ge=False, join=False)

Enables:

1. Get last n minutes
2. Give me data I don’t have

* **Parameters:**
  * **start** – starting range key of item inclusive
  * **stop** – ending range key of item inclusive
  * **step**
  * **peek** – if True, last_item cursor will not be updated
  * **ignore_no_item_found** – if True, return None when no next item
    instead of raising exception.
  * **only_new_items** – if True and no new items, raise ValueError
    or return None if ignore_no_item_found
  * **start_le** – if True, increase the search range to find start less than or equal by
    rounding down if start is in between keys,
    i.e. keys=[0, 10, 20], start=9 will include key=0
  * **stop_ge** – if True, raise ValueError when there is no key greater than or equal to
    stop in buffer, if ignore_no_item_found is also True, return None instead of ValueError
  * **join** – if True, return ONE item instead of a list: the items in range
    trimmed to exactly `[start, stop]` and joined, using the source reader’s
    `slice_item` and `join_items` (both must be implemented, otherwise
    NotImplementedError is raised before anything is read). Implies
    `start_le=True` so the chunk containing `start` is included, and is
    incompatible with `step`. The `last_item` cursor still moves to the
    last *buffer* item, not the trimmed one. With `only_new_items` the
    joined item starts after the cursor. When nothing is found the result is
    the same as without `join` (`[]`, `None` or an exception).
* **Returns:**
  list of items in range (a single joined item if `join`)

#### read(n=None, , peek=None, ignore_no_item_found=None, strict_n=None, blocking=False, timeout=None)

Finds an item with a key greater than the last returned item.
Raise ValueError if no item found with key above last item.

#### NOTE
Arguments whose values are not specified will be replaced with
self.

* **Parameters:**
  * **n** – number of items to return
  * **peek** – if True, last_item cursor will not be updated
  * **ignore_no_item_found** – if True, return None when no next item
    instead of raising exception
  * **strict_n** – if True, raise ValueError if n items are not available
  * **blocking** – if True, wait to return next item if not yet available
  * **timeout** – only used when `blocking` is True. Maximum number of seconds
    to wait; `None` (default) waits until an item is available or the stream
    stops. When it runs out, returns None (as when the stream stops).
* **Returns:**
  next item or list of next items if n > 1

#### set_sleep_time_on_iter_none(sleep_time_s=0.1)

Set the sleep time of the iter yield loop when next data item is not yet available.

* **Parameters:**
  **sleep_time_s** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`float`](https://docs.python.org/3/builtins/functions.html#float)]) – seconds to sleep

#### *property* source_reader_info *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

A dict with important source info set by SourceReader.

* **Returns:**
  dict

#### tail(, peek=False, ignore_no_item_found=False, only_new_items=False)

Finds the last item in buffer. Raise ValueError if no item found.

* **Parameters:**
  * **peek** – if True, last_item cursor will not be updated
  * **ignore_no_item_found** – if True, return None when no next item
    instead of raising exception
  * **only_new_items** – if True and no new items, raise ValueError
    or return None if ignore_no_item_found
* **Returns:**
  tail item
