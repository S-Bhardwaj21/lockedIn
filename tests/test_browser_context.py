import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from context.windows_context import WindowsContextObserver
from context.browser_context import BrowserContextProvider

observer = WindowsContextObserver()
browser = BrowserContextProvider()

print("LOCKEDIN Browser Context Test")
print("Switch to Edge/Chrome and change tabs.")
print("Press Ctrl+C to stop.\n")

while True:
    window = observer.get_active_window()
    if window:
        context = browser.get_context(window)
        print(f"Process: {window.process}")
        print(f"Title:   {window.title}")
        print(f"Context: {context}")
        print()
    time.sleep(2)