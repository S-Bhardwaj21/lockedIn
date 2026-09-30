import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

@dataclass
class WindowContext:
    timestamp: str
    title: str
    process: str
    pid: int
    hwnd: int

class WindowsContextObserver:
    def get_active_window(self):
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        title_buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title_buffer, 512)
        title = title_buffer.value.strip()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = self._get_process_name(pid.value)
        return WindowContext(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            title=title,
            process=process,
            pid=pid.value,
            hwnd=hwnd,
        )

    def _get_process_name(self, pid):
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return "unknown"
        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buffer))
            success = kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)
            )
            if not success:
                return "unknown"
            return buffer.value.rsplit("\\", 1)[-1]
        finally:
            kernel32.CloseHandle(handle)

    def get_context_string(self):
        context = self.get_active_window()
        if context is None:
            return ""
        return f"{context.process} | {context.title}"