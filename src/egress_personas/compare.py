"""Comparing a sampled population against the team's first hand-typed roster.

The roster is kept as a reference, never as an input. It disagrees with the
occupancy and mix targets, and saying exactly how is more useful than either
adopting it or ignoring it.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from .sample import Population

#: The old workbook's fused labels, split into the covariates they were hiding.
LEGACY_TYPE: dict[str, dict[str, Any]] = {
    "adult male": {"sex": "male", "adult": True},
    "adult female": {"sex": "female", "adult": True},
    "elderly male": {"sex": "male", "elderly": True},
    "elderly female": {"sex": "female", "elderly": True},
    "child": {"child": True},
    "mobility impaired": {"limiting": True},
    "abscent": {"absent": True},
}


def read_roster(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("unit") or "").strip()]


def compare(pop: Population, roster_path: Path) -> str:
    rows = read_roster(roster_path)
    L: list[str] = ["# Sampled population against the first hand-typed roster", ""]

    units_roster = {r["unit"] for r in rows}
    n_roster = len(rows)
    n_units = len(pop.units)
    L += [
        f"The roster lists **{n_roster}** residents across **{len(units_roster)}** "
        f"flats — {n_roster / max(len(units_roster), 1):.2f} per flat. This sample has "
        f"**{len(pop.people)}** across **{n_units}** — "
        f"{len(pop.people) / max(n_units, 1):.2f} per flat, against a target of "
        f"{pop.targets.persons_per_flat}.",
        "",
        "The roster is kept as a reference, not read as an input. Where the two differ "
        "it is worth asking which is wrong; the roster was typed by hand and never "
        "reconciled with a census figure, but it is also the only record of what the "
        "team believed the building held.",
        "",
    ]

    counts = Counter((r.get("type") or "").strip().lower() for r in rows)
    L += ["## What the roster's own labels imply", "",
          "| roster label | count | share |", "|---|---|---|"]
    for label, c in counts.most_common():
        L.append(f"| {label or '(blank)'} | {c} | {c / max(n_roster, 1):.1%} |")
    L += ["",
          "Three of these labels are not occupant types at all. `abscent` is a state, "
          "so it is presence here, not a class. `mobility impaired` descends stairs in "
          "the roster's own table at 1.5 floors a minute, so it is a walking difficulty "
          "rather than a wheelchair — and at "
          f"{counts.get('mobility impaired', 0) / max(n_roster, 1):.1%} it matches the "
          "census ambulatory-difficulty share, not the 1.3% wheelchair share. And the "
          "`adult`/`elderly` split throws away age, which every target in the "
          "literature is conditioned on.",
          ""]

    L += ["## Side by side", "", "| | roster | sampled |", "|---|---|---|"]
    n = max(len(pop.people), 1)
    female_r = sum(c for t, c in counts.items() if "female" in t)
    male_r = sum(c for t, c in counts.items() if "male" in t and "female" not in t)
    L.append(f"| female | {female_r / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if p.identity['sex'] == 'female') / n:.1%} |")
    L.append(f"| male | {male_r / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if p.identity['sex'] == 'male') / n:.1%} |")
    eld_r = sum(c for t, c in counts.items() if t.startswith("elderly"))
    L.append(f"| 65 and over | {eld_r / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if p.identity['age_years'] >= 65) / n:.1%} |")
    kid_r = counts.get("child", 0)
    L.append(f"| under 18 | {kid_r / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if p.identity['age_years'] < 18) / n:.1%} |")
    L.append(f"| walking difficulty or wheelchair | "
             f"{counts.get('mobility impaired', 0) / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if p.body['mobility'] != 'none') / n:.1%} |")
    L.append(f"| not in the building | "
             f"{counts.get('abscent', 0) / max(n_roster, 1):.1%} | "
             f"{sum(1 for p in pop.people if not p.situation['present']) / n:.1%} |")
    pets_r = sum(1 for r in rows if (r.get("has_pet") or "").strip().lower()
                 in ("yes", "true", "y"))
    L.append(f"| flats with a pet | {pets_r / max(len(units_roster), 1):.1%} | "
             f"{sum(1 for h in pop.households if h.has_pet) / max(len(pop.households), 1):.1%} |")
    L += ["",
          f"The roster has **{kid_r}** child in {n_roster} residents. A tower with one "
          f"child in the whole building is possible but unlikely, and it is the kind of "
          f"thing a hand-typed roster produces and a sampled one does not.",
          ""]
    return "\n".join(L)
