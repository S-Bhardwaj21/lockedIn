import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from context.windows_context import WindowsContextObserver

observer = WindowsContextObserver()

print("LOCKEDIN Windows Context Observer")
print("Switch between windows for a few seconds.\n")

for _ in range(10):
    context = observer.get_active_window()
    if context:
        print(f"[{context.timestamp}]")
        print(f"Process: {context.process}")
        print(f"Title:   {context.title}")
        print(f"Context: {observer.get_context_string()}")
        print()
    time.sleep(1)