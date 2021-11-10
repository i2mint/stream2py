"""Deque sorted by a key function."""
from bisect import bisect_left, bisect_right
from collections import deque
from itertools import islice

from stream2py.utility.sorted_collection import SortedCollection


class SortedDeque(SortedCollection):
    """Deque sorted by a key function.

    Intent of SortedDeque is to efficiently search buffered data while efficiently maintaining a fixed length buffer
    that is frequently popping the head and appending to the tail.

    Overloaded SortedCollection methods __contains__, index, and count due to the lack of
    slicing in deques. Efficiency of said methods is still better than base deque.

    Added an append method for cases where the new item to insert is known to be the last.
    """

    def __init__(self, iterable=(), key=None, maxlen=None):
        SortedCollection.__init__(self, iterable, key)
        self._keys = deque(self._keys, maxlen=maxlen)
        self._items = deque(self._items, maxlen=maxlen)
        self._maxlen = maxlen

    def to_jdict(self):
        """TODO: WIP. Need to convert key function and iterable items to json friendly format"""
        return {
            'iterable': list(self._items),
            'key': self._key,
            'maxlen': self._maxlen,
        }

    @classmethod
    def from_jdict(cls, params_dict):
        return cls(**params_dict)

    def _getmaxlen(self):
        return self._maxlen

    def _setmaxlen(self, maxlen):
        if maxlen is not self._maxlen:
            self.__init__(self._items, key=self._key, maxlen=maxlen)

    def _delmaxlen(self):
        self._setmaxlen(None)

    maxlen = property(_getmaxlen, _setmaxlen, _delmaxlen, 'maxlen function')

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key, maxlen=self._maxlen)

    def clear(self):
        self.__init__([], self._key, self._maxlen)

    def copy(self):
        return self.__class__(self, self._key, self._maxlen)

    def __repr__(self):
        return '%s(%r, key=%s, maxlen=%s)' % (
            self.__class__.__name__,
            list(self._items),  # Not sure if the is the best way to do this
            getattr(self._given_key, '__name__', repr(self._given_key)),
            getattr(self._maxlen, '__name__', repr(self._maxlen)),
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key, self._maxlen)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in islice(self._items, i, j)

    def index(self, item):
        """Find the position of an item.  Raise ValueError if not found."""
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items.index(item, i, j)

    def count(self, item):
        """Return number of occurrences of item"""
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return sum(1 for chk_item in islice(self._items, i, j) if chk_item == item)

    def append(self, item):
        """Append item to the end.  Raise ValueError if item key is less than last item key"""
        k = self._key(item)
        try:
            if k <= self._keys[-1]:
                raise ValueError(
                    'Item key must be greater than last item key to append: %r' % (k,)
                )
        except IndexError as e:
            if len(self._keys) != 0:
                raise e
        self._keys.append(k)
        self._items.append(item)

    def range(self, start, stop, step=None):
        """Return list of items within start and stop key range.

        :param start: starting key
        :param stop: stopping key
        :param step:
        :return: list with items in range
        """
        i = bisect_left(self._keys, start)
        j = bisect_right(self._keys, stop)
        return self.range_by_index(i, j, step)

    def range_by_index(self, start_index, stop_index, step=None):
        """Return list of items within start and stop index range.

        :param start_index: starting index
        :param stop_index: stopping index
        :param step:
        :return: list with items in range
        """
        return list(islice(self._items, start_index, stop_index, step))

    def find_last_gt(self, k):
        """Return last item with a key > k.  Raise ValueError if not found.
        Basically a tail function with a greater than check"""
        try:
            if self._keys[-1] > k:
                return self._items[-1]
        except IndexError as e:
            if len(self._keys) != 0:
                raise e
        raise ValueError('No item found with key above: %r' % (k,))

    def drop(self, n=1):
        """Remove n items from the left

        :param n:
        :return:
        """
        for _ in range(n):
            del self._keys[0]
            del self._items[0]


