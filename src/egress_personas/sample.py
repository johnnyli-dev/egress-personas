"""Drawing a whole population: the thirteen phases, in order.

Two invariants hold throughout:

* a persona pinned by a Cases row is never deleted and never demographically
  altered;
* a repair only ever adjusts the sampled remainder.

Where a target cannot be met — because the hand-authored cases alone already break
it — the drift is reported, loudly, and nothing is quietly moved.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from . import households as hh
from . import ties as tie_mod
from .narrative import render
from .parameters import Trace, apply_rules, load_rules
from .persona import FIELDS, Persona
from .rng import draw_rng
from .tables import Tables, as_bool, as_float, as_int, as_list, text
from .validate import CASE_FIELD

VERSION = "0.1.0"


@dataclass
class Household:
    id: str
    unit: str
    floor_label: int
    sim_floor: int
    members: list[str] = field(default_factory=list)
    member_indices: list[int] = field(default_factory=list)
    first_index: int | None = None
    has_pet: bool = False
    pinned: bool = False
    notes: str = ""


@dataclass
class Population:
    scenario: dict[str, Any]
    units: list[dict[str, Any]]
    households: list[Household]
    people: list[Persona]
    groups: list[dict[str, Any]]
    traces: dict[str, dict[str, Trace]]
    targets: hh.Targets
    theta: float = 1.0
    tilted: list[float] = field(default_factory=list)
    tie_stats: list[dict[str, Any]] = field(default_factory=list)
    repairs: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    conformance: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    inapplicable: list[str] = field(default_factory=list)
    snapshot: dict[str, Any] = field(default_factory=dict)
    seed: int = 0
    run_id: str = ""
    matched: dict[str, int] = field(default_factory=dict)
    missing_attrs: set[str] = field(default_factory=set)


def _clause_holds(clause: Any, view: dict[str, Any]) -> bool:
    """Whether one applies_to clause holds for a scenario-level attribute."""
    from .filters import matches
    from .filters import Predicate
    return matches(Predicate((clause,)), view)


def scenario_of(tables: Tables, scenario_id: str) -> dict[str, Any]:
    for row in tables["scenarios"]:
        if text(row.get("scenario_id")) == scenario_id:
            return dict(row)
    known = [text(r.get("scenario_id")) for r in tables["scenarios"]]
    raise KeyError(f"no scenario {scenario_id!r}; the Scenarios tab has {known}")


def _attrs(p: Persona, household: Household, size: int, has_children: bool,
           scenario: dict[str, Any], fire_floor: int | None) -> dict[str, Any]:
    """The attribute view `applies_to` reads. Sampler-owned values only."""
    floor = p.situation.get("floor_label")
    return {
        "age_years": p.identity.get("age_years"),
        "age_band": p.identity.get("age_band"),
        "sex": p.identity.get("sex"),
        "sim_agent_type": p.body.get("sim_agent_type"),
        "mobility": p.body.get("mobility"),
        "household_role": p.identity.get("household_role"),
        "household_size": size,
        "tenure_years": p.identity.get("tenure_years"),
        "present": p.situation.get("present"),
        "asleep": p.situation.get("asleep"),
        "has_pet": household.has_pet,
        "has_children": has_children,
        "lives_alone": size == 1,
        "unit": p.situation.get("unit"),
        "unit_letter": (p.situation.get("unit") or " ")[-1],
        "floor_label": floor,
        "sim_floor": p.situation.get("sim_floor"),
        "on_fire_floor": fire_floor is not None and floor == fire_floor,
        "above_fire": fire_floor is not None and floor is not None and floor > fire_floor,
        "time_of_day": text(scenario.get("time_of_day")),
        "alarm_quality": text(scenario.get("alarm_quality")),
    }


def sample(tables: Tables, scenario_id: str, seed: int | None = None) -> Population:  # noqa: C901
    scenario = scenario_of(tables, scenario_id)
    if seed is None:
        seed = as_int(scenario.get("default_seed")) or 0
    plan = text(scenario.get("plan_id"))
    fire_floor = as_int(scenario.get("fire_floor_label"))
    absent_share = as_float(scenario.get("absent_share"))
    asleep_share = as_float(scenario.get("asleep_share"))
    out_of_flat = as_float(scenario.get("out_of_flat_share")) or 0.0
    targets = hh.read_targets(tables)
    if absent_share is None:
        absent_share = targets.absence_share

    warnings: list[str] = []

    # --- 1. units ------------------------------------------------------------
    units: list[dict[str, Any]] = []
    for row in tables["building"]:
        if text(row.get("plan_id")) != plan or as_bool(row.get("occupiable")) is False:
            continue
        units.append({
            "label": text(row.get("unit_label")),
            "floor_label": as_int(row.get("floor_label")),
            "letter": text(row.get("unit_letter")),
            "sim_floor": as_int(row.get("sim_floor")),
            "seed_tile": [as_int(row.get("seed_tile_x")), as_int(row.get("seed_tile_y"))],
            "state": "vacant",
            "household": None,
        })
    units.sort(key=lambda u: (u["sim_floor"], u["letter"]))
    by_label = {u["label"]: u for u in units}
    if not units:
        raise ValueError(f"the Building tab has no occupiable units for plan {plan!r}")

    people: list[Persona] = []
    homes: dict[str, Household] = {}

    def household_for(unit_label: str, hid: str | None, pinned: bool) -> Household:
        u = by_label[unit_label]
        key = hid or f"HH-{unit_label}"
        if key not in homes:
            homes[key] = Household(id=key, unit=unit_label,
                                   floor_label=u["floor_label"],
                                   sim_floor=u["sim_floor"], pinned=pinned)
            u["state"] = "occupied"
            u["household"] = key
        return homes[key]

    # --- 2. the hand-authored cases ------------------------------------------
    for row in tables["cases"]:
        unit = text(row.get("unit"))
        cid = text(row.get("case_id")) or "?"
        if unit not in by_label:
            warnings.append(f"case {cid}: unit {unit!r} is not in this plan; skipped")
            continue
        house = household_for(unit, text(row.get("household_id")), pinned=True)
        u = by_label[unit]
        p = Persona(key=f"case:{cid}", case_id=cid)
        age = as_int(row.get("age_years"))
        mobility = text(row.get("mobility"))
        p.identity.update({
            "name": text(row.get("name")),
            "age_years": age,
            "sex": text(row.get("sex")),
            "household_role": text(row.get("household_role")) or "head",
            "tenure_years": as_float(row.get("tenure_years")),
        })
        if age is not None:
            p.identity["age_band"] = hh.band_of(age)
        if mobility:
            p.body["mobility"] = mobility
        p.situation.update({
            "unit": unit, "floor_label": u["floor_label"], "sim_floor": u["sim_floor"],
            "present": as_bool(row.get("present")),
            "asleep": as_bool(row.get("asleep")),
            "activity": text(row.get("activity")),
        })
        p.household = house.id
        house.members.append(p.key)
        if as_bool(row.get("has_pet")):
            house.has_pet = True
        for part in as_list(row.get("commitments")):
            bits = part.split(":")
            if len(bits) == 3:
                p.commitments.append({
                    "kind": bits[0], "what": bits[1], "where": "unit",
                    "delay_s": as_float(bits[2]), "abandon_probability": None,
                })
        # Pinned fields: whatever the case actually filled in.
        for col, path in CASE_FIELD.items():
            raw = text(row.get(col))
            if raw is None:
                continue
            spec = FIELDS[path]
            value: Any
            if spec.dtype == "bool":
                value = as_bool(raw)
            elif spec.dtype == "int":
                value = as_int(raw)
            elif spec.dtype == "float":
                value = as_float(raw)
            else:
                value = raw
            p.set(path, value)
            p.pinned.add(path)
        p.narrative = text(row.get("narrative_override")) or ""
        p.identity["notes"] = text(row.get("notes")) or ""
        people.append(p)

    # Cases may leave demographics blank too; fill those now so every persona is whole.
    for p in people:
        if p.identity.get("age_years") is None:
            age, band = hh.draw_age(p.key, seed, targets, adult_only=True)
            p.identity["age_years"], p.identity["age_band"] = age, band
        if not p.identity.get("sex"):
            p.identity["sex"] = hh.draw_sex(p.key, seed, targets)
        if not p.body.get("mobility"):
            p.body["mobility"] = hh.draw_mobility(
                p.key, seed, p.identity["age_years"], targets)
        if p.identity.get("tenure_years") is None:
            p.identity["tenure_years"] = hh.draw_tenure(
                p.key, seed, p.identity["age_years"], targets)

    pinned_people = len(people)

    # --- 3. occupancy budget -------------------------------------------------
    total_target = round(targets.persons_per_flat * len(units))
    remaining = total_target - pinned_people
    if remaining < 0:
        warnings.append(
            f"the {pinned_people} hand-authored cases already exceed the occupancy "
            f"target of {total_target} ({targets.persons_per_flat} per flat x "
            f"{len(units)} flats). Every case is kept; no flat beyond them is filled."
        )
        remaining = 0

    # --- 4. household sizes, tilted to the occupancy target ------------------
    tilted, theta = hh.tilt(list(targets.size_weights), targets.persons_per_flat)

    # --- 5 & 6. fill the vacant flats ---------------------------------------
    for u in units:
        if remaining <= 0:
            break
        if u["state"] == "occupied":
            continue
        label = u["label"]
        size = draw_rng(seed, f"unit/{label}/occupancy").weighted(tilted) + 1
        size = min(size, remaining)
        house = household_for(label, None, pinned=False)
        head_age = 40
        for slot in range(size):
            key = f"synth:{label}:{slot}"
            adult_only = slot == 0
            age, band = hh.draw_age(key, seed, targets, adult_only=adult_only,
                                    child_bias=0.8 if slot >= 2 else 0.0)
            if slot == 0:
                head_age = age
            mobility = hh.draw_mobility(key, seed, age, targets)
            p = Persona(key=key)
            p.identity.update({
                "age_years": age, "age_band": band,
                "sex": hh.draw_sex(key, seed, targets),
                "household_role": hh.role_for(slot, age, head_age),
                "tenure_years": hh.draw_tenure(key, seed, age, targets),
            })
            p.body["mobility"] = mobility
            p.situation.update({
                "unit": label, "floor_label": u["floor_label"],
                "sim_floor": u["sim_floor"],
            })
            p.household = house.id
            house.members.append(p.key)
            people.append(p)
            remaining -= 1
        if draw_rng(seed, f"unit/{label}/pet").chance(targets.pet_share):
            house.has_pet = True

    notes: list[str] = []
    if remaining > 0:
        notes.append(
            f"{remaining} of the {total_target} residents in the occupancy target were "
            f"not placed: every flat already holds a household, and filling one further "
            f"would distort the household-size distribution more than it would improve "
            f"the occupancy figure. Check the occupancy row of the report."
        )

    # --- 7. children never alone --------------------------------------------
    for house in homes.values():
        members = [p for p in people if p.household == house.id]
        if not members:
            continue
        if any(p.identity["age_years"] < 18 for p in members) and not any(
                p.identity["age_years"] >= 18 for p in members):
            fixable = [p for p in members if not p.pinned]
            if not fixable:
                warnings.append(
                    f"{house.id} holds only children and every member is a pinned "
                    f"case, so it is left as authored"
                )
                continue
            p = fixable[-1]
            for attempt in range(8):
                age, band = hh.draw_age(f"{p.key}#repair/{attempt}", seed, targets,
                                        adult_only=True)
                if age >= 18:
                    p.identity["age_years"], p.identity["age_band"] = age, band
                    p.identity["household_role"] = "head" if len(members) == 1 else "parent"
                    p.body["mobility"] = hh.draw_mobility(
                        f"{p.key}#repair/{attempt}", seed, age, targets)
                    break

    # --- 8. presence and what they are doing --------------------------------
    for p in people:
        if p.situation.get("present") is None:
            p.situation["present"] = not draw_rng(
                seed, f"persona/{p.key}/present").chance(absent_share)
        if p.situation.get("asleep") is None:
            p.situation["asleep"] = (
                bool(p.situation["present"])
                and draw_rng(seed, f"persona/{p.key}/asleep").chance(asleep_share or 0.0)
            )
        if not p.situation.get("activity"):
            if not p.situation["present"]:
                p.situation["activity"] = "out_of_flat"
            elif p.situation["asleep"]:
                p.situation["activity"] = "asleep"
            elif draw_rng(seed, f"persona/{p.key}/activity").chance(out_of_flat):
                p.situation["activity"] = "out_of_flat"
            else:
                p.situation["activity"] = "awake_home"

    for house in homes.values():
        if all(not p.situation["present"] for p in people if p.household == house.id):
            u = by_label[house.unit]
            u["state"] = "all_absent"

    repairs: list[dict[str, Any]] = []

    # --- 9. share repairs ----------------------------------------------------
    def mob_repair(name: str, value: str, target: float, tol: float, pool) -> None:
        moves = hh.repair_share(
            people, seed, name=name,
            is_member=lambda p: p.body.get("mobility") == value,
            make_member=lambda p: (p.body.get("mobility"),
                                   p.body.__setitem__("mobility", value))[0],
            unmake_member=lambda p: (p.body.get("mobility"),
                                     p.body.__setitem__("mobility", "none"))[0],
            candidates=pool, target=target, tolerance=tol,
        )
        repairs.extend({"repair": name, **m} for m in moves)

    repairs.extend(
        {"repair": "age_band", **m}
        for m in hh.repair_child_share(people, seed, targets, household_of=homes)
    )

    repairs.extend(
        {"repair": "tenure", **m}
        for m in hh.repair_tenure_share(people, seed, targets)
    )

    mob_repair("wheelchair", "wheelchair", targets.wheelchair_share,
               targets.tolerance.get("mobility.wheelchair", 0.008),
               lambda ps: [p for p in ps if p.identity["age_years"] >= 18])

    for p in people:
        p.body["sim_agent_type"] = hh.sim_agent_type(
            p.identity["age_years"], p.body["mobility"])
        p.body["can_use_stairs"] = p.body["mobility"] != "wheelchair"
        p.body["limiting_condition"] = p.body["mobility"] in (
            "ambulatory_difficulty", "walker_cane")

    # --- 10. caregiver pairing ----------------------------------------------
    gaps: list[dict[str, Any]] = []
    unpaired: list[str] = []
    for p in people:
        if p.body["mobility"] != "wheelchair" or not p.situation["present"]:
            continue
        mates = [
            q for q in people
            if q.household == p.household and q is not p
            and q.identity["age_years"] >= 18 and q.situation["present"]
            and q.body["mobility"] != "wheelchair"
        ]
        helper = next((q for q in mates if q.identity.get("household_role") == "carer"),
                      mates[0] if mates else None)
        if helper is None:
            unpaired.append(p.key)
            continue
        helper.body["sim_agent_type"] = "caregiver"
        helper.body["escorts"] = p.key
        p.body["escorted_by"] = helper.key
    if unpaired:
        gaps.append({
            "what": "a wheelchair user with nobody in the flat who could help",
            "count": len(unpaired), "who": unpaired,
            "why": "The simulation looks for a caregiver on the same floor and a "
                   "one-person household has none, so these occupants depend entirely "
                   "on the lift or on the fire service. Inventing a carer would hide "
                   "the finding.",
        })

    # --- 11. order, households contiguous ------------------------------------
    order = {u["label"]: i for i, u in enumerate(units)}
    role_rank = {"head": 0, "partner": 1, "carer": 2, "parent": 3, "child": 4,
                 "lodger": 5, "other": 6}
    people.sort(key=lambda p: (
        order.get(p.situation["unit"], 0),
        p.household,
        role_rank.get(p.identity.get("household_role", "other"), 9),
        p.key,
    ))
    for i, p in enumerate(people):
        p.index = i
        p.id = f"P{i:04d}"
    house_list: list[Household] = []
    for house in homes.values():
        members = [p for p in people if p.household == house.id]
        if not members:
            continue
        house.members = [p.key for p in members]
        house.member_indices = [p.index for p in members]
        house.first_index = members[0].index
        for p in members:
            p.household_index = house.first_index if len(members) > 1 else None
        house_list.append(house)
    house_list.sort(key=lambda h: h.first_index or 0)

    # --- 12. home tiles ------------------------------------------------------
    for house in house_list:
        tile = by_label[house.unit]["seed_tile"]
        for n, p in enumerate([q for q in people if q.household == house.id]):
            p.situation["home_tile"] = [house.sim_floor, tile[0], tile[1]]
            p.situation["home_slot"] = n

    # --- 13. parameters, ties, narratives ------------------------------------
    rules = load_rules(tables)
    traces: dict[str, dict[str, Trace]] = {}
    matched: dict[str, int] = {}
    missing: set[str] = set()
    by_id = {h.id: h for h in house_list}
    for p in people:
        house = by_id[p.household]
        members = house.members
        kids = any(q.identity["age_years"] < 18 for q in people if q.household == house.id)
        if house.has_pet and not any(c["kind"] == "pet" for c in p.commitments):
            if p.identity.get("household_role") in ("head", "partner"):
                p.commitments.append({"kind": "pet", "what": "pet", "where": "unit",
                                      "delay_s": 45.0, "abandon_probability": 0.2})
        traces[p.key] = apply_rules(
            p, _attrs(p, house, len(members), kids, scenario, fire_floor),
            rules, seed, warnings=warnings, missing_attrs=missing, matched=matched,
        )

    tie_rules = tie_mod.load_tie_rules(tables)
    groups, tie_stats = tie_mod.build(people, tie_rules, seed)

    for p in people:
        if not p.narrative:
            p.narrative = render(p, by_id[p.household], people)

    scenario_attrs = {"time_of_day", "alarm_quality"}
    scenario_view = {"time_of_day": text(scenario.get("time_of_day")),
                     "alarm_quality": text(scenario.get("alarm_quality"))}
    inapplicable: list[str] = []
    for rule in rules:
        if matched.get(rule.id, 0) != 0:
            continue
        gated = [c for c in rule.pred.clauses if c.attr in scenario_attrs]
        if gated and not all(_clause_holds(c, scenario_view) for c in gated):
            inapplicable.append(
                f"{rule.id} ({rule.name}) does not apply to this scenario: "
                f"{' and '.join(str(c) for c in gated)}"
            )
            continue
        warnings.append(
            f"{rule.id} ({rule.name}) matched no persona — its applies_to is "
            f"almost certainly wrong: {rule.pred}"
        )
    for attr in sorted(missing):
        warnings.append(
            f"some personas have no {attr!r}, so every condition on it was false"
        )

    # One warning per distinct message: an authoring mistake is one mistake, even when
    # it shows up on two hundred personas.
    warnings[:] = list(dict.fromkeys(warnings))

    pop = Population(
        scenario=scenario, units=units, households=house_list, people=people,
        groups=groups, traces=traces, targets=targets, theta=theta, tilted=tilted,
        tie_stats=tie_stats, repairs=repairs, warnings=warnings, gaps=gaps,
        snapshot=tables.snapshot, seed=seed, matched=matched, missing_attrs=missing,
        notes=notes, inapplicable=inapplicable,
    )
    pop.conformance = conformance(pop)
    pop.run_id = "blake2b128:" + hashlib.blake2b(
        "|".join([VERSION, tables.snapshot.get("content_hash", ""),
                  scenario_id, str(seed)]).encode(), digest_size=16).hexdigest()
    return pop


def conformance(pop: Population) -> list[dict[str, Any]]:
    """Realized shares against the Population targets."""
    people = pop.people
    n = len(people) or 1
    t = pop.targets
    out: list[dict[str, Any]] = []

    def row(tid: str, dim: str, cat: str, target: float, realized: float,
            unit: str = "share", base: int | None = None) -> None:
        """One target against what was drawn, with its sampling noise.

        `base` is how many people the share was measured over. A share measured on
        twenty-five occupants moves four percentage points when one person changes, so
        a miss on such a row usually says the building is small, not that the sampler
        is biased. Separating the two is the difference between a report you act on and
        one you learn to ignore.
        """
        tol = t.tolerance.get(f"{dim}.{cat}")
        n_base = base if base is not None else len(people)
        stderr = None
        z = None
        if unit == "share" and n_base > 0 and 0.0 < target < 1.0:
            stderr = (target * (1.0 - target) / n_base) ** 0.5
            if stderr > 0:
                z = (realized - target) / stderr
        out.append({
            "id": tid, "dimension": dim, "category": cat, "unit": unit,
            "target": round(target, 4), "realized": round(realized, 4),
            "tolerance": tol,
            "measured_over": n_base,
            "stderr": None if stderr is None else round(stderr, 4),
            "z": None if z is None else round(z, 2),
            "within": None if tol is None else abs(realized - target) <= tol,
            # Three standard errors, not two. A report carries a few dozen of these
            # rows and a run carries many reports, so a 2-sigma line would flag one or
            # two every single time and the reader would learn to skip the section.
            # Beyond 3 sigma, something is actually wrong.
            "noise": None if z is None else abs(z) <= 3.0,
        })

    occupiable = [u for u in pop.units]
    row("occupancy", "occupancy", "persons_per_flat", t.persons_per_flat,
        len(people) / max(len(occupiable), 1), "persons")

    for band in hh.AGE_BANDS:
        if band in t.age_weights:
            share = sum(1 for p in people if p.identity["age_band"] == band) / n
            row(f"age.{band}", "age_band", band, t.age_weights[band], share)
    for sex in ("female", "male", "other"):
        if sex in t.sex_weights:
            share = sum(1 for p in people if p.identity["sex"] == sex) / n
            row(f"sex.{sex}", "sex", sex, t.sex_weights[sex], share)
    row("mobility.wheelchair", "mobility", "wheelchair", t.wheelchair_share,
        sum(1 for p in people if p.body["mobility"] == "wheelchair") / n)
    for key, target in sorted(t.ambulatory_share.items()):
        if key == "65_plus":
            pool = [p for p in people if p.identity["age_years"] >= 65]
        elif key == "18_64":
            pool = [p for p in people if 18 <= p.identity["age_years"] < 65]
        else:
            pool = [p for p in people if p.identity["age_years"] < 18]
        share = (sum(1 for p in pool if p.body["mobility"] in
                     ("ambulatory_difficulty", "walker_cane")) / len(pool)) if pool else 0.0
        row(f"mobility.amb@{key}", "mobility", f"ambulatory_difficulty@{key}",
            target, share, base=len(pool))
    # The scenario's own absent share wins where it sets one: a weekday afternoon
    # empties a tower that a 3 a.m. fire does not, and the Population tab's figure is
    # only the fallback.
    absent_target = as_float(pop.scenario.get("absent_share"))
    if absent_target is None:
        absent_target = t.absence_share
    row("absence.share", "absence", "share", absent_target,
        sum(1 for p in people if not p.situation["present"]) / n)
    row("pet.share", "pet", "share", t.pet_share,
        sum(1 for h in pop.households if h.has_pet) / max(len(pop.households), 1),
        base=len(pop.households))
    for band, (lo, hi) in hh.TENURE_BANDS.items():
        if band in t.tenure_weights:
            share = sum(1 for p in people
                        if lo <= (p.identity["tenure_years"] or 0) < hi) / n
            row(f"tenure.{band}", "tenure", band, t.tenure_weights[band], share)
    sizes = [len(h.members) for h in pop.households]
    for k in (1, 2, 3, 4):
        want = pop.tilted[k - 1] if len(pop.tilted) >= k else 0.0
        got = (sum(1 for s in sizes if (s >= 4 if k == 4 else s == k))
               / max(len(sizes), 1))
        row(f"household_size.{k}", "household_size",
            "4plus" if k == 4 else str(k), want, got, base=len(sizes))
    return out
