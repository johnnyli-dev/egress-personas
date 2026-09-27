"""A committed population, to catch a behaviour change nobody meant to make.

The other tests check properties; this one checks that the numbers themselves have not
moved. A refactor that quietly reorders a draw passes every property test and fails
this one, which is the point.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from egress_personas.emit import population_json
from egress_personas.sample import sample
from egress_personas.tables import load_dir

GOLDEN = Path(__file__).resolve().parent / "golden" / "night_fire12-1234.personas.json"
AT = "2026-01-01T00:00:00+00:00"


def current(data_dir):
    return population_json(sample(load_dir(data_dir), "night_fire12", 1234),
                           generated_at=AT)


def test_the_population_matches_the_committed_golden(data_dir):
    now = current(data_dir)
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(now, indent=2) + "\n", encoding="utf-8")
        return
    assert GOLDEN.exists(), (
        f"{GOLDEN} is missing; write it with "
        f"UPDATE_GOLDEN=1 pytest tests/test_golden.py"
    )
    want = json.loads(GOLDEN.read_text())

    if want == now:
        return

    # A diff a person can read, rather than a wall of JSON.
    lines = []
    wp = {p["key"]: p for p in want["personas"]}
    np_ = {p["key"]: p for p in now["personas"]}
    for key in sorted(set(wp) | set(np_)):
        if key not in wp:
            lines.append(f"  + {key}")
        elif key not in np_:
            lines.append(f"  - {key}")
        elif wp[key] != np_[key]:
            for block in ("identity", "sim", "body", "knowledge", "dispositions",
                          "situation", "commitments", "ties", "narrative"):
                if wp[key].get(block) != np_[key].get(block):
                    lines.append(f"  ~ {key}.{block}")
    if want["meta"]["counts"] != now["meta"]["counts"]:
        lines.append(f"  ~ counts {want['meta']['counts']} -> {now['meta']['counts']}")
    raise AssertionError(
        "the generated population no longer matches tests/golden/.\n"
        + "\n".join(lines[:40])
        + ("\n  ... and more" if len(lines) > 40 else "")
        + "\n\nIf the change was intended, refresh it with:\n"
          "  UPDATE_GOLDEN=1 pytest tests/test_golden.py"
    )
