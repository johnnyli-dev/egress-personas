"""Who lives where: targets, household formation, demographics, repairs.

The occupancy target is stated per flat because that is plan-independent; a
per-floor figure only means something once you fix how many flats a floor has. The
household-size weights then have to be reconciled with it, because census household
sizes and the people-per-flat figure for large buildings do not agree. That is done
with a single-parameter exponential tilt whose parameter is reported, rather than by
quietly editing either number.

Ages are drawn per member from the age-band targets subject to role constraints,
rather than roles being assigned from ages. It is the honest direction: the head of
a household is an adult by definition, but whether the third person in a flat is a
child or a lodger is something the age tells us.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .rng import draw_rng
from .tables import Tables, as_float, text

AGE_BANDS: dict[str, tuple[int, int]] = {
    "0_17": (0, 17),
    "18_34": (18, 34),
    "35_49": (35, 49),
    "50_64": (50, 64),
    "65_74": (65, 74),
    "75_plus": (75, 95),
}
ADULT_BANDS = tuple(b for b in AGE_BANDS if b != "0_17")

TENURE_BANDS: dict[str, tuple[float, float]] = {
    "lt_1": (0.0, 1.0),
    "1_5": (1.0, 5.0),
    "5_plus": (5.0, 30.0),
}

#: Of the occupants with a walking difficulty, the share who use an aid. An estimate:
#: the census tables count difficulty, not devices.
WALKER_SHARE = 0.33


@dataclass
class Targets:
    persons_per_flat: float = 1.66
    size_weights: list[float] = field(default_factory=lambda: [40.65, 32.67, 12.12, 14.57])
    age_weights: dict[str, float] = field(default_factory=dict)
    sex_weights: dict[str, float] = field(default_factory=dict)
    tenure_weights: dict[str, float] = field(default_factory=dict)
    wheelchair_share: float = 0.013
    ambulatory_share: dict[str, float] = field(default_factory=dict)
    absence_share: float = 0.06
    pet_share: float = 0.25
    tolerance: dict[str, float] = field(default_factory=dict)

    def ambulatory_for(self, age: int) -> float:
        if age >= 65:
            return self.ambulatory_share.get("65_plus", 0.182)
        if age >= 18:
            return self.ambulatory_share.get("18_64", 0.038)
        return self.ambulatory_share.get("0_17", 0.004)


def read_targets(tables: Tables) -> Targets:
    t = Targets(age_weights={}, sex_weights={}, tenure_weights={}, ambulatory_share={})
    sizes: dict[str, float] = {}
    for row in tables["population"]:
        dim = text(row.get("dimension"))
        cat = text(row.get("category")) or ""
        val = as_float(row.get("value"))
        tol = as_float(row.get("tolerance"))
        if val is None:
            continue
        key = f"{dim}.{cat}"
        if tol is not None:
            t.tolerance[key] = tol
        if dim == "occupancy":
            t.persons_per_flat = val
        elif dim == "household_size":
            sizes[cat] = val
        elif dim == "age_band":
            t.age_weights[cat] = val
        elif dim == "sex":
            t.sex_weights[cat] = val
        elif dim == "tenure":
            t.tenure_weights[cat] = val
        elif dim == "absence":
            t.absence_share = val
        elif dim == "pet":
            t.pet_share = val
        elif dim == "mobility":
            if cat == "wheelchair":
                t.wheelchair_share = val
            elif cat.startswith("ambulatory_difficulty@"):
                t.ambulatory_share[cat.split("@", 1)[1]] = val
    if sizes:
        t.size_weights = [sizes.get(k, 0.0) for k in ("1", "2", "3", "4plus")]
    return t


# --- reconciling household sizes with the per-flat occupancy target --------------

def tilt(weights: list[float], target_mean: float,
         tol: float = 1e-9, iters: int = 200) -> tuple[list[float], float]:
    """Reweight `weights` by theta**k so the mean household size hits `target_mean`.

    Monotone in theta, so bisection is enough, and it returns the input weights
    exactly when the means already agree. Returns (normalized weights, theta).
    """
    sizes = list(range(1, len(weights) + 1))

    def mean_at(theta: float) -> float:
        w = [wk * theta ** k for wk, k in zip(weights, sizes)]
        total = sum(w)
        return sum(wk * k for wk, k in zip(w, sizes)) / total if total else 0.0

    target_mean = min(max(target_mean, sizes[0] + 1e-9), sizes[-1] - 1e-9)
    if abs(mean_at(1.0) - target_mean) < 1e-6:
        total = sum(weights)
        return [w / total for w in weights], 1.0

    lo, hi = 1e-6, 1e6
    if mean_at(lo) > target_mean or mean_at(hi) < target_mean:
        total = sum(weights)
        return [w / total for w in weights], 1.0
    for _ in range(iters):
        mid = (lo * hi) ** 0.5  # geometric bisection: theta is a scale, not a position
        if mean_at(mid) < target_mean:
            lo = mid
        else:
            hi = mid
        if hi / lo - 1.0 < tol:
            break
    theta = (lo * hi) ** 0.5
    w = [wk * theta ** k for wk, k in zip(weights, sizes)]
    total = sum(w)
    return [x / total for x in w], theta


# --- drawing one person ----------------------------------------------------------

def draw_age(key: str, seed: int, targets: Targets, *, adult_only: bool,
             child_bias: float = 0.0) -> tuple[int, str]:
    """An age in years and its band. `child_bias` pushes a slot towards under-18."""
    bands = list(AGE_BANDS)
    weights = [targets.age_weights.get(b, 0.0) for b in bands]
    if adult_only:
        weights = [0.0 if b == "0_17" else w for b, w in zip(bands, weights)]
    elif child_bias:
        weights = [
            w * (1.0 + child_bias) if b == "0_17" else w
            for b, w in zip(bands, weights)
        ]
    if not any(weights):
        weights = [0.0 if (adult_only and b == "0_17") else 1.0 for b in bands]
    rng = draw_rng(seed, f"{key}/age_band")
    band = bands[rng.weighted(weights)]
    lo, hi = AGE_BANDS[band]
    return int(draw_rng(seed, f"{key}/age").range_f(lo, hi + 0.999)), band


def band_of(age: int) -> str:
    for band, (lo, hi) in AGE_BANDS.items():
        if lo <= age <= hi:
            return band
    return "75_plus"


def draw_sex(key: str, seed: int, targets: Targets) -> str:
    opts = ["female", "male", "other"]
    weights = [targets.sex_weights.get(o, 0.0) for o in opts]
    if not any(weights):
        weights = [1.0, 1.0, 0.0]
    return opts[draw_rng(seed, f"{key}/sex").weighted(weights)]


def draw_mobility(key: str, seed: int, age: int, targets: Targets) -> str:
    if draw_rng(seed, f"{key}/wheelchair").chance(targets.wheelchair_share):
        return "wheelchair"
    if draw_rng(seed, f"{key}/ambulatory").chance(targets.ambulatory_for(age)):
        if draw_rng(seed, f"{key}/walker").chance(WALKER_SHARE):
            return "walker_cane"
        return "ambulatory_difficulty"
    return "none"


def tenure_ceiling(age: int) -> float:
    """The longest this person could have lived here.

    An adult did not sign a lease as a child, so an adult's ceiling is the years since
    they turned 18 and a child's is their own age. Somebody who genuinely grew up in
    the building is a case to author by hand, not something to draw by accident.
    """
    return max(age - 18.0, 0.0) if age >= 18 else max(age - 0.5, 0.0)


def draw_tenure(key: str, seed: int, age: int, targets: Targets) -> float:
    """Years in the building, drawn only from the bands this person could reach.

    Drawing a band and then clamping it would pile everybody too young for a band onto
    its floor, and the long-tenure share would come out short every single time -
    a bias no tolerance would attribute to the right cause.
    """
    ceiling = tenure_ceiling(age)
    bands = list(TENURE_BANDS)
    weights = [targets.tenure_weights.get(b, 0.0) for b in bands]
    if not any(weights):
        weights = [1.0] * len(bands)
    feasible = [w if TENURE_BANDS[b][0] <= ceiling else 0.0
                for b, w in zip(bands, weights)]
    if not any(feasible):
        return round(min(ceiling, 0.5), 1)
    band = bands[draw_rng(seed, f"{key}/tenure_band").weighted(feasible)]
    lo, hi = TENURE_BANDS[band]
    years = draw_rng(seed, f"{key}/tenure").range_f(lo, min(hi, max(ceiling, lo)))
    return round(min(years, ceiling), 1)


def sim_agent_type(age: int, mobility: str) -> str:
    """The simulation's occupant class, derived rather than drawn.

    Order matters: a wheelchair user is a wheelchair user whatever their age,
    because that is the distinction the simulation acts on (it decides who cannot
    use the stairs at all).
    """
    if mobility == "wheelchair":
        return "wheelchair"
    if age < 18:
        return "child"
    if age >= 65:
        return "elderly"
    return "adult"


def role_for(slot: int, age: int, head_age: int) -> str:
    if slot == 0:
        return "head"
    if age < 18:
        return "child"
    if age >= head_age + 18:
        return "parent"
    if slot == 1:
        return "partner"
    return "lodger"


# --- repairs ---------------------------------------------------------------------

def repair_share(
    people: list[Any],
    seed: int,
    *,
    name: str,
    is_member,
    make_member,
    unmake_member,
    candidates,
    target: float,
    tolerance: float,
) -> list[dict[str, Any]]:
    """Nudge a realized share into tolerance, touching as few people as possible.

    Deterministic: candidates are ordered by a value drawn from their own substream,
    so the same snapshot and seed always move the same people. Pinned personas are
    never candidates. Every move is returned so the report can show it.
    """
    moves: list[dict[str, Any]] = []
    n = len(people)
    if n == 0:
        return moves
    have = sum(1 for p in people if is_member(p))
    want = target * n
    lo, hi = (target - tolerance) * n, (target + tolerance) * n

    def order(pool):
        return sorted(pool, key=lambda p: draw_rng(seed, f"repair/{name}/{p.key}").unit())

    if have < lo:
        pool = order([p for p in candidates(people) if not is_member(p) and not p.pinned])
        for p in pool:
            if have >= want:
                break
            before = make_member(p)
            moves.append({"who": p.key, "change": f"{name}: {before} -> in"})
            have += 1
    elif have > hi:
        pool = order([p for p in people if is_member(p) and not p.pinned])
        for p in pool:
            if have <= want:
                break
            before = unmake_member(p)
            moves.append({"who": p.key, "change": f"{name}: {before} -> out"})
            have -= 1
    return moves


def repair_child_share(
    people: list[Any],
    seed: int,
    targets: Targets,
    *,
    household_of,
) -> list[dict[str, Any]]:
    """Bring the under-18 share to its target by re-aging eligible members.

    A child needs an adult in the flat, so only a non-head member of a household that
    keeps at least one other adult is eligible. That is also why the target and the
    per-flat occupancy figure constrain each other: with a mean household size of m,
    no more than (m-1)/m of the building can be under 18 however the ages are drawn.

    Deterministic, minimal, and never touches a pinned case.
    """
    target = targets.age_weights.get("0_17")
    if not target:
        return []
    tol = targets.tolerance.get("age_band.0_17", 0.04)
    n = len(people)
    if n == 0:
        return []
    moves: list[dict[str, Any]] = []

    def adults_in(house_id: str) -> int:
        return sum(1 for q in people
                   if q.household == house_id and q.identity["age_years"] >= 18)

    def redraw(p: Any, adult_only: bool, tag: str) -> int:
        key = f"{p.key}#agerepair/{tag}"
        age, band = draw_age(key, seed, targets, adult_only=adult_only,
                             child_bias=0.0 if adult_only else 6.0)
        if adult_only and age < 18:
            age, band = 30, "18_34"
        if not adult_only and age >= 18:
            age, band = 9, "0_17"
        p.identity["age_years"], p.identity["age_band"] = age, band
        p.body["mobility"] = draw_mobility(key, seed, age, targets)
        p.identity["tenure_years"] = draw_tenure(key, seed, age, targets)
        return age

    have = sum(1 for p in people if p.identity["age_years"] < 18)
    want = target * n
    lo, hi = (target - tol) * n, (target + tol) * n

    def ordered(pool):
        return sorted(pool, key=lambda p: draw_rng(
            seed, f"repair/age_band/{p.key}").unit())

    if have < lo:
        pool = ordered([
            p for p in people
            if not p.pinned and p.identity["age_years"] >= 18
            and p.identity.get("household_role") != "head"
            and adults_in(p.household) >= 2
        ])
        for p in pool:
            if have >= want:
                break
            before = p.identity["age_years"]
            age = redraw(p, adult_only=False, tag="to_child")
            p.identity["household_role"] = "child"
            moves.append({"who": p.key,
                          "change": f"age_band: {before} -> {age} (to reach the "
                                    f"under-18 share)"})
            have += 1
    elif have > hi:
        pool = ordered([p for p in people
                        if not p.pinned and p.identity["age_years"] < 18])
        for p in pool:
            if have <= want:
                break
            before = p.identity["age_years"]
            age = redraw(p, adult_only=True, tag="to_adult")
            p.identity["household_role"] = "lodger"
            moves.append({"who": p.key,
                          "change": f"age_band: {before} -> {age} (to reach the "
                                    f"under-18 share)"})
            have -= 1

    if have < lo:
        mean = len(people) / max(len({p.household for p in people}), 1)
        ceiling = (mean - 1.0) / mean if mean > 0 else 0.0
        moves.append({
            "who": "-",
            "change": f"could not reach the under-18 share of {target:.0%}: only "
                      f"{have / n:.1%} of residents are under 18. With a mean household "
                      f"size of {mean:.2f} the arithmetic ceiling is {ceiling:.0%}, "
                      f"because a child needs an adult in the flat. Either the age "
                      f"target or the occupancy target has to move.",
        })
    del household_of
    return moves


def repair_tenure_share(people: list[Any], seed: int, targets: Targets) -> list[dict]:
    """Bring each tenure band's share to its target, within what ages allow.

    Tenure and age constrain each other: somebody of 22 cannot have lived here five
    years, so if a fifth of the building is too young to reach a band, drawing that
    band independently per person can never hit its marginal share. Rather than leave
    a silent shortfall, move the minimum number of people who *can* reach the band,
    deterministically, and say when feasibility still binds.
    """
    moves: list[dict[str, Any]] = []
    n = len(people)
    if not n or not targets.tenure_weights:
        return moves

    def band_of_tenure(years: float) -> str:
        for band, (lo, hi) in TENURE_BANDS.items():
            if lo <= years < hi:
                return band
        return "5_plus"

    def place(p: Any, band: str, tag: str) -> float:
        lo, hi = TENURE_BANDS[band]
        ceiling = tenure_ceiling(p.identity["age_years"])
        years = draw_rng(seed, f"{p.key}#tenurerepair/{tag}").range_f(
            lo, min(hi, max(ceiling, lo)))
        years = round(min(years, max(ceiling, lo)), 1)
        p.identity["tenure_years"] = years
        return years

    # Longest band first: it is the binding one, and it is what drives how much of the
    # building a resident knows.
    for band in sorted(TENURE_BANDS, key=lambda b: -TENURE_BANDS[b][0]):
        target = targets.tenure_weights.get(band)
        if not target:
            continue
        tol = targets.tolerance.get(f"tenure.{band}", 0.06)
        lo_bound = TENURE_BANDS[band][0]
        have = sum(1 for p in people
                   if band_of_tenure(p.identity["tenure_years"] or 0.0) == band)
        want = target * n
        # Aim at the target, not at the edge of its tolerance. A shortfall that always
        # sits just inside tolerance is still a bias, and it would quietly skew every
        # familiarity figure downstream.
        if have >= want:
            continue
        pool = sorted(
            (p for p in people
             if not p.pinned
             and band_of_tenure(p.identity["tenure_years"] or 0.0) != band
             and tenure_ceiling(p.identity["age_years"]) >= lo_bound),
            key=lambda p: draw_rng(seed, f"repair/tenure/{band}/{p.key}").unit(),
        )
        for p in pool:
            if have >= want:
                break
            before = p.identity["tenure_years"]
            after = place(p, band, band)
            moves.append({"who": p.key,
                          "change": f"tenure: {before}y -> {after}y (to reach the "
                                    f"{band} share)"})
            have += 1
        if have < (target - tol) * n:
            eligible = sum(1 for p in people
                           if tenure_ceiling(p.identity["age_years"]) >= lo_bound)
            moves.append({
                "who": "-",
                "change": f"could not reach the tenure {band} share of {target:.0%}: "
                          f"only {eligible} of {n} residents are old enough to have "
                          f"lived here {lo_bound:g} years, so the ceiling is "
                          f"{eligible / n:.0%}. Either the tenure target or the age "
                          f"distribution has to move.",
            })
    return moves
