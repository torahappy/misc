#!/bin/python3
import wave
import glob
import re
import json
from utils import *

def sort_key(x: str):
    m = re.findall(r"\d+", x)
    return int(m[-1])

wavs = sorted(glob.glob('./orig/*.wav'), key=sort_key)

culmative_sec = 0

out_data = []

for wav_filename in wavs:
    out_data_segment = []
    out_data.append(out_data_segment)
    print("FileName", wav_filename, wav_filename + ".json")
    with wave.open(wav_filename, 'r') as f:
        len_sec = f.getnframes() / f.getframerate()
    print("Length", to_timecode(len_sec), "CurrentCursor", to_timecode(culmative_sec))
    with open(wav_filename + ".json") as f:
        txt_data = json.loads(f.read())
    for line in txt_data['transcription']:
        m1 = re.match(r'(\d\d):(\d\d):(\d\d),(\d\d\d)', line['timestamps']['from'])
        m2 = re.match(r'(\d\d):(\d\d):(\d\d),(\d\d\d)', line['timestamps']['to'])
        txt = line['text']
        if m1 and m2:
            [h1, m1, s1, x1] = m1.groups()
            [h2, m2, s2, x2] = m2.groups()
            t_start = (int(h1), int(m1), int(s1), int(x1) / 1000)
            t_end = (int(h2), int(m2), int(s2), int(x2) / 1000)
            t_start_sec_fix = from_timecode(t_start) + culmative_sec
            t_end_sec_fix = from_timecode(t_end) + culmative_sec
            t_start_fix = to_timecode(t_start_sec_fix)
            t_end_fix = to_timecode(t_end_sec_fix)
            print(t_start_fix, t_end_fix, txt)
            out_data_segment.append({
                "start": t_start_fix,
                "end": t_end_fix,
                "text": txt
            })
    culmative_sec += len_sec

print("Total Length", to_timecode(culmative_sec))

with open("out.json", "w") as f:
    json.dump(out_data, f)
