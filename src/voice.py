from pathlib import Path
import random
import threading
import winsound


class VoicePersonality:
    def __init__(self, voice_dir=None):
        root = Path(__file__).resolve().parent.parent
        self.voice_dir = Path(voice_dir) if voice_dir else root / "voice" / "wav"
        self.clips = sorted(self.voice_dir.glob("*.wav"))
        self.last_clip = None
        self.intervention_count = 0

        if not self.clips:
            print(f">>> WARNING: No voice clips found in {self.voice_dir}")
        else:
            print(f">>> Voice personality loaded: {len(self.clips)} clips")

    def _choose_clip(self):
        if len(self.clips) == 1:
            return self.clips[0]

        choices = [clip for clip in self.clips if clip != self.last_clip]
        return random.choice(choices)

    def intervene(self):
        if not self.clips:
            return

        clip = self._choose_clip()
        self.last_clip = clip
        self.intervention_count += 1

        print(f">>> LOCKEDIN voice: {clip.name}")

        threading.Thread(
            target=self._play_clip,
            args=(clip,),
            daemon=True,
        ).start()

    def _play_clip(self, clip):
        try:
            winsound.PlaySound(
                str(clip),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        except Exception as exc:
            print(f">>> Voice playback failed: {exc}")

    def stop(self):
        winsound.PlaySound(None, winsound.SND_PURGE)