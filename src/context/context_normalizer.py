from urllib.parse import urlparse
import re

BROWSERS = {"msedge.exe", "chrome.exe"}

class ContextNormalizer:
    def normalize(self, process, title, url=None):
        process = process.lower().strip()
        if process in BROWSERS:
            return self._normalize_browser(title, url)
        return self._normalize_desktop(process, title)

    def _normalize_browser(self, title, url):
        domain = self._extract_domain(url)
        clean_title = self._clean_browser_title(title)
        parts = []
        if domain:
            parts.append(domain)
        if clean_title:
            parts.append(clean_title)
        return " | ".join(parts)

    def _extract_domain(self, url):
        if not url:
            return ""
        try:
            hostname = urlparse(url).hostname
            if not hostname:
                return ""
            if hostname.startswith("www."):
                hostname = hostname[4:]
            return hostname
        except Exception:
            return ""

    def _clean_browser_title(self, title):
        title = title.strip()
        title = re.sub(r"^\(\d+\)\s*", "", title)
        title = re.sub(r"\s+and\s+\d+\s+more\s+pages?$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+-\s+Personal\s+-\s+Microsoft.*Edge$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+-\s+Microsoft.*Edge$", "", title, flags=re.IGNORECASE)
        title = title.strip()
        if title.lower() in {"new tab", "untitled"}:
            return ""
        return title

    def _normalize_desktop(self, process, title):
        process_name = process.removesuffix(".exe")
        title = title.strip()
        if title:
            return f"{process_name} | {title}"
        return process_name