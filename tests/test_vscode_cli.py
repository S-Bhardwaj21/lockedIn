import os
import subprocess
from pathlib import Path

CANDIDATES = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "bin" / "code.exe",
    Path("C:/Program Files/Microsoft VS Code/bin/code.cmd"),
    Path("C:/Program Files/Microsoft VS Code/bin/code.exe"),
]

print("Searching for VS Code CLI...\n")

for path in CANDIDATES:
    print(f"{path} -> {'FOUND' if path.exists() else 'not found'}")

code_path = next(
    (path for path in CANDIDATES if path.exists()),
    None,
)

if code_path is None:
    print("\nVS Code CLI was not found in the standard locations.")
    raise SystemExit(1)

print(f"\nUsing: {code_path}")

result = subprocess.run(
    [str(code_path), "--version"],
    capture_output=True,
    text=True,
    shell=False,
)

print("\nReturn code:", result.returncode)

if result.stdout:
    print("\nSTDOUT:")
    print(result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)