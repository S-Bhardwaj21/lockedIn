import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from context.windows_context import WindowsContextObserver
from context.browser_context import BrowserContextProvider


def main():
    observer = WindowsContextObserver()
    browser = BrowserContextProvider()

    print("LOCKEDIN window context inspector")
    print("Press Ctrl+C to stop.\n")

    while True:
        window = observer.get_active_window()

        if window is None:
            time.sleep(1)
            continue

        browser_context = browser.get_context(window)

        print("-" * 80)
        print("PROCESS :", window.process)
        print("PID     :", window.pid)
        print("HWND    :", window.hwnd)
        print("TITLE   :", repr(window.title))

        if browser_context:
            print("BROWSER :", True)
            print("URL     :", repr(browser_context.url))
        else:
            print("BROWSER :", False)

        time.sleep(2)


if __name__ == "__main__":
    main()