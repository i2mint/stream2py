import pytest

from stream2py.tests.utils_for_testing import RandomFloatSource, TenthSecondCounter

# note that the class to test must have the additional attribute open_count for the test to pass
@pytest.mark.parametrize(
    'n_reads,n_open_close,source_reader_class,class_params',
    [
        (1, 10, RandomFloatSource, {'seed': 1}),
        (5, 100, RandomFloatSource, {'seed': 1}),
        (10, 10, RandomFloatSource, {'seed': 1}),
        (10, 10, TenthSecondCounter, dict()),
    ],
)
def test_source_readers_open_close(
    n_reads, n_open_close, source_reader_class, class_params
):
    sc = source_reader_class(**class_params)
    for open_number in range(n_open_close):
        with sc:
            # check that the count increments
            assert sc.open_count == open_number + 1
            random_numbers = [sc.read() for i in range(n_reads)]
            # check that each read yielding one float
            assert len(random_numbers) == n_reads
        # check that after closing, the count of open did not increment
        assert sc.open_count == open_number + 1
        # checking access to the info
        assert isinstance(sc.info, dict)
