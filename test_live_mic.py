# test_live_mic.py

import pyaudio
import audioop

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
)

print("Speak into the microphone...")

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    volume = audioop.rms(data, 2)
    print(volume)