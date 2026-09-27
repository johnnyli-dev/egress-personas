# The persona schema

One record per resident. Run `personas fields` for the authoritative list of writable
fields and readable attributes; this file says why the blocks are the blocks.

## Why six blocks

`context.md` §2 groups occupant behaviour into four patterns: pre-evacuation,
wayfinding, social interaction, and interaction with the building and the fire. A flat
row of statistics cannot express three of the four. The blocks exist so each has
somewhere to live, and so that a reader can tell at a glance which part of the model a
field belongs to.

```
identity      age_years, sex, household_role, tenure_years
body          base_speed, patience_s, stair_fatigue_rate, ... (simulation field names)
situation     unit, floor, home_tile, present, asleep, activity, alarm_audible
knowledge     floorplan_familiarity, habitual_stair, knows_second_stair,
              prior_false_alarms, fire_safety_training
dispositions  mill_tendency, seeks_confirmation, authority_compliance,
              altruism, risk_tolerance, leadership
commitments   [{kind, what, where, delay_s, abandon_probability}]
ties          [{to, kind, strength}]
narrative     a card rendered from all of the above
```

`identity` carries **age in years**, not a band. Every target in the literature is
conditioned on age — 18-34 at 27%, ambulatory difficulty at 3.8% for 35-64 against
18.2% for 65 and over — and a fused `adult` / `elderly` label throws the covariate away
and makes those targets uncheckable. The band is derived, never stored as the truth.

`body` uses the simulation's own field names so a loader needs no translation layer.
It also carries `mobility` as a four-way category — `none`, `ambulatory_difficulty`,
`walker_cane`, `wheelchair` — because the team's first workbook had one label,
"mobility impaired", covering two very different occupants. Its own table gave that
label a stair descent speed of 1.5 floors a minute, so those occupants *walk down
stairs*: that is a walking difficulty, which the census puts at 3.8% and 18.2% by age,
not a wheelchair, which is about 1.3%. `can_use_stairs` and `limiting_condition` are
derived from `mobility`, which is the distinction the simulation actually acts on.

## What is writable, and what is not

Two closed registries, and nothing appears in both:

- **`FIELDS`** — what a `Parameters` row may write.
- **`ATTRS`** — what a `Parameters` row may read in `applies_to`.

The separation is load-bearing. If a filter could read a field some row writes, the
filter's answer would depend on the order the rows happened to be applied in, and the
whole determinism story would collapse. So everything readable is owned by the sampler:
demographics, placement, presence, and the scenario's own settings.

## Absent means inherit

A `body` field left out of the JSON means *the simulation's own rules decide it*. This
is the most consequential decision in the schema. `rules/sf_realistic.toml` carries
values with citations behind them; this Sheet should override one only when it has
something better to say.

`body.delay_s` is the worked example. The sheet's pre-movement figures — 240 s awake,
420 s asleep — are midpoints from a review. The simulation fits a Weibull from
Lovreglio's residential clusters: scale 102.475 s shape 0.767 from 149 observations for
a good alarm, scale 724.617 s shape 0.978 from 78 for a poor one, and it picks between
them by time of day. Replacing a fitted, scenario-dependent distribution with a
constant would be a regression, so the `Parameters` row that would do it is **parked
and switched off** — present, so the value is on the record and arguable, but not
emitted.

## Ties

Four kinds. `household` is structural: everyone in a flat, at full strength. The other
three are drawn:

| kind | scope | stated as | evidence |
|---|---|---|---|
| `knock` | same floor, and adjacent floors | per pair | ESTIMATE — Proulx's 62% leaving in groups and NIST's 30-34% helping others bound it |
| `phone` | building | per person | ESTIMATE — calling loved ones is one of NIST's listed pre-evacuation actions |
| `group_chat` | building | per person | **INVENTED** — no literature at all; it comes from the team's own first-person walkthrough |

`phone` is stated as an average number of ties **per person**, not as a chance per
pair, and that matters: a per-pair rate silently means six phone contacts in a 27-floor
tower and one in a five-floor block, so it could not be carried between buildings. The
generator converts a stated degree into the per-pair probability that population
implies.

Tie formation scales with **tenure** (`tenure_ref_years`), because somebody who moved
in last month has not met their neighbours. This is what produces a resident who
genuinely knows nobody in the building — which is a case the project cares about, and
one a uniform graph cannot represent. Children are tied to their household and nothing
else (`min_age_years`): a three-year-old does not knock on doors or telephone anybody.

## The narrative card

Rendered from the blocks by template, with no model call, so the same snapshot and seed
give the same words. It is assembled from clauses that each read one or two fields, so
it can never assert something the persona does not carry.

The team's `notes` on a case — *why this persona exists* — stays **out** of the card.
The card says who the person is; mixing in the authoring commentary would feed the
team's own reasoning to a model as if it were biography.
