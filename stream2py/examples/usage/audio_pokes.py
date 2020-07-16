from functools import partial
from io import BytesIO
from itertools import chain
from contextlib import contextmanager

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


def waveform_to_bytes(wf, sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH):
    b = BytesIO()
    subtype = read_kwargs_for_sample_width[sample_width]['subtype']
    sf.write(b, wf, samplerate=sr, format='RAW', subtype=subtype)
    b.seek(0)
    return b.read()


########################################################################################################################

def find_a_device_index(filt='microphone', dflt=None):
    if isinstance(filt, str):
        match_str = filt

        def filt(x):
            return match_str in x.get('name', match_str).lower()
    match = next(filter(filt, PyAudioSourceReader.list_device_info()), None)
    return (match is not None and match['index']) or dflt


def ensure_source_input_device_index(input_device_index=None):
    input_device_index = input_device_index or find_a_device_index(filt='microphone', dflt=None)
    if input_device_index is not None:
        return input_device_index
    else:
        # TODO: Nicer way to print info (perhaps only relevant info, formated as table)
        print("Need a valid input_device_index. Calling live_audio_chks.list_device_info() to information about the "
              "devices I can detect:\n")
        for item in PyAudioSourceReader.list_device_info():
            print(item)
            print("")
        print("---> Look in the list above and choose an input_device_index (it's called index in the printout above) "
              "that seems to be right for you!")
        raise ValueError("Need a valid input_device_index")


@contextmanager
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
    input_device_index = ensure_source_input_device_index(input_device_index)

    seconds_per_read = chk_size / sr

    maxlen = int(stream_buffer_size_s / seconds_per_read)
    source_reader = PyAudioSourceReader(rate=sr, width=sample_width, channels=n_channels, unsigned=True,
                                        input_device_index=input_device_index,
                                        frames_per_buffer=chk_size)

    _bytes_to_waveform = partial(bytes_to_waveform, sr=sr, n_channels=n_channels, sample_width=sample_width)
    with StreamBuffer(source_reader=source_reader, maxlen=maxlen) as stream_buffer:
        """keep open and save to file until stop event"""
        yield iter(stream_buffer)


live_audio_chks.list_device_info = PyAudioSourceReader.list_device_info


# TODO: live_wf_ctx and live_wf: Lot's of repeated code. Address this.
@contextmanager
def live_wf_ctx(input_device_index=None, sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH, n_channels=DFLT_N_CHANNELS,
                chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """A context manager providing a generator of live waveform sample values taken from a stream sourced
    from specified microphone.

    :param rate: Specifies the desired sample rate (in Hz)
    :param sample_bytes: Sample width in bytes (1, 2, 3, or 4)
    :param n_channels: The desired number of input channels. Ignored if input_device is not specified (or None).
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)

    >>> from time import sleep
    >>> from itertools import islice
    >>> # enter the id of your microphone and get a live waveform source!
    >>> # (if None, will try to figure it out)
    >>> with live_wf_ctx(input_device_index=None) as wf_gen:
    ...
    ...     # Now wait a bit, say some silly things, then ask for a few samples...
    ...     sleep(1.1)
    ...     wf = list(islice(wf_gen, 0, 44100 * 1))
    >>> # and now listen to that wf and be embarrassed...
    >>> # ... or just look at the size (less fun though)
    >>> len(wf)
    44100
    """
    with live_audio_chks(input_device_index=input_device_index,
                         sr=sr, sample_width=sample_width, n_channels=n_channels,
                         chk_size=chk_size,
                         stream_buffer_size_s=stream_buffer_size_s) as live_audio_chunks:
        _bytes_to_waveform = partial(bytes_to_waveform, sr=sr, n_channels=n_channels, sample_width=sample_width)
        yield chain.from_iterable(map(lambda x: _bytes_to_waveform(x[1]), live_audio_chunks))
    live_audio_chunks.close()


def live_wf(input_device_index=None, sr=DFLT_SR, sample_width=DFLT_SAMPLE_WIDTH, n_channels=DFLT_N_CHANNELS,
            chk_size=DFLT_CHK_SIZE, stream_buffer_size_s=DFLT_STREAM_BUF_SIZE_S):
    """A generator of live waveform sample values taken from a stream sourced from specified microphone.

    :param rate: Specifies the desired sample rate (in Hz)
    :param sample_bytes: Sample width in bytes (1, 2, 3, or 4)
    :param n_channels: The desired number of input channels. Ignored if input_device is not specified (or None).
    :param input_device_index: Index of Input Device to use. Unspecified (or None) uses default device.
    :param stream_buffer_size_s: How many seconds of data to keep in the buffer (i.e. how far in the past you can see)

    >>> from time import sleep
    >>> from itertools import islice
    >>> # enter the id of your microphone and get a live waveform source!
    >>> # (if None, will try to figure it out)
    >>> wf_gen = live_wf(input_device_index=None)
    >>>
    >>> # Now wait a bit, say some silly things, then ask for a few samples...
    >>> sleep(1.2)
    >>> wf = list(islice(wf_gen, 0, 44100 * 1))
    >>> # and now listen to that wf and be embarrassed...
    >>> # ... or just look at the size (less fun though)
    >>> len(wf)
    44100

    Don't forget to close! (or use live_wf_ctx context manager).
    >>> wf_gen.close()

    After wf_gen is closed, you can still ask it for data.
    It just won't give you any.
    >>> wf = list(islice(wf_gen, 0, 44100 * 1))
    >>> len(wf)
    0

    Here wf_gen is a generator, so closing means: https://docs.python.org/2.5/whatsnew/pep-342.html
    """
    # TODO: Find a way to copy from containing function's signature and calling LiveAudioChunks with that
    with live_wf_ctx(input_device_index=input_device_index,
                     sr=sr, sample_width=sample_width, n_channels=n_channels,
                     chk_size=chk_size,
                     stream_buffer_size_s=stream_buffer_size_s) as live_wf:
        yield from live_wf


live_wf.list_device_info = PyAudioSourceReader.list_device_info


def simple_chunker(a, chk_size: int):
    return zip(*([iter(a)] * chk_size))


def rechunker(chks, chk_size):
    yield from simple_chunker(chain.from_iterable(chks), chk_size)


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
    # Create an interface to PortAudio
    p = pyaudio.PyAudio()

    # Open a .Stream object to write the WAV file to
    # 'output = True' indicates that the sound will be played rather than recorded
    stream = p.open(format=sample_width,
                    channels=1,
                    rate=int(sr / 2),  # why? I don't know. It's just accelerated if I don't
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
