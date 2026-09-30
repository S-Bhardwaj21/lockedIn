import uiautomation as auto
from dataclasses import dataclass

BROWSERS = {"msedge.exe", "chrome.exe"}

@dataclass
class BrowserContext:
    title: str
    url: str | None

class BrowserContextProvider:
    def get_context(self, window):
        if window.process.lower() not in BROWSERS:
            return None
        try:
            root = auto.ControlFromHandle(window.hwnd)
            if not root:
                return BrowserContext(window.title, None)
            url = self._get_address_bar(root)
            return BrowserContext(window.title, url)
        except Exception:
            return BrowserContext(window.title, None)

    def _get_address_bar(self, root):
        address_bar = root.EditControl(Name="Address and search bar")
        if address_bar.Exists(0.2):
            try:
                value = address_bar.GetValuePattern().Value
                if value:
                    return value.strip()
            except Exception:
                pass
        return None