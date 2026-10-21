"""Checking the Sheet before anything is generated from it.

Every problem names an A1 cell reference and, where it can, suggests what was
meant. This is the module that decides whether somebody who does not write Python
can safely edit the registry: if a typo silently matched nobody, the run would
still succeed and the sheet would be quietly lying.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from . import dists
from .filters import FilterError, parse
from .persona import ATTRS, FIELDS, SAMPLER_OWNED
from .tables import TABS, Tables, as_bool, as_float, as_int, as_list, text

#: Which Enums vocab each column is checked against.
VOCAB_OF: dict[tuple[str, str], str] = {
    ("parameters", "phase"): "phase",
    ("parameters", "category"): "category",
    ("parameters", "mechanism"): "mechanism",
    ("parameters", "dist"): "dist",
    ("parameters", "evidence"): "evidence",
    ("parameters", "effect_size"): "effect_size",
    ("parameters", "status"): "status",
    ("sources", "kind"): "source_kind",
    ("population", "dimension"): "dimension",
    ("population", "basis"): "basis",
    ("social", "tie_kind"): "tie_kind",
    ("outputs", "dtype"): "dtype",
    ("outputs", "phase"): "phase",
    ("outputs", "status"): "status",
    ("distributions", "family"): "family",
    ("distributions", "evidence"): "evidence",
    ("distributions", "status"): "status",
    ("effects", "mechanism"): "effect_mechanism",
    ("effects", "evidence"): "evidence",
    ("effects", "status"): "status",
    ("social", "scope"): "scope",
    ("social", "rate_kind"): "rate_kind",
    ("social", "strength_dist"): "dist",
    ("social", "evidence"): "evidence",
    ("cases", "sex"): "sex",
    ("cases", "mobility"): "mobility",
    ("cases", "household_role"): "household_role",
    ("cases", "activity"): "activity",
    ("cases", "habitual_stair"): "stair",
    ("building", "unit_letter"): "unit_letter",
    ("scenarios", "time_of_day"): "time_of_day",
    ("scenarios", "alarm_quality"): "alarm_quality",
}

#: Columns that must parse as a number, a whole number, or a yes/no.
FLOAT_COLS = {
    "parameters": ("p1", "p2", "p3", "p4", "lit_low", "lit_high",
                   "sensitivity_delta_tts_s", "sensitivity_delta_tte_s"),
    "population": ("value", "tolerance"),
    "social": ("formation_rate", "tenure_ref_years", "min_age_years",
               "s1", "s2", "s3", "s4"),
    "cases": ("age_years", "tenure_years", "floorplan_familiarity", "mill_tendency",
              "seeks_confirmation", "authority_compliance", "altruism",
              "risk_tolerance", "leadership"),
    "scenarios": ("absent_share", "asleep_share", "out_of_flat_share"),
    "outputs": ("lo", "hi"),
    "distributions": ("p1", "p2", "p3", "p4"),
    "effects": ("value",),
}
INT_COLS = {
    "parameters": ("priority", "sensitivity_rank"),
    "sources": ("year",),
    "cases": ("prior_false_alarms",),
    "building": ("floor_label", "sim_floor", "seed_tile_x", "seed_tile_y"),
    "outputs": ("decimals",),
    "effects": ("priority",),
    "scenarios": ("num_floors", "fire_floor_label", "default_seed"),
    "enums": ("sort_order",),
}
BOOL_COLS = {
    "parameters": ("enabled",),
    "social": ("symmetric",),
    "cases": ("present", "asleep", "alarm_audible", "has_pet",
              "knows_second_stair", "fire_safety_training"),
    "building": ("occupiable",),
    "outputs": ("required",),
    "effects": ("enabled",),
}

#: Cases columns that pin a persona field, and the field each pins.
CASE_FIELD: dict[str, str] = {
    "alarm_audible": "situation.alarm_audible",
    "floorplan_familiarity": "knowledge.floorplan_familiarity",
    "habitual_stair": "knowledge.habitual_stair",
    "knows_second_stair": "knowledge.knows_second_stair",
    "prior_false_alarms": "knowledge.prior_false_alarms",
    "fire_safety_training": "knowledge.fire_safety_training",
    "mill_tendency": "dispositions.mill_tendency",
    "seeks_confirmation": "dispositions.seeks_confirmation",
    "authority_compliance": "dispositions.authority_compliance",
    "altruism": "dispositions.altruism",
    "risk_tolerance": "dispositions.risk_tolerance",
    "leadership": "dispositions.leadership",
}

COMMITMENT_KINDS = ("pet", "child", "dependent", "valuables", "documents", "neighbour")


@dataclass(frozen=True)
class Problem:
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where:24} {self.message}"


def _suggest(value: str, known) -> str:
    close = difflib.get_close_matches(value, sorted(known), n=1, cutoff=0.6)
    return f" — did you mean {close[0]!r}?" if close else ""


def vocabularies(tables: Tables) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for row in tables["enums"]:
        v, val = text(row.get("vocab")), text(row.get("value"))
        if v and val:
            out.setdefault(v, set()).add(val)
    return out


def problems(tables: Tables) -> list[Problem]:  # noqa: C901 - a checklist, read top to bottom
    out: list[Problem] = []
    vocab = vocabularies(tables)

    def add(where: str, msg: str) -> None:
        out.append(Problem(where, msg))

    # --- 1. every declared vocabulary exists in Enums --------------------------
    for (tab, col), v in sorted(VOCAB_OF.items()):
        if v not in vocab:
            add(f"{tab.capitalize()}!{col}",
                f"checked against Enums vocab {v!r}, which the Enums tab does not define")

    # --- 2. per-tab: keys, types, vocabularies --------------------------------
    for name, spec in TABS.items():
        tab = tables[name]
        seen: dict[str, int] = {}
        for i, row in enumerate(tab):
            width = tab.widths[i] if i < len(tab.widths) else len(tab.columns)
            if width < len(tab.columns):
                add(tab.where(i),
                    f"this row has {width} field(s) but the header declares "
                    f"{len(tab.columns)}. Every value from column "
                    f"{tab.columns[width] if width < len(tab.columns) else '?'!r} "
                    f"onwards has shifted left, so the row parses and means something "
                    f"other than what it says. Add the missing commas.")
            elif width > len(tab.columns):
                add(tab.where(i),
                    f"this row has {width} field(s) but the header declares "
                    f"{len(tab.columns)}; the extra value(s) are dropped")
            for col in spec.required:
                if text(row.get(col)) is None:
                    add(tab.where(i, col), f"{col} is required and blank")
            if spec.key:
                k = text(row.get(spec.key))
                if k is not None:
                    if k in seen:
                        add(tab.where(i, spec.key),
                            f"duplicate {spec.key} {k!r} (first seen at "
                            f"{tab.where(seen[k], spec.key)})")
                    seen[k] = i
            for col in FLOAT_COLS.get(name, ()):
                try:
                    as_float(row.get(col))
                except ValueError:
                    add(tab.where(i, col), f"{col}: {row.get(col)!r} is not a number")
            for col in INT_COLS.get(name, ()):
                try:
                    as_int(row.get(col))
                except ValueError:
                    add(tab.where(i, col), f"{col}: {row.get(col)!r} is not a whole number")
            for col in BOOL_COLS.get(name, ()):
                try:
                    as_bool(row.get(col))
                except ValueError:
                    add(tab.where(i, col),
                        f"{col}: {row.get(col)!r} is not a yes/no value")
            for col in spec.columns:
                v = VOCAB_OF.get((name, col))
                if not v or v not in vocab:
                    continue
                val = text(row.get(col))
                if val is not None and val not in vocab[v]:
                    add(tab.where(i, col),
                        f"{col}: {val!r} is not in Enums vocab {v!r}"
                        f"{_suggest(val, vocab[v])}")

    # --- 3. source ids resolve ------------------------------------------------
    source_ids = {text(r.get("id")) for r in tables["sources"]} - {None}
    for name in ("parameters", "population", "social"):
        tab = tables[name]
        if "source_ids" not in tab.columns:
            continue
        for i, row in enumerate(tab):
            for sid in as_list(row.get("source_ids")):
                if sid not in source_ids:
                    add(tab.where(i, "source_ids"),
                        f"unknown source {sid!r}{_suggest(sid, source_ids)} "
                        f"(add a row to the Sources tab)")

    # --- 4. Parameters: target, dist arity, applies_to, set-priority ties ------
    ptab = tables["parameters"]
    set_rows: dict[tuple[str, int], list[tuple[int, str]]] = {}
    for i, row in enumerate(ptab):
        pid = text(row.get("id")) or f"row {i + 2}"
        target = text(row.get("target"))
        if target and target not in FIELDS:
            if target in SAMPLER_OWNED:
                add(ptab.where(i, "target"),
                    f"target {target!r} is owned by the sampler and cannot be set by a "
                    f"parameter row — it is drawn to hit a Population target instead")
            else:
                add(ptab.where(i, "target"),
                    f"unknown target {target!r}{_suggest(target, FIELDS)} "
                    f"({len(FIELDS)} writable fields are defined)")

        dist = text(row.get("dist"))
        if dist in dists.PARAMS:
            n = dists.arity(dist)
            names = dists.PARAMS[dist]
            for j in range(4):
                col = f"p{j + 1}"
                given = text(row.get(col)) is not None
                if j < n and not given:
                    add(ptab.where(i, col),
                        f"dist {dist!r} needs {col} = {names[j]}")
                if j >= n and given:
                    extra = f" ({', '.join(names)})" if names else ""
                    add(ptab.where(i, col),
                        f"dist {dist!r} takes {n} parameter(s){extra}; "
                        f"{col} = {text(row.get(col))!r} is set and would be ignored")
            if dist in dists.CATEGORICAL_DISTS:
                cats = as_list(row.get("categories"))
                ws = as_list(row.get("weights"))
                if not cats:
                    add(ptab.where(i, "categories"),
                        "dist 'categorical' needs categories, separated by ';'")
                if ws and len(ws) != len(cats):
                    add(ptab.where(i, "weights"),
                        f"{len(ws)} weight(s) for {len(cats)} categor(ies)")
            elif as_list(row.get("categories")):
                add(ptab.where(i, "categories"),
                    f"categories are only used by dist 'categorical', not {dist!r}")

        try:
            pred = parse(row.get("applies_to") or "", set(ATTRS))
            for attr in pred.attrs:
                if attr in FIELDS:
                    add(ptab.where(i, "applies_to"),
                        f"{attr!r} is a field a parameter row can write, so filtering on "
                        f"it would depend on the order rows are applied in. Filter on a "
                        f"sampler-owned attribute instead.")
        except FilterError as e:
            add(ptab.where(i, "applies_to"), f"applies_to: {e}")

        if (text(row.get("mechanism")) == "set" and target in FIELDS
                and as_bool(row.get("enabled")) is not False):
            key = (target, as_int(row.get("priority")) or 100)
            set_rows.setdefault(key, []).append((i, pid))

    for (target, prio), rows in sorted(set_rows.items()):
        if len(rows) < 2:
            continue
        # Two `set` rows at one priority only clash when they can match the same
        # persona. Non-overlapping filters are the normal way to split by age band,
        # so only flag rows that could both fire.
        preds = []
        for i, pid in rows:
            try:
                preds.append((i, pid, parse(ptab.rows[i].get("applies_to") or "", set(ATTRS))))
            except FilterError:
                preds.append((i, pid, parse("")))
        for a in range(len(preds)):
            for b in range(a + 1, len(preds)):
                ia, pa, qa = preds[a]
                ib, pb, qb = preds[b]
                if _may_overlap(qa, qb):
                    add(ptab.where(ib, "priority"),
                        f"{pb} and {pa} both 'set' {target} at priority {prio} and their "
                        f"applies_to can match the same persona ({qa} / {qb}). Give one a "
                        f"higher priority, or narrow one of them.")

    # --- 5. Cases: units, households, pinned values in range ------------------
    units = {text(r.get("unit_label")): r for r in tables["building"]}
    ctab = tables["cases"]
    hh_units: dict[str, str] = {}
    for i, row in enumerate(ctab):
        unit = text(row.get("unit"))
        if unit and unit not in units:
            add(ctab.where(i, "unit"),
                f"unit {unit!r} is not in the Building tab{_suggest(unit, set(units) - {None})}")
        hid = text(row.get("household_id"))
        if hid and unit:
            if hid in hh_units and hh_units[hid] != unit:
                add(ctab.where(i, "household_id"),
                    f"household {hid!r} is in both {hh_units[hid]} and {unit}; "
                    f"a household lives in one flat")
            hh_units[hid] = unit
        for col, path in CASE_FIELD.items():
            if col not in ctab.columns:
                continue
            raw = text(row.get(col))
            if raw is None:
                continue
            spec = FIELDS[path]
            if spec.dtype == "float":
                try:
                    v = as_float(raw)
                except ValueError:
                    continue
                if (spec.lo is not None and v < spec.lo) or (spec.hi is not None and v > spec.hi):
                    add(ctab.where(i, col),
                        f"{col} = {v} is outside {path}'s range "
                        f"[{spec.lo}, {spec.hi}]")
        for part in as_list(row.get("commitments")):
            bits = part.split(":")
            if len(bits) != 3:
                add(ctab.where(i, "commitments"),
                    f"{part!r} should read kind:what:delay_s, e.g. 'pet:cat:60'")
                continue
            kind, _what, delay = bits
            if kind not in COMMITMENT_KINDS:
                add(ctab.where(i, "commitments"),
                    f"commitment kind {kind!r} is not one of "
                    f"{', '.join(COMMITMENT_KINDS)}{_suggest(kind, COMMITMENT_KINDS)}")
            try:
                as_float(delay)
            except ValueError:
                add(ctab.where(i, "commitments"),
                    f"{part!r}: delay {delay!r} is not a number of seconds")

    # --- 6. Building: floors, sim floors, unit labels --------------------------
    btab = tables["building"]
    for i, row in enumerate(btab):
        label, floor = text(row.get("unit_label")), text(row.get("floor_label"))
        letter = text(row.get("unit_letter"))
        if label and floor and letter and label != f"{floor}{letter}":
            add(btab.where(i, "unit_label"),
                f"unit_label {label!r} does not match floor {floor} and letter {letter!r}")

    # --- 7. Scenarios: plan and fire floor exist ------------------------------
    plans = {text(r.get("plan_id")) for r in btab} - {None}
    floors = {text(r.get("floor_label")) for r in btab} - {None}
    stab = tables["scenarios"]
    for i, row in enumerate(stab):
        plan = text(row.get("plan_id"))
        if plan and plan not in plans:
            add(stab.where(i, "plan_id"),
                f"no Building rows for plan {plan!r}{_suggest(plan, plans)}")
        fire = text(row.get("fire_floor_label"))
        if fire and fire not in floors:
            add(stab.where(i, "fire_floor_label"),
                f"floor {fire} has no flats in the Building tab")
        n = as_int(row.get("num_floors"))
        worst = max((as_int(r.get("sim_floor")) or 0) for r in btab) if len(btab) else 0
        if n is not None and worst >= n:
            add(stab.where(i, "num_floors"),
                f"num_floors = {n} but the Building tab reaches sim_floor {worst}; "
                f"the simulation only populates floors below num_floors")

    # --- 8. Population: shares that should sum to one, per cohort -------------
    # A cohort's rows are a complete replacement for the dimension it touches, so each
    # cohort's shares have to sum on their own. Checking them together would add five
    # buildings' worth of age bands and get five.
    for dim in ("age_band", "sex", "tenure", "household_size"):
        groups: dict[str, list[tuple[int, dict]]] = {}
        for i, r in enumerate(tables["population"]):
            if text(r.get("dimension")) != dim or text(r.get("unit")) != "share":
                continue
            groups.setdefault(text(r.get("cohort")) or "", []).append((i, r))
        for cohort, rows in sorted(groups.items()):
            total = sum((as_float(r.get("value")) or 0.0) for _, r in rows)
            scale = 100.0 if total > 50 else 1.0
            if abs(total / scale - 1.0) > 0.02:
                i = rows[0][0]
                whose = f"cohort {cohort!r}'s " if cohort else ""
                add(tables["population"].where(i, "value"),
                    f"{whose}{dim} shares sum to {total:g}, not "
                    f"{'100' if scale == 100 else '1'}")

    # --- 8b. Outputs, Distributions and Effects: the compile layer ------------
    from . import effects as _fx
    from .dists_ref import FAMILIES

    otab, dtab, etab = (tables.get("outputs"), tables.get("distributions"),
                        tables.get("effects"))
    out_ids = {text(r.get("output_id")) for r in (otab or [])} - {None}
    dist_ids = {text(r.get("dist_id")) for r in (dtab or [])} - {None}
    readable = _fx.readable()

    #: How many positional parameters each family takes.
    ARITY = {"const": 1, "uniform": 2, "normal": 2, "lognormal": 2, "weibull": 2,
             "triangular": 3, "bernoulli": 1, "empirical_curve": 0}

    if dtab is not None:
        for i, row in enumerate(dtab):
            fam = text(row.get("family"))
            if fam not in FAMILIES:
                continue
            want = ARITY[fam]
            for j in range(1, 5):
                given = text(row.get(f"p{j}")) is not None
                if j <= want and not given:
                    add(dtab.where(i, f"p{j}"),
                        f"family {fam!r} needs p{j}")
                if j > want and given:
                    add(dtab.where(i, f"p{j}"),
                        f"family {fam!r} takes {want} parameter(s); p{j} is set and "
                        f"would be ignored")
            curve = as_list(row.get("curve"))
            if fam == "empirical_curve" and not curve:
                add(dtab.where(i, "curve"),
                    "family 'empirical_curve' needs a curve of value:share pairs, "
                    "separated by ';'")
            for pair in curve:
                if len(pair.split(":")) != 2:
                    add(dtab.where(i, "curve"),
                        f"{pair!r} should read value:share, e.g. '1.83:0.385'")

    if otab is not None:
        for i, row in enumerate(otab):
            want = text(row.get("reference_dist"))
            if not want or "{" in want:
                continue   # templated references resolve at compile time
            if want not in dist_ids:
                add(otab.where(i, "reference_dist"),
                    f"no distribution {want!r} on the Distributions tab"
                    f"{_suggest(want, dist_ids) if dist_ids else ''}")

    if etab is not None:
        quantile_per_output: dict[str, list[tuple[int, str]]] = {}
        for i, row in enumerate(etab):
            eid = text(row.get("effect_id")) or f"row {i + 2}"
            mech = text(row.get("mechanism"))
            out_id = text(row.get("output"))
            if out_id and out_id not in out_ids:
                add(etab.where(i, "output"),
                    f"no output {out_id!r} on the Outputs tab"
                    f"{_suggest(out_id, out_ids) if out_ids else ''}")
            for part in as_list(row.get("terms")):
                name, _, weight = part.partition(":")
                name = name.strip()
                if name and name not in readable:
                    add(etab.where(i, "terms"),
                        f"term {name!r} is not a field an effect can read"
                        f"{_suggest(name, readable)}")
                try:
                    float(weight)
                except ValueError:
                    add(etab.where(i, "terms"),
                        f"{part!r} should read name:weight, e.g. 'mill_tendency:1.0'")
            w = text(row.get("within"))
            if w and w not in readable:
                add(etab.where(i, "within"),
                    f"within {w!r} is not a field an effect can read{_suggest(w, readable)}")
            try:
                pred = parse(row.get("applies_to") or "", readable)
                del pred
            except FilterError as e:
                add(etab.where(i, "applies_to"), f"applies_to: {e}")
            if mech in ("direct", "sum") and not text(row.get("from_field")):
                add(etab.where(i, "from_field"),
                    f"mechanism {mech!r} needs from_field: it names what to read")
            if mech == "gate" and text(row.get("value")) is None:
                add(etab.where(i, "value"),
                    "mechanism 'gate' needs value: what the output is forced to")
            if mech == "scale" and text(row.get("value")) is None \
                    and not text(row.get("from_field")):
                add(etab.where(i, "value"),
                    "mechanism 'scale' needs either value or from_field as the factor")
            if mech == "quantile" and as_bool(row.get("enabled")) is not False:
                if not text(row.get("terms")):
                    add(etab.where(i, "terms"),
                        "a quantile effect needs terms: they are what decides a "
                        "resident's place in the distribution")
                quantile_per_output.setdefault(out_id or "", []).append((i, eid))

        for out_id, rows in sorted(quantile_per_output.items()):
            if len(rows) > 1:
                names = ", ".join(e for _i, e in rows)
                add(etab.where(rows[-1][0], "mechanism"),
                    f"{names} are all quantile effects on {out_id!r}. Only one is "
                    f"allowed: two would rank different populations and the published "
                    f"marginal would not survive. Fold the extra conditions into one "
                    f"row's terms — a term contributes nothing for a resident whose "
                    f"value is zero.")

    # --- 9. Cohorts: every one named, and every one actually overriding something ---
    ctab = tables.get("cohorts")
    if ctab is not None:
        named = {text(r.get("cohort_id")) for r in ctab} - {None}
        used: dict[str, int] = {}
        ptab = tables["population"]
        for i, r in enumerate(ptab):
            c = text(r.get("cohort"))
            if not c:
                continue
            used.setdefault(c, i)
            if c not in named:
                add(ptab.where(i, "cohort"),
                    f"no cohort {c!r} on the Cohorts tab"
                    f"{_suggest(c, named) if named else ''}")
        for i, r in enumerate(ctab):
            cid = text(r.get("cohort_id"))
            if cid and cid not in used:
                add(ctab.where(i, "cohort_id"),
                    f"cohort {cid!r} overrides nothing: no Population row names it in "
                    f"its `cohort` column, so building it would be the base building "
                    f"under another name")
            try:
                as_bool(r.get("include_cases"))
            except ValueError:
                add(ctab.where(i, "include_cases"),
                    f"include_cases: {r.get('include_cases')!r} is not a yes/no value")

    return out


def _may_overlap(a, b) -> bool:
    """Whether two predicates could both match one persona.

    Conservative: only returns False when a pair of clauses on the same attribute is
    provably disjoint. Anything subtler is reported and left to a human.
    """
    for ca in a.clauses:
        for cb in b.clauses:
            if ca.attr != cb.attr:
                continue
            if _disjoint(ca, cb) or _disjoint(cb, ca):
                return False
    return True


def _disjoint(x, y) -> bool:
    if x.op == "==" and y.op == "==":
        return x.value != y.value
    if x.op == "==" and y.op == "in":
        return x.value not in y.value
    if x.op == "==" and y.op == "not in":
        return x.value in y.value
    if x.op == "in" and y.op == "in":
        return not (set(map(str, x.value)) & set(map(str, y.value)))
    try:
        if x.op in ("<", "<=") and y.op in (">", ">="):
            return float(x.value) <= float(y.value)
        if x.op in (">", ">=") and y.op in ("<", "<="):
            return float(x.value) >= float(y.value)
    except (TypeError, ValueError):
        return False
    return False
