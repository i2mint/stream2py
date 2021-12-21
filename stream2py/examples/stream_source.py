"""Examples"""
from stream2py.stream_source import StreamSource


class SimpleCounterString(StreamSource):
    """Count in range returning a string formatted as f's{count}'"""

    def __init__(self, *, start=0, stop=1):
        StreamSource.__init__(self)
        assert start < stop
        self.start = start
        self.stop = stop
        self.range_iterator = None
        self.open_count = 0

    def open(self):
        self.open_count += 1
        self.range_iterator = iter(range(self.start, self.stop))

    def read(self):
        value = next(self.range_iterator, None)
        if value is not None:
            return f's{value}'
        else:
            return None

    def close(self):
        del self.range_iterator
        self.range_iterator = None

    @property
    def info(self):
        return dict(start=self.start, stop=self.stop, open_count=self.open_count)

    def key(self, data):
        return int(data[1:])
