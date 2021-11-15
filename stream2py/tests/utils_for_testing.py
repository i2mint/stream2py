"""Utils for testing"""

from itertools import tee
import itertools
from functools import wraps


@wraps(itertools.islice)
def get_slice(*args, **kwargs):
    return list(itertools.islice(*args, **kwargs))


def pairwise(iterable):
    """
    >>> list(pairwise('ABCD')) == [('A', 'B'), ('B', 'C'), ('C', 'D')]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


# ---------------------------------------------------------------------------------------
# Online (streaming) testing of monotonicity
def is_strictly_increasing(iterable):
    return all(x < y for x, y in pairwise(iterable))


def is_strictly_decreasing(iterable):
    return all(x > y for x, y in pairwise(iterable))


def is_non_increasing(iterable):
    """
    >>> is_non_increasing([9, 2, 2, 1])
    True
    >>> is_non_increasing([9, 2, 2, 1, 6])
    False
    >>> is_non_increasing([2, 2, 2])
    True
    >>> is_non_increasing([])
    True
    """
    return all(x >= y for x, y in pairwise(iterable))

def is_non_decreasing(iterable):
    """
    >>> is_non_decreasing([1, 2, 2, 9])
    True
    >>> is_non_decreasing([1, 2, 2, 9, 6])
    False
    >>> is_non_decreasing([2, 2, 2])
    True
    >>> is_non_decreasing([])
    True
    """
    return all(x <= y for x, y in pairwise(iterable))

# More intuitive aliases
is_increasing = is_non_decreasing
is_decreasing = is_non_increasing

def is_monotonic(iterable):
    """True if and only if iterable is non-increasing or non-decreasing

    >>> is_monotonic([1, 2, 2, 9])
    True
    >>> is_monotonic([1, 2, 2, 9, 6])
    False
    >>> is_monotonic([9, 2, 2, 1])
    True
    >>> is_monotonic([9, 2, 2, 1, 6])
    False
    >>> is_monotonic([2, 2, 2])
    True
    >>> is_monotonic([])
    True
    """
    pairs = pairwise(iterable)
    while True:
        x, y = next(pairs)
        if x != y:
            break
    if x < y:  # if the first (different) pairs were increasing
        # all the others must be non-decreasing
        return all(x <= y for x, y in pairs)
    else:  # if the first (different) pairs were decreasing]
        # all the others must be non-increasing
        return all(x >= y for x, y in pairs)


# ---------------------------------------------------------------------------------------
