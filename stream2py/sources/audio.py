__all__ = ['PyAudioSourceReader', 'PaCallbackFlags', 'PaCallbackReturnCodes', 'pyaudio']

from _collections import deque
from contextlib import suppress, contextmanager
from enum import IntFlag

import operator
import pyaudio
import threading

from stream2py import SourceReader


class PaCallbackFlags(IntFlag):
    """stream_callback status_flag"""
    paNoError = pyaudio.paNoError
    paInputUnderflow = pyaudio.paInputUnderflow
    paInputOverflow = pyaudio.paInputOverflow
    paOutputUnderflow = pyaudio.paOutputUnderflow
    paOutputOverflow = pyaudio.paOutputOverflow
    paPrimingOutput = pyaudio.paPrimingOutput


class PaCallbackReturnCodes(IntFlag):
    """stream_callback return codes"""
    paContinue = pyaudio.paContinue
    paComplete = pyaudio.paComplete
    paAbort = pyaudio.paAbort


class PyAudioSourceReader(SourceReader):
    _pyaudio_instance = None

    def __init__(self, *, rate=44100, format=pyaudio.paInt16, channels=1, input_device_index=None,
                 frames_per_buffer=1024):
        """TODO: get input device by name instead of index and warn of duplicates or missing
        TODO: input from file"""
        self._init_kwargs = {k: v for k, v in locals().items() if k not in ('self', '__class__')}
        with self._pyaudio() as pa:
            pa.is_format_supported(rate=rate, input_device=input_device_index, input_channels=channels,
                                   input_format=format, output_device=None, output_channels=None, output_format=None)

        self._pyaudio_open_params = {'rate': rate, 'channels': channels, 'format': format, 'input': True,
                                     'output': False, 'input_device_index': input_device_index,
                                     'output_device_index': None, 'frames_per_buffer': frames_per_buffer, 'start': True,
                                     'input_host_api_specific_stream_info': None,
                                     'output_host_api_specific_stream_info': None,
                                     'stream_callback': self.stream_callback}
        self._data_lock = threading.Lock()

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
    def sleep_time_on_read_none_s(self):
        """One third of the expected rate frames_per_buffer will be filled"""
        seconds_per_read = self._init_kwargs['frames_per_buffer'] / self._init_kwargs['rate']
        one_third_read_rate = seconds_per_read / 3
        return one_third_read_rate

    @property
    def info(self):
        _info = {'bt': self.bt}
        _info.update(**self._init_kwargs)
        with suppress(Exception):
            _info.update(
                device_info=self._pyaudio_instance.get_device_info_by_index(self._init_kwargs['input_device_index']))
        return _info

    key = operator.itemgetter(0)  # (timestamp, in_data, frame_count, time_info, status_flags) -> timestamp

    def data_to_append(self, timestamp, waveform, frame_count, time_info, status_flags):
        """Intended to be overloaded to change read outputs.
        The key function must be overloaded if timestamp is moved from the first tuple position"""
        return timestamp, waveform, frame_count, time_info, status_flags

    def open(self):
        self._init_vars()
        self._init_pyaudio()
        self.bt = self.get_timestamp()
        self._start_time = self.bt
        self._fp = self._pyaudio_instance.open(**self._pyaudio_open_params)

    def close(self):
        with suppress(Exception):
            self._fp.stop_stream()
        with suppress(Exception):
            self._fp.close()
        self._terminate_pyaudio()

    def read(self):
        """
        :return: timestamp, wf, frame_count, time_info, status_flags
        """
        if len(self.data):
            with self._data_lock:
                return self.data.popleft()

    def stream_callback(self, in_data, frame_count, time_info, status_flags):
        """Calculates timestamp based on open() bt and frames read.
        If there is an error conveyed by status_flags, the frame count is reset to 0 and starting timestamp is shifted
        from open() bt by time_info to approximate actual time in case of sample loss.
        See stream_callback in https://people.csail.mit.edu/hubert/pyaudio/docs/#class-stream
        :param in_data: recorded input data, waveform
        :param frame_count: number of frames, sample count
        :param time_info: dictionary
        :param status_flags: PaCallbackFlags
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

        with self._data_lock:  # add data for read
            self.data.append(self.data_to_append(timestamp, in_data, frame_count, time_info, status_flags))

        if PaCallbackFlags(status_flags) != PaCallbackFlags.paNoError:
            # reset frame index and thus self._start_time on any error status
            self.frame_index = 0
        else:
            self.frame_index += frame_count
        return None, PaCallbackReturnCodes.paContinue

    @classmethod
    def _init_pyaudio(cls):
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
    def _pyaudio(cls):
        try:
            yield cls._init_pyaudio()
        finally:
            cls._terminate_pyaudio()

    @classmethod
    def list_device_info(cls):
        """TODO: filter for only devices with input channels"""
        with cls._pyaudio() as pa:
            return [pa.get_device_info_by_index(idx) for idx in range(pa.get_device_count())]


if __name__ == '__main__':
    from pprint import pprint

    pprint(PyAudioSourceReader.list_device_info())

    source = PyAudioSourceReader(rate=44100, format=pyaudio.paInt16, channels=1,
                                 input_device_index=7, frames_per_buffer=4096)
    try:
        source.open()
        pprint(source.info)
        i = 0
        while i < 600:
            data = source.read()
            if data:
                i += 1
                timestamp, in_data, frame_count, time_info, status_flags = data
                if PaCallbackFlags(status_flags) != PaCallbackFlags.paNoError:
                    print(timestamp, len(in_data), status_flags, PaCallbackFlags(status_flags))
                else:
                    print(timestamp, len(in_data), status_flags)
    finally:
        source.close()
