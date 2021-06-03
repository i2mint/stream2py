__all__ = ['StreamBuffer']

import threading
import time

from stream2py.utility.locked_sorted_deque import RWLockSortedDeque
from stream2py.utility.typing_hints import Optional, Union

from stream2py import *

import logging

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
    >>> assert open1_reader1.is_same_buffer(open1_reader2) is True  # readers from the same open instance are the same
    >>> assert open1_reader1.next() != open1_reader2.next()  # item cursor position is different
    >>> stream_buffer.stop()
    >>>
    >>> with stream_buffer:
    ...     stream_buffer.source_reader_info
    ...     open2_reader1  = stream_buffer.mk_reader()
    ...     open2_reader2  = stream_buffer.mk_reader()
    ...     assert open2_reader1.is_same_buffer(open2_reader2) is True  # readers from the same open instance are the same
    ...     assert open2_reader1.is_same_buffer(open1_reader1) is False  # readers from the different open instances
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
        :param maxlen: max number of read data points to store in buffer before data starts dropping off the queue
        :param sleep_time_on_read_none_s: Seconds to sleep when reading None from source_reader. None to use defaults.
        :param auto_drop: False to stop reading when buffer is full and use StreamBuffer.drop() to manually make space.
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
        self.start_lock = (
            threading.Lock()
        )  # used to lock mk_reader while source is still starting up

    def __iter__(self):
        reader = self.mk_reader()
        yield from iter(reader)

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
        Calls source_reader.open() and then sets up source_buffer with latest source_reader.info"""
        self.source_reader.open()
        self.source_buffer = _SourceBuffer(
            source_reader_info=self.source_reader.info,
            stop_event=self._stop_event,
            key=self.source_reader.key,
            maxlen=self._maxlen,
        )


if __name__ == '__main__':
    import operator

    class TenthSecondCounter(SourceReader):
        """Example SourceReader
        Start counting when as soon as you construct"""

        def __init__(self, starting_count=0):
            self._init_kwargs = {
                k: v for k, v in locals().items() if k not in ('self', '__class__')
            }
            self.starting_count = starting_count
            self._count = 0
            self._start_time = 0

        def open(self):
            """Reset params for first read"""
            self._count = self.starting_count
            self._start_time = int(time.time() * 10)

        @property
        def info(self):
            _info = self._init_kwargs.copy()
            _info.update(name=self.__class__.__name__, bt=self._start_time * 100000)
            return _info

        def close(self):
            """Not needed but satisfies the abstract"""

        def read(self):
            next_count = self._count
            next_time = self._start_time + self._count
            now = time.time() * 10
            if now >= next_time:
                self._count += 1
                return next_time * 100000, next_count  # (timestamp_us, count)

        key = operator.itemgetter(0)  # (timestamp_us, count) -> timestamp_us

    sc = TenthSecondCounter()  # source
    sc_buf = StreamBuffer(source_reader=sc, maxlen=100)  # buffer

    # start source, print some data, and check last_item cursor is working
    sc_buf.start()  # start reader to buffer thread
    sc_reader = (
        sc_buf.mk_reader()
    )  # reader must be made after start to have data related to said start
    time.sleep(2)
    assert sc_reader.source_reader_info['bt'] != 0, sc_reader.source_reader_info
    print('data as shown is (timestamp, count) at every tenth of a second')
    while True:
        x = sc_reader.next(ignore_no_item_found=True)
        if x:
            last_read = x
            print(x)
        else:
            break
    assert sc_reader.last_item == last_read, 'last_item did not follow last next() call'

    # check range works and last_item cursor is working
    rstart = 5
    rstop = 10
    source_info = sc_reader.source_reader_info
    start_key = source_info['bt'] + 1e5 * rstart  # 5
    stop_key = source_info['bt'] + 1e5 * rstop  # 10
    range_data = sc_reader.range(start_key, stop_key)
    for expected_data, rdata in zip(range(rstart, rstop + 1), range_data):
        timestamp, data = rdata
        assert data == expected_data, 'wrong data does not match'
    assert (
        expected_data == sc_reader.last_item[1]
    ), f'last_item did not follow last range({start_key}, {stop_key}) call'
    previous_last_item = expected_data

    # check range works with step and peek, and last_item does not move with peek=True
    rstart = 10
    rstop = 15
    rstep = 2
    source_info = sc_reader.source_reader_info
    start_key = source_info['bt'] + 1e5 * rstart  # 5
    stop_key = source_info['bt'] + 1e5 * rstop  # 10
    range_data = sc_reader.range(start_key, stop_key, step=rstep, peek=True)
    for expected_data_value, rdata in zip(range(rstart, rstop + 1, rstep), range_data):
        timestamp, data = rdata
        assert data == expected_data_value, 'wrong data does not match'
    assert (
        previous_last_item == sc_reader.last_item[1]
    ), f'last_item moved but should not when peek=True'

    # stop source and check if reader see it
    sc_reader12 = sc_buf.mk_reader()  # reader1
    assert sc_reader.is_same_buffer(sc_reader12), 'first readers should be equal'
    assert (
        sc_reader.last_item != sc_reader12.last_item
    ), 'first readers should have a different last_item cursor position'
    assert sc_reader.is_stopped is False, 'Reader should see source is not stopped'
    sc_buf.stop()
    assert sc_reader.is_stopped is True, 'Reader should see source is stopped'

    # restart source and make new readers then check old reader is different from new reader
    with sc_buf:  # start and stop with a context manager

        sc_reader21 = sc_buf.mk_reader()  # reader2
        sc_reader22 = sc_buf.mk_reader()  # reader2
        assert sc_reader21.is_same_buffer(
            sc_reader22
        ), 'two new readers should be equal'
        assert not sc_reader.is_same_buffer(
            sc_reader21
        ), 'first reader should not equal new reader'
        assert (
            sc_reader.is_stopped is True
        ), 'first reader should still see a stopped source'
        assert (
            sc_reader21.is_stopped is False
        ), 'new reader should see the source is running'
        assert (
            sc_reader22.last_item == sc_reader21.last_item
        ), 'new readers should now have the same last_item cursor position'

        # print some data from old and new reader and see they are different
        time.sleep(1.5)
        print('comparing first start reader values to second start')
        while True:
            r22 = sc_reader22.next(ignore_no_item_found=True)
            r12 = sc_reader12.next(ignore_no_item_found=True)

            if r22:

                def zero_if_none(val):
                    if val is None:
                        return 0, 0
                    return val

                print(f'{r22} > {r12}, ts_diff={r22[0] - r12[0]}')
                assert r22 > zero_if_none(r12)
            else:
                break
        assert (
            sc_reader22.last_item != sc_reader21.last_item
        ), 'new readers should now have a different last_item cursor position'
