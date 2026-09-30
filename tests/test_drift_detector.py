import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic.embedder import MiniLMEmbedder
from semantic.drift_detector import DriftDetector

embedder = MiniLMEmbedder()
detector = DriftDetector()

goal = embedder.embed("Finish my machine learning assignment")

activities = [
    ("Gradient Descent Explained", 30),
    ("MrBeast Shorts", 20),
    ("MrBeast Shorts", 50),
]

for activity, duration in activities:
    embedding = embedder.embed(activity)
    result = detector.assess(goal, embedding, activity, duration)
    print(f"{result.activity:<30} similarity={result.similarity:.4f} duration={result.duration_seconds:.0f}s state={result.state.value}")