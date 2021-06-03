"""
Recording audio to wav file
---------------------------
This example requires PyAudio
::
    pip install PyAudio

.. autoclass:: stream2py.examples.usage.record_audio_to_files.BufferReaderConsumer()
    :members:
    :show-inheritance:
    :undoc-members:

    .. automethod:: __init__

.. autoclass:: stream2py.examples.usage.record_audio_to_files.PyAudioSaver()
    :members:
    :show-inheritance:
    :undoc-members:

    .. automethod:: __init__

.. autofunction:: stream2py.examples.usage.record_audio_to_files.audio_to_files

"""

from abc import ABCMeta, abstractmethod

from contextlib import suppress
import logging
import os
import threading
import time
import wave

from stream2py import StreamBuffer, BufferReader
from stream2py.sources.audio import PyAudioSourceReader, PaStatusFlags
from stream2py.utility.typing_hints import Union

logger = logging.getLogger(__name__)


class BufferReaderConsumer(threading.Thread, metaclass=ABCMeta):
    """Call reader_handler function with reader at defined time intervals between calls"""

    def __init__(
        self,
        buffer_reader: BufferReader,
        interval: Union[int, float],
        logging_enabled: bool = False,
    ):
        """

        :param buffer_reader: BufferReader created from a StreamBuffer
        :param interval: seconds between reader_handler calls
        :param logging_enabled: log debug messages using logging module
        """
        threading.Thread.__init__(self, daemon=True)
        assert isinstance(buffer_reader, BufferReader)
        self.buffer_reader = buffer_reader
        self.interval = interval
        self.stop_event = threading.Event()
        self.logging_enabled = logging_enabled

    def stop(self):
        """Sets stop event and waits for thread to finish"""
        self.stop_event.set()
        if self.logging_enabled:
            logger.debug(f'Consumer stopping... {self.__class__.__name__}')
        self.join()

    def run(self):
        """Calls self.reader_handler in a loop while sleeping for self.interval seconds after each call until stop event
        is set or Exception is raised by self.reader_handler"""
        if self.logging_enabled:
            logger.debug(f'Consumer starting! {self.__class__.__name__}')
        try:
            while not self.stop_event.is_set():
                self.reader_handler(self.buffer_reader)
                time.sleep(self.interval)
        finally:
            with suppress(Exception):
                self.stop()
        if self.logging_enabled:
            logger.debug(f'Consumer stopped! {self.__class__.__name__}')

    @abstractmethod
    def reader_handler(self, buffer_reader: BufferReader):
        """Implements how to read from buffer and what to do with the data"""
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class PyAudioSaver(BufferReaderConsumer):
    """Save audio to wav file. Start a new wav file on errors such as input overflow."""

    def __init__(self, buffer_reader, interval, rootdir, logging_enabled):
        """

        :param buffer_reader: BufferReader created from a StreamBuffer with PyAudioSourceReader
        :param interval: seconds between reader_handler calls
        :param rootdir: folder path where files will be saved under
        :param logging_enabled: log debug messages using logging module
        """
        super().__init__(buffer_reader, interval, logging_enabled)

        self.session_data_path_format = os.path.join(
            os.path.expanduser(rootdir), '{session}', 'd'
        )
        self.path_format = os.path.join(
            self.session_data_path_format, '{timestamp}.wav'
        )
        self.error_path_format = os.path.join(
            self.session_data_path_format, '{timestamp}_ERROR_{status_flags}.wav',
        )
        self.file = None

    def reader_handler(self, buffer_reader: BufferReader):
        new_data_list = buffer_reader.range(
            start=0, stop=float('inf'), ignore_no_item_found=True, only_new_items=True,
        )
        if new_data_list is not None:
            for (
                timestamp,
                in_data,
                frame_count,
                time_info,
                status_flags,
            ) in new_data_list:
                if PaStatusFlags(status_flags) != PaStatusFlags.paNoError:
                    if self.logging_enabled:
                        logger.debug(PaStatusFlags(status_flags))
                    # an error occurred, close file
                    self.close_file()
                    # save to error file
                    self.save_error(
                        buffer_reader.source_reader_info,
                        timestamp,
                        in_data,
                        status_flags,
                    )
                else:
                    if self.file_is_open() is False:
                        self.open_file(buffer_reader.source_reader_info, timestamp)
                    self.write_to_file(in_data)

    def file_is_open(self) -> bool:
        """
        Check if file is open
        :return: boolean
        """
        return self.file is not None

    def open_file(self, source_reader_info: dict, timestamp: int) -> wave.Wave_write:
        """open wav file for writing"""
        file_path = self.path_format.format(
            session=source_reader_info['bt'], timestamp=timestamp
        )
        if self.logging_enabled:
            logger.debug(f'opening file: {file_path}')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.file = wave.open(file_path, mode='wb')
        self.set_params(self.file, source_reader_info)
        return self.file

    @staticmethod
    def set_params(file: wave.Wave_write, source_reader_info: dict):
        """Set wav file params"""
        nchannels = source_reader_info['channels']
        sampwidth = source_reader_info['width']
        framerate = source_reader_info['rate']
        nframes = 0
        comptype = 'NONE'
        compname = 'not compressed'
        file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))

    def write_to_file(self, in_data):
        """Write to wav file"""
        self.file.writeframes(in_data)

    def close_file(self):
        """Close wav file"""
        self.file.close()
        self.file = None

    def stop(self):
        """Stop BufferReaderConsumer loop and close wav file"""
        super().stop()
        if self.file_is_open() is True:
            self.close_file()

    def save_error(self, source_reader_info, timestamp, in_data, status_flags):
        """Save to error wav file"""
        file_path = self.error_path_format.format(
            session=source_reader_info['bt'],
            timestamp=timestamp,
            status_flags=status_flags,
        )
        if self.logging_enabled:
            logger.debug(f'saving error file: {file_path}')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        error_file = wave.open(file_path, mode='wb')
        self.set_params(error_file, source_reader_info)
        error_file.writeframes(in_data)
        error_file.close()


