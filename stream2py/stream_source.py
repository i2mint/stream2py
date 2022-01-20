"""
A BufferReader gives data access to any number of consumers and provides methods to seek data such
as next(), range(), head(), tail().  Each BufferReader instance has it's own cursor keeping track of
what data was last seen."""

from abc import ABCMeta, abstractmethod
import time
from typing import Optional, Union

from stream2py.protocols import Source
from stream2py.buffer_reader import BufferReader
from stream2py.stream_buffer import StreamBuffer

DFLT_READ_SIZE = 1
DFLT_MAX_LEN = 10000

timestamp_seconds_to_unit_conversion: Union[int, float] = 1e6  # to microseconds


def defaulted_values(source_dict, defaults):
    """Returns a the values of source_dict where None values are replaced with the
    corresponding `default_dict` values.

    >>> defaults = {'a': 1, 'b': 2, 'c': 3}
    >>> tuple(defaulted_values({'a': None, 'b': 22, 'c': None}, defaults))
    (1, 22, 3)
    >>> tuple(defaulted_values({'a': False, 'b': True, 'c': None}, defaults))
    (False, True, 3)
    """
    return {
        k: v if v is not None else defaults[k] for k, v in source_dict.items()
    }.values()


class StreamSource(Source, metaclass=ABCMeta):
    """Abstract parent class for reading from a source into a StreamBuffer.

    Provides interfaces for configuring the StreamBuffer and instantiating BufferReaders.

    The open method will be called when creating a reader with open_reader().
    The close method will be called when all open readers have been closed().
    This will also stop the StreamBuffer. A closed source can be reopened by opening another reader.

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
    """

    _buffer_kwargs: dict = {}
    _open_readers = 0
    _reader_cls = BufferReader
    _sleep_time_on_iter_none_s = 0.001
    _stream_buffer: StreamBuffer = None

    def __init__(self, *, reader_cls=BufferReader):
        self._reader_cls = reader_cls

    def __iter__(self):
        while True:
            _next = self.read()
            if _next is not None:
                yield _next
            elif self.is_stopped:
                return None
            else:
                time.sleep(self._sleep_time_on_iter_none_s)

    def set_sleep_time_on_iter_none(self, sleep_time_s: Union[int, float] = 0.001):
        """Set the sleep time of the iter yield loop when next data item is not yet available.

        :param sleep_time_s: seconds to sleep
        """
        self._sleep_time_on_iter_none_s = sleep_time_s

    def configure_buffer(
        self,
        *,
        maxlen: Optional[int] = None,
        sleep_time_on_read_none_s: Optional[Union[int, float]] = None,
        auto_drop=True,
    ):
        """Sets custom buffer parameters."""
        if self._stream_buffer:
            raise ValueError('Buffer has already been started.')
        self._buffer_kwargs = dict(
            maxlen=maxlen,
            sleep_time_on_read_none_s=sleep_time_on_read_none_s,
            auto_drop=auto_drop,
        )
        return self

    def _ensure_buffer(self):
        if not self._stream_buffer:
            self._stream_buffer = StreamBuffer(self, **self._buffer_kwargs)
            self._stream_buffer.start()

    def _handle_reader_open(self):
        self._open_readers += 1

    def _handle_reader_closed(self):
        self._open_readers -= 1
        if self._open_readers <= 0:
            self.exit()

    def open_reader(self, read_size=1, strict_n=False, ignore_no_item_found=False):
        """Instantiates a reader.
        :param read_size: number of items to return by default when reading.
            Is also used as the "chunk size" when iterating.
        :param strict_n: if True, by default a ValueError witll be raised if the
            exact number of requested items are not available when reading.
        :param ignore_no_item_found: if True, by default return None when no next item
            instead of raising exception during a read
        """
        self._ensure_buffer()
        new_reader = self._stream_buffer.mk_reader(
            read_size=read_size,
            strict_n=strict_n,
            ignore_no_item_found=ignore_no_item_found,
        )
        self._handle_reader_open()
        new_reader.open()
        new_reader.onclose = self._handle_reader_closed
        return new_reader

    def set_sleep_time_on_iter_none(self, sleep_time_s: Union[int, float] = 0.1):
        """Set the sleep time of the iter yield loop when next data item is not yet available.

        :param sleep_time_s: seconds to sleep
        """
        self._sleep_time_on_iter_none_s = sleep_time_s

    @property
    def sleep_time_on_read_none_s(self) -> Optional[Union[int, float]]:
        """Sets default sleep time for StreamBuffer when it reads None from SourceReader.
        Useful when you know the period between data points.

        For example if data only comes once every 10 seconds,
        it would be inefficient to try and read again every 0.1 seconds and get None up to 100 times
        but every 10 seconds or even 1 second would be much more reasonable depending on the use
        case. Not necessary if read is a blocking function that always returns a data point.

        Default is None which delegates the sleep time to StreamBuffer's default.

        :return: Optional[Union[int, float]] number of seconds to sleep
        """
        return None

    @classmethod
    def get_timestamp(cls) -> int:
        """Get timestamp of now as int microseconds

        :return: timestamp in UTC microseconds
        """
        return int(time.time() * cls.timestamp_seconds_to_unit_conversion)

    def exit(self):
        if self._stream_buffer:
            self._stream_buffer.stop()
        else:
            self.close()