# ---------------------------  Simple demo and tests  -------------------------
if __name__ == '__main__':
    # ---------------------------  Below tests are copied from SortedCollection  -------------------------

    def ve2no(f, *args):
        """Convert ValueError result to -1"""
        try:
            return f(*args)
        except ValueError:
            return -1

    def slow_index(seq, k):
        """Location of match or -1 if not found"""
        for i, item in enumerate(seq):
            if item == k:
                return i
        return -1

    def slow_find(seq, k):
        """First item with a key equal to k. -1 if not found"""
        for item in seq:
            if item == k:
                return item
        return -1

    def slow_find_le(seq, k):
        """Last item with a key less-than or equal to k."""
        for item in reversed(seq):
            if item <= k:
                return item
        return -1

    def slow_find_lt(seq, k):
        """Last item with a key less-than k."""
        for item in reversed(seq):
            if item < k:
                return item
        return -1

    def slow_find_ge(seq, k):
        """First item with a key-value greater-than or equal to k."""
        for item in seq:
            if item >= k:
                return item
        return -1

    def slow_find_gt(seq, k):
        """First item with a key-value greater-than or equal to k."""
        for item in seq:
            if item > k:
                return item
        return -1

    from random import choice

    pool = [1.5, 2, 2.0, 3, 3.0, 3.5, 4, 4.0, 4.5]
    for i in range(500):
        for n in range(6):
            s = [choice(pool) for i in range(n)]
            sc = SortedDeque(s)
            s.sort()
            for probe in pool:
                assert repr(ve2no(sc.index, probe)) == repr(slow_index(s, probe))
                assert repr(ve2no(sc.find, probe)) == repr(slow_find(s, probe))
                assert repr(ve2no(sc.find_le, probe)) == repr(slow_find_le(s, probe))
                assert repr(ve2no(sc.find_lt, probe)) == repr(slow_find_lt(s, probe))
                assert repr(ve2no(sc.find_ge, probe)) == repr(slow_find_ge(s, probe))
                assert repr(ve2no(sc.find_gt, probe)) == repr(slow_find_gt(s, probe))
            for i, item in enumerate(s):
                assert repr(item) == repr(sc[i])  # test __getitem__
                assert item in sc  # test __contains__ and __iter__
                assert s.count(item) == sc.count(item)  # test count()
            assert len(sc) == n  # test __len__
            assert list(map(repr, reversed(sc))) == list(
                map(repr, reversed(s))
            )  # test __reversed__
            assert list(sc.copy()) == list(sc)  # test copy()
            sc.clear()  # test clear()
            assert len(sc) == 0

    sd = SortedCollection('The quick Brown Fox jumped'.split(), key=str.lower)
    assert sd._keys == ['brown', 'fox', 'jumped', 'quick', 'the']
    assert sd._items == ['Brown', 'Fox', 'jumped', 'quick', 'The']
    assert sd._key == str.lower
    assert (
        repr(sd)
        == "SortedCollection(['Brown', 'Fox', 'jumped', 'quick', 'The'], key=lower)"
    )
    sd.key = str.upper
    assert sd._key == str.upper
    assert len(sd) == 5
    assert list(reversed(sd)) == ['The', 'quick', 'jumped', 'Fox', 'Brown']
    for item in sd:
        assert item in sd
    for i, item in enumerate(sd):
        assert item == sd[i]
    sd.insert('jUmPeD')
    sd.insert_right('QuIcK')
    assert sd._keys == [
        'BROWN',
        'FOX',
        'JUMPED',
        'JUMPED',
        'QUICK',
        'QUICK',
        'THE',
    ]
    assert sd._items == [
        'Brown',
        'Fox',
        'jUmPeD',
        'jumped',
        'quick',
        'QuIcK',
        'The',
    ]
    assert sd.find_le('JUMPED') == 'jumped', sd.find_le('JUMPED')
    assert sd.find_ge('JUMPED') == 'jUmPeD'
    assert sd.find_le('GOAT') == 'Fox'
    assert sd.find_ge('GOAT') == 'jUmPeD'
    assert sd.find('FOX') == 'Fox'
    assert sd[3] == 'jumped'
    assert sd[3:5] == ['jumped', 'quick']
    assert sd[-2] == 'QuIcK'
    assert sd[-4:-2] == ['jumped', 'quick']
    for i, item in enumerate(sd):
        assert sd.index(item) == i
    try:
        sd.index('xyzpdq')
    except ValueError:
        pass
    else:
        assert 0, 'Oops, failed to notify of missing value'
    sd.remove('jumped')
    assert list(sd) == ['Brown', 'Fox', 'jUmPeD', 'quick', 'QuIcK', 'The']

    # ---------------------------  Above tests are copied from SortedCollection  -------------------------
    # TODO: add test examples specific to SortedDeque
    import doctest
    from operator import itemgetter

    print(doctest.testmod())
