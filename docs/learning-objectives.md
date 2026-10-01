# What there is to learn here

Written for the semester this work sits in: a URAP apprenticeship on an agent-based fire
evacuation model, where the apprentice wants the project to be worth something
intellectually and not only worth credit. It is meant to be arguable — if an objective
below does not survive contact with your advisor, that is the doc working.

The short version: **the most valuable thing this project has produced is not a model of
people, it is a measurement of how little is known about them.** Of the 31 parameter rows
in the registry, 8 are SOURCED, 14 are ESTIMATE and 9 are INVENTED — a quarter of a
behavioural model rests on numbers nobody has measured. That is not a defect to hide; it
is a result, and it is the thing that tells you what to do next.

---

## 1. Turning a literature into a parameterised model, and labelling your own ignorance

**The claim.** You can take a body of empirical work on human behaviour in fire and turn
it into something executable, while keeping honest track of which parts are measured,
which are reasoned, and which are made up.

**What it rests on.** Every parameter row carries `SOURCED` / `ESTIMATE` / `INVENTED` —
the same three words the simulation's own provenance layer uses, so the two speak one
language. The split is 26% / 45% / 29%. The social-tie rules are worse: of five, one is
sourced, two are estimates, two are invented. One row (`P090`, pre-movement time) is
deliberately **parked and switched off** with its reason recorded, because the sheet's
figure is a review midpoint and the simulation fits the distribution from 149 and 78
observations — overriding a fitted distribution with a constant would have been a
regression dressed up as an improvement.

**Why it is a real skill.** The instinct in a modelling project is to fill every cell and
move on. Labelling a cell `INVENTED` costs nothing technically and quite a lot socially,
and it is the difference between a model you can defend and one you cannot. It also makes
the next objective possible.

**How to evidence it.** A short methods note on the labelling scheme, the current split,
and two or three rows where the label changed your decision. `P090` is the best example
in the repo.

---

## 2. Population synthesis under conflicting marginals

**The claim.** You can draw a statistically defensible synthetic population when the
targets you have been given contradict each other — and you can say *how* they
contradict, rather than splitting the difference.

**What it rests on.** Three reconciliations, each in the repo and each reported in the
output:

- Census household sizes imply 1.99 people per household; the figure for large San
  Francisco buildings is nearer 1.66 per flat. Resolved by an **exponential tilt** on the
  size weights, solved by bisection, whose single parameter (θ = 0.69) is printed. θ = 1
  would mean the two agreed.
- Tenure and age constrain each other — somebody of 22 cannot have lived here five years —
  so drawing tenure bands independently always undershot the long-tenure share. Resolved
  by **iterative proportional fitting**: one multiplier per band so the expected marginal
  matches, given who can reach it.
- A child needs an adult in the flat, so the under-18 share and the per-flat occupancy
  constrain each other. With a mean household size of *m*, no more than (m−1)/m of the
  building can be under 18 however the ages are drawn. The tool prints that ceiling when
  a target exceeds it.

**Why it is a real skill.** This is a named methods area with a literature of its own —
synthetic populations and microsimulation, used in travel-demand modelling and
epidemiology as much as in egress. IPF goes back to Deming and Stephan (1940); synthetic
population generation to Beckman, Baggerly and McKay (1996). Being able to say "I used
iterative proportional fitting to reconcile a marginal against a feasibility constraint"
places the work in a tradition instead of leaving it as ad-hoc code.

**How to evidence it.** Read those two papers and write a page connecting what the repo
does to what they describe. That is a genuine literature contribution and it is small.

---

## 3. Telling sampling noise apart from bias

**The claim.** You can distinguish "the number moved" from "the number moved for a
reason", and you know why that distinction decides whether a result means anything.

**What it rests on.** Every demographic target carries its binomial standard error and a
z. A share measured over 25 occupants moves four percentage points when one person
changes, so a tolerance can be tighter than the building can resolve; the report
separates *outside tolerance but within noise* from *the sampler is actually off*. The
noise line is three standard errors, not two, because a report carries dozens of these
rows and a 2σ line would flag one every time until the reader learned to skip the
section. And there is a test asserting the mean z over 30 seeds stays within a fraction
of a standard error — bias, as opposed to variance, is what no single run can show you.

**Why it is a real skill.** It is the same habit that stops you over-reading a single
simulation run, and it transfers to every empirical thing you will ever do. The specific
trap — that enough comparisons will always produce a significant one — is worth having
met once in your own code.

**How to evidence it.** The cohort comparison ranks what moved by the change against the
base building's own seed-to-seed spread. Explain that ranking and why the raw difference
would have been the wrong ordering.

---

## 4. Reproducibility as a design constraint

**The claim.** You can build a research tool where a result names the exact inputs that
produced it, and where changing one thing changes one thing.

**What it rests on.**

- Every random draw comes from its own stream, keyed by a content hash of a stable path
  (`persona/{key}/{field}/{parameter}`), never an array index. So editing one persona
  cannot move another's numbers, and editing one parameter row moves only the fields it
  feeds. A test asserts exactly that boundary — including the two places where it
  genuinely does not hold, membership and repair passes, which are population-level by
  nature.
- The snapshot hash covers normalised content, not bytes, so re-exporting the same sheet
  from Google does not move a run id.
- `build` reads a pinned snapshot and never the network, because a generator that fetched
  live could not be repeated.
- The population carries no fetch timestamp, after one was found leaking in and changing
  every output file on a pull that changed nothing.

**Why it is a real skill.** Research software that cannot reproduce its own results is
the normal case, not the exception, and most people learn this the hard way after a
reviewer asks. The specific techniques — content addressing, per-draw substreams,
snapshot pinning — are the same ones used in experiment tracking and data versioning
generally.

