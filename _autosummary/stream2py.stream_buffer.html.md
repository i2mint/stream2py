# stream2py.stream_buffer

A StreamBuffer has 2 jobs: First, it manages the open, read, and close of a SourceReader
and puts read data onto a thread-safe buffer.
Second, it is a factory of BufferReaders instances for multiple consumers.

### Classes

| [`StreamBuffer`](#stream2py.stream_buffer.StreamBuffer)(source_reader, \*[, maxlen, ...])   | Handles starting and stopping SourceReader and making BufferReaders   |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|

### *class* stream2py.stream_buffer.StreamBuffer(source_reader, , maxlen=100, sleep_time_on_read_none_s=None, auto_drop=True)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Handles starting and stopping SourceReader and making BufferReaders

```pycon
>>> from stream2py import StreamBuffer
>>> from stream2py.examples.source_reader import SimpleCounterString
>>>
>>> source_reader = SimpleCounterString(start=0, stop=100)
>>> stream_buffer = StreamBuffer(source_reader=source_reader, maxlen=100)
>>> stream_buffer.is_running
False
>>> print(stream_buffer.source_reader_info)
None
>>> stream_buffer.start()
>>> assert stream_buffer.is_running
>>> stream_buffer.source_reader_info
{'start': 0, 'stop': 100, 'open_count': 1}
>>> open1_reader1 = stream_buffer.mk_reader()
>>> open1_reader1.next()
's0'
>>> open1_reader2 = stream_buffer.mk_reader()
>>> # readers from the same open instance are the same
>>> assert open1_reader1.is_same_buffer(open1_reader2) is True
>>> assert open1_reader1.next() != open1_reader2.next()  # item cursor position is different
>>> stream_buffer.stop()
>>>
>>> with stream_buffer:
...     stream_buffer.source_reader_info
...     open2_reader1  = stream_buffer.mk_reader()
...     open2_reader2  = stream_buffer.mk_reader()
...     # readers from the same open instance are the same
...     assert open2_reader1.is_same_buffer(open2_reader2) is True
...     # readers from the different open instances
...     assert open2_reader1.is_same_buffer(open1_reader1) is False
{'start': 0, 'stop': 100, 'open_count': 2}
```

#### attach_reader(reader)

Allows a StreamReader instance to read from this buffer.

* **Raises:**
  [**StreamNotStartedError**](stream2py.exceptions.html.md#stream2py.exceptions.StreamNotStartedError) – if the StreamBuffer hasn’t been started yet

#### drop(n=1)

Manually drop items from buffer when auto_drop is False

* **Parameters:**
  **n** – number of items to drop from the left side
* **Returns:**

#### *property* is_running *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Checks if stop event has been set.

* **Returns:**
  bool

#### mk_reader(\*\*read_kwargs)

Makes a BufferReader instance for the currently running  StreamBuffer.
Reader must be made after start() to have data from said start.

* **Return type:**
  [`BufferReader`](stream2py.buffer_reader.html.md#stream2py.buffer_reader.BufferReader)
* **Returns:**
  BufferReader instance
* **Raises:**
  [**StreamNotStartedError**](stream2py.exceptions.html.md#stream2py.exceptions.StreamNotStartedError) – if the StreamBuffer hasn’t been started yet

#### *property* source_reader_info *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[dict](https://docs.python.org/3/builtins/stdtypes.html#dict)]*

A dict with important source info set by SourceReader.

* **Returns:**
  dict or None

#### start()

Open and start reading from source_reader into buffer

#### stop()

Stop reading and close source_reader
