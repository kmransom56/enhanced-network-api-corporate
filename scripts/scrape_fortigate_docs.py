import os
import time
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://fortigate-api.readthedocs.io/en/latest/"
START_PATH = "index.html"

# Where to store scraped HTML files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ROOT = os.path.join(PROJECT_ROOT, "docs", "fortigate-api")

# Only crawl within this netloc and path prefix
ALLOWED_NETLOC = urlparse(BASE_URL).netloc
ALLOWED_PREFIX = urlparse(BASE_URL).path.rstrip("/")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "enhanced-network-api-doc-scraper/1.0 (+https://fortigate-api.readthedocs.io/)"
})


def is_internal_doc_link(href: str) -> bool:
    if not href:
        return False
    href, _ = urldefrag(href)

    # Ignore mailto:, javascript:, etc.
    if ":" in href.split("?")[0] and not href.startswith("/") and not href.startswith("."):
        return False

    url = urlparse(urljoin(BASE_URL, href))
    if url.netloc != ALLOWED_NETLOC:
        return False

    # Only follow within the /en/latest/ tree
    return url.path.startswith(ALLOWED_PREFIX)


def to_local_path(url: str) -> str:
    parsed = urlparse(url)
    rel_path = parsed.path.lstrip("/")
    if rel_path.endswith("/"):
        rel_path = os.path.join(rel_path, "index.html")
    if not rel_path.endswith(".html"):
        # Keep non-HTML assets in case we need them later
        return rel_path
    return rel_path


def save_page(url: str, content: bytes) -> str:
    rel_path = to_local_path(url)
    out_path = os.path.join(OUTPUT_ROOT, rel_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(content)
    return out_path


def scrape():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    start_url = urljoin(BASE_URL, START_PATH)
    queue = [start_url]
    seen = set()

    print(f"[scraper] Starting from {start_url}")
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        print(f"[scraper] Fetching {url}")
        try:
            resp = SESSION.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[scraper] ERROR fetching {url}: {e}")
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            # Save assets but don't parse links
            save_page(url, resp.content)
            continue

        out_path = save_page(url, resp.content)
        print(f"[scraper] Saved to {os.path.relpath(out_path, PROJECT_ROOT)}")

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not is_internal_doc_link(href):
                continue
            next_url = urljoin(url, href)
            # Strip fragment
            next_url, _ = urldefrag(next_url)
            if next_url not in seen and next_url not in queue:
                queue.append(next_url)

        # Be polite to the host
        time.sleep(0.2)

    print(f"[scraper] Done. Pages saved under {os.path.relpath(OUTPUT_ROOT, PROJECT_ROOT)}")


if __name__ == "__main__":
    scrape()
