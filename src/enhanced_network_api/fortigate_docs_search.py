import json
import os
import time
from functools import lru_cache
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from bs4 import BeautifulSoup

_TREE_MTIME_CACHE: Dict[str, Tuple[float, float]] = {}
_MTIME_CACHE_TTL = 30.0
_CACHE_VERSION = 1
_CACHE_FILENAME = "fortigate_docs_index.json"


def _iter_html_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    for path in root.rglob("*.html"):
        if path.is_file():
            yield path


def _extract_text_from_html(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    # Prefer main content if present
    main = soup.find("main") or soup.find("div", {"role": "main"})
    text = main.get_text("\n") if main else soup.get_text("\n")
    return unescape(text)


def _build_index(root: Path) -> List[Dict[str, Any]]:
    index: List[Dict[str, Any]] = []
    for path in _iter_html_files(root):
        text = _extract_text_from_html(path)
        if not text.strip():
            continue
        title = path.stem.replace("_", " ")
        index.append({
            "path": path,
            "rel_path": str(path.relative_to(root.parent.parent)),
            "title": title,
            "text": text,
        })
    return index


@lru_cache(maxsize=2)
def _cached_index(root_str: str, mtime: float) -> List[Dict[str, Any]]:
    root = Path(root_str)
    persisted = _load_persisted_index(root, mtime)
    if persisted is not None:
        return persisted
    index = _build_index(root)
    _persist_index(root, mtime, index)
    return index


def _compute_tree_mtime(root: Path) -> float:
    latest = 0.0
    if not root.exists():
        return latest
    for path in root.rglob("*.html"):
        try:
            m = path.stat().st_mtime
        except OSError:
            continue
        if m > latest:
            latest = m
    return latest


def _cached_tree_mtime(root: Path) -> float:
    key = str(root)
    now = time.time()
    cached = _TREE_MTIME_CACHE.get(key)
    if cached and now - cached[0] < _MTIME_CACHE_TTL:
        return cached[1]
    persisted_mtime = _load_cached_tree_mtime_from_disk(root)
    if persisted_mtime is not None:
        _TREE_MTIME_CACHE[key] = (now, persisted_mtime)
        return persisted_mtime
    mtime = _compute_tree_mtime(root)
    _TREE_MTIME_CACHE[key] = (now, mtime)
    return mtime


def _cache_dir(root: Path) -> Path:
    return root / ".cache"


def _cache_file(root: Path) -> Path:
    return _cache_dir(root) / _CACHE_FILENAME


def _read_persisted_payload(root: Path) -> Dict[str, Any] | None:
    path = _cache_file(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("version") != _CACHE_VERSION:
        return None
    return data


def _load_persisted_index(root: Path, mtime: float) -> List[Dict[str, Any]] | None:
    data = _read_persisted_payload(root)
    if not data:
        return None
    if abs(data.get("tree_mtime", -1.0) - mtime) > 0.001:
        return None
    entries = []
    for entry in data.get("entries", []):
        entries.append(
            {
                "path": Path(entry["path"]),
                "rel_path": entry["rel_path"],
                "title": entry["title"],
                "text": entry["text"],
            }
        )
    return entries


def _persist_index(root: Path, mtime: float, index: List[Dict[str, Any]]) -> None:
    try:
        cache_dir = _cache_dir(root)
        cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _CACHE_VERSION,
            "tree_mtime": mtime,
            "entries": [
                {
                    "path": str(entry["path"]),
                    "rel_path": entry["rel_path"],
                    "title": entry["title"],
                    "text": entry["text"],
                }
                for entry in index
            ],
        }
        _cache_file(root).write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        # Non-fatal: cache directory may be read-only.
        pass


def _load_cached_tree_mtime_from_disk(root: Path) -> float | None:
    data = _read_persisted_payload(root)
    if not data:
        return None
    return data.get("tree_mtime")


def warm_index(root: Path) -> None:
    """Preload the on-disk FortiGate documentation into memory caches."""
    mtime = _cached_tree_mtime(root)
    _cached_index(str(root), mtime)


def search_docs(root: Path, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    query = query.strip()
    if not query:
        return []
    query_lower = query.lower()

    mtime = _cached_tree_mtime(root)
    index = _cached_index(str(root), mtime)

    results: List[Dict[str, Any]] = []
    for entry in index:
        text = entry["text"]
        pos = text.lower().find(query_lower)
        if pos == -1:
            continue
        start = max(0, pos - 160)
        end = min(len(text), pos + 160)
        snippet = text[start:end].replace("\n", " ")
        results.append({
            "title": entry["title"],
            "path": entry["rel_path"],
            "snippet": snippet,
        })
        if len(results) >= limit:
            break
    return results
