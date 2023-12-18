#!/bin/env python3

# DEPENDENCIES :
# - ffmpeg               https://ffmpeg.org/
# - vosk (pip)           https://github.com/alphacep/vosk-api

# install:
# sudo dnf install ffmpeg && pip3 install vosk

##################################################

# The model and API to use can be configured without changing
# the variables. The programm accepts arguments to define these
# parameters.
#
# Usage :
# transcript.py [OPTIONS] audio_input_file
# The optional parameters are :
# --api=api_name            The API to use for the transcription
# --model=model_name        The model to use for the corresponding API.
# --output=output_dir       A directory where the transcripted audio should be stored.
# --language=language_code  The language of the speech in the audio file, in its short form (fr, en, jp).

##################################################

# Please consider that any data provided as arguments to the script
# will override the variables defined here.

# the language to use for the speech recognition
language="fr"

# the model to use for the speech recognition
# models for vosk:
# - vosk-model-fr-0.22
# - vosk-model-fr-0.6-linto
# - vosk-model-fr-0.6-linto-2.0.0
# - vosk-model-fr-0.6-linto-2.2.0
# - vosk-model-small-fr-0.22
# - vosk-model-small-fr-pguyot-0.3
# models for whisper:
# - tiny
# - base
# - small
# - medium
# - large (NOT RECOMMENDED, VERY HEAVY TO USE)
model_name="vosk-model-fr-0.22"

output_dir="transcripts"

# "vosk" or "whisper"
transcription_api="vosk"

# A message that will be inserted before the text in the transcript output
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
 │               https://github.com/Sawors/cmu-transcript               │
 ╰──────────────────────────────────────────────────────────────────────╯
 
"""

# If set to true, the output of the transcription will be formatted
# to be more readable and comparable
pretty_output=True
pretty_line_length=80

# FOR THE WHISPER API ONLY
# The prompt that will be submited to the model before the speech recognition
# begins. Used to give some context or special vocabulary.
whisper_initial_prompt = "L'audio à transcrire est un cours de niveau universitaire en médecine. Il couvre des sujets généraux de médecine, et comporte un vocabulaire technique de médecine et de sciences biomédicales. Le sujet du cours est {}. La retranscription se fait en français."

##################################################
import tempfile
import subprocess
from sys import argv
import os

if not os.access(output_dir, os.W_OK):
    print(f"ERROR: cannot access output directory (./{output_dir})")
    exit()

if len(argv) < 2:
    print("ERROR: please provide the file to analyze as the last argument to this script!")
    exit()

input_file = argv[len(argv)-1]

if not os.path.isfile(input_file):
    print("ERROR: the file provided does not exist or is not readable")
    exit()


for arg in argv:
    payload=arg[arg.find("=")+1:len(arg)]
    if "--api=" in arg:
        transcription_api=payload
    elif "--model=" in arg:
        model_name=payload
    elif "--output=" in arg:
        output_dir=payload
    elif arg == "--raw" or arg == "-r":
        pretty_output=False
        

print(f"using the {transcription_api} api with the {model_name} model")

file_name = input_file[input_file.rfind("/")+1:min(input_file.rfind("."),len(input_file))]
subject=file_name[file_name.find('_')+1:file_name.rfind('_')].replace("BA1-Med","").replace("-"," ")
whisper_initial_prompt=whisper_initial_prompt.format(subject)
output_file = f"{output_dir}/{transcription_api}.{model_name}.{file_name}.txt"

def check_model_presence(model_list:list, print_error:True) -> bool:
    if model_name in model_list:
        return True
    elif print_error:
            print(f"ERROR: Model \'{model_name}\' is not available in the {transcription_api} API.\nAvailable models for the language [{language}] are :")
            if transcription_api == "vosk":
                for mdnm in model_list:
                    if language in mdnm:
                        print(f"-> {mdnm}")
                print(f"To get all available models, run \'vosk-transcriber --list-models\' in a terminal.")
            elif transcription_api == "whisper":
                for mdnm in model_list:
                    if ("en" in language and ".en" in mdnm) or not ".en" in mdnm:
                        print(f"-> {mdnm}")
                print(f"To get all available models, see https://github.com/openai/whisper#available-models-and-languages ")
            return False

if transcription_api == "vosk":
    from vosk import Model, KaldiRecognizer, SetLogLevel, MODEL_LIST_URL
    import requests

    model_list = []
    try:
        response = requests.get(MODEL_LIST_URL, timeout=5)
        for model in response.json():
            model_list.append(model["name"])
    except:
        pass

    if not check_model_presence(model_list=model_list, print_error=True):exit(1)
    
    # vosk loglevel
    SetLogLevel(0)
    
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
    raw_text=""
    text=""
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        while True:
            # Why precisely 4000 ? Only god (and the guy on stackoverflow) knows...
            data = proc.stdout.read(4000)
            if len(data) == 0:
                break
    
            if rec.AcceptWaveform(data):
                result = rec.Result()
                content = result[result.rfind(": \"")+3:result.rfind("\"")]
                print(content)
                raw_text += content+" "
            else:
                #print(rec.PartialResult())
                pass

    cut_signal=False
    if pretty_output:
        for index,char in enumerate(text):
            if index%pretty_line_length == 0 and index > 0:
                cut_signal = True
            if cut_signal == True and not char.isalnum():
                cut_signal = False
                text += char+"\n"
    else:
        text = raw_text
    
    with open(output_file, "w") as out:
        out.write(warning_message+"\n"+text)

elif transcription_api == "whisper":
    import whisper
    
    if not check_model_presence(model_list=whisper.available_models(), print_error=True):exit(1)

    # https://github.com/openai/whisper
    model = whisper.load_model(model_name)
    
    # https://github.com/openai/whisper/blob/8bc8860694949db53c42ba47ddc23786c2e02a8b/whisper/transcribe.py#L37
    print("beginning transcription...")
    result = model.transcribe(
                                input_file, 
                                initial_prompt=whisper_initial_prompt, 
                                language=language
                                )
    raw_text = result["text"]
    text = ""
    print("transcription done!")
    print("writting to file...")
    print(result.keys())

    cut_signal=False
    if pretty_output:
        for index,char in enumerate(text):
            if index%pretty_line_length == 0 and index > 0:
                cut_signal = True
            if cut_signal == True and not char.isalnum():
                cut_signal = False
                text += char+"\n"       
    else:
        text = raw_text

    with open(output_file, "w") as out:
        out.write(warning_message+"\n"+text)


else:
    print(f"ERROR: please specify a valid speech recognition api (api \'{transcription_api}\' not recognized)")   
    exit()
print(f"everything save and finished, transcription is saved as {output_file}")
