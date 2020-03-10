from functools import partial
from io import BytesIO
from itertools import chain

from stream2py import StreamBuffer
from stream2py.sources.audio import PyAudioSourceReader

######## AUDIO: TODO: service this will builtins only ##################################################################
import soundfile as sf

DFLT_SR = 44100
DFLT_N_CHANNELS = 1
DFLT_SAMPLE_WIDTH = 2
DFLT_CHK_SIZE = 1024 * 4
DFLT_STREAM_BUF_SIZE_S = 60

read_kwargs_for_sample_width = {
    2: dict(format='RAW', subtype='PCM_16', dtype='int16'),
    3: dict(format='RAW', subtype='PCM_24', dtype='int32'),
    4: dict(format='RAW', subtype='PCM_32', dtype='int32'),
}


def bytes_to_waveform(b, sr=DFLT_SR, n_channels=DFLT_N_CHANNELS, sample_width=DFLT_SAMPLE_WIDTH):
    return sf.read(BytesIO(b), samplerate=sr, channels=n_channels, **read_kwargs_for_sample_width[sample_width])[0]


########################################################################################################################


def live_audio_chks(input_device_index=None, sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH, n_channels=DFLT_N_CHANNELS,
                    chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """A generator of live chunks of audio bytes taken from a stream sourced from specified microphone.

    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param sr: Specifies the desired sample rate (in Hz)
    :param sample_bytes: Sample width in bytes (1, 2, 3, or 4)
    :param n_channels: The desired number of input channels. Ignored if input_device is not specified (or None).
    :param sample_width: Specifies the number of frames per buffer.
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)
    """

    if input_device_index is None:  # TODO: Has no effect. See why.
        # TODO: Nicer way to print info (perhaps only relevant info, formated as table)
        print("Need a valid input_device_index. Here's some information aboout that:")
        for item in PyAudioSourceReader.list_device_info():
            print(item)
            print("")
        raise ValueError("Need a valid input_device_index")

    seconds_per_read = chk_size / sr

    maxlen = int(stream_buffer_size_s / seconds_per_read)
    source_reader = PyAudioSourceReader(rate=sr, width=sample_width, channels=n_channels, unsigned=True,
                                        input_device_index=input_device_index,
                                        frames_per_buffer=chk_size)

    _bytes_to_waveform = partial(bytes_to_waveform, sr=sr, n_channels=n_channels, sample_width=sample_width)
    with StreamBuffer(source_reader=source_reader, maxlen=maxlen) as stream_buffer:
        """keep open and save to file until stop event"""
        yield from iter(stream_buffer)


live_audio_chks.list_device_info = PyAudioSourceReader.list_device_info


def live_wf(input_device_index=None, sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH, n_channels=DFLT_N_CHANNELS,
            chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """A generator of live waveform sample values taken from a stream sourced from specified microphone.

    :param rate: Specifies the desired sample rate (in Hz)
    :param sample_bytes: Sample width in bytes (1, 2, 3, or 4)
    :param n_channels: The desired number of input channels. Ignored if input_device is not specified (or None).
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)

    >>> # if you're not sure of the index of your microphone, use this to see a list
    >>> device_info_list = live_wf.list_device_info()
    >>> wf_gen = live_wf(input_device_index=1)  # enter the id of your microphone and get a live waveform source!
    >>>
    >>> # Now wait a bit, say some silly things, then ask for a few samples...
    >>> from itertools import islice
    >>> wf = list(islice(wf_gen, 0, 44100 * 3))
    >>> # and now listen to that wf and be embarrassed...
    >>>
    """
    # TODO: Find a way to copy from containing function's signature and calling LiveAudioChunks with that
    live_audio_chunks = live_audio_chks(
        input_device_index=input_device_index, sr=sr, sample_width=sample_width, n_channels=n_channels,
        chk_size=chk_size, stream_buffer_size_s=stream_buffer_size_s)
    _bytes_to_waveform = partial(bytes_to_waveform, sr=sr, n_channels=n_channels, sample_width=sample_width)
    yield from chain.from_iterable(map(lambda x: _bytes_to_waveform(x[1]), live_audio_chunks))


live_wf.list_device_info = PyAudioSourceReader.list_device_info


def simple_chunker(a, chk_size: int):
    return zip(*([iter(a)] * chk_size))


def rechunker(chks, chk_size):
    yield from simple_chunker(chain.from_iterable(chks), chk_size)
