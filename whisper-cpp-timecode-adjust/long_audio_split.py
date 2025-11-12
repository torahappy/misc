import sys
import os
import argparse
from numpy.typing import NDArray
import scipy.io.wavfile as wavfile
import numpy as np
import typing

class CustomHelpFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        help = action.help
        if action.default is not argparse.SUPPRESS and help is not None:
            help += f' [default: {action.default}]'
        return help

parser = argparse.ArgumentParser(prog=str(os.path.basename(__file__)), description='split long wav file to smaller wav files', formatter_class=CustomHelpFormatter)
parser.add_argument('filename')
parser.add_argument('--window', type=int, default=100, help='the duration to calculate the silence index (in milliseconds)')
parser.add_argument('--segment_length', type=int, default=90000, help='the standard duration of each segment (in milliseconds)')
parser.add_argument('--search_resolution', type=int, default=100000, help='the stepping resolution for finding the optimal silence threshold value')
# parser.add_argument('--search_length', type=int, default=30000, help='the longest duration to search the most silent moment (in milliseconds)')
config = parser.parse_args(sys.argv[1:])

basepath = os.path.dirname(os.path.abspath(__file__))

wav_path = config.filename

wavfile_read = wavfile.read(wav_path)

rate: int = wavfile_read[0]
data = wavfile_read[1]
total_samples = data.shape[0]
if len(data.shape) == 1:
    data_mono = typing.cast(np.ndarray[tuple[int], np.dtype[typing.Any]], data)
else:
    data_mono = typing.cast(np.ndarray[tuple[int], np.dtype[typing.Any]], data.mean(axis = 1))

data_mono_abs = np.abs(data_mono)

window_samples: int = int(rate * (config.window / 1000.0))
window_ones = np.ones(window_samples) / window_samples

silence_index_py: list[np.float64] = []
for i in range(0, data_mono.shape[0], window_samples):
    if i + window_samples <= data_mono.shape[0]:
        silence_index_py.append(data_mono_abs[i:i+window_samples].dot(window_ones))
    else:
        silence_index_py.append(data_mono_abs[i:data_mono.shape[0]].dot(np.ones(data_mono.shape[0] - i) / (data_mono.shape[0] - i)))
silence_index: NDArray[np.float64] = np.array(silence_index_py, dtype=np.float64)
del silence_index_py
del data_mono_abs
del data_mono

silence_index_mean = silence_index.mean()
silence_index_std = silence_index.std()

# TODO: calculate the criteria more robustly
silence_criteria = silence_index_mean
segment_length_in_windows = config.segment_length // config.window

optimal = None

for i in np.arange(0, silence_criteria, silence_criteria / config.search_resolution):
    if np.convolve(
                np.ones(segment_length_in_windows),
                silence_index <= i, mode='valid'
            ).min() != 0:
        # if we slice silence_index into an array of length [segment_length_in_windows; the standard duration of the output segments], no matter where we slice, we certainly get at least one element that suffices the condition [silence_index<=i; the candidates of spots to cut the audio file], within the sliced array.
        optimal = i
        break

if optimal is None:
    raise ValueError('Sorry; something is wrong with the audio wave')

# i = the current time (unit = config.window milliseconds)
# s = loudness / silence level for each window (the bigger the louder)
# optimal = the optimal threshold which guarantees the existence of a [s <= optimal] spot within the range of [config.segment_length] milliseconds = [segment_length_in_windows] array units
last_match = 0
culmative = 0
segment_positions = []
for (i, s) in enumerate(silence_index):
    culmative += 1
    if culmative == segment_length_in_windows:
        segment_positions.append(last_match)
        culmative = i - last_match
    if s <= optimal:
        last_match = i

assert (np.diff(segment_positions) <= segment_length_in_windows).all()
assert silence_index.shape[0] - segment_positions[-1] <= segment_length_in_windows
assert np.array([silence_index[i] <= optimal for i in segment_positions]).all()

segment_positions_wave = []

for i in segment_positions:
    sample_first = config.window * (i - 1) / 1000 * rate
    sample_last  = config.window * i / 1000 * rate
    segment_positions_wave.append(int((sample_first + sample_last) / 2))

segment_positions_wave.append(total_samples)

current_frame = 0
for file_index, i in enumerate(segment_positions_wave):
    wavfile.write(os.path.join(basepath, 'orig', 'data-%s.wav' % file_index), rate, data[current_frame:i])
    current_frame = i
