"""Tests for ``SortedCollection`` and ``SortedDeque`` (search, ordering, copy/pickle, error paths)."""

import pickle

import pytest

from stream2py.utility.sorted_collection import SortedCollection
from stream2py.utility.sorted_deque import SortedDeque

KINDS = [SortedCollection, SortedDeque]


def _pair(n):
    return (n, f"v{n}")


@pytest.fixture(params=KINDS)
def cls(request):
    return request.param


def test_construction_sorts_by_key(cls):
    c = cls([(3, "c"), (1, "a"), (2, "b")], key=lambda p: p[0])
    assert list(c) == [(1, "a"), (2, "b"), (3, "c")]
    assert len(c) == 3 and c[0] == (1, "a") and list(reversed(c))[0] == (3, "c")


def test_insert_left_vs_right_for_equal_keys(cls):
    if cls is SortedDeque:
        pytest.skip("a SortedDeque inserts by append; covered separately")
    c = cls([("a", 1)], key=lambda p: p[1])
    c.insert(("b", 1))
    c.insert_right(("c", 1))
    assert [x[0] for x in c] == ["b", "a", "c"]


def test_contains_index_count_and_remove(cls):
    c = cls([(1, "a"), (2, "b"), (2, "b"), (3, "c")], key=lambda p: p[0])
    assert (2, "b") in c and (2, "x") not in c and (9, "z") not in c
    assert c.index((2, "b")) == 1
    assert c.count((2, "b")) == 2 and c.count((9, "z")) == 0
    with pytest.raises(ValueError):
        c.index((2, "x"))
    if cls is SortedCollection:
        c.remove((2, "b"))
        assert c.count((2, "b")) == 1
        with pytest.raises(ValueError):
            c.remove((9, "z"))


def test_find_family(cls):
    c = cls([_pair(n) for n in (10, 20, 30)], key=lambda p: p[0])
    assert c.find(20) == (20, "v20")
    assert c.find_le(25) == (20, "v20") and c.find_le(20) == (20, "v20")
    assert c.find_lt(20) == (10, "v10")
    assert c.find_ge(25) == (30, "v30") and c.find_ge(20) == (20, "v20")
    assert c.find_gt(20) == (30, "v30")
    for call, k in [
        (c.find, 25),
        (c.find_le, 5),
        (c.find_lt, 10),
        (c.find_ge, 31),
        (c.find_gt, 30),
    ]:
        with pytest.raises(ValueError):
            call(k)


def test_key_property_set_rebuilds_and_del_restores_identity(cls):
    c = cls([(2, 1), (1, 2)], key=lambda p: p[0])
    assert list(c) == [(1, 2), (2, 1)]
    c.key = lambda p: p[1]
    assert list(c) == [(2, 1), (1, 2)]
    del c.key
    assert list(c) == [(1, 2), (2, 1)]


def test_clear_and_copy_are_independent(cls):
    c = cls([3, 1, 2])
    twin = c.copy()
    c.clear()
    assert len(c) == 0 and list(twin) == [1, 2, 3]
    assert isinstance(twin, cls)


def test_repr_names_the_class_and_key(cls):
    def by_first(p):
        return p[0]

    assert "by_first" in repr(cls([(1, 2)], key=by_first))
    assert repr(cls([1])).startswith(cls.__name__)


def test_pickle_round_trip_with_a_named_key(cls):
    c = cls([3, 1, 2], key=abs)
    assert list(pickle.loads(pickle.dumps(c))) == [1, 2, 3]


# --- SortedDeque specifics ---------------------------------------------------------------


def test_maxlen_property_evicts_from_the_left():
    d = SortedDeque([1, 2, 3], maxlen=3)
    d.append(4)
    assert list(d) == [2, 3, 4] and d.maxlen == 3


def test_append_requires_a_strictly_greater_key():
    d = SortedDeque([1, 2])
    with pytest.raises(ValueError, match="greater than last"):
        d.append(2)
    d.append(3)
    assert list(d) == [1, 2, 3]
    empty = SortedDeque()
    empty.append(1)
    assert list(empty) == [1]


def test_range_and_range_by_index():
    d = SortedDeque([_pair(n) for n in range(0, 50, 10)], key=lambda p: p[0])
    assert [p[0] for p in d.range(10, 30)] == [10, 20, 30]
    assert [p[0] for p in d.range(10, 40, 2)] == [10, 30]
    assert d.range(100, 200) == []
    assert [p[0] for p in d.range_by_index(1, 3)] == [10, 20]


def test_find_last_gt_and_drop():
    d = SortedDeque([1, 2, 3])
    assert d.find_last_gt(2) == 3
    with pytest.raises(ValueError):
        d.find_last_gt(3)
    with pytest.raises(ValueError):
        SortedDeque().find_last_gt(0)
    d.drop()
    assert list(d) == [2, 3]
    d.drop(2)
    assert len(d) == 0


def test_jdict_round_trip():
    d = SortedDeque([3, 1, 2], maxlen=5)
    params = d.to_jdict()
    assert params["maxlen"] == 5 and params["iterable"] == [1, 2, 3]
    assert list(SortedDeque.from_jdict(params)) == [1, 2, 3]


def test_deque_copy_keeps_maxlen():
    d = SortedDeque([1, 2], maxlen=2)
    twin = d.copy()
    twin.append(3)
    assert list(twin) == [2, 3] and list(d) == [1, 2]


def test_insert_into_a_full_deque_raises_and_leaves_it_unchanged():
    """Pins current behaviour: ``insert`` (unlike ``append``) does not evict at ``maxlen``."""
    d = SortedDeque([1, 2, 3], maxlen=3)
    with pytest.raises(IndexError):
        d.insert(0)
    assert list(d) == [1, 2, 3]
    d2 = SortedDeque([1, 3], maxlen=5)
    d2.insert(2)
    assert list(d2) == [1, 2, 3]
