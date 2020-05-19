"""
PyAudio Source
--------------
This source requires PyAudio
::
    pip install PyAudio

.. autoclass:: stream2py.sources.audio.PyAudioSourceReader()
    :members:
    :show-inheritance:

    .. automethod:: __init__

.. autoclass:: stream2py.sources.audio.PaStatusFlags
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource
"""

__all__ = ['PyAudioSourceReader', 'PaStatusFlags', 'PaCallbackReturnCodes']

from collections import deque
from contextlib import suppress, contextmanager
from enum import IntFlag
import math
import operator
import threading

import pyaudio

from stream2py import SourceReader
from stream2py.utility.typing_hints import Generator, ComparableType, List

_ITEMGETTER_0 = operator.itemgetter(0)


class PaStatusFlags(IntFlag):
    """Enum to check status_flag for error codes

    >>> from stream2py.sources.audio import PaStatusFlags
    >>> PaStatusFlags(0)
    <PaStatusFlags.paNoError: 0>
    >>> PaStatusFlags(2)
    <PaStatusFlags.paInputOverflow: 2>
    >>> PaStatusFlags(3)
    <PaStatusFlags.paInputOverflow|paInputUnderflow: 3>
    >>> PaStatusFlags.paInputOverflow in PaStatusFlags(3)  # Check if contains certain error
    True
    >>> PaStatusFlags.paNoError == PaStatusFlags(3)  # Check for no error
    False
    """
    paNoError = pyaudio.paNoError
    paInputUnderflow = pyaudio.paInputUnderflow
    paInputOverflow = pyaudio.paInputOverflow
    paOutputUnderflow = pyaudio.paOutputUnderflow
    paOutputOverflow = pyaudio.paOutputOverflow
    paPrimingOutput = pyaudio.paPrimingOutput


class PaCallbackReturnCodes(IntFlag):
    """Enum of valid _stream_callback return codes.
    Only used by PyAudioSourceReader._stream_callback"""
    paContinue = pyaudio.paContinue
    paComplete = pyaudio.paComplete
    paAbort = pyaudio.paAbort


