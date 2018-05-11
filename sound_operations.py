import wave
import pyaudio

from storage_helpers import audio_data


def record(duration, print_progress):
    ad = audio_data
    p = pyaudio.PyAudio()

    stream = p.open(format=ad.format(),
                    channels=ad.channels(),
                    rate=ad.rate(),
                    input=True,
                    frames_per_buffer=ad.chunk())

    frames = []

    fps = ad.rate() / ad.chunk()
    n_frames = int(fps * duration)
    remainder = ad.rate() * duration - ad.chunk() * n_frames

    for i in range(0, n_frames):
        data = stream.read(ad.chunk())
        frames.append(data)

        sec = int(i / fps)
        print_progress('{}/{}'.format(sec, duration))

    data = stream.read(remainder)
    frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio_data.set_data(frames)


def save(filename):
    ad = audio_data
    frames = ad._frames

    wf = wave.open(filename, 'wb')
    wf.setnchannels(ad.channels())
    wf.setsampwidth(pyaudio.PyAudio()
                    .get_sample_size(ad.format()))
    wf.setframerate(ad.rate())
    wf.writeframes(b''.join(frames))
    wf.close()


def open_(filename):
    file = wave.open(filename, 'rb')
    n_frames = file.getnframes()

    parts, remainder = int(n_frames / 1024), n_frames % 1024
    frames = []
    for i in range(0, parts):
        data = file.readframes(1024)
        frames.append(data)
    if remainder != 0:
        data = file.readframes(remainder)
        frames.append(data)
    file.close()

    audio_data.reset_params(channels=file.getnchannels(), rate=file.getframerate())
    audio_data.set_data(frames)


def play():
    ad = audio_data
    p = pyaudio.PyAudio()

    stream = p.open(format=ad.format(),
                    channels=ad.channels(),
                    rate=ad.rate(),
                    output=True,
                    frames_per_buffer=ad.chunk())

    data = audio_data.intensities()
    stream.write(data, data.size)

    stream.stop_stream()
    stream.close()
    p.terminate()