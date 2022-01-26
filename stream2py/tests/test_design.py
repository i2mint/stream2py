"""Interface definition based on Stream2py design notes
https://github.com/i2mint/stream2py/wiki/Stream2py-design-notes

TODO: Separate protocols and reorganize tests as pytests
"""
from typing import Iterator, Callable, Protocol

CursorFunc = Callable
# example of a CursorFunc: iter([1,2,3]).__next__


class Reader(Protocol):
    def __getitem__(self, item):
        """Sliceable and single point"""

    def __iter__(self):
        """Iterable"""

    def __next__(self):
        """Iterator"""

    def __call__(self, *args, **kwargs):
        """CursorFunc"""
        return self.__next__()

    def __enter__(self):
        """Starts source and populate buffer"""
        self.enter()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """Stop source and buffer when all readers are stopped"""
        return self.exit(exc_type, exc_val, exc_tb)

    def __del__(self):
        """Ensure proper closing and clean up when instance will be garbage collected

        :return:
        """
        self.__exit__()

    def exit(self, exc_type=None, exc_val=None, exc_tb=None):
        pass

    def enter(self):
        pass


class Buffer(Protocol):
    pass


class Source(Protocol):
    def open_reader(self, **reader_kw) -> Reader:
        """Make reader for source buffer data.
        Can be used as a context manager similar to builtin open()

        :param reader_kw:
        :return:
        """

    def config_buffer(self, **buffer_kw):
        pass

    @property
    def opened(self) -> bool:
        """Source is opened and running either by enter(), context manager, or open_reader()

        :return: 
        """
        return False

    def exit(self, exc_type=None, exc_val=None, exc_tb=None):
        pass

    def enter(self):
        pass

    def __enter__(self):
        self.enter()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        return self.exit(exc_type, exc_val, exc_tb)

    def __del__(self):
        """Ensure proper closing and clean up when instance will be garbage collected

        :return:
        """
        self.__exit__()


# Multireader context management
#   example: SlabsIter


# Source Basic Interface
########################
s = {}  # kwargs for initializing source

# Opening and Closing Source
# ==========================

# source as context manager
src_cm = Source(**s)
assert not src_cm.opened
with src_cm:
    assert src_cm.opened
    reader_of_src_cm = src_cm.open_reader()
assert not src_cm.opened
del src_cm

# open_reader as context manager
src_or_as_cm = Source(**s)
assert not src_or_as_cm.opened
with src_or_as_cm.open_reader() as reader_of_src_or_as_cm:
    assert src_or_as_cm.opened
assert not src_or_as_cm.opened
del src_or_as_cm

# open_reader
src_or = Source(**s)
assert not src_or.opened
reader_of_src_or1 = src_or.open_reader()
reader_of_src_or2 = src_or.open_reader()
assert src_or.opened
reader_of_src_or1.exit()
assert src_or.opened  # remain open while reader has not closed
reader_of_src_or2.exit()
assert not src_or.opened  # close if all readers have exited
del src_or

src_or = Source(**s)
assert not src_or.opened
reader_of_src_or1 = src_or.open_reader()
reader_of_src_or2 = src_or.open_reader()
assert src_or.opened
src_or.exit()  # exit source to close source and all readers
assert not src_or.opened
del src_or


# Reader Interface
##################


def mk_data_gen_for_source():
    for i in range(10):
        start = i * 10
        end = start + 10
        yield dict(bt=start, tt=end, data=list(range(start, end)))


src = Source(**s)
reader = src.open_reader()

# query data items by bt only inclusive
assert reader[1:11] == [dict(bt=10, tt=20, data=list(range(10, 20)))]

# query merges joinable continuous data
assert reader[1:21] == dict(bt=1, tt=21, data=list(range(1, 21)))

# query data items by bt/tt inclusive
assert reader[1:11] == []
assert reader[1:21] == [dict(bt=10, tt=20, data=list(range(10, 20)))]
