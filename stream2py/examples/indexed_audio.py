"""
[taped](https://github.com/otosense/taped)) provides a `LiveWf`, but one would like to have more control over
 it's behavior. Namely:
* Getting an exception or sentinel value (of user's choice) when "some data might have been lost"
* repeats of `live_wf[:100]` give me 0-100, then 100-200, then 200-300...
    - this would be more clear to all users with a live_wf.next(100) method: Actually not: read is better.
* `live_wf[i:j]` is such that i and j are in samples since the process started, with customizable behavior when data
requested is no longer (past) or not yet (future) in buffer (behaviors such as returning exception, or sentinel,
or (in the case of future data), simply block (sleep) until data is available...


**Problem**

`PyAudioSourceReader` doesn't handle error flags and doesn't keep track of frame index out of the box.

_Doesn't handle errors_: Meaning if `PyAudio` catches an error (most likely one to encounter
being the "InputOverFlow" error, meaning the data wasn't read fast enough), tags it with a flag,
you'll see the corresponding `PyAudioSourceReader` item, which will be placed as is on the buffer,
but no special handling of these errors is done implicitly. **You** need to chose what to do with this.

_Doesn't keep track of frame index_: If you are dumping the `PyAudioSourceReader` items on a buffer,
then reading that buffer with some (or multiple) readers, that reader might want to know if it missed an item or not.
It can do so with some calculation involving the timestamp information, sample rate,
etc. but time and data rate are rarely multiple of each other, so some complexity is needed to resolve phase.
It would be more convenient to have a frame index (i.e. offset -- relative to the very first frame we read).

**Solution**

- `FillErrorWithZeroesMixin` is an element of a solution to the "handle errors" problem.
It solves the problem by filling missing data with zeros.

- `FrameIndexAsKeyMixin` is a solution for "frame index tracking" problem.
This solution assumes that frame index is more important than timestamp.
"""

import time
from collections import namedtuple

from stream2py.sources.audio import (
    PyAudioSourceReader,
    FillErrorWithZeroesMixin,
)
from stream2py import StreamBuffer, BufferReader


# TODO: Questions to consider:
#  Should we really fill with zeros, not None? Is parametrization worth it?
#  Consider this:
#    - no 0 in code, use class property instead (so semantic is clear, and possibilities of extension): Open closed principle
#    - possibility that -1 is a better fillval??
class FrameIndexAsKeyMixin(FillErrorWithZeroesMixin):
    """Must be used with FillErrorWithZeroesMixin for accurate frame count in case of errors"""

    _total_frame_index = 0

    def open(self):
        self._total_frame_index = 0  # ?? What about FrameIndexAsKeyMixin._total_frame_index? Needed? Safety measure?
        return super(FrameIndexAsKeyMixin, self).open()

    def data_to_append(self, timestamp, waveform, frame_count, time_info, status_flags):
        frame_index = self._total_frame_index
        self._total_frame_index += frame_count
        return (
            frame_index,
            timestamp,
            waveform,
            frame_count,
            time_info,
            status_flags,
        )


class PyAudioWithNamedTupleMixin:
    _data_to_append_namedtuple = namedtuple(
        typename='PyAudioSourceReaderData',
        field_names=['timestamp', 'bytes', 'frame_count', 'time_info', 'status_flags',],
    )

    def key(self, data):
        return data.timestamp

    def data_to_append(self, timestamp, waveform, frame_count, time_info, status_flags):
        return self._data_to_append_namedtuple(
            timestamp, waveform, frame_count, time_info, status_flags
        )


# TODO: Consider __init_subclass__ to check on proper subclassing (like no conflicts of Mixin method names)


class PyAudioWithZeroedErrorsSourceReader(
    FillErrorWithZeroesMixin, PyAudioSourceReader
):
    """PyAudioSourceReader with source errors resulting in (null) value filling"""

    pass


class PyAudioWithZeroedErrorsAndFrameIndexingSourceReader(
    FrameIndexAsKeyMixin, PyAudioSourceReader
):
    """PyAudioSourceReader with frame index tracking"""

    pass


def list_recording_device_index_names():
    """List (index, name) of available recording devices"""
    return sorted(
        (d['index'], d['name'])
        for d in PyAudioSourceReader.list_device_info()
        if d['maxInputChannels'] > 0
    )


