#!/bin/env python3

# DEPENDENCIES :
# - ffmpeg               https://ffmpeg.org/
# - vosk (pip)           https://github.com/alphacep/vosk-api

# install:
# sudo dnf install ffmpeg && pip3 install vosk

##################################################

# the language to use for the speech recognition
language="fr"

# the model to use for the speech recognition
model_name="vosk-model-small-fr-0.22"

output_dir="transcripts"

##################################################
import tempfile
import subprocess
from sys import argv
import os
from vosk import Model, KaldiRecognizer, SetLogLevel

if not os.access(output_dir, os.W_OK):
    print(f"ERROR: cannot access output directory (./{output_dir})")
    exit()

# vosk loglevel
SetLogLevel(0)

if len(argv) < 2:
    print("ERROR: please provide the file to analyze as the first argument to this script!")
    exit()

input_file = argv[1]

if not os.path.isfile(input_file):
    print("ERROR: the file provided does not exist or is not readable")
    exit()


file_name = input_file[max(input_file.rfind("/"),0):len(input_file)]
output_file = f"{output_dir}/{file_name}.txt"

SAMPLE_RATE=16000

use_light_model = "--light" in argv or "-l" in argv

model = Model(lang=language, model_name=model_name)
rec = KaldiRecognizer(model, SAMPLE_RATE)

command = [
    "ffmpeg",
    "-loglevel", "quiet",
    "-i", input_file,
    "-ar", str(SAMPLE_RATE),
    "-ac", "1",
    "-f", "s16le",
    "-"
]

warning_message =""" 
 ╭──────────────────────────────────────────────────────────────────────╮
 │                          - Sofian Tounsi -                           │
 │                                                                      │
 │    Ce texte est un retranscrit automatique, il n'est en aucun cas    │
 │        une copie fiable de la réalité. La fiabilité du modèle        │
 │     de détection de voix est très limitée en ce qui concerne le      │
 │ vocabulaire médical. Certains mots techniques peuvent donc parfois   │
 │ être retranscrits phonétiquement sans que le texte ne soit cohérent. │
 │                                                                      │
 │ Merci de ne pas utiliser ce texte pour prouver quoi que ce soit, il  │
 │    n'est pas suffisament fiable pour faire foi en cas de doute.      │
 │                                                                      │
 │                                                                      │
 ╰──────────────────────────────────────────────────────────────────────╯
 """

with open(output_file, "w") as out:
    out.write(warning_message)

text_data=""
with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
    while True:
        data = proc.stdout.read(4000)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            result = rec.Result()
            content = result[result.rfind(": \"")+3:result.rfind("\"")]
            print(content)
            #text_data += content+"\n"
            with open(output_file, "a") as out:
                out.write(content+"\n")
        else:
            #print(rec.PartialResult())
            pass


result = rec.FinalResult()

#with open(output, "w") as out_file:
#    out_file.write(text_data)       
