__all__ = ['SourceReader']


from abc import ABCMeta, abstractmethod
import time

from stream2py.utility.typing_hints import Optional, Union, ComparableType, Any, Callable


class SourceReader(metaclass=ABCMeta):
    """Abstract class interface to be used by StreamBuffer."""

    @abstractmethod
    def open(self) -> None:
        """Set up source to be read and set some source info affected by open time like the time of open.
        Will be called in StreamBuffer immediately before first read."""

    @abstractmethod
    def read(self) -> Optional[Any]:
        """Must return data that is sortable with 'key' method or None. Data that is not readily sortable such as
        ordered words of a sentence can be wrapped in a tuple (word_index, word).

        :return: data or None
        """
        raise NotImplementedError("Implement the 'read' method returning data that is sortable with 'key' method")

    @abstractmethod
    def close(self) -> None:
        """Close and clean up source reader.
        Will be called when StreamBuffer stops or if an exception is raised during read and append loop.
        """

    @property
    @abstractmethod
    def info(self) -> dict:
        """A dict with important source info. Default can be init_kwargs and open timestamp.

        This info will be available in BufferReader after SourceReader has opened but any changes made between open and
        close are not guaranteed to be visible. Any continuous status updates should be included with read data instead.

        :return: dict
        """
        raise NotImplementedError("no source info set")

    @abstractmethod
    def key(self, data: Any) -> ComparableType:
        """
        Converts data into a comparable value to sort by

        :param data: the return value of the 'read' method
        :return: ComparableType
        """
        raise NotImplementedError("Implement the 'key' method to convert data into a comparable value to sort by")

    @property
    def sleep_time_on_read_none_s(self) -> Optional[Union[int, float]]:
        """Sets default sleep time for StreamBuffer when it reads None from SourceReader.
        Useful when you know the period between data points.

        For example if data only comes once every 10 seconds,
        it would be inefficient to try and read again every 0.1 seconds and get None up to 100 times
        but every 10 seconds or even 1 second would be much more reasonable depending on the use case.
        Not necessary if read is a blocking function that always returns a data point.

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

    def __enter__(self) -> Callable[[], Optional[Any]]:
        self.open()
        return self.read

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
