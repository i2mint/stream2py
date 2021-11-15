from stream2py.utility.locked_sorted_deque import RWLockSortedDeque
import pytest
import operator


@pytest.mark.parametrize('initial_size,maxlen', [(100, 110), (10, 12),])
def test_rw_lock_sorted_deque(initial_size, maxlen):
    locked_deque = RWLockSortedDeque(
        ((('plc', i), f'data_{i}') for i in range(initial_size)),
        key=operator.itemgetter(0),
        maxlen=maxlen,
    )
    assert len(locked_deque) == initial_size

    new_item = (('plc', initial_size + 1), 'new data')
    # add an item and check that the len incremented accordingly
    with locked_deque.writer_lock() as writer:
        writer.append(new_item)
    assert len(locked_deque) == initial_size + 1

    # looking for the first element greater than all of those in the initial deque
    with locked_deque.reader_lock() as reader:
        assert reader.find_gt(('plc', initial_size)) == new_item

    # the deque cannot exceed its maxlen
    with locked_deque.writer_lock() as writer:
        for i in range(maxlen):
            new_item = (('plc', initial_size + 2 + i), 'new data')
            writer.append(new_item)
        assert len(locked_deque) == maxlen

    # attempting to add another element, not larger than the previous one, will raise an error
    with locked_deque.writer_lock() as writer:
        with pytest.raises(ValueError):
            writer.append(new_item)
