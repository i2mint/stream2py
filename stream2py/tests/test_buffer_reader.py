from itertools import count

from stream2py.buffer_reader import BufferReader
from stream2py.tests.utils_for_testing import SimpleSourceReader


def test_inject_buffer_reader():
    """Test injecting custom buffer reader"""
    test_msg = 'test_msg'

    class TestBufferReader(BufferReader):
        def custom_function(self):
            return test_msg

    class TestSourceReader(SimpleSourceReader):
        buffer_reader_class = TestBufferReader

    source = TestSourceReader(count())
    with source.stream_buffer(10) as buffer:
        reader = buffer.mk_reader()
        assert isinstance(reader, TestBufferReader)
        assert reader.custom_function() is test_msg
