"""The guarantee that makes the registry editable: one change moves one thing.

Every draw comes from a stream keyed by a content hash of a stable path, so editing
one persona cannot perturb another, and editing one parameter row cannot perturb a
field it does not contribute to. Without that, nobody could tell whether a change in
the results came from the change they made or from the reshuffling it caused.
"""

from __future__ import annotations

import copy
import json

from egress_personas.emit import population_json
from egress_personas.sample import sample
from egress_personas.tables import content_hash, load_dir, read_csv_text

AT = "2026-01-01T00:00:00+00:00"


def blocks(js):
    return {p["key"]: {k: p[k] for k in
                       ("identity", "sim", "body", "knowledge", "dispositions",
                        "situation", "commitments", "ties")}
            for p in js["personas"]}


def test_the_same_snapshot_and_seed_give_identical_output(data_dir):
    a = population_json(sample(load_dir(data_dir), "night_fire12", 1234), generated_at=AT)
    b = population_json(sample(load_dir(data_dir), "night_fire12", 1234), generated_at=AT)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_a_different_seed_moves_almost_everybody(data_dir):
    a = blocks(population_json(sample(load_dir(data_dir), "night_fire12", 1234),
                               generated_at=AT))
    b = blocks(population_json(sample(load_dir(data_dir), "night_fire12", 99),
                               generated_at=AT))
    shared = set(a) & set(b)
    moved = sum(1 for k in shared if a[k]["body"] != b[k]["body"])
    assert moved / max(len(shared), 1) > 0.9


def test_editing_one_case_leaves_every_other_persona_untouched(data_dir, mutate,
                                                              edit_cell):
    """The whole point of keying draws by a stable identity rather than an index."""
    base = blocks(population_json(sample(load_dir(data_dir), "night_fire12", 1234),
                                  generated_at=AT))
    t = mutate("cases", lambda x: edit_cell(x, "C07", "notes", "reworded entirely"))
    after = blocks(population_json(sample(t, "night_fire12", 1234), generated_at=AT))
    for key in set(base) & set(after):
        if key == "case:C07":
            continue
        assert base[key] == after[key], key


def test_adding_a_case_moves_only_what_it_provably_had_to(data_dir):
    """The exact boundary of the insulation guarantee.

    Values drawn *for* a persona are keyed by that persona's own identity, so they
    cannot move. Two things are population-level by nature and therefore can:

    * membership - one more resident placed means one fewer drawn elsewhere;
    * a repair pass - "bring the under-18 share to 12%" is a statement about everybody.

    So the test is not "nothing changed". It is: nobody changed except the people the
    repair log names, and no tie changed except where its other end came or went. That
    is a property worth having, and one worth stating honestly.
    """
    from egress_personas.tables import Tables

    tabs = {}
    for name in ("parameters", "sources", "population", "social", "cases",
                 "building", "scenarios", "enums"):
        text = (data_dir / f"{name}.csv").read_text(encoding="utf-8-sig")
        if name == "cases":
            lines = text.rstrip("\n").splitlines()
            width = len(lines[0].split(","))
            lines.append(",".join(["C09", "An added resident", "25D"] + [""] * (width - 3)))
            text = "\n".join(lines) + "\n"
        tabs[name] = read_csv_text(name, text)

    before = sample(load_dir(data_dir), "night_fire12", 1234)
    after = sample(Tables(tabs, {}), "night_fire12", 1234)
    assert any(p.case_id == "C09" for p in after.people)

    base = blocks(population_json(before, generated_at=AT))
    now = blocks(population_json(after, generated_at=AT))
    common = set(base) & set(now)
    assert len(common) > 100

    repaired = {m["who"] for m in before.repairs} | {m["who"] for m in after.repairs}
    drawn = ("identity", "sim", "body", "knowledge", "dispositions", "situation",
             "commitments")
    for key in common:
        if key in repaired:
            continue
        for block in drawn:
            assert base[key][block] == now[key][block], (key, block)

    entered, left = set(now) - set(base), set(base) - set(now)
    for key in common:
        was = {(t["to"], t["kind"]) for t in base[key]["ties"]}
        is_ = {(t["to"], t["kind"]) for t in now[key]["ties"]}
        for to, _ in (was - is_):
            assert to in left or key in repaired or to in repaired, (key, to)
        for to, _ in (is_ - was):
            assert to in entered or key in repaired or to in repaired, (key, to)


