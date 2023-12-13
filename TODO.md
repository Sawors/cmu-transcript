## TODO
- [ ] trim the audio input
	- [X] remove heads and tails blanks -> limit the audio to only the content of the course
	- [ ] **if necessary**, denoise the audio to allow better speech recognition
- [ ] feed the audio data to the speech recognition model
	- [ ] slice the audio in *slices of ~10 minutes*, or make a mark each 10 minutes
	- [ ] BETTER IDEA -> **OR** instead of slices of 10 minutes, we can do 1 minute per line of text !
	- [ ] **if results are poor with only one model**, combine mutliple models to have a better output
- [X] output the text data into a file
	- [ ] add time markers for every 10 minutes of audio to simplify synchronisation
- [ ] split the pipeline in a server-client relation

---

We have a performance problem: the trimming and speech recognition should not be done on the
recording device. These 2 operations are performance intensive, and not suited for being run
on a portable machine.
All recordings should be sent to the server, and trimmed/recognized on the server.

---

We currently do not have time splits, I might try to find a way to get time
from within the analysis process loop, but currently we do not have
indicators.

In the current pipeline, we are using the [vosk](https://github.com/alphacep/vosk-api) API
with fairly decent results using only the light french model. Tests need to be done in order
to verify if better results are yielded by the heavy model. If no improvement can be noticed,
we might want to test with the 2 other community models (pguyot and linto).

Another API worth considering is the [whisper](https://github.com/openai/whisper) API. Although
it seems that this API is less customizable, it has a higher popularity and is backed by
OpenAI, which is a pretty good insurance of quality.

But please note that whatever API we are using, it WILL struggle with specific medicine 
vocabulary and might need further training and vocabulary enhancements in order to
develop a better speech recognition ability. With the generals models, the text
almost always phoenetically matches the audio, but this state is not satisfying enough. 