**How to evidence it.** `personas build` twice and diff. Then write the paragraph on why
`--pull` is opt-in.

---

## 5. Social structure as a modelling choice with consequences

**The claim.** You understand that how you parameterise a social network determines
whether your results transfer between buildings, and that most of this layer is not
grounded in anything.

**What it rests on.** Two decisions worth defending:

- Tie rates that should transfer are stated as an **average degree per person**, not a
  probability per pair. A per-pair rate silently means six phone contacts in a 27-floor
  tower and one in a five-floor block. This was a live bug: the first version produced an
  average of 6.25 people each resident would telephone.
- Tie formation scales with **tenure**, which is what produces a resident who genuinely
  knows nobody. Without it, 97% of residents had a neighbour they would knock for, and the
  isolated resident — one of the cases the project exists to study — did not exist.

**Why it is the interesting gap.** The project's hypothesis is about agents that
*communicate*. The communication layer is the least grounded thing in the registry. That
coincidence is where an undergraduate contribution is actually available: a focused
literature search for neighbour-warning rates in residential buildings. If the answer is
that nobody has measured it, **that is a publishable sentence**, and it justifies every
`INVENTED` label on those rows.

**How to evidence it.** Either a set of sourced replacements for `S010`–`S030`, or a
written account of having looked and found nothing, with the search strategy recorded.

---

## 6. Reporting a limitation as a finding

**The claim.** You can tell the difference between a gap you should fill and a gap you
should report, and you know that inventing a plausible value hides the more interesting
result.

**What it rests on.** The clearest case is the wheelchair user who lives alone. The
simulation looks for a caregiver on the same floor and will not find one for a
one-person household. The generator could quietly invent a carer; instead it leaves
`partner` null and records a gap, and the accessible-building cohort raises the number of
such residents on purpose, because that is the question that cohort asks. Two more:
the first workbook's `mobility impaired` label conflated a walking difficulty (3.8% and
18.2% by age, census) with a wheelchair (about 1.3%) — a tenfold difference in who can
use a staircase at all; and its `Pre` and `Panick` columns were constant down all 143
rows, so they carried no information while looking like parameters.

**How to evidence it.** A limitations register ranked by consequence. Section 7 is how you
get the ranking.

---

## 7. What is actually open — where the contribution is

Three pieces of work, in the order I would do them. Each is scoped to a semester and each
produces something citable.

**(a) The sensitivity analysis.** This is the headline and it is what `context.md` §6 asked
for before anything else. The registry already has `sensitivity_rank`,
`sensitivity_delta_tts_s` and `sensitivity_delta_tte_s` sitting empty. Vary each parameter
across its literature range, measure how far TTS and TTE move, and fill them in. The
output is an **evidence-based ranking of what to build next** — and, more interestingly, a
ranking of which `INVENTED` values actually matter. A guess that moves nothing is not a
problem; a guess that moves everything is the project's main risk, and right now nobody
knows which guesses are which.

**(b) Close the loop to the simulation.** The cohorts currently move *inputs* to RSET, not
RSET. Turning "this building has a slower left tail" into "this building takes four more
minutes" needs the population JSON loaded by `FireEgress-3dsim` — its own reserved roadmap
item 3.2, with the invariants already documented in `sim-contract.md` and already
satisfied by the output. It is a contained piece of Rust: a serde struct of `Option<f32>`,
a branch in `population::spawn`, and a scenario key.

**(c) Source the social layer.** Section 5. Smallest, and the one most likely to produce a
sentence nobody has written down.

---

## What this project does not teach

Worth saying plainly, so the claims above stay credible.

- **Not fire science.** Smoke movement, heat release and tenability are the simulation's,
  and they came from a sourcing effort that is already done. You are downstream of it.
- **Not agent-based modelling from scratch.** The simulation exists and is good. What you
  are building is the population that goes into it, which is a narrower and more
  defensible claim.
- **Nothing yet about LLMs or reinforcement learning,** which is where the research plan's
  stated novelty lies (`context.md` §2). The persona schema is shaped to condition a model
  — the narrative cards exist for exactly that — but no model has been conditioned on it.
  If the LLM half is what you want from the semester, say so, because it is a different
  piece of work and the schema is the input to it rather than a step along the way.
- **Not validated.** Nothing here has been checked against a real evacuation. The
  comparison the project eventually needs is against the physics-based tools named in
  `context.md` §3, and that is a longer horizon than a semester.

---

## A sequence for the semester

| | Work | What it produces |
|---|---|---|
| 1 | Read Lovreglio et al. (2019) and Haghani et al. (2024) properly, and fill in the `read_by` column | 14 of 15 sources are currently carried from somewhere else rather than read first-hand. This is the cheapest credibility you will ever buy. |
| 2 | Write up the labelling scheme and the 26/45/29 split | The methods note for objectives 1 and 6 |
| 3 | The sensitivity analysis (§7a) | A ranked table; the project's main deliverable |
| 4 | The limitations register, ordered by §7a's ranking | Objective 6, with evidence |
| 5 | Either the loader (§7b) or the social literature search (§7c) | Depending on whether you want to write Rust or read papers |

Steps 1 and 2 are a week. Step 3 is the semester. Steps 4 and 5 are what you present.

---

## One thing to be careful about

The tooling here is more finished than the science. There are 150 tests, a validated
palette and a reproducibility story — and a quarter of the model is still invented. It
would be easy to spend the semester making the tool nicer, and to end it with an elegant
instrument and no finding. The sensitivity analysis is the thing that converts the
instrument into a result; everything else is in service of it.
