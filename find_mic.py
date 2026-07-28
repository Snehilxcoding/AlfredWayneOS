import pyaudio
import audioop
import time

p = pyaudio.PyAudio()

print("=== INPUT DEVICES ===")
input_devices = []
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d["maxInputChannels"] > 0:
        print(f"Device {i}: {d['name']}")
        input_devices.append(i)

p.terminate()

print("\n=== VOLUME TEST — SPEAK NOW ===")
for device_id in input_devices[:6]:
    try:
        p2 = pyaudio.PyAudio()
        stream = p2.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=512,
        )
        volumes = []
        for _ in range(30):
            data = stream.read(512, exception_on_overflow=False)
            volumes.append(audioop.rms(data, 2))
            time.sleep(0.03)
        stream.stop_stream()
        stream.close()
        p2.terminate()
        print(f"Device {device_id}: max={max(volumes)} avg={sum(volumes)//len(volumes)}")
    except Exception as e:
        print(f"Device {device_id}: ERROR - {e}")