def test_a_repair_pass_names_everybody_it_touched(population):
    """The coupling above is only acceptable because it is reported."""
    for move in population.repairs:
        assert move["who"]
        assert move["change"]
    touched = [m for m in population.repairs if m["who"] != "-"]
    for m in touched:
        assert any(p.key == m["who"] for p in population.people), m


def test_no_repair_ever_touches_a_hand_authored_case(data_dir):
    for seed in (1, 42, 1234, 7777):
        pop = sample(load_dir(data_dir), "night_fire12", seed)
        cases = {p.key for p in pop.people if p.case_id}
        for move in pop.repairs:
            assert move["who"] not in cases, (seed, move)


def test_editing_one_parameter_moves_only_the_fields_it_feeds(data_dir, mutate,
                                                              edit_cell):
    base = blocks(population_json(sample(load_dir(data_dir), "night_fire12", 1234),
                                  generated_at=AT))
    # P023 sets dispositions.altruism and nothing else.
    t = mutate("parameters", lambda x: edit_cell(x, "P023", "p1", "0.55"))
    after = blocks(population_json(sample(t, "night_fire12", 1234), generated_at=AT))
    changed_fields: set[str] = set()
    for key in set(base) & set(after):
        for block in ("body", "knowledge", "dispositions", "identity", "situation"):
            for field, value in base[key][block].items():
                if after[key][block].get(field) != value:
                    changed_fields.add(f"{block}.{field}")
    assert changed_fields == {"dispositions.altruism"}


def test_the_snapshot_hash_survives_a_reexport(data_dir):
    """Re-exporting from Sheets changes line endings, padding and float spellings.

    Hashing the bytes would move the run id without a single value changing, which
    would make the id useless within a week.
    """
    original = load_dir(data_dir)
    tabs = {}
    for name, tab in original.tabs.items():
        text = (data_dir / f"{name}.csv").read_text(encoding="utf-8-sig")
        noisy = text.replace("\n", "\r\n")
        noisy = noisy.replace(",TRUE,", ",true,").replace(",FALSE,", ",false,")
        tabs[name] = read_csv_text(name, noisy)
    assert content_hash(tabs) == content_hash(original.tabs)


def test_a_real_value_change_does_move_the_hash(data_dir, mutate, edit_cell):
    original = load_dir(data_dir)
    t = mutate("population", lambda x: edit_cell(x, "T001", "value", "1.90"))
    assert content_hash(t.tabs) != content_hash(original.tabs)


def test_the_run_id_is_reproducible_and_scenario_specific(data_dir):
    a = sample(load_dir(data_dir), "night_fire12", 1234)
    b = sample(load_dir(data_dir), "night_fire12", 1234)
    c = sample(load_dir(data_dir), "day_fire12", 1234)
    d = sample(load_dir(data_dir), "night_fire12", 1235)
    assert a.run_id == b.run_id
    assert len({a.run_id, c.run_id, d.run_id}) == 3


def test_draw_streams_are_independent_across_personas_and_fields():
    from egress_personas.rng import draw_rng
    seen = {}
    for who in ("case:C01", "synth:4A:0", "synth:4A:1"):
        for field in ("body.base_speed", "dispositions.altruism"):
            v = draw_rng(7, f"persona/{who}/{field}/P001").unit()
            assert v not in seen, (who, field, seen.get(v))
            seen[v] = (who, field)


def test_the_pcg32_port_does_not_drift():
    """A regression vector for the generator itself.

    Generated from this port, so it pins the Python side; it does not by itself prove
    parity with the simulation's Rust PCG32. Nothing here depends on that parity - only
    on this side staying put - but a matching test on the Rust side would close it.
    """
    from egress_personas.rng import Pcg32
    r = Pcg32(1234, 2)
    assert [r.next_u32() for _ in range(6)] == [
        172642925, 2324288160, 2928762487, 525694823, 3570080288, 2494153234,
    ]
