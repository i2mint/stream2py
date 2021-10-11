if __name__ == '__main__':
    from stream2py.stream_buffer import StreamBuffer
    from stream2py.sources.keyboard_input import KeyboardInputSourceReader
    from stream2py.sources.audio import PyAudioSourceReader

    # audio parameters
    input_device_index = 2  # find index with PyAudioSourceReader.list_device_info()
    rate = 44100
    width = 2
    channels = 1
    frames_per_buffer = 44100  # same as sample rate for 1 second intervals
    seconds_to_keep_in_stream_buffer = 60

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

    with StreamBuffer(
        source_reader=audio_source_reader, maxlen=maxlen
    ) as audio_stream_buffer:
        with StreamBuffer(
            source_reader=KeyboardInputSourceReader(), maxlen=maxlen
        ) as keyboard_stream_buffer:
            audio_buffer_reader = audio_stream_buffer.mk_reader()
            keyboard_buffer_reader = keyboard_stream_buffer.mk_reader()

            print('getch! Press any key! Esc to quit!')
            while True:
                keyboard_data = next(keyboard_buffer_reader)
                audio_data = next(audio_buffer_reader)

                if keyboard_data is not None:
                    index, keyboard_timestamp, char = keyboard_data
                    print(f'[Keyboard] {keyboard_timestamp}: {char}', end='\n\r')

                    if char == '\x1b':  # ESC key
                        break

                if audio_data is not None:
                    (
                        audio_timestamp,
                        waveform,
                        frame_count,
                        time_info,
                        status_flags,
                    ) = audio_data
                    print(
                        f'   [Audio] {audio_timestamp}:  {len(waveform)=} {type(waveform).__name__}',
                        end='\n\r',
                    )
