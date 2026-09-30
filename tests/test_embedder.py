import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic.embedder import MiniLMEmbedder

embedder = MiniLMEmbedder()

goal = embedder.embed("Finish my machine learning assignment")
relevant = embedder.embed("Gradient Descent Explained")
distracting = embedder.embed("MrBeast Shorts")

print("Providers:", embedder.providers)
print("Goal shape:", goal.shape)
print("Goal norm:", np.linalg.norm(goal))
print("Relevant similarity:", float(np.dot(goal, relevant)))
print("Distracting similarity:", float(np.dot(goal, distracting)))