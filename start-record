#!/bin/env bash

# note: This script is made to work with PulseAudio only.

# DEPENDENCIES:
# - pulseaudio (pacat)
# - playerctl
# - date
#
# install:
# sudo dnf install playerctl date pulseaudio-libs

##################################################

# This script will loop indefinitely until a valid
# media to record is found. When it happens, the
# recording process starts.
# When the recording stops, either because the time
# frame has been exceeded or the media has changed,
# an OGG audio file is saved and the loop will resume.

##################################################

# When not recording, it checks each N seconds if
# a valid media is being played.
base_probe_interval_seconds=10

# At which hour should this script automatically stop.
cutoff_hour=19

# If one of these identifiers is present in the title
# of the media currently being played, the media is considered
# as a media to record.
title_identifiers=( "BA1 Med" "BA1_Med" "Statistiques pour médecins" )

# The directory in which all the data will be saved,
# can be relative or absolute.
save_directory="data"

# The exetension of the file.
file_format="ogg"

# How the timestamp in the file name should be formated.
name_timestamp_format="%Yy-%mm-%dd-%Hh"

# The media player to keep track of.
# [player] is the identifier used by playerctl, and
# [player_record_name] is the identifier used by pacat
player="firefox"
player_record_name="Firefox"

# Tries to record for this amount of minutes. The recording will
# persist for this amount of minutes unless interrupted
time_frame_minutes=50

# Checks each N seconds if the media player is currently playing
# valid content to record.
probe_interval_seconds=5

##################################################

get_player_status() {
	echo $(playerctl --player=$player status 2>/dev/null || echo "Not playing")
}

check_valid_media() {
	status=$(get_player_status) 
	playing=false

	# We are allowing paused media in order to prevent
	# interrupting the record if the media is only
	# paused, but might be resumed.
	if [[ $status == "Playing" || $status == "Paused" ]]; then
		playing=true
	fi
	
	if [[ $playing = false ]]; then return 1; fi
	# From here, the player is validated as playing.
	
	content=$(playerctl --player=$player metadata --format "{{ title }}")
	
	
	valid_title=false
	for ((i = 0; i < ${#title_identifiers[@]}; i++))
	do
		identifier=${title_identifiers[$i]}
		if [[ $content == *"$identifier"* ]]; then
			valid_title=true
			break
		fi
	done
	
	if ! [[ $valid_title = true ]]; then return 1; fi
	return 0
}

get_log_timestamp() {
	echo "[$(date '+%Y.%m.%d %H:%M:%S')]"
}

log_info() {
	echo "$(get_log_timestamp) $1"
}

start_record() {
	echo "$(get_log_timestamp) valid media found, beginning to record..."
	# wait until the media gets resumed to beggin recording
	if [[ $(get_player_status) == "Paused" ]]; then
		echo "$(get_log_timestamp) waiting for the media to be resumed..."
		while [[ $(get_player_status) == "Paused" ]];
		do
			sleep $(( ${probe_interval_seconds}/2 ))
		done
	fi

	track=$(playerctl --player=$player metadata --format "{{ title }}")
	timestamp=$(date "+${name_timestamp_format}")
	file_name="${timestamp}_$(echo ${track//\ /-} | sed 's/[^0-9A-Za-z_)()-]*//g').${file_format}"
	

	mkdir -p ${save_directory}
	
	target="${save_directory}/${file_name}"
	if test -f $target; then log_info "file already exists, appending data..."; fi
	# There is a risk that the main microphone will be used instead, but it should not be the case.
	#############
	# recording #
	#############
	pid=$(/bin/env pacat -r -d ${player_record_name} --volume=65536 --rate=44100 --channels=2 --file-format=ogg $target & echo $!)
	#############
	# recording #
	#############
	echo "$(get_log_timestamp) recording started!"
	# for a reason I ignore, the recording always seems to be cut 2 seconds to early,
	# so I've added a 2 second delay to the end_epoch
	end_epoch=$(( $(date "+%s") + (${time_frame_minutes}*60) ))
	while [[ $(date "+%s") -lt $end_epoch ]]
	do
		current=$(playerctl --player=$player metadata --format "{{ title }}")
		if ! check_valid_media; then
			echo "$(get_log_timestamp) media not valid, ending recording"
			break
		fi
		if ! [[ $track == $current ]]; then
			echo "$(get_log_timestamp) media has changed, interrupting current record"
			break
		fi
		sleep ${probe_interval_seconds}
	done

	if [[ $(date "+%s") -ge $end_epoch ]]; then
		echo "time frame exceeded, cutting recording... (this is normal)"
	fi
	
	kill -TERM $pid
	echo "$(get_log_timestamp) recording of ${file_name} done!"
}

echo "$(get_log_timestamp) media check loop started"
while [[ $(date "+%-H") -le ${cutoff_hour} ]];
do
	if check_valid_media; then
		start_record
		echo "$(get_log_timestamp) media check loop resumed"
	else
		sleep ${base_probe_interval_seconds}
	fi
done
