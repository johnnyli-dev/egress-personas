# What the population JSON owes the simulation

Cross-repo notes. **Nothing in `FireEgress-3dsim` is read at runtime or modified by this
project**; these are citations, so that the reasons behind the JSON's shape stay
traceable when somebody later writes the loader.

Paths are relative to `../FireEgress-3dsim/`. Line numbers were correct at
2026-09-26; treat them as pointers, not addresses.

## The slot this fills

`docs/ROADMAP.md`, item 3.2, **Agent list input**:

> The notebook's agent JSON (`class`, `group_id`, `floor`, `room`) and room letters;
> rooms need to be defined in the building JSON rather than hard-coded.

`docs/DIFFERENCES.md` lists the same thing under "not ported yet" as *"Agent list from
JSON / spreadsheet, room letters A-D"*, with a warning not to reproduce the notebook's
silent failures. There is no stub module for it; `crates/fe-core/src/population.rs`
says so in its own module docstring.

## Invariants the JSON already satisfies

| invariant | why | where it comes from |
|---|---|---|
| `personas` array order **is** spawn order | the loader appends in order | `crates/fe-core/src/population.rs:14` `spawn()` |
| a household is a **contiguous run** of indices | `refresh_household_pace` walks members by position | `crates/fe-core/src/sim.rs:390-396` |
| `household_index` = the index of the household's **first member**, `null` for somebody living alone | that is exactly what `Agent::household` holds | `population.rs:78`, `crates/fe-core/src/agent.rs:270` |
| escort links are **symmetric indices**, one wheelchair user to one caregiver | `Agent::partner` is a `Vec` index, set both ways | `agent.rs:341`, `population.rs:126-150` |
| `home_tile` is `[sim_floor, x, y]` | matches `Agent::home: [u16; 3]` | `agent.rs:306`, `population.rs:267` |
| `sim.agent_type` and `sim.gender` use **lowercase** spellings | `#[serde(rename_all = "lowercase")]` | `agent.rs:13`, `agent.rs:53` |
| `0 < sim_floor < num_floors` | the ground floor is never populated | `population.rs:47` |
| every `body` field is **optional** | so `Rules::sf_realistic()` stays authoritative for anything the Sheet does not set | `crates/fe-core/src/rules.rs:104` |

A loader is therefore a `#[serde(default, deny_unknown_fields)]` struct of
`Option<f32>` whose field names match `body`, plus the four keys it needs from
`situation` and `sim`. If it wants `deny_unknown_fields` at the persona level — which
would match the rest of that repo — it must also declare `knowledge`, `dispositions`,
`ties`, `narrative`, `notes`, `key` and `case_id` as opaque. That is a three-line cost
and the right call.

## Two traps

**`--rules FILE` merges over the notebook set, not the sourced one.**
`Rules::resolve(Some(path))` sends any path to `Rules::load` → `from_toml`, which lays
the file over `Rules::default()` — the notebook's record, not `rules/sf_realistic.toml`
(`crates/fe-core/src/rules.rs:86-118`). So a bare `[profiles.*]` overlay would silently
revert every sourced value: the Weibull pre-movement, the census household weights, the
door model. Anything this project ever emits as rules TOML must be
`sf_realistic.toml` **verbatim plus an appended override block**. It does not emit one
today.

**There are no unit names, and the A/B/C/D letters are not a flat index.** Flats are
inferred from walls and doors and numbered row-major
(`crates/fe-core/src/areas.rs`, `AreaKind::Flat(u16)`). Running that repo's own
inspector over `buildings/plan2_drawing_v2_2.json` finds **twelve** compartments, of
which several are dead-end pockets the classifier would also number as flats. The four
letters exist only as SVG text in `analysis/inspect_floorplan.py:140`
(`D`→(2,2), `B`→(22,2), `C`→(2,15), `A`→(30,16)).

This is why the `Building` tab carries a **seed tile** per unit rather than a flat
index: four coordinates a human reads off the committed drawing, instead of a mapping
nobody has verified. Every `seed_tile` in the output is marked `estimate`, and the
report says why. A `flat_index` can be added later, when somebody checks it.

## Numbers in the team's first workbook that contradict the simulation

Recorded here so nobody re-enters them. These belong to the simulation's rules, which
are already sourced.

| workbook | simulation |
|---|---|
| floor height 3.2 m | `floor_height_m = 3.0` in every scenario |
| 1 tile = 0.80 m | 1 tile = 1 m (`buildings/README.md`; sub-metre tiles are roadmap B.4) |
| no floor 13 | floors are contiguous; the `Building` tab carries both `floor_label` and `sim_floor` so the translation is explicit |
| lift holds 8, cycles every 4 min | `[elevator]` in `rules/sf_realistic.toml`, capacity by car area |
| "assume no heart attacks" | `profiles.*.medical_events_per_hour` is modelled for every type |

Also not carried across, and why: `chances_per_500_ticks` (negative, undefined); the
`speed_sd` column (unit-ambiguous — 0.7 is implausible as an m/s standard deviation
beside a 1.25 m/s mean, against Bohannon's measured 0.24); the `Pre` and `Panick`
columns (constant across all 143 rows, so they carry no information).

## The existing evidence ledgers

`docs/sources/*.md` holds about 1,400 sourced rows in almost exactly the shape
`context.md` §6 proposes, with a `Maps to our parameter` column and an explicit
sourcing discipline. The Sheet here is authored fresh by choice, so they are not a
source — but they are the best available cross-check, and they are worth reading before
re-deriving a number. `docs/sources/B_behaviour.md` in particular covers pre-movement,
waking, actions before leaving, mobility impairment and social groups.
