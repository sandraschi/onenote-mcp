"""Ring-buffer activity log served to the webapp Logging page."""

from __future__ import annotations

import json
import time
import uuid
from collections import deque
from typing import Any


class ActivityLog:
    """Bounded in-memory ring buffer of log entries."""

    def __init__(self, max_entries: int = 2000):
        self.max_entries = max_entries
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_entries)

    def add(self, level: str, kind: str, detail: str, meta: dict | None = None) -> str:
        entry_id = f"{time.time():.6f}.{uuid.uuid4().hex[:6]}"
        self._entries.append(
            {
                "id": entry_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                "level": level.upper(),
                "kind": kind,
                "detail": detail,
                "meta": meta or {},
            }
        )
        return entry_id

    def info(self, kind: str, detail: str, **meta: Any) -> str:
        return self.add("INFO", kind, detail, meta)

    def warn(self, kind: str, detail: str, **meta: Any) -> str:
        return self.add("WARNING", kind, detail, meta)

    def error(self, kind: str, detail: str, **meta: Any) -> str:
        return self.add("ERROR", kind, detail, meta)

    def query(
        self,
        limit: int = 50,
        offset: int = 0,
        level: str | None = None,
        kind: str | None = None,
        search: str | None = None,
        sort: str = "desc",
        after_id: str | None = None,
    ) -> dict[str, Any]:
        entries = list(self._entries)
        if after_id:
            try:
                at = float(after_id.split(".")[0])
                entries = [e for e in entries if float(e["id"].split(".")[0]) > at]
            except (TypeError, ValueError):
                pass
        if level:
            levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            min_level = levels.get(level.upper(), 1)
            entries = [e for e in entries if levels.get(e["level"], 1) >= min_level]
        if kind:
            entries = [e for e in entries if e["kind"] == kind]
        if search:
            q = search.lower()
            entries = [e for e in entries if q in e["detail"].lower()]
        entries.sort(key=lambda e: e["id"], reverse=(sort == "desc"))
        total = len(entries)
        page = entries[offset : offset + limit]
        return {
            "entries": page,
            "total": total,
            "limit": limit,
            "offset": offset,
            "max_entries": self.max_entries,
            "sort": sort,
        }

    def stats(self) -> dict[str, Any]:
        levels: dict[str, int] = {}
        kinds: dict[str, int] = {}
        for entry in self._entries:
            levels[entry["level"]] = levels.get(entry["level"], 0) + 1
            kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
        return {
            "total": len(self._entries),
            "max_entries": self.max_entries,
            "levels": levels,
            "kinds": kinds,
        }

    def export(
        self, format: str = "json", level: str | None = None, kind: str | None = None, search: str | None = None
    ) -> str:
        result = self.query(limit=self.max_entries, level=level, kind=kind, search=search)
        if format == "csv":
            import csv
            import io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "timestamp", "level", "kind", "detail", "meta"])
            for entry in result["entries"]:
                writer.writerow(
                    [
                        entry["id"],
                        entry["timestamp"],
                        entry["level"],
                        entry["kind"],
                        entry["detail"],
                        json.dumps(entry["meta"]),
                    ]
                )
            return buf.getvalue()
        return json.dumps(result["entries"], indent=2)

    def clear(self) -> None:
        self._entries.clear()
