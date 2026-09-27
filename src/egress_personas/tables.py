"""Reading the Sheet's tabs as CSV, and hashing them by content.

The declared column list per tab is the contract. An unknown column is an error
rather than a silent no-op — the same posture the simulation's config takes
(`deny_unknown_fields`, crates/fe-core/src/rules.rs:13-14), because a column
somebody added and the generator ignored is the worst kind of bug here: the sheet
says one thing and the run does another.

The content hash covers *normalized logical content*, not the CSV bytes. Exporting
the same sheet twice changes line endings, float spellings and column padding
without changing a single value; hashing bytes would make a run id useless within
a week.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

TRUE_WORDS = {"true", "t", "yes", "y", "1"}
FALSE_WORDS = {"false", "f", "no", "n", "0"}


@dataclass(frozen=True)
class TabSpec:
    name: str
    key: str | None
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()

    @property
    def columns(self) -> tuple[str, ...]:
        return self.required + self.optional


#: Every tab of the Sheet, with its columns. `key` is the column that must be
#: unique and non-blank.
TABS: dict[str, TabSpec] = {t.name: t for t in [
    TabSpec(
        "parameters", "id",
        required=("id", "name", "phase", "category", "target", "mechanism", "dist",
                  "evidence", "status", "enabled"),
        optional=("applies_to", "p1", "p2", "p3", "p4", "categories", "weights",
                  "unit", "lit_low", "lit_high", "effect_size", "source_ids",
                  "finding", "priority", "sensitivity_rank",
                  "sensitivity_delta_tts_s", "sensitivity_delta_tte_s",
                  "owner", "last_reviewed", "notes"),
    ),
    TabSpec(
        "sources", "id",
        required=("id", "short", "cite"),
        optional=("url", "kind", "year", "finding", "read_by", "read_on", "notes"),
    ),
    TabSpec(
        "population", "id",
        required=("id", "dimension", "category", "value", "unit"),
        optional=("tolerance", "basis", "source_ids", "notes"),
    ),
    TabSpec(
        "social", "id",
        required=("id", "tie_kind", "scope", "formation_rate", "strength_dist",
                  "symmetric", "evidence"),
        optional=("rate_kind", "tenure_ref_years", "min_age_years", "s1", "s2",
                  "s3", "s4", "source_ids", "finding", "notes"),
    ),
    TabSpec(
        "cases", "case_id",
        required=("case_id", "name", "unit"),
        optional=("household_id", "household_role", "age_years", "sex", "mobility",
                  "tenure_years", "present", "asleep", "activity", "alarm_audible",
                  "has_pet", "floorplan_familiarity", "habitual_stair",
                  "knows_second_stair", "prior_false_alarms", "fire_safety_training",
                  "mill_tendency", "seeks_confirmation", "authority_compliance",
                  "altruism", "risk_tolerance", "leadership", "commitments",
                  "narrative_override", "notes"),
    ),
    TabSpec(
        "building", "unit_label",
        required=("unit_label", "floor_label", "unit_letter", "sim_floor", "plan_id",
                  "seed_tile_x", "seed_tile_y", "occupiable"),
        optional=("notes",),
    ),
    TabSpec(
        "scenarios", "scenario_id",
        required=("scenario_id", "plan_id", "num_floors", "time_of_day",
                  "alarm_quality", "default_seed"),
        optional=("building_json", "fire_floor_label", "absent_share", "asleep_share",
                  "out_of_flat_share", "notes"),
    ),
    TabSpec(
        "enums", None,
        required=("vocab", "value"),
        optional=("label", "description", "sort_order"),
    ),
]}


def col_letter(i: int) -> str:
    """0-based column index to its spreadsheet letter."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class Table:
    """One tab: its declared columns, and its rows as dicts of raw strings."""

    def __init__(self, name: str, columns: list[str], rows: list[dict[str, str]],
                 row_numbers: list[int], widths: list[int] | None = None) -> None:
        self.name = name
        self.columns = columns
        self.rows = rows
        self.row_numbers = row_numbers  # 1-based sheet row of each entry
        #: How many fields each row actually had. A row narrower than the header has
        #: silently shifted its values one column left, which is the worst kind of
        #: error here: it parses, and every value afterwards is wrong.
        self.widths = widths if widths is not None else [len(columns)] * len(rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict[str, str]]:
        return iter(self.rows)

    def tab(self) -> str:
        return self.name.capitalize()

    def where(self, i: int, column: str | None = None) -> str:
        """An A1 reference a person can click, e.g. 'Parameters!G23'."""
        row = self.row_numbers[i] if 0 <= i < len(self.row_numbers) else i + 2
        if column is None or column not in self.columns:
            return f"{self.tab()}!{row}"
        return f"{self.tab()}!{col_letter(self.columns.index(column))}{row}"


