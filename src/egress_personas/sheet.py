"""Fetching the Google Sheet into a snapshot.

`pull` writes each tab to data/*.csv and records a hash per tab in
data/snapshot.json. Nothing else in this package touches the network: `build` reads
the snapshot. That is what makes a live, collaboratively edited sheet compatible with
a reproducible generator — the sheet can change under you, but a run names the exact
revision it came from, and pulling is a reviewable commit whose diff shows what moved.

Default transport is the sheet's CSV export endpoint, which needs no credentials for
a link-shared sheet. If the sheet must stay private, a service-account token can be
passed instead; credentials belong in .secrets/, which is gitignored.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .tables import TABS, Table, _norm, read_csv_text, text

GVIZ = ("https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        "?tqx=out:csv&headers=1&sheet={tab}")

#: `headers=1` above matters: left to itself the visualization endpoint guesses how
#: many leading rows are headers, and a guess of 0 or 2 shifts every value.

_ID_IN_URL = re.compile(r"/spreadsheets/d/([A-Za-z0-9_-]{20,})")
_BARE_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def sheet_id_from(text: str) -> str:
    """The id, from either a pasted URL or the id itself."""
    value = (text or "").strip()
    m = _ID_IN_URL.search(value)
    if m:
        return m.group(1)
    if _BARE_ID.match(value):
        return value
    raise ValueError(
        f"{value!r} is neither a Google Sheets URL nor a sheet id.\n"
        f"Open the sheet and copy the address bar; it looks like\n"
        f"  https://docs.google.com/spreadsheets/d/1AbC…xyz/edit#gid=0"
    )


def tab_title(name: str) -> str:
    return name.capitalize()


def fetch_tab(sheet_id: str, name: str, *, token: str | None = None,
              timeout: float = 30.0) -> str:
    url = GVIZ.format(sheet_id=sheet_id,
                      tab=urllib.parse.quote(tab_title(name)))
    req = urllib.request.Request(url, headers={"User-Agent": "egress-personas"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8-sig")
    except urllib.error.HTTPError as e:
        hint = ""
        if e.code in (401, 403):
            hint = ("\nThe sheet is not readable without credentials. In Google "
                    "Sheets: Share -> General access -> Anyone with the link -> "
                    "Viewer. Or pass --token-file with an OAuth access token if it "
                    "has to stay private.")
        elif e.code == 400:
            hint = (f"\nGoogle rejected the request, which usually means there is no "
                    f"tab called {tab_title(name)!r} in that sheet. The eight tabs "
                    f"have to be named exactly as `personas init-sheet` writes them.")
        elif e.code == 404:
            hint = ("\nNo sheet with that id. Check the URL you pasted, and that the "
                    "sheet has not been deleted or moved to another account.")
        raise RuntimeError(
            f"pulling {tab_title(name)}: HTTP {e.code} {e.reason}{hint}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"pulling {tab_title(name)}: could not reach Google ({e.reason}). "
            f"`build` does not need the network — it reads the snapshot in data/ — so "
            f"this only stops you refreshing it."
        ) from e
    if body.lstrip().startswith("<"):
        raise RuntimeError(
            f"pulling {tab_title(name)}: Google returned a sign-in page rather than "
            f"CSV, so the sheet is not shared for reading by link.\n"
            f"In Google Sheets: Share -> General access -> Anyone with the link -> "
            f"Viewer."
        )
    return body


@dataclass
class TabChange:
    """What moved in one tab between the snapshot on disk and the Sheet."""

    tab: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[tuple[str, list[str]]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        bits = []
        if self.added:
            bits.append(f"{len(self.added)} added")
        if self.removed:
            bits.append(f"{len(self.removed)} removed")
        if self.changed:
            bits.append(f"{len(self.changed)} changed")
        return ", ".join(bits) if bits else "unchanged"

    def detail(self, limit: int = 6) -> list[str]:
        out = [f"+ {k}" for k in self.added[:limit]]
        out += [f"- {k}" for k in self.removed[:limit]]
        out += [f"~ {k}  ({', '.join(cols)})" for k, cols in self.changed[:limit]]
        more = (len(self.added) + len(self.removed) + len(self.changed)) - len(out)
        if more > 0:
            out.append(f"… and {more} more")
        return out


def _keyed(tab: Table) -> dict[str, dict[str, str]]:
    key = TABS[tab.name].key
    out: dict[str, dict[str, str]] = {}
    for i, row in enumerate(tab.rows):
        k = (text(row.get(key)) if key else None) or f"row {tab.row_numbers[i]}"
        out[k] = row
    return out


def compare(old: Table | None, new: Table) -> TabChange:
    """Row-level differences, keyed by each tab's own key column."""
    change = TabChange(tab=new.name)
    if old is None:
        change.added = list(_keyed(new))
        return change
    a, b = _keyed(old), _keyed(new)
    change.added = [k for k in b if k not in a]
    change.removed = [k for k in a if k not in b]
    for k in b:
        if k not in a:
            continue
        cols = [c for c in set(a[k]) | set(b[k])
                if _norm(a[k].get(c)) != _norm(b[k].get(c))]
        if cols:
            change.changed.append((k, sorted(cols)))
    return change


def pull(sheet_id: str, dest: Path, *, token: str | None = None,
         only: list[str] | None = None,
         dry_run: bool = False) -> tuple[dict[str, object], list[TabChange]]:
    """Fetch every tab, check its shape, and write the snapshot.

    With `dry_run`, nothing is written: the differences come back so you can be told
    whether the snapshot on disk is behind the Sheet without changing it.
    """
    dest = Path(dest)
    names = only or list(TABS)
    bodies: dict[str, str] = {}
    for name in names:
        body = fetch_tab(sheet_id, name, token=token)
        read_csv_text(name, body)  # fail before overwriting a good snapshot
        bodies[name] = body

    changes: list[TabChange] = []
    for name, body in bodies.items():
        path = dest / f"{name}.csv"
        before = None
        if path.exists():
            try:
                before = read_csv_text(name, path.read_text(encoding="utf-8-sig"))
            except ValueError:
                before = None  # the snapshot on disk is itself broken; treat as new
        changes.append(compare(before, read_csv_text(name, body)))

    if dry_run:
        return {"sheet_id": sheet_id, "tabs": {}}, changes

    dest.mkdir(parents=True, exist_ok=True)
    meta_path = dest / "snapshot.json"
    meta: dict[str, object] = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    tabs = dict(meta.get("tabs") or {})
    for name, body in bodies.items():
        (dest / f"{name}.csv").write_text(body, encoding="utf-8")
        tabs[name] = {
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "bytes": len(body.encode("utf-8")),
        }
    meta.update({
        "sheet_id": sheet_id,
        "pulled_at": _dt.datetime.now(_dt.timezone.utc)
                        .replace(microsecond=0).isoformat(),
        "tabs": tabs,
    })
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta, changes
