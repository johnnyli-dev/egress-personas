"""Does the sampler actually hit the targets, across seeds and scenarios?

One seed landing inside tolerance proves very little; these run twenty and require
the aggregate to hold, which is the property the sensitivity analysis will depend on.
"""

from __future__ import annotations

import pytest

from egress_personas.households import AGE_BANDS, tilt
from egress_personas.sample import sample
from egress_personas.tables import load_dir

SEEDS = list(range(1, 21))


@pytest.fixture(scope="module")
def runs(data_dir):
    tables = load_dir(data_dir)
    return [sample(tables, "night_fire12", s) for s in SEEDS]


def test_every_target_lands_inside_tolerance_on_the_mean_over_seeds(runs):
    """A single seed may miss; the mean over twenty must not."""
    totals: dict[str, list] = {}
    for pop in runs:
        for c in pop.conformance:
            if c["tolerance"] is None:
                continue
            totals.setdefault(f"{c['dimension']}.{c['category']}",
                              []).append((c["target"], c["realized"], c["tolerance"]))
    assert totals
    bad = []
    for key, vals in sorted(totals.items()):
        target = vals[0][0]
        tol = vals[0][2]
        mean = sum(v[1] for v in vals) / len(vals)
        if abs(mean - target) > tol:
            bad.append(f"{key}: target {target} ±{tol}, mean over "
                       f"{len(vals)} seeds {mean:.4f}")
    assert not bad, "\n".join(bad)


def test_no_single_seed_misses_a_target_by_more_than_sampling_noise(runs):
    """A tolerance can be tighter than the building can resolve - a share measured over
    twenty-five people moves four points when one person changes. What must not happen
    is a miss that sampling noise cannot explain, because that is bias."""
    bad = [
        f"seed {pop.seed} {c['dimension']}.{c['category']}: target {c['target']}, "
        f"got {c['realized']}, z = {c['z']}"
        for pop in runs for c in pop.conformance
        if c["within"] is False and c.get("noise") is False
    ]
    assert not bad, "\n".join(bad)


def test_the_drawn_shares_are_unbiased_across_seeds(runs):
    """Averaged over seeds, every z should sit near zero. A consistent sign means the
    sampler is skewed, which no tolerance would reveal on its own."""
    import statistics
    zs: dict[str, list[float]] = {}
    for pop in runs:
        for c in pop.conformance:
            if c.get("z") is not None:
                zs.setdefault(f"{c['dimension']}.{c['category']}", []).append(c["z"])
    bad = []
    for key, vals in sorted(zs.items()):
        if len(vals) < 10:
            continue
        mean_z = statistics.fmean(vals)
        # The mean of n z-scores has s.d. 1/sqrt(n); 3 of those is a real skew.
        if abs(mean_z) > 3.0 / len(vals) ** 0.5:
            bad.append(f"{key}: mean z over {len(vals)} seeds = {mean_z:+.2f}")
    assert not bad, "\n".join(bad)


def test_no_household_is_children_only(runs):
    for pop in runs:
        for h in pop.households:
            ages = [p.identity["age_years"] for p in pop.people if p.household == h.id]
            if any(a < 18 for a in ages):
                assert any(a >= 18 for a in ages), (pop.seed, h.id, ages)


def test_every_household_lives_in_one_flat(runs):
    for pop in runs:
        for h in pop.households:
            units = {p.situation["unit"] for p in pop.people if p.household == h.id}
            assert units == {h.unit}, (pop.seed, h.id, units)


def test_household_sizes_stay_inside_the_weighted_range(runs):
    for pop in runs:
        for h in pop.households:
            assert 1 <= len(h.members) <= len(pop.tilted), (pop.seed, h.id)


def test_the_tilt_hits_the_occupancy_target_exactly():
    weights = [40.65, 32.67, 12.12, 14.57]
    for target in (1.2, 1.66, 1.99, 2.5, 3.2):
        w, theta = tilt(list(weights), target)
        mean = sum(x * (i + 1) for i, x in enumerate(w))
        assert abs(mean - target) < 1e-3, (target, mean, theta)
        assert abs(sum(w) - 1.0) < 1e-9


def test_the_tilt_is_a_no_op_when_the_means_already_agree():
    weights = [40.65, 32.67, 12.12, 14.57]
    mean = sum(w * (i + 1) for i, w in enumerate(weights)) / sum(weights)
    w, theta = tilt(list(weights), mean)
    assert abs(theta - 1.0) < 1e-3
    for a, b in zip(w, [x / sum(weights) for x in weights]):
        assert abs(a - b) < 1e-3


def test_nobody_has_lived_here_longer_than_they_have_been_an_adult(runs):
    for pop in runs:
        for p in pop.people:
            age = p.identity["age_years"]
            tenure = p.identity["tenure_years"] or 0
            ceiling = max(age - 18, 0) if age >= 18 else age
            assert tenure <= ceiling + 0.05, (pop.seed, p.key, age, tenure)


def test_age_bands_agree_with_the_ages(runs):
    for pop in runs:
        for p in pop.people:
            lo, hi = AGE_BANDS[p.identity["age_band"]]
            assert lo <= p.identity["age_years"] <= hi, (p.key, p.identity)


def test_derived_types_follow_age_and_mobility(runs):
    for pop in runs:
        for p in pop.people:
            age, mob = p.identity["age_years"], p.body["mobility"]
            t = p.body["sim_agent_type"]
            if mob == "wheelchair":
                assert t == "wheelchair"
            elif t == "caregiver":
                assert age >= 18  # promoted for a pairing
            elif age < 18:
                assert t == "child"
            elif age >= 65:
                assert t == "elderly"
            else:
                assert t == "adult"


def test_a_day_scenario_empties_the_building_and_wakes_it(data_dir):
    tables = load_dir(data_dir)
    night = sample(tables, "night_fire12", 1234)
    day = sample(tables, "day_fire12", 1234)
    asleep = lambda p: sum(1 for x in p.people if x.situation["asleep"]) / len(p.people)
    absent = lambda p: sum(1 for x in p.people if not x.situation["present"]) / len(p.people)
    assert asleep(night) > 0.8 and asleep(day) < 0.1
    assert absent(day) > absent(night) * 3


def test_the_poor_alarm_scenario_actually_silences_people(data_dir):
    tables = load_dir(data_dir)
    good = sample(tables, "night_fire12", 1234)
    poor = sample(tables, "night_poor_alarm", 1234)
    unheard = lambda p: sum(1 for x in p.people
                            if x.situation.get("alarm_audible") is False) / len(p.people)
    assert unheard(good) < 0.06
    assert 0.15 < unheard(poor) < 0.35, unheard(poor)


def test_hand_authored_cases_survive_every_seed(data_dir):
    tables = load_dir(data_dir)
    for seed in (1, 7, 1234, 99999):
        pop = sample(tables, "night_fire12", seed)
        cases = {p.case_id: p for p in pop.people if p.case_id}
        assert set(cases) == {f"C0{i}" for i in range(1, 9)}
        widow = cases["C01"]
        assert widow.identity["age_years"] == 79
        assert widow.body["mobility"] == "walker_cane"
        assert widow.knowledge["prior_false_alarms"] == 11
        assert widow.knowledge["floorplan_familiarity"] == 0.95
        toddler = cases["C05"]
        assert toddler.identity["age_years"] == 3
        assert toddler.situation["unit"] == "14A"
