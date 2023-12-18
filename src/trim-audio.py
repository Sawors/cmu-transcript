#!/bin/env python3

# DEPENDENCIES : pydub, numpy, soundfile

##################################################

# Defines how much time does an analysis frame covers (in seconds).
# These frames are used for sound analysis as a simplification of the actual sound frames
# to lower the data actually being stored in RAM.
# If you want maximum precision, set this to 1/sample_rate
# (ususally 1/44100)
visual_frame_duration=1/2

# Defines how much time ahead should the program look 
# for speech presence
check_range_seconds = 10

# Sounds louder than this percentage of the max volume will be considered as speech
volume_threshold_percentage = 0.2

##################################################from pydub import AudioSegment
import tempfile, os, soundfile, threading, numpy
from os import sys
from soundfile import SoundFile
from time import sleep
from playsound import playsound
from statistics import median
from datetime import timedelta

if len(sys.argv) < 2:
    print("ERROR: Please provide a file to trim as the first argument.")
    exit()

file_name = sys.argv[1]
file_format = file_name[file_name.rfind(".")+1:len(file_name)]

if not file_format.upper() in soundfile.available_formats().keys():
    print(f"ERROR: File format {file_format.upper()} cannot be used.")
    print("Please use one of the following formats :")
    for key, value in soundfile.available_formats().items():
        print("  - "+key+": "+value)
    exit()

output_file = "trimmed.ogg"
try:
    if len(sys.argv) >= 3 and os.access(os.path.dirname(sys.argv[2]), os.W_OK):
        output_file = sys.argv[2]
    else:
        output_file = file_name[0:file_name.rfind(".")]+"_trimmed"+"."+file_format
except:
    print(f"WARNING: an error occured while defining the output file. This is not fatal, but the trimmed file will be saved as {output_file}.")


verbose_mode = "--verbose" in sys.argv or "-v" in sys.argv
if verbose_mode: print("  using verbose mode")

block_size = 1024

# each audio frame is 1/sample_rate of a second.

info = soundfile.info(file_name)

duration=info.duration
# the duration of each visual frame, in seconds
total_visual_frame=int(duration/visual_frame_duration)+1

visual_frames = [0]*total_visual_frame

with SoundFile(file_name) as sound:
    
    for visual_frame_number in range(0,total_visual_frame):
        mean = 0
        total = 0
        samples = 0
        # https://python-soundfile.readthedocs.io/en/0.11.0/index.html?highlight=blocks#soundfile.SoundFile.blocksize
        for block in sound.blocks(blocksize=block_size, frames=int(info.samplerate*visual_frame_duration)):
            # rms of the block :
            block_rms = numpy.sqrt(numpy.mean(block**2))
            total += block_rms
            samples += 1
        visual_frames[visual_frame_number] = total/samples


if verbose_mode:
    print(f"  infos of sound file:\n  {info}")
    print(f"  file size (in bytes): {os.path.getsize(file_name)}")
    print(f"  visual frame duration: {visual_frame_duration} fps so for {int(duration)}s we have {total_visual_frame} visual frames")

max_volume = max(visual_frames)
min_volume = min(visual_frames)

volume_threshold = min_volume+(volume_threshold_percentage*(max_volume-min_volume))

start_frame = 0
end_frame = len(visual_frames)-1

check_range_frames = int(check_range_seconds/visual_frame_duration)+1
# get start frame
for index, frame in enumerate(visual_frames):
    if frame >= volume_threshold:
        ahead = visual_frames[min(index,len(visual_frames)-1):min(index+check_range_frames,len(visual_frames)-1)]
        mean_ahead = median(ahead)
        if mean_ahead >= volume_threshold:
            start_frame = index
            break
            
# get end frame     
for reverse_index in range(len(visual_frames)-1,0,-1):
    frame = visual_frames[reverse_index]
    if frame >= volume_threshold:
        ahead = visual_frames[max(reverse_index-check_range_frames,0):reverse_index]
        mean_ahead = median(ahead)
        if mean_ahead >= volume_threshold:
            end_frame = reverse_index
            break

print(f"  start ({timedelta(seconds=start_frame*visual_frame_duration)}) and end ({timedelta(seconds=end_frame*visual_frame_duration)}) positions found, writting to file")        

def visual_to_audio(visual_frame:int) -> int:
    return int(visual_frame_duration*info.samplerate*visual_frame)

def audio_to_visual(audio_frame:int) -> int:
    return int((audio_frame/info.samplerate)/visual_frame_duration)

def trim_audio(file:str, output_file:str, start_frame_audio:int, end_frame_audio):
    info = soundfile.info(file)
    frame_amount_audio = end_frame_audio-start_frame_audio
    with SoundFile(file) as sound, SoundFile(output_file, "w", info.samplerate, info.channels) as output:
        sound.seek(start_frame_audio)
        for block in sound.blocks(blocksize=1024**2, frames=frame_amount_audio):
            output.write(block)

trim_audio( file=file_name, 
            output_file=output_file, 
            start_frame_audio=visual_to_audio(start_frame), 
            end_frame_audio=visual_to_audio(end_frame)
            )
print("  file written")

if verbose_mode:
    width = os.get_terminal_size()[0]-3
    
    print(f"  look ahead duration: {check_range_seconds}s")
    print(f"  each visual frame takes {visual_to_audio(1)} audio frames")
    print(f"  start (visual frame): {start_frame}")
    print(f"  end (visual frame): {end_frame}")
    print("  threshold:\n  "+"0"*(1+len(str(total_visual_frame))*2)+" "+"█"*int((volume_threshold/max_volume)*(width-9))+"\n")

    for index, frame in enumerate(visual_frames):
        position = str(timedelta(seconds=int(index*visual_frame_duration)))
        
        if index == start_frame:
            print("  start"+"-"*(width-5))
        print(f"  {position} {'█'*int((frame/max_volume)*(width-len(position)))}")
        if index == end_frame:
            print("  end"+"-"*(width-3))