class PyAudioSourceReader(SourceReader):
    _pyaudio_instance = None

    def __init__(self, *, rate=44100, width=2, unsigned=True, channels=1, input_device_index=None,
                 frames_per_buffer=1024):
        """

        :param rate: Specifies the desired sample rate (in Hz)
        :param width: Sample width in bytes (1, 2, 3, or 4)
        :param unsigned: For 1 byte width, specifies signed or unsigned format. Ignored if byte width is not 1.
        :param channels: The desired number of input channels. Ignored if input_device is not specified (or None).
        :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
        :param frames_per_buffer: Specifies the number of frames per buffer.

        .. todo::
            * option to get input device by name instead of index and warn of duplicate names or missing
            * input_device_index is used by info and must be found and filled into _init_kwargs if looking up by name
            * warn if index does not match name when both name and index are specified
            * option to get input from file
        """
        self._init_kwargs = {k: v for k, v in locals().items() if k not in ('self', '__class__')}
        with self._pyaudio() as pa:
            input_format = pa.get_format_from_width(width, unsigned)
            pa.is_format_supported(rate=rate, input_device=input_device_index, input_channels=channels,
                                   input_format=input_format, output_device=None, output_channels=None,
                                   output_format=None)

        self._pyaudio_open_params = {'rate': rate, 'channels': channels, 'format': input_format, 'input': True,
                                     'output': False, 'input_device_index': input_device_index,
                                     'output_device_index': None, 'frames_per_buffer': frames_per_buffer, 'start': True,
                                     'input_host_api_specific_stream_info': None,
                                     'output_host_api_specific_stream_info': None,
                                     'stream_callback': self._stream_callback}
        #self._data_lock = threading.Lock()

        self._fp = None
        self._first_time_info = None
        self.frame_index = 0
        self.bt = -1
        self._start_time = self.bt
        self.data = None

        self._init_vars()

    def _init_vars(self):
        if self._fp:
            self.close()
        self._fp = None
        self._first_time_info = None
        self.frame_index = 0
        self.bt = -1
        self._start_time = self.bt
        if self.data:
            self.data.clear()
        self.data = deque()

    @property
    def sleep_time_on_read_none_s(self) -> float:
        """One third of the expected rate frames_per_buffer will be filled"""
        seconds_per_read = self._init_kwargs['frames_per_buffer'] / self._init_kwargs['rate']
        one_third_read_rate = seconds_per_read / 3
        return one_third_read_rate

    @property
    def info(self) -> dict:
        """
        Provides a dict with init kwargs, bt, and device info

        >>> from stream2py.sources.audio import PyAudioSourceReader
        >>> from pprint import pprint
        >>> source = PyAudioSourceReader(rate=44100, width=2, channels=1, input_device_index=7, frames_per_buffer=4096)
        >>> source.open()
        >>> pprint(source.info) # doctest: +SKIP
        {'bt': 1582851038965183,
         'channels': 1,
         'device_info': {'defaultHighInputLatency': 0.021333333333333333,
                         'defaultHighOutputLatency': 0.021333333333333333,
                         'defaultLowInputLatency': 0.021333333333333333,
                         'defaultLowOutputLatency': 0.021333333333333333,
                         'defaultSampleRate': 48000.0,
                         'hostApi': 0,
                         'index': 7,
                         'maxInputChannels': 128,
                         'maxOutputChannels': 128,
                         'name': 'sysdefault',
                         'structVersion': 2},
         'frames_per_buffer': 4096,
         'input_device_index': 7,
         'rate': 44100,
         'unsigned': True,
         'width': 2}
        >>> source.close()

        :return: dict
        """
        _info = {'bt': self.bt}
        _info.update(**self._init_kwargs)
        with suppress(Exception):
            _info.update(
                device_info=self._pyaudio_instance.get_device_info_by_index(self._init_kwargs['input_device_index']))
        return _info

    def key(self, data) -> ComparableType:
        """
        :param data: (timestamp, waveform, frame_count, time_info, status_flags)
        :return: timestamp
        """
        return _ITEMGETTER_0(data)

    def data_to_append(self, timestamp, waveform, frame_count, time_info, status_flags):
        """Can to be overloaded to change the shape of read outputs by altering the return value.
        The key function must also be overloaded to return timestamp from the new shape.

        :param timestamp: start time of waveform
        :param waveform: recorded input data
        :param frame_count: number of frames, sample count
        :param time_info: dict, see http://portaudio.com/docs/v19-doxydocs/structPaStreamCallbackTimeInfo.html
        :param status_flags: PaStatusFlags
        :return: (timestamp, waveform, frame_count, time_info, status_flags)
        """
        return timestamp, waveform, frame_count, time_info, status_flags

    def open(self):
        """Will first close if already open and clear any data before starting the audio stream"""
        self._init_vars()
        self._init_pyaudio()
        self.bt = self.get_timestamp()
        self._start_time = self.bt
        self._fp = self._pyaudio_instance.open(**self._pyaudio_open_params)

    def close(self):
        """Stop audio stream"""
        with suppress(Exception):
            self._fp.stop_stream()
        with suppress(Exception):
            self._fp.close()
        self._terminate_pyaudio()

    def read(self):
        """Returns one data item as structured by PyAudioSourceReader.data_to_append

        :return: (timestamp, waveform, frame_count, time_info, status_flags)
        """
        if len(self.data):
            #with self._data_lock:
           return self.data.popleft()

    def _stream_callback(self, in_data, frame_count, time_info, status_flags):
        """Calculates timestamp based on open() bt and frames read.
        If there is an error conveyed by status_flags, the frame count is reset to 0 and starting timestamp is shifted
        from open() bt by time_info to approximate actual time in case of sample loss.
        See _stream_callback in https://people.csail.mit.edu/hubert/pyaudio/docs/#class-stream

        :param in_data: recorded input data, waveform
        :param frame_count: number of frames, sample count
        :param time_info: dictionary
        :param status_flags: PaStatusFlags
        :return: None, PaCallbackReturnCodes.paContinue
        """
        if not self._first_time_info:
            self._first_time_info = time_info

        if self.frame_index == 0:
            # set start time based on audio time_info difference
            _time_info_diff_s = (time_info['input_buffer_adc_time'] - self._first_time_info['input_buffer_adc_time'])
            _timestamp_diff = _time_info_diff_s * self.timestamp_seconds_to_unit_conversion
            self._start_time = self.bt + _timestamp_diff

        _frame_time_s = self.frame_index / self._init_kwargs['rate']
        timestamp = int(self._start_time + _frame_time_s * self.timestamp_seconds_to_unit_conversion)

        #with self._data_lock:  # add data for read
        self.data.append(self.data_to_append(timestamp, in_data, frame_count, time_info, status_flags))

        if PaStatusFlags(status_flags) != PaStatusFlags.paNoError:
            # reset frame index and thus self._start_time on any error status
            self.frame_index = 0
        else:
            self.frame_index += frame_count
        return None, PaCallbackReturnCodes.paContinue

    @classmethod
    def _init_pyaudio(cls) -> pyaudio.PyAudio:
        cls._terminate_pyaudio()
        cls._pyaudio_instance = pyaudio.PyAudio()
        return cls._pyaudio_instance

    @classmethod
    def _terminate_pyaudio(cls):
        with suppress(Exception):
            if cls._pyaudio_instance is not None and isinstance(cls._pyaudio_instance, (pyaudio.PyAudio,)):
                cls._pyaudio_instance.terminate()
                cls._pyaudio_instance = None

    @classmethod
    @contextmanager
    def _pyaudio(cls) -> Generator[pyaudio.PyAudio, None, None]:
        try:
            yield cls._init_pyaudio()
        finally:
            cls._terminate_pyaudio()

    @classmethod
    def list_device_info(cls) -> List[dict]:
        """
        .. todo::
            * filter for only devices with input channels

        :return: list
        """
        with cls._pyaudio() as pa:
            return [pa.get_device_info_by_index(idx) for idx in range(pa.get_device_count())]

    @staticmethod
    def audio_buffer_size_seconds_to_maxlen(buffer_size_seconds, rate, frames_per_buffer) -> int:
        """Calculate maxlen for StreamBuffer to keep a minimum of buffer_size_seconds of data on buffer

        :param buffer_size_seconds: desired length of StreamBuffer in seconds
        :param rate: sample rate
        :param frames_per_buffer: number of frames per buffer
        :return: maxlen for StreamBuffer
        """
        seconds_per_read = frames_per_buffer / rate
        return math.ceil(buffer_size_seconds / seconds_per_read)


if __name__ == '__main__':
    from pprint import pprint

    pprint(PyAudioSourceReader.list_device_info())

    source = PyAudioSourceReader(rate=44100, width=2, channels=1, input_device_index=0, frames_per_buffer=4096)
    #pprint(source.info)
    try:
        source.open()
        pprint(source.info)
        #exit()
        i = 0
        while i < 600:
            data = source.read()
            if data:
                i += 1
                timestamp, in_data, frame_count, time_info, status_flags = data
                if PaStatusFlags(status_flags) != PaStatusFlags.paNoError:
                    print(timestamp, len(in_data), status_flags, PaStatusFlags(status_flags))
                else:
                    print(timestamp, len(in_data), status_flags)
    finally:
        source.close()
        pprint(source.info)