def audio_to_files(
    rate,
    width,
    channels,
    input_device_index,
    frames_per_buffer,
    interval,
    rootdir,
    logging_enabled,
):
    """Basically the main function to run the example.
    It will record audio with stream2py.sources.audio.PyAudioSourceReader
    and save to wav files with stream2py.examples.usage.record_audio_to_files.PyAudioSaver

    Check this source code to see how to put together the three components: SourceReader, StreamBuffer, BufferReader

    :param rate: Specifies the desired sample rate (in Hz)
    :param width: Sample width in bytes (1, 2, 3, or 4)
    :param channels: The desired number of input channels. Ignored if input_device is not specified (or None).
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param frames_per_buffer: Specifies the number of frames per buffer.
    :param interval: seconds between reader_handler calls
    :param rootdir: folder path where files will be saved under
    :param logging_enabled: log debug messages using logging module
    """
    from stream2py.utility.logger import set_logging_config

    set_logging_config(level=logging.DEBUG)

    seconds_per_read = frames_per_buffer / rate
    seconds_to_keep_in_stream_buffer = 60

    maxlen = int(seconds_to_keep_in_stream_buffer / seconds_per_read)
    source_reader = PyAudioSourceReader(
        rate=rate,
        width=width,
        channels=channels,
        unsigned=True,
        input_device_index=input_device_index,
        frames_per_buffer=frames_per_buffer,
    )

    with StreamBuffer(source_reader=source_reader, maxlen=maxlen) as stream_buffer:
        """keep open and save to file until stop event"""
        buffer_reader = stream_buffer.mk_reader()
        with PyAudioSaver(
            buffer_reader,
            interval=interval,
            rootdir=rootdir,
            logging_enabled=logging_enabled,
        ) as pasave:
            try:
                pasave.join()
            except KeyboardInterrupt:
                pass


audio_to_files.list_device_info = lambda: PyAudioSourceReader.list_device_info()

if __name__ == '__main__':
    audio_to_files(
        rate=44100,
        width=2,
        channels=1,
        input_device_index=6,
        frames_per_buffer=1024 * 4,
        interval=1,
        rootdir='~/odir/stream2py',
        logging_enabled=True,
    )