def device_info_by_index(index):
    return next(
        d for d in PyAudioSourceReader.list_device_info() if d['index'] == index
    )


# Slicing ##############################################################################################################


class PyAudioStreamBuffer(StreamBuffer):
    _internal_reader: BufferReader = None  # reader persists here after source is stopped

    def __init__(
        self,
        input_device_index,
        sr=None,
        width=2,
        channels=None,
        frames_per_buffer=None,
        *,
        source_reader_class=PyAudioSourceReader,
    ):
        _info = device_info_by_index(input_device_index)
        sr = int(sr or _info['defaultSampleRate'])
        frames_per_buffer = int(frames_per_buffer or sr / 10)
        super(PyAudioStreamBuffer, self).__init__(
            source_reader=source_reader_class(
                input_device_index=input_device_index,
                rate=sr,
                width=width,
                channels=int(channels or _info['maxInputChannels']),
                frames_per_buffer=frames_per_buffer,
            ),
            maxlen=source_reader_class.audio_buffer_size_seconds_to_maxlen(
                buffer_size_seconds=60, rate=sr, frames_per_buffer=frames_per_buffer,
            ),
            auto_drop=False,
            sleep_time_on_read_none_s=0.1,
        )

    @property
    def reader(self):
        if self._internal_reader is None:
            self._internal_reader = self.mk_reader()
        return self._internal_reader

    def start(self):
        if self._internal_reader is not None:  # reset reader on start
            del self._internal_reader
            self._internal_reader = None
        return super(PyAudioStreamBuffer, self).start()

    def __getitem__(self, item):
        if not isinstance(item, slice):
            item = slice(item, item + 1)
        reader = self.reader
        return reader.range(item.start, item.stop, item.step, start_le=True)


class PyAudioStreamBufferWithByteSlice(PyAudioStreamBuffer):
    def __getitem__(self, item):
        # TODO: handle steps
        # TODO: robust way of defining how to slice items into subitems without making any assumptions
        if not isinstance(item, slice):
            item = slice(item, item + 1)
        items = super(PyAudioStreamBufferWithByteSlice, self).__getitem__(
            slice(item.start, item.stop)
        )
        i_bytes = b''.join(_i[1] for _i in items)

        first_item_bt = items[0][0]
        first_item_tt = items[1][0]
        subitem_index_per_time = len(items[0][1]) / (first_item_tt - first_item_bt)
        last_item_bt = items[-1][0]
        last_item_tt = last_item_bt + (len(items[-1][1]) / subitem_index_per_time)

        i_start = int((item.start - first_item_bt) * subitem_index_per_time)
        i_stop = int((item.stop - last_item_tt) * subitem_index_per_time)

        return i_bytes[i_start : i_stop : item.step]


