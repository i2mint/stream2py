from stream2py.tests.utils_for_testing import TenthSecondCounterStreamSource
import time


def test_stream_source():
    source = TenthSecondCounterStreamSource()  # source
    with source.open_reader() as sc_reader:
        sc_buf = source._stream_buffer
        time.sleep(2)
        assert source.info['bt'] != 0, source.info
        print('data as shown is (timestamp, count) at every tenth of a second')
        while True:
            x = sc_reader.read(n=1, ignore_no_item_found=True)
            print('x: ' + str(x))
            if x:
                last_read = x
                print(x)
            else:
                break
        assert (
            sc_reader.last_item == last_read
        ), 'last_item did not follow last next() call'

        # check range works and last_item cursor is working
        rstart = 5
        rstop = 10
        source_info = source.info
        start_key = source_info['bt'] + 1e5 * rstart  # 5
        stop_key = source_info['bt'] + 1e5 * rstop  # 10
        range_data = sc_reader.range(start_key, stop_key)
        expected_data = None
        for expected_data, rdata in zip(range(rstart, rstop + 1), range_data):
            timestamp, _data = rdata
            assert _data == expected_data, 'wrong data does not match'
        assert (
            expected_data == sc_reader.last_item[1]
        ), f'last_item did not follow last range({start_key}, {stop_key}) call'
        previous_last_item = expected_data

        # check range works with step and peek, and last_item does not move with peek=True
        rstart = 10
        rstop = 15
        rstep = 2
        source_info = source.info
        start_key = source_info['bt'] + 1e5 * rstart  # 5
        stop_key = source_info['bt'] + 1e5 * rstop  # 10
        range_data = sc_reader.range(start_key, stop_key, step=rstep, peek=True)
        for expected_data_value, rdata in zip(
            range(rstart, rstop + 1, rstep), range_data
        ):
            timestamp, _data = rdata
            assert _data == expected_data_value, 'wrong data does not match'
        assert (
            previous_last_item == sc_reader.last_item[1]
        ), 'last_item moved but should not when peek=True'

        # stop source and check if reader sees it
        sc_reader12 = source.open_reader()
        assert sc_reader.is_same_buffer(sc_reader12), 'first readers should be equal'
        assert (
            sc_reader.last_item != sc_reader12.last_item
        ), 'first readers should have a different last_item cursor position'
        assert sc_reader.is_stopped is False, 'Reader should see source is not stopped'
        sc_buf.stop()
        assert sc_reader.is_stopped is True, 'Reader should see source is stopped'

        # restart source and make new readers then check old reader is different from new reader
        with sc_buf:  # start and stop with a context manager
            sc_reader21 = sc_buf.mk_reader()  # reader2
            sc_reader22 = sc_buf.mk_reader()  # reader2
            assert sc_reader21.is_same_buffer(
                sc_reader22
            ), 'two new readers should be equal'
            assert not sc_reader.is_same_buffer(
                sc_reader21
            ), 'first reader should not equal new reader'
            assert (
                sc_reader.is_stopped is True
            ), 'first reader should still see a stopped source'
            assert (
                sc_reader21.is_stopped is False
            ), 'new reader should see the source is running'
            assert (
                sc_reader22.last_item == sc_reader21.last_item
            ), 'new readers should now have the same last_item cursor position'

            # print some data from old and new reader and see they are different
            time.sleep(1.5)
            print('comparing first start reader values to second start')
            while True:
                r22 = sc_reader22.read(n=1, ignore_no_item_found=True)
                r12 = sc_reader12.read(n=1, ignore_no_item_found=True)

                if r22:

                    def zero_if_none(val):
                        if val is None:
                            return 0, 0
                        return val

                    print(f'{r22} > {r12}, ts_diff={r22[0] - r12[0]}')
                    assert r22 > zero_if_none(r12)
                else:
                    break
            assert (
                sc_reader22.last_item != sc_reader21.last_item
            ), 'new readers should now have a different last_item cursor position'
