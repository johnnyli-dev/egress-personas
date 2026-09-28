# Egress personas

A **persona schema** and a **population sampler** for the URAP fire-egress project: it
turns a living Google Sheet of literature-backed parameters into a reproducible
population of residents for a 27-floor high-rise — households, social ties,
dispositions, commitments, and a text card per person.

The project's premise (see `../context.md`) is that occupants are *persona-conditioned
cognitive agents* that perceive, interpret, communicate and decide. Nothing in the
project previously said what a persona **was**. This does.

```bash
uv sync
uv run personas validate                              # check the snapshot in data/
uv run personas build --scenario night_fire12 --seed 1234
uv run personas show --filter isolated                # sample somebody and read them
uv run personas explore                               # a page for browsing the population
uv run personas compare                               # against the team's first roster
uv run pytest
```

## Looking at the people

The population JSON is a good contract and a poor thing to read, so there are two ways
to look at who the sampler actually produced.

`personas show` samples somebody and prints them: the card, the blocks the simulation
will act on, who they would reach for, and which paper each number came from.
`--list` counts the subsets worth sampling from — `isolated`, `lift`, `unheard`,
`committed`, `cases` — and `--filter` draws from one. Sampling is seeded, so
`--pick-seed` draws the same people again.

```
P0100  Long-tenured widow above the fire  ·  case C01
18C · floor 18 (simulation floor 17) · asleep
  …
  connections   4
    would knock   P0087 17A   adult                     ████     0.50
    would phone   P0035 8D    adult                     █████    0.67
    building chat G_group_chat_building  (55 members)    ██       0.28
```

`personas explore` writes a self-contained page — the tower floor by floor, a filtered
resident list, the selected person's card, and their ties drawn as a graph you can click
through. It embeds the population, a provenance index and the source list, so it opens
from disk and can be sent to somebody who does not have the repository. Following the
ties is the point: who could pass a warning to whom, and who would hear from nobody.

Four files land in `out/`:

| file | for |
|---|---|
| `*.personas.json` | the contract a simulation loads. Lean, schema-validated. |
| `*.provenance.json` | every number's derivation: which row, which distribution, which draw, which paper. |
| `*.report.md` | the human read: targets against what was drawn, gaps, repairs, warnings. |
| `*.cards.md` | the narrative cards, for reading and for prompting a model. |

## What a persona is

Six blocks, one per thing the four behaviour categories in `context.md` §2 need:

| block | holds | feeds |
|---|---|---|
| `identity` | age in years, sex, household role, tenure | everything; keeps age as a real covariate rather than an `adult`/`elderly` bin |
| `body` | the numeric stats, under **the simulation's own field names** | movement, fatigue, smoke |
| `situation` | unit, floor, home tile, present, asleep, what they are doing, whether the alarm is audible where they are | pre-evacuation |
| `knowledge` | how well they know the layout, habitual stair, whether they know a second stair exists, false alarms lived through | wayfinding |
| `dispositions` | milling, seeking confirmation, compliance, altruism, risk tolerance, leadership | pre-evacuation, social |
| `commitments` | the cat, the toddler, the documents — each with a delay | pre-evacuation |
| `ties` | household, would-knock, would-phone, building group chat | social |

plus `narrative`, a card rendered from the blocks above.

**Every `body` field is optional, and absent means "let the simulation's rules decide".**
That is deliberate: it keeps a sourced, fitted distribution authoritative wherever this
sheet has nothing better to say. `body.delay_s` is the worked example — the sheet's
pre-movement figure is a review midpoint, the simulation fits it from 149 and 78
observations, so the row that would set it is **parked and switched off**, and the
registry records why.

## The Sheet

Eight tabs, deliberately small, because every row is hand-maintained.

| tab | one row per |
|---|---|
| `Parameters` | a finding that sets or modifies a persona field — the registry `context.md` §6 asks for, made executable |
| `Sources` | a citation, in the same shape as the simulation's `docs/bibliography.toml` |
| `Population` | a demographic or household target the sampler aims at |
| `Social` | a tie kind, its rate, and how connectedness grows with tenure |
| `Cases` | a hand-authored named persona |
| `Building` | a flat: its floor, its letter, and a seed tile |
| `Scenarios` | a set of conditions: day or night, alarm quality, where the fire starts |
| `Enums` | every controlled vocabulary, and so every dropdown *and* the validator's vocabulary |

`data/` holds the committed CSV snapshot. `personas pull` refreshes it from the Sheet;
**`personas build` reads the snapshot and never the network.** That is what makes a live,
collaboratively edited sheet compatible with a reproducible generator: the sheet can
change under you, but a run names the exact revision it came from, and pulling is a
commit whose diff shows what moved.

### Connecting a Google Sheet

```bash
uv sync --extra sheet
uv run personas init-sheet     # one workbook: eight named tabs, frozen headers, dropdowns
# upload it to Drive, open it as a Sheet, then
#   Share -> General access -> Anyone with the link -> Viewer
uv run personas pull --sheet-url "https://docs.google.com/spreadsheets/d/1AbC…/edit"
```

