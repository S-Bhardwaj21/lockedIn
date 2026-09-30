from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orchestration.coordinator import orchestrate

CASES = [
    ("Finish my ML assignment", "Watch a Gradient Descent lecture"),
    ("Finish my ML assignment", "Watch a Python tutorial"),
    ("Finish my ML assignment", "Watch Instagram memes"),
    ("Finish my ML assignment", "Shop for shoes"),
    ("Watch a C-drama", "Watch a C-drama episode"),
    ("Watch a C-drama", "Watch an ML lecture"),
    ("Cook pasta", "Read a pasta recipe"),
    ("Cook pasta", "Scroll Instagram"),
    ("Finish my ML assignment", "Study Python programming"),
    ("Finish my ML assignment", "Read about neural networks"),
    ("Finish my ML assignment", "Watch comedy memes"),
    ("Watch a C-drama", "C-drama episode"),
    ("Watch a C-drama", "Study machine learning"),
    ("Watch a C-drama", "Read romance drama reviews"),
    ("Cook pasta", "Pasta cooking instructions"),
    ("Cook pasta", "Study Python programming"),
    ("Scroll Instagram for fun", "Scroll Instagram"),
    ("Scroll Instagram for fun", "Finish my ML assignment"),
]

def main():
    print("=" * 72)
    print("LOCKEDIN — SEMANTIC ORCHESTRATION EVALUATION")
    print("=" * 72)

    for index, (goal, activity) in enumerate(CASES, 1):
        print(f"\n[{index}]")
        print(f"Goal:         {goal}")
        print(f"Activity:     {activity}")

        result = orchestrate(goal, activity)

        print(f"Alignment:    {result['alignment']:.6f}")
        print(f"Classification: {result['classification']}")
        print(f"Reason:        {result['reason']}")
        print(f"Worker:       {result['worker']}")

if __name__ == "__main__":
    main()