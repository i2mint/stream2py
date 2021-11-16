"""Utils for testing"""
import operator
import random
import time

from typing import Iterator
from itertools import tee
import itertools
from functools import wraps

from stream2py import SourceReader
from stream2py.utility.typing_hints import ComparableType


def consume_iterator_and_return_last_element(iterator, default=None):
    x = default
    for x in iterator:
        pass
    return x  # return last element


@wraps(itertools.islice)
def get_slice(*args, **kwargs):
    return list(itertools.islice(*args, **kwargs))


def pairwise(iterable):
    """
    >>> list(pairwise('ABCD'))
    [('A', 'B'), ('B', 'C'), ('C', 'D')]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


# ---------------------------------------------------------------------------------------
# Online (streaming) testing of monotonicity
def is_strictly_increasing(iterable):
    return all(x < y for x, y in pairwise(iterable))


def is_strictly_decreasing(iterable):
    return all(x > y for x, y in pairwise(iterable))


def is_non_increasing(iterable):
    """
    >>> is_non_increasing([9, 2, 2, 1])
    True
    >>> is_non_increasing([9, 2, 2, 1, 6])
    False
    >>> is_non_increasing([2, 2, 2])
    True
    >>> is_non_increasing([])
    True
    """
    return all(x >= y for x, y in pairwise(iterable))


def is_non_decreasing(iterable):
    """
    >>> is_non_decreasing([1, 2, 2, 9])
    True
    >>> is_non_decreasing([1, 2, 2, 9, 6])
    False
    >>> is_non_decreasing([2, 2, 2])
    True
    >>> is_non_decreasing([])
    True
    """
    return all(x <= y for x, y in pairwise(iterable))


# More intuitive aliases
is_increasing = is_non_decreasing
is_decreasing = is_non_increasing
no_more_data = type('NoMore_data', (), {})()


def is_monotonic(iterable):
    """True if and only if iterable is non-increasing or non-decreasing

    >>> is_monotonic([1, 2, 2, 9])
    True
    >>> is_monotonic([1, 2, 2, 9, 6])
    False
    >>> is_monotonic([9, 2, 2, 1])
    True
    >>> is_monotonic([9, 2, 2, 1, 6])
    False
    >>> is_monotonic([2, 2, 2])
    True
    >>> is_monotonic([])
    True
    """
    pairs = pairwise(iterable)
    # TODO: Might be able to do something cleaner than while loop with itertools?
    while True:
        # The (no_more_data, no_more_data) is to signal end of iterator
        x, y = next(pairs, (no_more_data, no_more_data))
        if x is no_more_data:
            # Reaching here means that iterator was empty or all elements were equal
            # In any case, the iterable is monotonic, so:
            return True
        elif x != y:
            break  # you found your first non-trivial case, now the work begins

    if x < y:  # if the first (different) pairs were increasing
        # all the others must be non-decreasing
        return all(x <= y for x, y in pairs)
    else:  # if the first (different) pairs were decreasing]
        # all the others must be non-increasing
        return all(x >= y for x, y in pairs)


# ---------------------------------------------------------------------------------------
# A few source readers
from typing import Iterator, Any


class SimpleSourceReader(SourceReader):
    """A source reader that only requires an iterable"""

    _current_index = 0

    def __init__(self, data):
        """Instantiates the reader and creates an iterator if necessary"""
        if not isinstance(data, Iterator):
            data = iter(data)
        self._data = data

    def __iter__(self):
        while True:
            yield self.read()

    def open(self) -> None:
        return None

    # separate indexing concern (could be counter, could be time.time())
    def read(self):
        output = self._current_index, next(self._data)
        self._current_index += 1
        return output

    def close(self):
        return None

    @property
    def info(self) -> dict:
        return {}

    def key(self, data: Any) -> ComparableType:
        return data[0]

    def val(self, data: Any):
        return data[1]


class RandomFloatSource(SourceReader):
    """
    A simple example of source reader based on a random float generator
    """

    def __init__(self, seed=1):
        random.seed(seed)
        self.seed = seed
        self.open_count = 0

    def open(self):
        self.open_count += 1
        self.random_gen = iter(random.random, 2)

    def read(self):
        value = next(self.random_gen)
        return value

    def close(self):
        del self.random_gen

    @property
    def info(self):
        return dict(seed=self.seed, open_count=self.open_count)

    def key(self, data):
        return data


class TenthSecondCounter(SourceReader):
    """
    Example SourceReader
    Start counting when as soon as you construct
    """

    def __init__(self, starting_count=0):
        self._init_kwargs = {
            k: v for k, v in locals().items() if k not in ('self', '__class__')
        }
        self.starting_count = starting_count
        self._count = 0
        self._start_time = 0
        self.open_count = 0

    def open(self):
        """Reset params for first read"""
        self.open_count += 1
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
        return None

    key = operator.itemgetter(0)  # (timestamp_us, count) -> timestamp_us
