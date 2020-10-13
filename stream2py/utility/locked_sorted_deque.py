from contextlib import contextmanager

from stream2py.utility.reader_writer_lock import RWLock
from stream2py.utility.sorted_deque import SortedDeque


class RWLockSortedDeque(RWLock):
    """
    >>> import operator
    >>> locked_deque = RWLockSortedDeque(
    ...     ((('plc', int(i // 10 * 10), i), f'data_{i}') for i in range(100)),
    ...     key=operator.itemgetter(0),
    ...     maxlen=100000)
    >>> new_item = (('plc', 100000, 100000), 'new data')
    >>> with locked_deque.writer_lock() as writer:
    ...     writer.append(new_item)
    >>> with locked_deque.reader_lock() as reader:
    ...     print(reader.find_gt(('plc', 90, 91)))
    ...
    (('plc', 90, 92), 'data_92')
    >>> with locked_deque.reader_lock() as reader:
    ...     print(reader.find_gt(('plc', 90, 99)))
    ...
    (('plc', 100000, 100000), 'new data')
    """

    def __init__(self, iterable=(), *, key=None, maxlen=None):
        RWLock.__init__(self)
        self._sorted_deque = SortedDeque(iterable, key, maxlen)

    def __len__(self):
        return len(self._sorted_deque)

    @property
    def key(self):
        return self._sorted_deque.key

    @contextmanager
    def reader_lock(self):
        try:
            self.reader_acquire()
            yield self._sorted_deque
        finally:
            self.reader_release()

    @contextmanager
    def writer_lock(self):
        try:
            self.writer_acquire()
            yield self._sorted_deque
        finally:
            self.writer_release()
