# stream2py

## The Rationale

Stream2py enables you to create a single asynchronous Source Reader and simply distribute
thread-safe readers to one or more consumers for the same data window. Or in other words, read and
work on data without worrying about missing data.

Normal way to process audio recording:

```default
import pyaudio

CHUNK = 1024
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

p = pyaudio.PyAudio()

stream = p.open(
    format=p.get_format_from_width(WIDTH),
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    # risk of buffer overflow before next read
    long_calculations(data)

stream.stop_stream()
stream.close()
p.terminate()
```

Stream2py way to process audio recording:

```default
from stream2py.sources.audio import PyAudioSourceReader

CHUNK = 1024
WIDTH = 2
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

source_reader = PyAudioSourceReader(
    rate=RATE,
    width=WIDTH,
    channels=CHANNELS,
    frames_per_buffer=CHUNK
)
with StreamBuffer(
    source_reader=source_reader, maxlen=int(RATE / CHUNK * RECORD_SECONDS)
) as stream_buffer:
    buffer_reader = stream_buffer.mk_reader()

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = next(buffer_reader)
        long_calculations(data)
```

## How to use

There are 3 components

1. A SourceReader defines how to get data with the methods: open(), read(), and close(), and also how
   the data is ordered with the key() method and an info property describing the instance.

```default
from typing import Tuple
from stream2py import SourceReader

EnumeratedReadData = Tuple[int, str]

class LineSourceReader(SourceReader):
    def __init__(self, file, mode='rt'):
        self.file = file
        self.mode = mode
        self.line_count = 0
        self._f = None

    def open(self):
        self.line_count = 0
        self._f = open(self.file, self.mode)

    def read(self) -> EnumeratedReadData:
        read_data = (self.line_count, self._f.readline())
        self.line_count += 1
        return read_data

    def close(self):
        self._f.close()

    def key(self, data: EnumeratedReadData):
        return data[0]

    @property
    def info(self):
        return dict(file=self.file, mode=self.mode)
```

1. A StreamBuffer has 2 jobs: First, it manages the open, read, and close of a SourceReader and puts
   read data onto a thread-safe buffer.

Second, it is a factory of BufferReaders instances for multiple consumers.

```default
# ...Continued from above

# download txt from: https://www.gutenberg.org/cache/epub/1524/pg1524.txt
FILE = 'hamlet.txt'
source_reader = LineSourceReader(FILE)

with StreamBuffer(
    source_reader=source_reader,
    maxlen=None,  # None should only be used when reading objects with fixed lengths like a file
) as stream_buffer:
    buffer_reader = stream_buffer.mk_reader()
```

1. A BufferReader gives data access to any number of consumers and provides methods to seek data such
   as next(), range(), head(), tail().  Each BufferReader instance has it’s own cursor keeping track of
   what data was last seen.

```default
# ...Continued from above

    line_1 = buffer_reader.next()
    line_2 = next(buffer_reader)
    line_1_10 = buffer_reader.range(start=1, stop=10)
```

### The All-in-One Helper

Here’s a bonus helper function to shortcut the SourceReader class.

```default
from time import sleep
from stream2py import mk_stream_buffer

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

### Modules

| [`buffer_reader`](stream2py.buffer_reader.html.md#module-stream2py.buffer_reader)   | A BufferReader gives data access to any number of consumers and provides methods to seek data such as next(), range(), head(), tail().                                                     |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`exceptions`](stream2py.exceptions.html.md#module-stream2py.exceptions)         | Custom exception classes for stream2py                                                                                                                                                     |
| [`protocols`](stream2py.protocols.html.md#module-stream2py.protocols)           | Defines protocols for classes to avoid circular imports                                                                                                                                    |
| [`simply`](stream2py.simply.html.md#module-stream2py.simply)                 | Helper Function to construct a SourceReader and StreamBuffer in one                                                                                                                        |
| [`source_reader`](stream2py.source_reader.html.md#module-stream2py.source_reader)   | A SourceReader defines how to get data with the methods: open(), read(), and close(), and also how the data is ordered with the key() method and an info property describing the instance. |
| [`sources`](stream2py.sources.html.md#module-stream2py.sources)               | A few light weight (builtin-only ) source readers you can use                                                                                                                              |
| [`stream_buffer`](stream2py.stream_buffer.html.md#module-stream2py.stream_buffer)   | A StreamBuffer has 2 jobs: First, it manages the open, read, and close of a SourceReader and puts read data onto a thread-safe buffer.                                                     |
| [`stream_source`](stream2py.stream_source.html.md#module-stream2py.stream_source)   | A BufferReader gives data access to any number of consumers and provides methods to seek data such as next(), range(), head(), tail().                                                     |
| [`util`](stream2py.util.html.md#module-stream2py.util)                     | Util functions.                                                                                                                                                                            |
| [`utility`](stream2py.utility.html.md#module-stream2py.utility)               | Low-level building blocks used by stream2py's buffers and readers.                                                                                                                         |
