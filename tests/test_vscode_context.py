import ctypes
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import uiautomation as auto

user32 = ctypes.windll.user32

def get_foreground_window():
    return user32.GetForegroundWindow()

def inspect_vscode():
    hwnd = get_foreground_window()
    window = auto.ControlFromHandle(hwnd)

    print("\n=== ACTIVE WINDOW ===")
    print("Name:", window.Name)
    print("Class:", window.ClassName)
    print("ControlType:", window.ControlTypeName)

    print("\n=== CONTROLS CONTAINING LINE/COLUMN INFO ===")

    matches = []

    def walk(control, depth=0):
        if depth > 10:
            return

        try:
            name = control.Name or ""
        except Exception:
            name = ""

        if re.search(r"\bLn\s+\d+.*Col\s+\d+", name, re.IGNORECASE):
            matches.append(name)

        try:
            children = control.GetChildren()
        except Exception:
            return

        for child in children:
            walk(child, depth + 1)

    walk(window)

    if matches:
        for match in matches:
            print(match)
    else:
        print("No line/column control found.")

    print("\n=== TOP-LEVEL CHILDREN ===")

    try:
        children = window.GetChildren()

        for child in children:
            print(
                f"{child.ControlTypeName:20} | "
                f"{child.Name[:120]}"
            )

    except Exception as exc:
        print("Could not inspect children:", exc)


print("Switch to VS Code now.")
print("You have 5 seconds. DO NOT press anything in PowerShell.")
time.sleep(5)

inspect_vscode()