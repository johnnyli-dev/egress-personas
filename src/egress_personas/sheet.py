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
from pathlib import Path

from .tables import TABS, read_csv_text

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


def pull(sheet_id: str, dest: Path, *, token: str | None = None,
         only: list[str] | None = None) -> dict[str, object]:
    """Fetch every tab, validate its shape, and write the snapshot."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    names = only or list(TABS)
    bodies: dict[str, str] = {}
    for name in names:
        body = fetch_tab(sheet_id, name, token=token)
        read_csv_text(name, body)  # fail before overwriting a good snapshot
        bodies[name] = body

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
    return meta
