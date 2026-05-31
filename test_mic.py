import sounddevice as sd
import numpy as np

devices = sd.query_devices()
print("Testing all input devices - SPEAK CONTINUOUSLY...\n")

for i, d in enumerate(devices):
    if d["max_input_channels"] > 0:
        try:
            audio = sd.rec(
                int(16000 * 1),
                samplerate=16000,
                channels=1,
                dtype="float32",
                device=i
            )
            sd.wait()
            peak = float(np.max(np.abs(audio.flatten())))
            name = d["name"][:45]
            print(f"Device {i:2d} | peak={peak:.6f} | {name}")
        except Exception as e:
            name = d["name"][:35]
            print(f"Device {i:2d} | ERROR | {name} | {str(e)[:40]}")