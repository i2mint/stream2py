"""Example of processing audio and keyboard streams"""
from typing import Callable, NewType, Any
from stream2py.stream_buffer import StreamBuffer
from stream2py.sources.keyboard_input import KeyboardInputSourceReader
from stream2py.sources.audio import (
    PyAudioSourceReader,
    find_a_default_input_device_index,
)


AudioData = NewType('', Any)
KeyboardData = NewType('', Any)
AudioDataCallback = Callable[[AudioData], Any]
KeyboardDataCallback = Callable[[KeyboardData], Any]


def default_audio_callback(audio_data):
    if audio_data is not None:
        (audio_timestamp, waveform, frame_count, time_info, status_flags,) = audio_data
        print(
            f'   [Audio] {audio_timestamp}: {len(waveform)=} {type(waveform).__name__}',
            end='\n\r',
        )


def default_keyboard_event_callback(keyboard_data):
    if keyboard_data is not None:
        index, keyboard_timestamp, char = keyboard_data
        print(f'[Keyboard] {keyboard_timestamp}: {char}', end='\n\r')

        if char == '\x1b':  # ESC key
            return True
        else:
            return False


def keyboard_and_audio(
    input_device_index=None,  # find index with PyAudioSourceReader.list_device_info()
    rate=44100,
    width=2,
    channels=1,
    frames_per_buffer=44100,  # same as sample rate for 1 second intervals
    seconds_to_keep_in_stream_buffer=60,
    audio_data_callback: AudioDataCallback = default_audio_callback,
    keyboard_data_callback: KeyboardDataCallback = default_keyboard_event_callback,
):
    """Starts two independent streams: one for audio and another for keyboard inputs.
    Prints stream type, timestamp, and additional info about data:
    Shows input key pressed for keyboard and byte count for audio

    Press Esc key to quit.

    :param input_device_index: find index with PyAudioSourceReader.list_device_info()
    :param rate: audio sample rate
    :param width: audio byte width
    :param channels: number of audio input channels
    :param frames_per_buffer: audio samples per buffer
    :param seconds_to_keep_in_stream_buffer: max size of audio buffer before data falls off
    :return: None
    """

    if input_device_index is None:
        input_device_index = find_a_default_input_device_index()

    selected_device_info = next(
        dev
        for dev in PyAudioSourceReader.list_device_info()
        if dev['index'] == input_device_index
    )
    print(f"Starting audio device: {selected_device_info['name']}\n")

    # converts seconds_to_keep_in_stream_buffer to max number of buffers of size frames_per_buffer
    maxlen = PyAudioSourceReader.audio_buffer_size_seconds_to_maxlen(
        buffer_size_seconds=seconds_to_keep_in_stream_buffer,
        rate=rate,
        frames_per_buffer=frames_per_buffer,
    )
    audio_source_reader = PyAudioSourceReader(
        rate=rate,
        width=width,
        channels=channels,
        unsigned=True,
        input_device_index=input_device_index,
        frames_per_buffer=frames_per_buffer,
    )

    # open audio stream
    with StreamBuffer(
        source_reader=audio_source_reader, maxlen=maxlen
    ) as audio_stream_buffer:
        # open keyboard input stream
        with StreamBuffer(
            source_reader=KeyboardInputSourceReader(), maxlen=maxlen
        ) as keyboard_stream_buffer:

            audio_buffer_reader = audio_stream_buffer.mk_reader()
            keyboard_buffer_reader = keyboard_stream_buffer.mk_reader()

            print('getch! Press any key! Esc to quit!\n')  # replace w KeyboardInterrupt
            while True:
                try:
                    keyboard_data = next(keyboard_buffer_reader)
                    audio_data = next(audio_buffer_reader)

                    should_quit = keyboard_data_callback(keyboard_data)
                    if should_quit:
                        break

                    audio_data_callback(audio_data)

                except KeyboardInterrupt:
                    print("\n\nGot a : I'll quit now...\n")


if __name__ == '__main__':
    keyboard_and_audio()
