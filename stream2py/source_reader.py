"""
A SourceReader defines how to get data with the methods: open(), read(), and close(), and also how
the data is ordered with the key() method and an info property describing the instance."""
__all__ = ['SourceReader']


from abc import ABCMeta, abstractmethod
import time
from typing import Optional, Any, Union, NewType, Iterator

from stream2py.utility.typing_hints import ComparableType


class SourceReader(metaclass=ABCMeta):
    """Abstract class interface to be used by StreamBuffer.

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
    ...
    ...     @property
    ...     def info(self):
    ...         return dict(start=self.start, stop=self.stop, open_count=self.open_count)
    ...
    ...     def key(self, data):
    ...         return int(data[1:])
    ...
    >>> source_reader = SimpleCounterString(start=0, stop=10)
    >>> source_reader.open()
    >>> source_reader.info
    {'start': 0, 'stop': 10, 'open_count': 1}
    >>> source_reader.read()
    's0'
    >>> source_reader.close()
    >>> with source_reader:
    ...     source_reader.info
    ...     source_reader.read()
    ...     source_reader.read()
    ...     source_reader.read()
    {'start': 0, 'stop': 10, 'open_count': 2}
    's0'
    's1'
    's2'
    """

    _sleep_time_on_iter_none_s = 0.001

    def __iter__(self):
        while True:
            _next = self.read()
            if _next is not None:
                yield _next
            else:
                time.sleep(self._sleep_time_on_iter_none_s)

    def set_sleep_time_on_iter_none(self, sleep_time_s: Union[int, float] = 0.001):
        """Set the sleep time of the iter yield loop when next data item is not yet available.

        :param sleep_time_s: seconds to sleep
        """
        self._sleep_time_on_iter_none_s = sleep_time_s

    @abstractmethod
    def open(self) -> None:
        """Set up source to be read and set some source info affected by open time like the time of
        open. Will be called in StreamBuffer immediately before first read."""

    @abstractmethod
    def close(self) -> None:
        """Close and clean up source reader.
        Will be called when StreamBuffer stops or if an exception is raised during read and append
        loop.
        """

    @property
    def info(self) -> dict:
        """A dict with important source info. Default can be init_kwargs and open timestamp.

        This info will be available in BufferReader after SourceReader has opened but any changes
        made between open and close are not guaranteed to be visible. Any continuous status updates
        should be included with read data instead.

        :return: dict
        """
        return {}

    @abstractmethod
    def key(self, data: Any) -> ComparableType:
        """
        Converts data into a comparable value to sort by

        :param data: the return value of the 'read' method
        :return: ComparableType
        """
        raise NotImplementedError(
            "Implement the 'key' method to convert data into a comparable value to sort by"
        )

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

    timestamp_seconds_to_unit_conversion: Union[int, float] = 1e6  # to microseconds

    @classmethod
    def get_timestamp(cls) -> int:
        """Get timestamp of now as int microseconds

        :return: timestamp in UTC microseconds
        """
        return int(time.time() * cls.timestamp_seconds_to_unit_conversion)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    enter, exit = __enter__, __exit__

    def stream_buffer(
        self,
        maxlen: int,
        sleep_time_on_read_none_s: Optional[Union[int, float]] = None,
        auto_drop=True,
    ):
        from stream2py.stream_buffer import StreamBuffer

        return StreamBuffer(
            self,
            maxlen=maxlen,
            sleep_time_on_read_none_s=sleep_time_on_read_none_s,
            auto_drop=auto_drop,
        )


StreamItem = NewType('StreamItem', Any)


class QuickSourceReader(SourceReader):
    """
    A `SourceReader` with whose only required merthod is the read method.

    - open just sets an `open_time` attribute and a `read_idx` attribute (to 0)
    - close does nothing
    - info returns a `{`open_time`: ..., `open_instance`: ...}` dict
    - key just returns the data itself
    """

    read_idx = None
    open_time = None

    def __iter__(self) -> Iterator[StreamItem]:
        while True:
            _next = self.read()
            if self.is_valid_data(_next):
                yield _next
            else:
                self.when_no_data(_next)

    def is_valid_data(self, data: StreamItem) -> bool:
        """Bool function indicating whether the data should be released in an iteration.

        By default, all non-None data will be considered valid, but some streams
        might indicate "empty data" in a different way.
        In that case, `is_valid_data` can be used to adapt to the situation.

        This filter function is meant to indicate "empty data", or "don't yield this
        data" during iteration, but can also be used simply to filter out data that
        we don't want to release in the iteration.
        """
        return data is not None

    def when_no_data(self, _next=None):
        """Action taken when data is not valid (not yielded in iteration).
        Usually, the action is to sleep for a fixed amount of seconds to give a
        chance for the source data production to catch up, without hogging resources
        by waiting.
        The `when_no_data` can do much more though, and even use the source_reader
        instance and/or the (non valid) data itself to decide what action to take.

        For example, one may want to have when_no_data do some timing stats to decide
        on the number of seconds to stop, or send an interrupt signal if too many
        "non datas" happen in a row.
        """
        time.sleep(self._sleep_time_on_iter_none_s)

    def open(self):
        self.read_idx = 0
        self.open_time = self.get_timestamp()

    def close(self):
        """A dummy close class"""

    @property
    def info(self):
        return {
            'open_time': self.open_time,
            'open_instance': str(self.open_instance),
        }

    def key(self, data: StreamItem):
        return data