if __name__ == '__main__':
    # TODO: Explain what we're testing here. What is expected to be observed?
    # TODO: If not too much overhead, assert what is expected.
    # TODO: If not too much overhead, include these asserts as actual tests (copying this code to a pytest module)

    from stream2py.sources.audio import find_a_default_input_device_index

    device = find_a_default_input_device_index()

    stream_buffer = PyAudioStreamBuffer(device, sr=44100, frames_per_buffer=4096)

    print(f'\nTest 1: PyAudioSourceReader ####################')
    with stream_buffer:
        time.sleep(2)
        bt = PyAudioSourceReader.get_timestamp()
        time.sleep(2)
        tt = PyAudioSourceReader.get_timestamp()
        time.sleep(2)
        items = stream_buffer[bt:tt]

    print(f'{len(items)=}, ({items[0][0]=}, {items[-1][0]=}), ({bt=}, {tt=})')

    print(f'{stream_buffer[(bt + tt) / 2][0][0]=}')

    print(f'\nTest 2: PyAudioStreamBufferWithByteSlice ######################')

    stream_buffer_with_byte_slice = PyAudioStreamBufferWithByteSlice(
        device, sr=44100, frames_per_buffer=4096,
    )

    with stream_buffer_with_byte_slice:
        time.sleep(2)
        bt = PyAudioSourceReader.get_timestamp()
        time.sleep(2)
        tt = PyAudioSourceReader.get_timestamp()
        time.sleep(2)
        items = stream_buffer_with_byte_slice[bt:tt]

    print(f'{len(items)=}, {items[0:10]=}, ({bt=}, {tt=})')

    bt = stream_buffer_with_byte_slice.reader.head(peek=True)[0]
    tt = stream_buffer_with_byte_slice.reader.tail(peek=True)[0]
    wf_bytes = stream_buffer_with_byte_slice[bt:tt]
    print(f'{len(wf_bytes)=}')

    print(f'\nTest 3: BufferReader Queries #################################')

    with stream_buffer:
        time.sleep(5)
        reader = stream_buffer.mk_reader()
        print(reader.source_reader_info)
        bt = PyAudioSourceReader.get_timestamp()
        for x in range(3, 0, -1):
            print(x)
            time.sleep(1)
        tt = PyAudioSourceReader.get_timestamp()
        bt_tt_data = reader.range(bt, tt, start_le=True)

    print(len(bt_tt_data), bt - bt_tt_data[0][0], tt - bt_tt_data[-1][0])

    buffer_count = 5

    # iterating from reader
    print('   ... iterating from reader')

    with stream_buffer:
        reader = stream_buffer.mk_reader()
        for i, data in enumerate(reader):
            print(i, data[0])
            if i >= buffer_count:
                break

    # using next() with work around

    print('   ... using next() with work around')

    with stream_buffer:
        reader = stream_buffer.mk_reader()

        def yield_from_reader(reader):
            yield from reader

        reader_gen = yield_from_reader(reader)

        for i in range(buffer_count):
            data = next(reader_gen)
            print(i, data[0])

    # using BufferReader.next()

    print('   ... using BufferReader.next()')

    with stream_buffer:
        reader = stream_buffer.mk_reader()

        i = 0
        while i < buffer_count:
            data = reader.next(ignore_no_item_found=True)
            if data:
                print(i, data[0])
                i += 1

    # using BufferReader.next(n=5)
    # TODO: Not working: Repair.
    # print("   ... using BufferReader.next(n=5)")
    #
    # with stream_buffer:
    #     reader = stream_buffer.mk_reader()
    #
    #     i = 0
    #     while i < buffer_count:
    #         data = reader.next(5, ignore_no_item_found=True)
    #         if data:
    #             print(i, data[0][0], len(data))
    #             i += 1
    #             time.sleep(1)

    # Frame Count Indexing

    print('\nTest 4: Frame Count Indexing ##########################')

    frame_index_stream_buffer = PyAudioStreamBuffer(
        device,
        sr=44100,
        frames_per_buffer=4096,
        source_reader_class=PyAudioWithZeroedErrorsAndFrameIndexingSourceReader,
    )

    start_index = 4095
    end_index = 20000

    with frame_index_stream_buffer:
        time.sleep(1)
        reader = frame_index_stream_buffer.mk_reader()
        for x in range(3, 0, -1):
            print(x)
            time.sleep(1)
        with reader._buffer.reader_lock() as _reader:
            _start = _reader.find_le(start_index)[0]
            print(_start)
        data_range = reader.range(start_index, end_index, start_le=True)
    len(data_range), data_range[0][0], data_range[-1][0]

    # iterating from reader
    print('   ... iterating from reader')

    with frame_index_stream_buffer:
        reader = frame_index_stream_buffer.mk_reader()
        for i, data in enumerate(reader):
            print(i, data[0])
            if i >= buffer_count:
                break

    # using next() with work around
    print('   ... using next() with work around')

    with frame_index_stream_buffer:
        reader = frame_index_stream_buffer.mk_reader()

        def yield_from_reader(reader):
            yield from reader

        reader_gen = yield_from_reader(reader)

        for i in range(buffer_count):
            data = next(reader_gen)
            print(i, data[0])

    # using BufferReader.next()
    print('   ... using BufferReader.next()')

    with frame_index_stream_buffer:
        reader = frame_index_stream_buffer.mk_reader()

        i = 0
        while i < buffer_count:
            data = reader.next(ignore_no_item_found=True)
            if data:
                print(i, data[0])
                i += 1
