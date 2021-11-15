from stream2py.source_reader import SourceReader
import pytest
import random
import time
import operator


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


# note that the class to test must have the additional attribute open_count for the test to pass
@pytest.mark.parametrize(
    'n_reads,n_open_close,source_reader_class,class_params',
    [
        (1, 10, RandomFloatSource, {'seed': 1}),
        (5, 100, RandomFloatSource, {'seed': 1}),
        (10, 10, RandomFloatSource, {'seed': 1}),
        (10, 10, TenthSecondCounter, dict()),
    ],
)
def test_source_readers_open_close(
    n_reads, n_open_close, source_reader_class, class_params
):
    sc = source_reader_class(**class_params)
    for open_number in range(n_open_close):
        with sc:
            # check that the count increments
            assert sc.open_count == open_number + 1
            random_numbers = [sc.read() for i in range(n_reads)]
            # check that each read yielding one float
            assert len(random_numbers) == n_reads
        # check that after closing, the count of open did not increment
        assert sc.open_count == open_number + 1
        # checking access to the info
        assert isinstance(sc.info, dict)
