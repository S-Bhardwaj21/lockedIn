import sys
from pathlib import Path
import time
import uiautomation as auto

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from context.windows_context import WindowsContextObserver

observer = WindowsContextObserver()

print("Switch to Edge within 5 seconds...")
time.sleep(5)

window = observer.get_active_window()

if not window or window.process.lower() != "msedge.exe":
    print("ERROR: Active window is not Microsoft Edge.")
    print(f"Current: {window.process if window else 'None'}")
    raise SystemExit(1)

root = auto.ControlFromHandle(window.hwnd)

print(f"\nEdge window: {window.title}")
print("Searching for Edit controls...\n")

found = 0

def search(control, depth=0):
    global found
    if depth > 12:
        return
    try:
        if control.ControlTypeName == "EditControl":
            found += 1
            print(f"EDIT #{found}")
            print(f"  Name: {control.Name!r}")
            print(f"  AutomationId: {control.AutomationId!r}")
            print(f"  ClassName: {control.ClassName!r}")
            try:
                print(f"  Value: {control.GetValuePattern().Value!r}")
            except Exception:
                print("  Value: <unavailable>")
            print()
        for child in control.GetChildren():
            search(child, depth + 1)
    except Exception:
        pass

search(root)

print(f"Total Edit controls found: {found}")