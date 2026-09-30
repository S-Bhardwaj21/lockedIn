import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from context.context_normalizer import ContextNormalizer

normalizer = ContextNormalizer()

examples = [
    (
        "msedge.exe",
        "Netflix and 3 more pages - Personal - Microsoft Edge",
        "https://www.netflix.com/browse",
    ),
    (
        "msedge.exe",
        "Watch K-Dramas, Korean Shows & Chinese Dramas | Rakuten Viki and 5 more pages - Personal - Microsoft Edge",
        "https://www.viki.com",
    ),
    (
        "msedge.exe",
        "Post | LinkedIn and 4 more pages - Personal - Microsoft Edge",
        "https://www.linkedin.com/posts/example",
    ),
    (
        "msedge.exe",
        "Complete Machine Learning Course for Beginners - YouTube and 2 more pages - Personal - Microsoft Edge",
        "https://www.youtube.com/watch?v=example",
    ),
    (
        "Code.exe",
        "assignment.py - Visual Studio Code",
        None,
    ),
]

for process, title, url in examples:
    result = normalizer.normalize(process, title, url)
    print(f"RAW:        {title}")
    print(f"NORMALIZED: {result}")
    print()