import ctypes
import json
import os
import subprocess
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

import uiautomation as auto

RUNTIME_DIR = Path(r"C:\Users\Shreya\lockedin\runtime")
VSCODE_CONTEXT_FILE = RUNTIME_DIR / "vscode_context.json"
VSCODE_RESTORE_FILE = RUNTIME_DIR / "vscode_restore.json"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_RESTORE = 9
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_L = 0x4C
VK_V = 0x56
VK_RETURN = 0x0D


@dataclass
class WindowSnapshot:
    hwnd: int
    title: str
    process: str
    rect: tuple[int, int, int, int]


class WorkspaceRecovery:
    def __init__(self):
        self.destination = None

    def _get_process_name(self, pid):
        handle = kernel32.OpenProcess(0x1000, False, pid)

        if not handle:
            return "unknown"

        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))

            if not kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                return "unknown"

            return buffer.value.rsplit("\\", 1)[-1]

        finally:
            kernel32.CloseHandle(handle)

    def _get_process_path(self, pid):
        handle = kernel32.OpenProcess(0x1000, False, pid)

        if not handle:
            return None

        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))

            if not kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                return None

            return buffer.value

        finally:
            kernel32.CloseHandle(handle)

    def _get_window_title(self, hwnd):
        buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buffer, 512)
        return buffer.value.strip()

    def _get_window_process(self, hwnd):
        pid = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(pid),
        )

        return self._get_process_name(pid.value)

    def _get_window_process_path(self, hwnd):
        pid = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(pid),
        )

        return self._get_process_path(pid.value)

    def _get_window_rect(self, hwnd):
        rect = wintypes.RECT()

        if user32.GetWindowRect(
            hwnd,
            ctypes.byref(rect),
        ):
            return (
                rect.left,
                rect.top,
                rect.right,
                rect.bottom,
            )

        return (0, 0, 0, 0)

    def _enum_windows(self):
        windows = []

        @ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            wintypes.HWND,
            wintypes.LPARAM,
        )
        def callback(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            title = self._get_window_title(hwnd)

            if not title:
                return True

            windows.append(
                WindowSnapshot(
                    hwnd=hwnd,
                    title=title,
                    process=self._get_window_process(hwnd),
                    rect=self._get_window_rect(hwnd),
                )
            )

            return True

        user32.EnumWindows(callback, 0)

        return windows

    def _activate_window(self, hwnd):
        if not hwnd or not user32.IsWindow(hwnd):
            return False

        user32.ShowWindow(hwnd, SW_RESTORE)

        try:
            user32.BringWindowToTop(hwnd)
        except Exception:
            pass

        try:
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        time.sleep(0.7)

        foreground = user32.GetForegroundWindow()

        return foreground == hwnd

    def _read_vscode_context(self):
        if not VSCODE_CONTEXT_FILE.exists():
            return None

        try:
            return json.loads(
                VSCODE_CONTEXT_FILE.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return None

    def capture_vscode_destination(self, hwnd):
        context = self._read_vscode_context()

        if not context or not context.get("activeFile"):
            return False

        self.destination = {
            "type": "vscode",
            "hwnd": hwnd,
            "activeFile": context["activeFile"],
            "line": context.get("line"),
            "column": context.get("column"),
            "tabs": [
                tab["path"]
                for tab in context.get("tabs", [])
                if tab.get("path")
            ],
        }

        print("\n>>> TASK DESTINATION UPDATED")
        print("    Type: VS Code")
        print(f"    Window HWND: {hwnd}")
        print(f"    File: {context['activeFile']}")
        print(
            f"    Cursor: line {context.get('line')}, "
            f"column {context.get('column')}"
        )

        return True

    def capture_browser_destination(
        self,
        window,
        url,
        title,
    ):
        is_pwa = "__pwa=1" in (url or "").lower()

        if is_pwa:
            process_path = self._get_window_process_path(
                window.hwnd
            )

            self.destination = {
                "type": "browser_pwa",
                "hwnd": window.hwnd,
                "process": window.process,
                "process_path": process_path,
                "url": url,
                "title": title,
            }

            print("\n>>> TASK DESTINATION UPDATED")
            print("    Type: Browser PWA")
            print(f"    Process: {window.process}")
            print(f"    Window HWND: {window.hwnd}")
            print(f"    URL: {url}")
            print(f"    Title: {title[:100]}")

            return True

        self.destination = {
            "type": "browser",
            "hwnd": window.hwnd,
            "process": window.process,
            "url": url,
            "title": title,
        }

        print("\n>>> TASK DESTINATION UPDATED")
        print("    Type: Browser")
        print(f"    Window HWND: {window.hwnd}")
        print(f"    URL: {url}")
        print(f"    Title: {title[:100]}")

        return True

    def capture_window_destination(self, window):
        self.destination = {
            "type": "window",
            "hwnd": window.hwnd,
            "process": window.process,
            "title": window.title,
        }

        print("\n>>> TASK DESTINATION UPDATED")
        print("    Type: Window")
        print(f"    Process: {window.process}")
        print(f"    Window HWND: {window.hwnd}")
        print(f"    Title: {window.title[:100]}")

        return True

    def _write_vscode_restore_request(self):
        destination = self.destination

        request = {
            "activeFile": destination["activeFile"],
            "line": destination["line"],
            "column": destination["column"],
            "tabs": destination["tabs"],
        }

        RUNTIME_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_file = VSCODE_RESTORE_FILE.with_suffix(".tmp")

        temp_file.write_text(
            json.dumps(request, indent=2),
            encoding="utf-8",
        )

        temp_file.replace(VSCODE_RESTORE_FILE)

        print("\n>>> VS Code destination restore requested.")
        print(f"    File: {request['activeFile']}")
        print(
            f"    Cursor: line {request['line']}, "
            f"column {request['column']}"
        )

    def _find_browser_tab(
        self,
        window_hwnd,
        target_url,
        target_title,
    ):
        try:
            root = auto.ControlFromHandle(window_hwnd)

            if not root:
                return None

            target_title = (
                target_title or ""
            ).lower()

            clean_title = target_title

            clean_title = clean_title.split(
                " - personal - microsoft"
            )[0].strip()

            clean_title = clean_title.split(
                " - microsoft"
            )[0].strip()

            queue = list(root.GetChildren())

            while queue:
                control = queue.pop(0)

                try:
                    control_type = control.ControlTypeName
                    name = (
                        control.Name or ""
                    ).lower()

                    if control_type == "TabItemControl":
                        if (
                            clean_title
                            and (
                                clean_title in name
                                or name in clean_title
                            )
                        ):
                            return control

                    children = control.GetChildren()

                    if children:
                        queue.extend(children)

                except Exception:
                    continue

            return None

        except Exception:
            return None

    def _set_clipboard(self, text):
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()

            return True

        except Exception as error:
            print(
                f">>> WARNING: Clipboard setup failed: {error}"
            )
            return False

    def _send_key(self, key):
        user32.keybd_event(
            key,
            0,
            0,
            0,
        )

        user32.keybd_event(
            key,
            0,
            KEYEVENTF_KEYUP,
            0,
        )

    def _send_ctrl_key(self, key):
        user32.keybd_event(
            VK_CONTROL,
            0,
            0,
            0,
        )

        user32.keybd_event(
            key,
            0,
            0,
            0,
        )

        user32.keybd_event(
            key,
            0,
            KEYEVENTF_KEYUP,
            0,
        )

        user32.keybd_event(
            VK_CONTROL,
            0,
            KEYEVENTF_KEYUP,
            0,
        )

    def _navigate_browser_window(self, hwnd, url):
        if not self._activate_window(hwnd):
            print(
                ">>> WARNING: Could not activate "
                "browser window."
            )
            return False

        if not self._set_clipboard(url):
            return False

        time.sleep(0.3)

        self._send_ctrl_key(VK_L)
        time.sleep(0.4)

        self._send_ctrl_key(VK_V)
        time.sleep(0.3)

        self._send_key(VK_RETURN)
        time.sleep(2.0)

        foreground = user32.GetForegroundWindow()

        if foreground != hwnd:
            print(
                ">>> WARNING: Browser window lost "
                "foreground after navigation."
            )
            return False

        print(
            ">>> Browser destination navigation requested."
        )
        print(f"    URL: {url}")

        return True

    def _find_edge_executable(self):
        destination = self.destination

        process_path = destination.get(
            "process_path"
        )

        if process_path and Path(process_path).exists():
            return process_path

        candidates = [
            Path(
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            ),
            Path(
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ),
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        return None

    def _restore_browser_pwa(self):
        destination = self.destination
        url = destination["url"]
        hwnd = destination["hwnd"]

        print(
            ">>> Restoring Browser PWA destination..."
        )
        print(f"    URL: {url}")

        # First try the existing destination window.
        if self._activate_window(hwnd):
            print(
                ">>> Existing Edge destination window "
                "foregrounded."
            )

            # A PWA window does not reliably expose a
            # normal browser address bar, so use the
            # installed Edge app when possible.
            edge = self._find_edge_executable()

            if edge:
                try:
                    subprocess.Popen(
                        [
                            edge,
                            f"--app={url}",
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                    time.sleep(2.0)

                    print(
                        ">>> Browser PWA restore requested "
                        "through Microsoft Edge."
                    )

                    return True

                except Exception as error:
                    print(
                        ">>> WARNING: Could not launch "
                        f"Edge PWA: {error}"
                    )

            return True

        print(
            ">>> WARNING: Existing PWA window could "
            "not be foregrounded."
        )

        edge = self._find_edge_executable()

        if not edge:
            print(
                ">>> WARNING: Microsoft Edge executable "
                "was not found."
            )
            return False

        try:
            subprocess.Popen(
                [
                    edge,
                    f"--app={url}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            time.sleep(2.0)

            print(
                ">>> Browser PWA launched for destination."
            )

            return True

        except Exception as error:
            print(
                ">>> WARNING: Browser PWA launch failed: "
                f"{error}"
            )
            return False

    def _activate_browser_destination(self):
        destination = self.destination
        hwnd = destination["hwnd"]

        if not self._activate_window(hwnd):
            print(
                ">>> WARNING: Could not activate "
                "browser window."
            )
            return False

        time.sleep(0.5)

        tab = self._find_browser_tab(
            hwnd,
            destination["url"],
            destination["title"],
        )

        if tab is not None:
            try:
                pattern = tab.GetSelectionItemPattern()
                pattern.Select()

                time.sleep(0.7)

                print(
                    ">>> TASK DESTINATION restored: "
                    f"{destination['title'][:100]}"
                )

                return True

            except Exception as error:
                print(
                    ">>> WARNING: Could not activate "
                    f"browser tab: {error}"
                )

        print(
            ">>> Browser tab UIA lookup failed."
        )
        print(
            ">>> Falling back to direct URL navigation."
        )

        return self._navigate_browser_window(
            hwnd,
            destination["url"],
        )

    def capture(self):
        windows = self._enum_windows()
        foreground = user32.GetForegroundWindow()

        print("\n>>> Workspace snapshot captured:")

        for window in windows:
            print(
                f"    {window.process} | "
                f"{window.title[:80]}"
            )

        print(
            f">>> {len(windows)} window(s) captured.\n"
        )

        return foreground, windows

    def restore(self):
        if not self.destination:
            print(
                "\n>>> No task destination "
                "has been established."
            )
            return False

        destination_type = self.destination["type"]

        print(
            "\n>>> Restoring TASK DESTINATION..."
        )
        print(
            f"    Type: {destination_type}"
        )

        if destination_type == "vscode":
            self._write_vscode_restore_request()

            time.sleep(1.5)

            activated = self._activate_window(
                self.destination["hwnd"]
            )

            if activated:
                print(
                    ">>> TASK DESTINATION restored: "
                    f"{self.destination['activeFile']}"
                )
            else:
                print(
                    ">>> WARNING: Could not foreground "
                    f"VS Code HWND "
                    f"{self.destination['hwnd']}"
                )

            return activated

        if destination_type == "browser":
            return self._activate_browser_destination()

        if destination_type == "browser_pwa":
            return self._restore_browser_pwa()

        if destination_type == "window":
            activated = self._activate_window(
                self.destination["hwnd"]
            )

            if activated:
                print(
                    ">>> TASK DESTINATION restored: "
                    f"{self.destination['process']} | "
                    f"{self.destination['title'][:100]}"
                )
            else:
                print(
                    ">>> WARNING: Could not foreground "
                    f"window HWND "
                    f"{self.destination['hwnd']}"
                )

            return activated

        print(
            f">>> Unknown destination type: "
            f"{destination_type}"
        )

        return False