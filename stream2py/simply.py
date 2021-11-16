"""
Helper Function to construct a SourceReader and StreamBuffer in one


Example of usage:

::

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

"""

import contextlib
from typing import Callable, Any, Optional

from stream2py import SourceReader, StreamBuffer
from stream2py.utility.typing_hints import ComparableType, OpenInstance


@contextlib.contextmanager
def mk_stream_buffer(
    read_stream: Callable[[OpenInstance], Optional[Any]],
    open_stream: Callable[[], OpenInstance] = None,
    close_stream: Callable[[OpenInstance], None] = None,
    info: Callable[[OpenInstance], dict] = None,
    key: Callable[[Any], ComparableType] = None,
    maxlen: Optional[int] = 100,
    sleep_time_on_read_none_seconds: float = None,
    auto_drop: bool = True,
    enumerate_data: bool = True,
):
    """Helper Function to construct a SourceReader and StreamBuffer in one

    ::

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

    :param read_stream: takes open instance and returns the next read item
    :param open_stream: open stream and return an open instance such as a file descriptor
    :param close_stream: take open instance and close the instance
    :param info: dict help in describing the instance
    :param key: sort key for read items
    :param maxlen: max read items to keep in buffer window
    :param sleep_time_on_read_none_seconds: time to wait if data is not ready to be read
    :param auto_drop: False is useful when data can be read independent of time and will quickly
        overflow the buffer maxlen before data is consumed. StreamBuffer.drop() must be called to
        continue reading after buffer has filled up. Default True.
    :param enumerate_data: wrap read data in an enumerated tuple. Default True.
    :return:
    """

    class SimplifiedSourceReader(SourceReader):
        open_instance: OpenInstance = None
        open_time = 0
        sleep_time_on_read_none_s = sleep_time_on_read_none_seconds
        read_idx = 0

        def open(self):
            self.read_idx = 0
            if open_stream is not None:
                self.open_instance = open_stream()
            self.open_time = self.get_timestamp()

        def read(self):
            read_data = read_stream(self.open_instance)
            if enumerate_data:
                read_data = (self.read_idx, read_data)
            self.read_idx += 1

            return read_data

        def close(self):
            if close_stream is not None:
                close_stream(self.open_instance)

        @property
        def info(self):
            if info is not None:
                return info(self.open_instance)
            return {
                'open_time': self.open_time,
                'open_instance': str(self.open_instance),
            }

        def key(self, data: Any):
            if key is not None:
                return key(data)
            return data

    stream_buffer = StreamBuffer(
        source_reader=SimplifiedSourceReader(),
        maxlen=maxlen,
        sleep_time_on_read_none_s=sleep_time_on_read_none_seconds,
        auto_drop=auto_drop,
    )

    try:
        stream_buffer.start()
        yield stream_buffer
    finally:
        stream_buffer.stop()
