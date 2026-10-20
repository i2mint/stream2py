# stream2py.simply

Helper Function to construct a SourceReader and StreamBuffer in one

Example of usage:

```default
from stream2py.simply import mk_stream_buffer

counter = iter(range(10))
with mk_stream_buffer(
    read_stream=lambda open_inst: next(counter),
    open_stream=lambda: print('open'),
    close_stream=lambda open_inst: print('close'),
    auto_drop=False,
    maxlen=2,
) as count_stream_buffer:
    count_reader = count_stream_buffer.mk_reader()
    print(f'start reading {count_reader.source_reader_info}')
    for i in count_reader:
        # do stuff with read data
        print(i)
        if count_stream_buffer.auto_drop is False:
            count_stream_buffer.drop()

    print('done reading')
```

### Functions

| [`mk_stream_buffer`](#stream2py.simply.mk_stream_buffer)(read_stream[, open_stream, ...])   | Helper Function to construct a SourceReader and StreamBuffer in one   |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|

### stream2py.simply.mk_stream_buffer(read_stream, open_stream=None, close_stream=None, info=None, key=None, maxlen=100, sleep_time_on_read_none_seconds=None, auto_drop=True, enumerate_data=True)

Helper Function to construct a SourceReader and StreamBuffer in one

```default
from time import sleep
from stream2py import mk_stream_buffer

# download txt from: https://www.gutenberg.org/cache/epub/1524/pg1524.txt
FILE = 'hamlet.txt'
with mk_stream_buffer(
    read_stream=lambda open_inst: next(open_inst, None),
    open_stream=lambda: open(FILE, 'rt'),
    close_stream=lambda open_inst: open_inst.close(),
    key=lambda read_data: read_data[0],
    maxlen=None,
) as stream_buffer:
    buffer_reader = stream_buffer.mk_reader()
    sleep(1)
    # do stuff with buffer_reader
    print(buffer_reader.range(start=40, stop=50))
```

* **Parameters:**
  * **read_stream** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]], [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – takes open instance and returns the next read item
  * **open_stream** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[], [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – open stream and return an open instance such as a file descriptor
  * **close_stream** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – take open instance and close the instance
  * **info** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]], [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – dict help in describing the instance
  * **key** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`ComparableType`](stream2py.utility.typing_hints.html.md#stream2py.utility.typing_hints.ComparableType)]) – sort key for read items
  * **maxlen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]) – max read items to keep in buffer window
  * **sleep_time_on_read_none_seconds** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – time to wait if data is not ready to be read
  * **auto_drop** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – False is useful when data can be read independent of time and will quickly
    overflow the buffer maxlen before data is consumed. StreamBuffer.drop() must be called to
    continue reading after buffer has filled up. Default True.
  * **enumerate_data** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – wrap read data in an enumerated tuple. Default True.
* **Returns:**
