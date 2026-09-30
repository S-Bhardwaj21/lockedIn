from pathlib import Path
import subprocess
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
VOICE_DIR = ROOT / "voice"
OUTPUT_DIR = VOICE_DIR / "wav"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

OUTPUT_DIR.mkdir(exist_ok=True)

files = sorted(VOICE_DIR.glob("*.mp4"))

if not files:
    print("No .mp4 voice files found.")
    raise SystemExit(1)

print(f"Found {len(files)} voice clips.")
print("Converting AAC/MP4 → WAV...\n")

for source in files:
    target = OUTPUT_DIR / f"{source.stem}.wav"

    command = [
        FFMPEG,
        "-y",
        "-i", str(source),
        "-ac", "1",
        "-ar", "44100",
        "-sample_fmt", "s16",
        str(target),
    ]

    print(f"{source.name} → {target.name}")
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(f"FAILED: {source.name}")
        print(result.stderr.decode(errors="ignore"))
        raise SystemExit(1)

print(f"\nDone. Converted {len(files)} clips.")
print(f"WAV files are in: {OUTPUT_DIR}")