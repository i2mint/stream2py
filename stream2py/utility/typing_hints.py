from abc import ABCMeta, abstractmethod
from typing import *


# ComparableType ##################################################################################
# Comparable type that works well enough to catch the most common errors
# From: https://www.python.org/dev/peps/pep-0484/#type-variables-with-an-upper-bound
# And From: https://stackoverflow.com/a/37669538/7643974


class Comparable(metaclass=ABCMeta):
    """Comparable is any object that implements "less than" and "greater than" comparisons"""

    @abstractmethod
    def __lt__(self, other: Any) -> bool:
        ...

    @abstractmethod
    def __gt__(self, other: Any) -> bool:
        ...


ComparableType = TypeVar('ComparableType', bound=Comparable)

if __name__ == '__main__':
    """Tests for checking value types against typing hints to ensure hints are correctly formatted"""
    from typeguard import check_type

    def check_type_same(value, value_type, memo=None):
        try:
            check_type(str(value_type), value, value_type, memo)
        except TypeError as e:
            msg = str(e)
            if (
                msg.startswith('type of ')
                and msg.endswith(' instead')
                and ' must be ' in msg
                and '; got ' in msg
            ):
                # fits template "type of {name} must be {expected_type}; got {actual_type} instead"
                # TODO: use regex
                return False
            raise e
        return True

    def check_type_different(value, value_type, memo=None):
        return check_type_same(value, value_type, memo) is False

    # Basic Tests #################################################################################
    assert check_type_same(1, int)
    assert check_type_different(1, str)

    assert check_type_same([1234], List[int])
    assert check_type_different(['1234'], List[int])

    assert check_type_same([{'x': 3}, {'y': 7}], List[Dict[str, int]])
    assert check_type_different([{'x': 3}, {'y': 7.5}], List[Dict[str, int]])

    # Custom Tests ################################################################################
    # TODO: look for a way to test TypeVars like ComparableType where the metaclass is not actually
    #   implemented but merely describing the expected interface.
    class _Memo:
        def __init__(self):
            self.typevars = {}  # type: Dict[Any, type]

    _memo = _Memo()

    assert hasattr(1, '__lt__')
    assert hasattr('a', '__lt__')
    assert check_type_same(1, ComparableType, _memo)  # doesn't work
    assert check_type_same('a', ComparableType, _memo)  # doesn't work
    assert check_type_different({}, ComparableType, _memo)
