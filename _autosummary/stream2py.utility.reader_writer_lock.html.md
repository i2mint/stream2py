# stream2py.utility.reader_writer_lock

READER-WRITER LOCK WITH PRIORITY FOR WRITERS

### Classes

| [`RWLock`](#stream2py.utility.reader_writer_lock.RWLock)()                                       | Synchronization object used in a solution of so-called second readers-writers problem.   |
|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`RWLockTestCase`](#stream2py.utility.reader_writer_lock.RWLockTestCase)([methodName])                   |                                                                                          |
| [`Reader`](#stream2py.utility.reader_writer_lock.Reader)(buffer_, rw_lock, init_sleep_time, ...) |                                                                                          |
| [`Writer`](#stream2py.utility.reader_writer_lock.Writer)(buffer_, rw_lock, init_sleep_time, ...) |                                                                                          |

### *class* stream2py.utility.reader_writer_lock.RWLock

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Synchronization object used in a solution of so-called second
readers-writers problem. In this problem, many readers can simultaneously
access a share, and a writer has an exclusive access to this share.
Additionally, the following constraints should be met:

1. no reader should be kept waiting if the share is currently opened for
   : reading unless a writer is also waiting for the share,
2. no writer should be kept waiting for the share longer than absolutely
   : necessary.

The implementation is based on [1, secs. 4.2.2, 4.2.6, 4.2.7]
with a modification – adding an additional lock (C{self._\_readers_queue})
– in accordance with [2].

Sources:
[1] A.B. Downey: “The little book of semaphores”, Version 2.1.5, 2008
[2] P.J. Courtois, F. Heymans, D.L. Parnas:

```default
"Concurrent Control with 'Readers' and 'Writers'",
Communications of the ACM, 1971 (via [3])
```

[3] [http://en.wikipedia.org/wiki/Readers-writers_problem](http://en.wikipedia.org/wiki/Readers-writers_problem)

### *class* stream2py.utility.reader_writer_lock.RWLockTestCase(methodName='runTest')

Bases: [`TestCase`](https://docs.python.org/3/library/unittest.html#unittest.TestCase)

### *class* stream2py.utility.reader_writer_lock.Reader(buffer_, rw_lock, init_sleep_time, sleep_time)

Bases: [`Thread`](https://docs.python.org/3/library/threading.html#threading.Thread)

#### buffer_read

a copy of a the buffer read while in critical section

#### entry_time

Time of entry to the critical section

#### exit_time

Time of exit from the critical section

#### run()

Method representing the thread’s activity.

You may override this method in a subclass. The standard run() method
invokes the callable object passed to the object’s constructor as the
target argument, if any, with sequential and keyword arguments taken
from the args and kwargs arguments, respectively.

### *class* stream2py.utility.reader_writer_lock.Writer(buffer_, rw_lock, init_sleep_time, sleep_time, to_write)

Bases: [`Thread`](https://docs.python.org/3/library/threading.html#threading.Thread)

#### entry_time

Time of entry to the critical section

#### exit_time

Time of exit from the critical section

#### run()

Method representing the thread’s activity.

You may override this method in a subclass. The standard run() method
invokes the callable object passed to the object’s constructor as the
target argument, if any, with sequential and keyword arguments taken
from the args and kwargs arguments, respectively.
