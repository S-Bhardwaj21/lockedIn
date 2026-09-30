from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic.decision import classify_alignment

CASES = [
    (0.3669, "Finish my ML assignment", "Watch a Gradient Descent lecture"),
    (0.2321, "Finish my ML assignment", "Watch a Python tutorial"),
    (0.1753, "Finish my ML assignment", "Watch Instagram memes"),
    (0.9232, "Watch a C-drama", "Watch a C-drama episode"),
    (0.2203, "Watch a C-drama", "Watch an ML lecture"),
    (0.8302, "Cook pasta", "Read a pasta recipe"),
    (0.0223, "Cook pasta", "Scroll Instagram"),
]

for alignment, goal, activity in CASES:
    result = classify_alignment(alignment, goal, activity)
    print(f"{goal} -> {activity}")
    print(result)
    print()