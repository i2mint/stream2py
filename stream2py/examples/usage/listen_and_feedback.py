import numpy as np

from stream2py.examples.usage.audio_pokes import (
    DFLT_SR, DFLT_SAMPLE_WIDTH, DFLT_CHK_SIZE, DFLT_STREAM_BUF_SIZE_S,
    live_wf_ctx, waveform_to_bytes
)

######################################################################################################
# Example applications

from itertools import islice
import pyaudio
from time import sleep
import soundfile as sf
from io import BytesIO


def asis(wf):
    return wf


def reverse_and_print(wf):
    print('reversed sounds like this...')
    return wf[::-1]


def listen_and_shout(transform_wf=asis, every_seconds=1, input_device_index=None,
                     sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH,
                     chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """

    :param transform_wf: Callable that will be called on recorded waveform before outputting to speakers
    :param every_seconds: Frequency
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param sr: Specifies the desired sample rate (in Hz)
    :param sample_width: Sample width in bytes (1, 2, 3, or 4)
    :param chk_size:
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)

    """
    # Create an interface to PortAudio
    p = pyaudio.PyAudio()

    if sample_width != 2:
        from warnings import warn
        warn("I've never seen it work with anything than sample_width=2")
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(format=sample_width,
                    channels=1,
                    rate=int(sr / sample_width),  # why? I don't know. I guess unit is bytes here?
                    output=True)

    with live_wf_ctx(input_device_index, sr=sr,
                     sample_width=sample_width, chk_size=chk_size,
                     stream_buffer_size_s=stream_buffer_size_s) as wf_gen:
        while True:
            try:
                wf = list(islice(wf_gen, int(sr * every_seconds)))
                b = waveform_to_bytes(transform_wf(wf), sr, sample_width)
                stream.write(b)
            except KeyboardInterrupt:
                print('KeyboardInterrupt... Closing down')
                break

    # Close and terminate the stream
    stream.close()
    p.terminate()


def vol(wf):
    return np.std(np.abs(wf))


def print_vol_num(wf):
    print(f"{vol(wf):0.04f}")


def print_vol(wf, char='-', gain=2, saturation_vol=99):
    log_vol = int(min(saturation_vol, max(1, gain * np.std(np.abs(wf)) / 100)))
    print(f"{char * log_vol}")


def push_sound_through_a_pipe(callback=print_vol_num, every_seconds=1, input_device_index=None,
                              sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH,
                              chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """

    :param transform_wf: Callable that will be called on recorded waveform before outputting to speakers
    :param every_seconds: Frequency
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param sr: Specifies the desired sample rate (in Hz)
    :param sample_width: Sample width in bytes (1, 2, 3, or 4)
    :param chk_size:
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)

    """
    with live_wf_ctx(input_device_index, sr=sr,
                     sample_width=sample_width, chk_size=chk_size,
                     stream_buffer_size_s=stream_buffer_size_s) as wf_gen:
        while True:
            try:
                callback(list(islice(wf_gen, int(sr * every_seconds))))
            except KeyboardInterrupt:
                print('KeyboardInterrupt... Closing down')
                break
