from __future__ import annotations

import copy
import io
from pathlib import Path

import pytest

from egress_personas.tables import Tables, load_dir, read_csv_text

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA


@pytest.fixture
def tables() -> Tables:
    return load_dir(DATA)


@pytest.fixture
def mutate():
    """Reload the snapshot with one tab's CSV text rewritten.

    Used to check that a broken cell produces the message a person needs, without
    touching the committed snapshot.
    """
    def _mutate(tab: str, fn) -> Tables:
        tabs = {}
        for name in ("parameters", "sources", "population", "social", "cases",
                     "building", "scenarios", "enums"):
            text = (DATA / f"{name}.csv").read_text(encoding="utf-8-sig")
            if name == tab:
                text = fn(text)
            tabs[name] = read_csv_text(name, text)
        return Tables(tabs, {})
    return _mutate


@pytest.fixture
def edit_cell():
    """Rewrite one cell of a CSV, by row key and column name."""
    import csv

    def _edit(text: str, key: str, column: str, value: str) -> str:
        rows = list(csv.reader(io.StringIO(text)))
        header = rows[0]
        col = header.index(column)
        for r in rows[1:]:
            if r and r[0] == key:
                while len(r) <= col:
                    r.append("")
                r[col] = value
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerows(rows)
        return buf.getvalue()
    return _edit


@pytest.fixture(scope="session")
def population():
    from egress_personas.sample import sample
    return sample(load_dir(DATA), "night_fire12", 1234)


@pytest.fixture
def fresh_population():
    from egress_personas.sample import sample

    def _make(scenario: str = "night_fire12", seed: int = 1234, tables=None):
        return sample(tables or load_dir(DATA), scenario, seed)
    return _make


@pytest.fixture(scope="session")
def population_json(population):
    from egress_personas.emit import population_json as pj
    return copy.deepcopy(pj(population, generated_at="2026-01-01T00:00:00+00:00"))
