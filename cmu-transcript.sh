#!/bin/env bash

# This scripts is used to connect all the others into
# one single streamlined process. You should normally
# never have to use the other scripts alone.

# Takes the file to analyze as its first argument.

file=$1

if ! test -f "$file"; then
	echo "ERROR: Please provide a valid file."
	echo "Usage : cmu-transcript [file_path]"
	exit
fi

save_trimmed=false

if [[ "$@" == *"--save"* || "$@" == *"-s"* ]]; then
	save_trimmed=true
fi

output=""
file_name=$(basename -- "$file")
trimmed_name="${file_name%.*}_trimmed.ogg"
echo $file_name

if [[ $save_trimmed = false ]]; then
	output="/tmp/$trimmed_name"
else
	output="data/trimmed/$file_name"
fi

echo "trimmed file will be saved as $output"
echo "trimming audio file..."
./src/trim-audio.py "$file" "$output"
echo "trimming of audio file done!"

echo "transcripting audio..."
./src/transcript.py "$output"
echo "transcritption done!"

if [[ $save_trimmed = false ]]; then
	rm $output
	echo "temporary audio file cleaned up!"
fi
