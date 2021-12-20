"""
A StreamBuffer has 2 jobs: First, it manages the open, read, and close of a SourceReader
and puts read data onto a thread-safe buffer.
Second, it is a factory of BufferReaders instances for multiple consumers.
"""
__all__ = ['StreamBuffer']

import logging
import threading
import time
from typing import Optional, Union

from stream2py import BufferReader, SourceReader
from stream2py.utility.locked_sorted_deque import RWLockSortedDeque

logger = logging.getLogger(__name__)

DFLT_SLEEP_TIME_ON_READ_NONE_S = 0.3


class _SourceBuffer:
    def __init__(
        self,
        source_reader_info: dict,
        stop_event: threading.Event,
        *,
        key=None,
        maxlen: int = 10000,
    ):
        """StreamBuffer helper class
        Thread safe buffer for reading and writing data items

        source_name should default to source class name
        source_info should default to args for constructing source class
        an audio source info should have info about sample rates, bit depth, etc.
        reader should get both source_name and source_info
        """
        self._stop_event = stop_event
        self._buffer = RWLockSortedDeque([], key=key, maxlen=maxlen)
        self._source_reader_info = source_reader_info

    def __len__(self):
        return len(self._buffer)

    @property
    def key(self):
        return self._buffer.key

    @property
    def source_reader_info(self):
        return self._source_reader_info

    def append(self, item):
        with self._buffer.writer_lock() as writer:
            writer.append(item)

    def drop(self, n=1):
        with self._buffer.writer_lock() as writer:
            writer.drop(n)

    def mk_reader(self):
        return BufferReader(
            buffer=self._buffer,
            source_reader_info=self._source_reader_info,
            stop_event=self._stop_event,
        )


class StreamBuffer:
    """Handles starting and stopping SourceReader and making BufferReaders

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
    """

    def __init__(
        self,
        source_reader: SourceReader,
        *,
        maxlen: int,
        sleep_time_on_read_none_s: Optional[Union[int, float]] = None,
        auto_drop=True,
    ):
        """
        TODO: option to auto restart source on read exception

        :param source_reader: instance of a SourceReader subclass
        :param maxlen: max number of read data points to store in buffer before data starts dropping
            off the queue
        :param sleep_time_on_read_none_s: Seconds to sleep when reading None from source_reader.
            None to use defaults.
        :param auto_drop: False to stop reading when buffer is full and use StreamBuffer.drop() to
            manually make space.
        """
        assert isinstance(
            source_reader, SourceReader
        ), 'source_reader is not a subclass of SourceReader'
        self.source_reader = source_reader
        self._maxlen = maxlen
        self.auto_drop = auto_drop
        if isinstance(sleep_time_on_read_none_s, (int, float)):
            self._sleep_time_on_read_none_s = sleep_time_on_read_none_s
        elif isinstance(source_reader.sleep_time_on_read_none_s, (int, float)):
            self._sleep_time_on_read_none_s = source_reader.sleep_time_on_read_none_s
        else:
            self._sleep_time_on_read_none_s = DFLT_SLEEP_TIME_ON_READ_NONE_S  # default

        self._stop_event = None
        self.source_buffer = None
        # start_lock used to lock mk_reader while source is still starting up
        self.start_lock = threading.Lock()
        self._next_reader = None
        self._read_to_buffer_thread = None

    def __iter__(self):
        reader = self.mk_reader()
        yield from iter(reader)

    def __next__(self):
        if self._next_reader is None:
            self._next_reader = self.mk_reader()
        return next(self._next_reader)

    def drop(self, n=1):
        """Manually drop items from buffer when auto_drop is False

        :param n: number of items to drop from the left side
        :return:
        """
        if self.auto_drop is True:
            raise RuntimeError(
                'auto_drop must be False to manually drop items from buffer'
            )
        self.source_buffer.drop(n)

    def start(self):
        """Open and start reading from source_reader into buffer"""
        with self.start_lock:
            if self._stop_event and not self._stop_event.is_set():
                self.stop()
            self._set_read_to_buffer_thread_and_source_buffer()
            self._open()
            self._read_to_buffer_thread.start()

    def stop(self):
        """Stop reading and close source_reader"""
        self._stop_event.set()
        time.sleep(1)
        self._next_reader = None

    def mk_reader(self) -> BufferReader:
        """ Makes a BufferReader instance for the currently running  StreamBuffer.
        Reader must be made after start() to have data from said start.

        :return: BufferReader instance
        """
        with self.start_lock:
            if not isinstance(self.source_buffer, _SourceBuffer):
                raise RuntimeError('Readers should be made after starting')
            return self.source_buffer.mk_reader()

    @property
    def source_reader_info(self) -> Optional[dict]:
        """A dict with important source info set by SourceReader.

        :return: dict or None
        """
        if self.source_buffer:
            return self.source_buffer.source_reader_info
        return None

    @property
    def is_running(self) -> bool:
        """Checks if stop event has been set.

        :return: bool
        """
        with self.start_lock:
            return self._stop_event is not None and not self._stop_event.is_set()

    @property
    def join(self):
        return self._read_to_buffer_thread.join

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    enter, exit = __enter__, __exit__

    def _run(self):
        try:
            while not self._stop_event.is_set():
                # check if buffer is full and skip read or append
                if self.auto_drop is True or len(self.source_buffer) < self._maxlen:
                    data = self.source_reader.read()
                else:
                    data = None

                if data is not None:
                    self.source_buffer.append(data)
                else:
                    time.sleep(self._sleep_time_on_read_none_s)
        finally:
            if not self._stop_event.is_set():
                self._stop_event.set()
            try:
                self.source_reader.close()
            except Exception as e:
                logger.error(e)

    def _set_read_to_buffer_thread_and_source_buffer(self):
        """Initialize source and buffer
        Makes a new run thread, and stop event that is unique to this run session"""
        if self._stop_event and not self._stop_event.is_set():
            self.stop()
        self.source_buffer = None
        self._read_to_buffer_thread = threading.Thread(target=self._run, daemon=True)
        self._stop_event = threading.Event()

    def _open(self):
        """First thing called after start/run
        Calls source_reader.open() and then sets up source_buffer with latest
        source_reader.info"""
        self.source_reader.open()
        self.source_buffer = _SourceBuffer(
            source_reader_info=self.source_reader.info,
            stop_event=self._stop_event,
            key=self.source_reader.key,
            maxlen=self._maxlen,
        )

    # def _mk_contextualized_iterator(self):
    #     """Return next item (entering the context beforehand, if not running).
    #     This method is meant to be called under context so that a clean exit is assured.
    #     """
    #     if not self.is_running:
    #         self.__enter__()
    #     return self.__next__()

    def __call__(self):
        """Return next item (entering the context beforehand, if not running).
        This method is meant to be called under context so that a clean exit is assured. """
        return next(self)
        # return self._mk_contextualized_iterator()

    def __del__(self):
        try:
            self.__exit__(None, None, None)
        except Exception:
            pass
