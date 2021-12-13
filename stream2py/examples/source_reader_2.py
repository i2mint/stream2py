"""Examples"""
from stream2py import SourceReader2


class SimpleCounterString(SourceReader2):
    """Count in range returning a string formatted as f's{count}'"""

    def __init__(self, begin, end):
        assert begin < end
        self.begin = begin
        self.end = end
        self.range_iterator = None
        self.open_count = 0

    def open(self):
        self.open_count += 1
        self.range_iterator = iter(range(self.begin, self.end))

    def get(self):
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
