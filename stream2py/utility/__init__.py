"""Low-level building blocks used by stream2py's buffers and readers.

These are general-purpose data structures and synchronization primitives that do not
depend on stream2py objects themselves:

- :mod:`stream2py.utility.sorted_collection` -- a sorted sequence with bisect-based lookup
- :mod:`stream2py.utility.sorted_deque` -- a bounded sorted deque
- :mod:`stream2py.utility.locked_sorted_deque` -- a sorted deque guarded by a lock
- :mod:`stream2py.utility.reader_writer_lock` -- a multi-reader/single-writer lock
- :mod:`stream2py.utility.typing_hints` -- shared type aliases
"""
