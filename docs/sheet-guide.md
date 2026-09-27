# Editing the Sheet

Eight tabs. Row 1 is the header. Blank always means *not stated* — never zero, never
false — which is what lets a `Cases` row pin two fields and leave the rest to be
sampled.

Run `personas validate` after any edit. It prints a cell reference for every problem,
and `personas build` refuses to run while any remain.

## Rules that the tools enforce

- **No formulas in a machine-read column.** A formula reads back as blank or as its own
  text. Put working in a column prefixed `x_` if you need scratch space.
- **An undeclared column is an error.** A column the generator ignores is worse than a
  column it rejects: the sheet would say one thing and the run would do another.
- **Mind the commas.** A value containing a comma must be quoted. A row with one field
  too few parses cleanly and shifts every value after it one column left — this bit the
  `Cases` tab seven rows at a time during development, which is why the validator now
  counts fields per row.
- **Booleans** are `TRUE`/`FALSE`, but `yes`/`no`/`y`/`n`/`1`/`0` are all accepted.
- **Lists** are separated by `;`, e.g. `source_ids = proulx1995;nist_ncstar_1_7`.
- **Dropdowns** come from the `Enums` tab. Adding a term there is how you add an option.

## `Parameters`

One row per finding that sets or modifies a persona field. The registry `context.md` §6
asks for, made executable.

| column | notes |
|---|---|
| `target` | dotted persona path. `personas fields` lists every legal value |
| `applies_to` | who it affects. Blank means everybody |
| `mechanism` | `set` / `add` / `mul` / `min` / `max` |
| `dist`, `p1`–`p4` | how it is drawn. The `Enums` tab documents each distribution's parameters in order |
| `categories`, `weights` | only for `dist = categorical`, `;`-separated |
| `priority` | higher wins a `set` contest. Default 100 |
| `evidence` | `SOURCED` / `ESTIMATE` / `INVENTED`. Be honest: `INVENTED` rows are the ones a sensitivity run should look at first |
| `lit_low`, `lit_high` | the range the literature supports, which is not always the value used |
| `enabled` | `FALSE` keeps a row on the record without applying it |
| `status` | `parked` plus a note in `notes` is how you record a decision *not* to use a value |
| `sensitivity_rank`, `sensitivity_delta_*` | left blank; a later sensitivity run fills them |

### `applies_to`

```
expr := term ("and" term)*
term := attribute op value
op   := == | != | < | <= | > | >= | in | not in
```

No `or`, no parentheses, no arithmetic. `or` is always two rows, and two rows can each
carry their own source and be switched off on their own — which is what a parameter
registry wants. Examples:

```
age_years >= 65
age_years >= 18 and age_years < 65 and mobility != wheelchair
sim_agent_type in [elderly, wheelchair]
has_pet == TRUE
alarm_quality == poor
lives_alone == TRUE and household_role == head
```

`applies_to` may only read attributes the **sampler** owns — ages, placement, presence,
scenario settings. It may not read a field another row writes, because then its answer
would depend on the order rows were applied in.

### How rows combine

For one persona and one field: every matching row draws its value first; then `set`
(highest `priority` wins, and a tie between two rows that could match the same person is
an error, not a coin flip); then every `add`; then every `mul`; then `min`/`max`; then
the field's own bounds and rounding.

Additive before multiplicative, because that is the shape the literature comes in: an
absolute anchor (adults walk 1.20 m/s), then relative modifiers (a pet costs a tenth).

A row that loses a `set` contest is recorded as **shadowed** in the provenance, not
dropped in silence.

## `Population`

The targets the sampler aims at. State occupancy **per flat**, not per floor: a
per-floor figure only means something once you fix how many flats a floor has.

`tolerance` is a research judgement, not a statistic. The report separately reports each
target's standard error, so you can tell a tolerance that is tighter than the building
can resolve from a sampler that is actually off. A share measured over twenty-five
occupants moves four percentage points when one person changes.

Targets can contradict each other, and the tool will say so rather than split the
difference — the under-18 share against occupancy, tenure against age, census household
sizes against people per flat.

## `Cases`

Six to ten hand-authored named personas, for the qualitative vignettes. **Fill in only
what you mean to pin**; everything blank is sampled like anybody else's, and nothing
pinned is ever overwritten, including by a repair pass.

`commitments` reads `kind:what:delay_s`, `;`-separated:
`pet:the cat:60;child:the toddler:120`. Kinds: `pet`, `child`, `dependent`, `valuables`,
`documents`, `neighbour`.

`notes` is for the team — *why this case exists*. It stays out of the narrative card.

## `Social`

| column | notes |
|---|---|
| `rate_kind` | `per_pair`, or `per_person_degree` for a rate that should not change when the building gets bigger |
| `tenure_ref_years` | the tenure at which somebody is as connected as an established resident. This is what makes a new tenant genuinely isolated |
| `min_age_years` | 18 on every non-household kind: a child is tied to their flat and nothing else |
| `symmetric` | whether both ends get the tie |

## `Building`

One row per flat. `floor_label` is what the building calls the floor (no 13);
`sim_floor` is what the simulation indexes it as. Two columns so nobody does the
arithmetic in their head.

`seed_tile_x` / `seed_tile_y` place the household on the floorplan. They are **not** a
flat index, deliberately — see `sim-contract.md`.

## `Sources`

Same field shape as the simulation's `docs/bibliography.toml`, so a row can be promoted
there by copy. Leave `read_by` blank until somebody has actually opened the source: a
citation carried from somewhere else is a lead, not evidence, and the `notes` should say
which.
