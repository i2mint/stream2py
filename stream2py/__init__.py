"""
.. graphviz::

    digraph {
        rankdir=LR;
        "SourceReader" [shape=cds]
        "StreamBuffer" [shape=box3d]
        "SourceReader" -> "StreamBuffer" -> "BufferReader1";
        "StreamBuffer" -> "BufferReader2";
        "StreamBuffer" -> "BufferReader3";
    }

The Rationale
-------------

Stream2py enables you to create a single asynchronous Source Reader and simply distribute
thread-safe readers to one or more consumers for the same data window. Or in other words, read and
work on data without worrying about missing data.

Normal way to process audio recording::

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

Stream2py way to process audio recording::

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

How to use
----------
There are 3 components

1. The SourceReader
^^^^^^^^^^^^^^^^^^^
A SourceReader defines how to get data with the methods: open(), read(), and close(), and also how
the data is ordered with the key() method and an info property describing the instance.

::

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
        def info(self)
            return dict(file=self.file, mode=self.mode)

2. The StreamBuffer
^^^^^^^^^^^^^^^^^^^
A StreamBuffer has 2 jobs: First, it manages the open, read, and close of a SourceReader and puts
read data onto a thread-safe buffer.
Second, it is a factory of BufferReaders instances for multiple consumers.

::

    # ...Continued from above

    # download txt from: https://www.gutenberg.org/cache/epub/1524/pg1524.txt
    FILE = 'hamlet.txt'
    source_reader = LineSourceReader(FILE)

    with StreamBuffer(
        source_reader=source_reader,
        maxlen=None,  # None should only be used when reading objects with fixed lengths like a file
    ) as stream_buffer:
        buffer_reader = stream_buffer.mk_reader()

3. The BufferReader
^^^^^^^^^^^^^^^^^^^
A BufferReader gives data access to any number of consumers and provides methods to seek data such
as next(), range(), head(), tail().  Each BufferReader instance has it's own cursor keeping track of
what data was last seen.

::

    # ...Continued from above

        line_1 = buffer_reader.next()
        line_2 = next(buffer_reader)
        line_1_10 = buffer_reader.range(start=1, stop=10)

The All-in-One Helper
^^^^^^^^^^^^^^^^^^^^^
Here's a bonus helper function to shortcut the SourceReader class.

::

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

"""

from stream2py.source_reader import *
from stream2py.buffer_reader import *
from stream2py.stream_buffer import *
from stream2py.simply import mk_stream_buffer
