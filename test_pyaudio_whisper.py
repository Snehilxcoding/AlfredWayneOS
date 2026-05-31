import os
import tempfile
import wave
import pyaudio

from faster_whisper import WhisperModel

RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024

THRESHOLD = 350
SILENCE_SECONDS = 1.2
MAX_SECONDS = 15

print("Loading Whisper...")
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
)

print("Listening...")

frames = []
recording = False
silence_start = None
start_time = None

while True:

    data = stream.read(CHUNK, exception_on_overflow=False)

    import audioop
    volume = audioop.rms(data, 2)

    if not recording:

        if volume > THRESHOLD:
            print("Speech detected")
            recording = True
            start_time = __import__("time").time()
            frames.append(data)

    else:

        frames.append(data)

        if volume < THRESHOLD:

            if silence_start is None:
                silence_start = __import__("time").time()

            elif (
                __import__("time").time()
                - silence_start
                > SILENCE_SECONDS
            ):
                break

        else:
            silence_start = None

        if (
            __import__("time").time()
            - start_time
            > MAX_SECONDS
        ):
            break

stream.stop_stream()
stream.close()
p.terminate()

fd, path = tempfile.mkstemp(suffix=".wav")
os.close(fd)

wf = wave.open(path, "wb")
wf.setnchannels(CHANNELS)
wf.setsampwidth(
    pyaudio.PyAudio().get_sample_size(FORMAT)
)
wf.setframerate(RATE)
wf.writeframes(b"".join(frames))
wf.close()

print("Transcribing...")

segments, _ = model.transcribe(
    path,
    language="en",
    beam_size=5
)

text = " ".join(
    segment.text
    for segment in segments
).strip()

print("\nRESULT:")
print(text)

os.unlink(path)