@dataclass
class Tables:
    tabs: dict[str, Table]
    snapshot: dict[str, Any]

    def __getitem__(self, name: str) -> Table:
        return self.tabs[name]

    def get(self, name: str) -> Table | None:
        return self.tabs.get(name)


# --- value coercion --------------------------------------------------------------
# Blank always means "not stated", never zero and never False. That is what lets a
# Cases row pin two fields and leave the rest to the sampler.

def text(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def as_float(v: Any) -> float | None:
    s = text(v)
    if s is None:
        return None
    return float(s.replace(",", "").rstrip("%")) / (100.0 if s.endswith("%") else 1.0)


def as_int(v: Any) -> int | None:
    f = as_float(v)
    return None if f is None else int(round(f))


def as_bool(v: Any) -> bool | None:
    s = text(v)
    if s is None:
        return None
    low = s.lower()
    if low in TRUE_WORDS:
        return True
    if low in FALSE_WORDS:
        return False
    raise ValueError(f"{s!r} is not a yes/no value")


def as_list(v: Any, sep: str = ";") -> list[str]:
    s = text(v)
    return [p.strip() for p in s.split(sep) if p.strip()] if s else []


def _norm(v: str | None) -> Any:
    """One cell, normalized for hashing: blanks unify, numbers lose their spelling."""
    s = text(v)
    if s is None:
        return None
    low = s.lower()
    if low in TRUE_WORDS and low not in {"1"}:
        return True
    if low in FALSE_WORDS and low not in {"0"}:
        return False
    try:
        f = float(s.replace(",", ""))
    except ValueError:
        return s
    return int(f) if f == int(f) and abs(f) < 1e15 else float(repr(f))


def content_hash(tabs: dict[str, Table]) -> str:
    """blake2b over normalized content, so a re-export does not move it."""
    payload = {
        name: [
            [[c, _norm(row.get(c))] for c in tab.columns]
            for row in tab.rows
        ]
        for name, tab in sorted(tabs.items())
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return "blake2b128:" + hashlib.blake2b(blob, digest_size=16).hexdigest()


def read_csv_text(name: str, body: str) -> Table:
    """One tab from CSV text. Undeclared and missing columns are both errors."""
    spec = TABS[name]
    reader = csv.reader(body.splitlines())
    try:
        header = [h.strip() for h in next(reader)]
    except StopIteration:
        raise ValueError(f"{name}.csv is empty (expected a header row)") from None

    # Trailing blank header cells are what Sheets exports past the last column.
    while header and not header[-1]:
        header.pop()

    unknown = [h for h in header if h and h not in spec.columns]
    if unknown:
        raise ValueError(
            f"{spec.name.capitalize()}: undeclared column(s) "
            f"{', '.join(repr(u) for u in unknown)}. Declared columns are: "
            f"{', '.join(spec.columns)}. Add the column to TABS in tables.py, or "
            f"rename it in the Sheet — a column the generator ignores is worse than "
            f"an error."
        )
    missing = [c for c in spec.required if c not in header]
    if missing:
        raise ValueError(
            f"{spec.name.capitalize()}: missing required column(s) "
            f"{', '.join(repr(m) for m in missing)}"
        )

    rows: list[dict[str, str]] = []
    numbers: list[int] = []
    widths: list[int] = []
    for n, raw in enumerate(reader, start=2):
        row = {h: (raw[i] if i < len(raw) else "") for i, h in enumerate(header) if h}
        if any(text(v) is not None for v in row.values()):
            rows.append(row)
            numbers.append(n)
            widths.append(len(raw))
    return Table(name, header, rows, numbers, widths)


def load_dir(path: Path) -> Tables:
    """Load every tab from a snapshot directory."""
    path = Path(path)
    tabs: dict[str, Table] = {}
    for name in TABS:
        f = path / f"{name}.csv"
        if not f.exists():
            raise FileNotFoundError(
                f"{f} not found. Run `personas pull` to snapshot the Sheet, or "
                f"`personas init-data` to write a starting set."
            )
        tabs[name] = read_csv_text(name, f.read_text(encoding="utf-8-sig"))

    meta_file = path / "snapshot.json"
    snapshot = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    snapshot["content_hash"] = content_hash(tabs)
    return Tables(tabs, snapshot)