Upload the workbook rather than pasting eight CSVs into eight tabs: that paste is where
a column lands one over, and a shifted row parses cleanly and means something else.
`init-sheet` and `pull` round-trip to the same content hash, so going through Google
does not by itself change a run id. Full walkthrough, including the private-sheet and
token case: [`docs/sheet-guide.md`](docs/sheet-guide.md).

### Adding a parameter

One row. No code:

| column | meaning |
|---|---|
| `target` | a dotted persona path, e.g. `dispositions.mill_tendency`. Checked against a closed registry — `personas fields` lists it |
| `applies_to` | who it affects, e.g. `age_years >= 65 and mobility != wheelchair`. Checked against a closed registry of readable attributes |
| `mechanism` | `set`, `add`, `mul`, `min`, `max` |
| `dist` + `p1`–`p4` | how the value is drawn |
| `evidence` | `SOURCED`, `ESTIMATE` or `INVENTED` — the simulation's own three words, so the two provenance layers speak one language |

A typo is an error with a cell reference and a suggestion, never a row that silently
does nothing:

```
Parameters!G23  unknown target 'dispositions.mill_tendancy'
                — did you mean 'dispositions.mill_tendency'?
Parameters!K9   applies_to: 'or' is not supported — write two rows instead, so each can
                carry its own source and be switched off on its own
```

Adding a genuinely new *field* costs one entry in `persona.FIELDS`. That is the right
friction: a new number is free, a new concept costs a commit.

## What is deliberately hard here

**Reproducibility against a live sheet.** Solved by snapshotting, above.

**One change moving one thing.** Every draw comes from its own stream, keyed by a
content hash of a stable path (`persona/{key}/{field}/{parameter}`), never an array
index. So editing one case, or adding one, cannot move another persona's numbers, and
editing one parameter row moves only the fields that row feeds. Two things are
population-level by nature and *can* move: **membership** (one more resident placed
means one fewer drawn elsewhere) and **repair passes** ("bring the under-18 share to
12%" is a statement about everybody). Both are deterministic, and every repair names
who it touched. `tests/test_determinism.py` asserts exactly this boundary rather than a
claim that is not true.

**Targets that contradict each other.** They do, and the tool says so instead of
splitting the difference:

- Census household sizes imply 1.99 people per household; large San Francisco buildings
  run nearer 1.66 per flat. Reconciled by an exponential tilt whose single parameter is
  reported (θ = 0.69 for this sheet), not by quietly editing either number.
- A child needs an adult in the flat, so the under-18 share and the occupancy target
  constrain each other. If the target is unreachable the report prints the arithmetic
  ceiling.
- Somebody of 22 cannot have lived here five years, so the tenure and age targets do
  too.

**Sampling noise against bias.** A share measured over twenty-five occupants moves four
percentage points when one person changes. Every target carries its standard error and
a `z`; the report separates "outside tolerance but within noise" from "the sampler is
actually off", so the section stays worth reading.

## Files

```
data/          the committed snapshot of the Sheet, one CSV per tab
reference/     the team's first hand-typed roster, archived. Never read by `build`.
schema/        the population JSON Schema, generated from the field registry
docs/          the persona schema, the Sheet guide, and the cross-repo contract
src/egress_personas/
  rng.py         PCG32, ported from the simulation; one stream per draw
  dists.py       the distribution vocabulary a Parameters row may draw from
  filters.py     the applies_to grammar
  tables.py      reading the Sheet's tabs; hashing them by content, not by bytes
  validate.py    every check, each with a cell reference
  persona.py     what a persona is: the field and attribute registries
  households.py  targets, household formation, demographics, repairs
  ties.py        the social graph
  parameters.py  composition: set, then add, then multiply, then clamp
  narrative.py   the text card
  sample.py      the thirteen phases, in order
  emit.py        writing it out
  report.py      the human read
  compare.py     against the archived roster
  sheet.py       pulling from Google Sheets
  seed.py        a starting set of tabs
  show.py        sampling somebody and reading them in the terminal
  explore.py     the payload behind the page
  explorer.html  the page: tower, list, card, tie graph
```

Dependencies: `jsonschema` only. Sheets arrive as CSV over `urllib`; the generator and
its distributions are pure Python, so there is no pandas, numpy or openpyxl to install.

## Where this is going

The population JSON is shaped for the simulation's own reserved roadmap item 3.2,
"Agent list input" (`../FireEgress-3dsim/docs/ROADMAP.md`): households are contiguous
runs named by their first member's index, escort links are symmetric, enum spellings are
the simulation's lowercase ones, and `home_tile` is `[sim_floor, x, y]`. The Rust loader
is not written yet; `docs/sim-contract.md` records every invariant it will rely on, with
citations. Also deferred, with their slots reserved: model-written narratives, trust
weights on ties, and writing sensitivity results back to the Sheet.
