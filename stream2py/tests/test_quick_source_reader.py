"""Tests for QuickSourceReader"""
import pytest
from stream2py.source_reader import QuickSourceReader


class SimpleQuickReader(QuickSourceReader):
    """A simple QuickSourceReader that reads from a list"""

    def __init__(self, data):
        self.data = iter(data)

    def read(self):
        try:
            return next(self.data)
        except StopIteration:
            return None


def test_quick_source_reader_basic():
    """Test basic QuickSourceReader functionality"""
    reader = SimpleQuickReader([1, 2, 3, 4, 5])

    # Check that open sets attributes
    assert reader.open_time is None
    assert reader.read_idx is None

    reader.open()
    assert reader.open_time is not None
    assert reader.read_idx == 0

    # Check that read works
    assert reader.read() == 1
    assert reader.read() == 2

    # Check close
    reader.close()  # Should do nothing but not raise


def test_quick_source_reader_context_manager():
    """Test QuickSourceReader as context manager"""
    reader = SimpleQuickReader([1, 2, 3])

    with reader:
        assert reader.open_time is not None
        assert reader.read() == 1
        assert reader.read() == 2


def test_quick_source_reader_info():
    """Test QuickSourceReader info property"""
    reader = SimpleQuickReader([1, 2, 3])
    reader.open()

    info = reader.info
    assert 'open_time' in info
    assert 'open_instance' in info
    assert info['open_time'] == reader.open_time


def test_quick_source_reader_key():
    """Test QuickSourceReader key method (default returns data itself)"""
    reader = SimpleQuickReader([1, 2, 3])

    # Default key should return the data itself
    assert reader.key(5) == 5
    assert reader.key('test') == 'test'


def test_quick_source_reader_iteration():
    """Test QuickSourceReader iteration behavior"""
    reader = SimpleQuickReader([1, 2, 3])
    reader.open()

    # Iteration should yield valid data and skip None
    results = []
    for i, item in enumerate(reader):
        results.append(item)
        if i >= 2:  # Get first 3 items
            break

    assert results == [1, 2, 3]


def test_quick_source_reader_custom_is_valid_data():
    """Test QuickSourceReader with custom is_valid_data"""

    class FilteringQuickReader(QuickSourceReader):
        def __init__(self, data):
            self.data = iter(data)

        def read(self):
            try:
                return next(self.data)
            except StopIteration:
                return None

        def is_valid_data(self, data):
            # Only consider even numbers as valid
            return data is not None and data % 2 == 0

    reader = FilteringQuickReader([1, 2, 3, 4, 5, 6])
    reader.open()

    # Iteration should only yield even numbers
    results = []
    for i, item in enumerate(reader):
        results.append(item)
        if i >= 2:  # Get first 3 valid items
            break

    assert results == [2, 4, 6]
