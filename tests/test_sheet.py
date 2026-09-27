"""Pulling from the Sheet: the one part that talks to the network.

The network call itself is stubbed; what is worth testing is everything around it —
that the right tabs are asked for, that a malformed tab is refused *before* a good
snapshot is overwritten, and that a pull followed by a build gives the same hash as the
committed snapshot. Without that last one, "the run names the revision it came from"
would be a claim rather than a property.
"""

from __future__ import annotations

import json

import pytest

from egress_personas import sheet as sheet_mod
from egress_personas.tables import TABS, load_dir
from egress_personas.validate import problems


@pytest.fixture
def stub_sheet(monkeypatch, data_dir):
    """Serve the committed snapshot as though it came from Google."""
    asked: list[tuple[str, str, str | None]] = []

    def fake_fetch(sheet_id, name, token=None, timeout=30.0):
        asked.append((sheet_id, sheet_mod.tab_title(name), token))
        return (data_dir / f"{name}.csv").read_text(encoding="utf-8-sig")

    monkeypatch.setattr(sheet_mod, "fetch_tab", fake_fetch)
    return asked


def test_pull_asks_for_every_tab_by_its_title(tmp_path, stub_sheet):
    sheet_mod.pull("SHEET123", tmp_path / "data", token="tok")
    titles = [a[1] for a in stub_sheet]
    assert titles == [t.capitalize() for t in TABS]
    assert all(a[0] == "SHEET123" for a in stub_sheet)
    assert all(a[2] == "tok" for a in stub_sheet)


def test_pull_records_the_sheet_and_when(tmp_path, stub_sheet):
    meta = sheet_mod.pull("SHEET123", tmp_path / "data")
    assert meta["sheet_id"] == "SHEET123"
    assert meta["pulled_at"].endswith("+00:00")
    assert set(meta["tabs"]) == set(TABS)
    for tab in meta["tabs"].values():
        assert len(tab["sha256"]) == 64
        assert tab["bytes"] > 0
    written = json.loads((tmp_path / "data" / "snapshot.json").read_text())
    assert written["sheet_id"] == "SHEET123"


def test_a_pulled_snapshot_hashes_and_validates_the_same(tmp_path, stub_sheet, data_dir):
    """The property behind 'a run names the revision it came from'."""
    dest = tmp_path / "data"
    sheet_mod.pull("SHEET123", dest)
    pulled = load_dir(dest)
    assert problems(pulled) == []
    assert pulled.snapshot["content_hash"] == load_dir(data_dir).snapshot["content_hash"]


def test_a_malformed_tab_does_not_overwrite_a_good_snapshot(tmp_path, stub_sheet,
                                                            data_dir, monkeypatch):
    dest = tmp_path / "data"
    sheet_mod.pull("SHEET123", dest)
    before = (dest / "sources.csv").read_text()

    good = sheet_mod.fetch_tab

    def broken(sheet_id, name, token=None, timeout=30.0):
        if name == "sources":
            return "id,short,favourite_colour\nx,y,blue\n"
        return good(sheet_id, name, token)

    monkeypatch.setattr(sheet_mod, "fetch_tab", broken)
    with pytest.raises(ValueError) as e:
        sheet_mod.pull("SHEET123", dest)
    assert "undeclared column(s) 'favourite_colour'" in str(e.value)
    assert (dest / "sources.csv").read_text() == before


def test_pulling_one_tab_leaves_the_others_alone(tmp_path, stub_sheet):
    dest = tmp_path / "data"
    sheet_mod.pull("SHEET123", dest)
    (dest / "cases.csv").write_text("case_id,name,unit\nCZZ,Edited by hand,4A\n")
    sheet_mod.pull("SHEET123", dest, only=["sources"])
    assert "CZZ" in (dest / "cases.csv").read_text()


def test_a_web_page_instead_of_csv_is_explained(monkeypatch):
    class Resp:
        def read(self):
            return b"<!DOCTYPE html><html>Sign in</html>"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(sheet_mod.urllib.request, "urlopen", lambda *a, **k: Resp())
    with pytest.raises(RuntimeError) as e:
        sheet_mod.fetch_tab("ID", "sources")
    assert "not shared for reading by link" in str(e.value)


def test_the_export_url_is_the_csv_endpoint():
    url = sheet_mod.GVIZ.format(sheet_id="ID", tab="Parameters")
    assert url.startswith("https://docs.google.com/spreadsheets/d/ID/")
    assert "tqx=out:csv" in url
    assert "sheet=Parameters" in url
