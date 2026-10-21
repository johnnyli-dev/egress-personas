# Buildings compared — night_fire12, 5 seeds

Each column is a building the Sheet describes: a set of demographic targets with a question attached. Figures are means over 5 seeds, with the spread across those seeds in brackets — a difference smaller than the spread is not a difference.

**Read this as arithmetic, not as evidence.** Every cohort target is `basis = team`: somebody chose it to ask a question, and no census or paper says a building looks like that. What the table shows is the consequence of those choices propagated through the model's own rules — including consequences nobody typed, which is the part worth looking at. It is not a finding about real buildings.

**These are inputs to RSET, not RSET.** Nothing here simulates an evacuation.

Counts are shown per 100 residents, with the raw count in brackets. Occupancy across these buildings runs from 0.85 to 3.1 people a flat, so an unscaled count rising would mostly mean the building got fuller rather than that anybody behaved differently.

## The questions

- **(base)** — the building as the census and the literature describe it, with the hand-authored cases in it.
- **Mostly elderly** (`elderly_block`) — Does a building of older residents fail on the stairs, or before anybody reaches them?
- **Students and new tenants** (`student_block`) — What happens when almost nobody knows the building, or each other?
- **Families with children** (`families`) — How much does gathering children cost against how fast the adults can move?
- **Accessible building** (`accessible_block`) — If a tower is let preferentially to disabled tenants, how many need the lift and how many have nobody to help?
- **Half the flats empty** (`transient`) — Does a half-occupied tower evacuate faster, or just leave more people unwarned?

## Drivers

| driver | unit | (base) | Mostly elderly | Students and new tenants | Families with children | Accessible building | Half the flats empty |
|---|---|---|---|---|---|---|---|
| **The building** | | | | | | | |
| in the building | people | 140.4 <sub>±7</sub> | 123 <sub>±4.2</sub> | 204.4 <sub>±7.8</sub> | 267.8 <sub>±6.7</sub> | 141.4 <sub>±6.2</sub> | 75 <sub>±1.4</sub> |
| **Before anybody moves (TTS)** | | | | | | | |
| asleep when it starts | share | 95% <sub>±1%</sub> | 96% <sub>±1%</sub> | 96% <sub>±1%</sub> | 96% <sub>±1%</sub> | 96% <sub>±1%</sub> | 95% <sub>±2%</sub> |
| cannot hear the alarm | per 100 residents | 1.7 <sub>±1.1</sub> <sub>(2.4)</sub> | 1.6 <sub>±1.2</sub> <sub>(2)</sub> | 1.6 <sub>±0.5</sub> <sub>(3.2)</sub> | 1.5 <sub>±0.4</sub> <sub>(4)</sub> | 1.7 <sub>±1.1</sub> <sub>(2.4)</sub> | 2.1 <sub>±1.2</sub> <sub>(1.6)</sub> |
| nobody would warn them | per 100 residents | 4.7 <sub>±1</sub> <sub>(6.6)</sub> | 3.1 <sub>±1.7</sub> <sub>(3.8)</sub> | 0.8 <sub>±0.3</sub> <sub>(1.6)</sub> | 0.1 <sub>±0.2</sub> <sub>(0.2)</sub> | 3.4 <sub>±1.1</sub> <sub>(4.8)</sub> | 1.9 <sub>±2.1</sub> <sub>(1.4)</sub> |
| confers before acting, mean | 0–1 | 0.59 <sub>±0.01</sub> | 0.62 <sub>±0.01</sub> | 0.52 <sub>±0.01</sub> | 0.63 <sub>±0.01</sub> | 0.60 <sub>±0.01</sub> | 0.61 <sub>±0.02</sub> |
| seeks a second cue, mean | 0–1 | 0.55 <sub>±0.02</sub> | 0.56 <sub>±0.02</sub> | 0.55 <sub>±0.01</sub> | 0.55 <sub>±0.01</sub> | 0.56 <sub>±0.02</sub> | 0.57 <sub>±0.03</sub> |
| will not leave without something | per 100 residents | 17.3 <sub>±2.8</sub> <sub>(24.4)</sub> | 19.6 <sub>±3.4</sub> <sub>(24.2)</sub> | 7 <sub>±2.9</sub> <sub>(14.4)</sub> | 20.3 <sub>±3.2</sub> <sub>(54.4)</sub> | 17.5 <sub>±3.3</sub> <sub>(24.8)</sub> | 17.4 <sub>±5</sub> <sub>(13)</sub> |
| gathering, per resident | seconds | 8.8 <sub>±1.3</sub> | 8.8 <sub>±1.5</sub> | 3.1 <sub>±1.3</sub> | 9.1 <sub>±1.4</sub> | 7.9 <sub>±1.5</sub> | 7.8 <sub>±2.3</sub> |
| **Getting out (TTE)** | | | | | | | |
| walking speed, mean | m/s | 1.06 <sub>±0.03</sub> | 0.95 <sub>±0.04</sub> | 1.16 <sub>±0.02</sub> | 1.04 <sub>±0.01</sub> | 0.92 <sub>±0.03</sub> | 1.06 <sub>±0.03</sub> |
| walking speed, slowest twentieth | m/s | 0.61 <sub>±0.03</sub> | 0.52 <sub>±0.03</sub> | 0.72 <sub>±0.02</sub> | 0.63 <sub>±0.02</sub> | 0.47 <sub>±0.02</sub> | 0.62 <sub>±0.05</sub> |
| walks with difficulty | per 100 residents | 6.7 <sub>±1.3</sub> <sub>(9.4)</sub> | 12.8 <sub>±1.4</sub> <sub>(15.8)</sub> | 4.8 <sub>±1.6</sub> <sub>(9.8)</sub> | 4.8 <sub>±0.7</sub> <sub>(12.8)</sub> | 22.2 <sub>±3.9</sub> <sub>(31.4)</sub> | 5.1 <sub>±1.1</sub> <sub>(3.8)</sub> |
| cannot use the stairs at all | per 100 residents | 1.3 <sub>±0.8</sub> <sub>(1.8)</sub> | 1.5 <sub>±0.4</sub> <sub>(1.8)</sub> | 1.5 <sub>±0.4</sub> <sub>(3)</sub> | 1.6 <sub>±0.3</sub> <sub>(4.2)</sub> | 13.7 <sub>±0.5</sub> <sub>(19.4)</sub> | 1.3 <sub>±0</sub> <sub>(1)</sub> |
| of those, nobody in the flat to help | per 100 residents | 1 <sub>±0.4</sub> <sub>(1.4)</sub> | 1 <sub>±0.7</sub> <sub>(1.2)</sub> | 0.2 <sub>±0.3</sub> <sub>(0.4)</sub> | 0.1 <sub>±0.2</sub> <sub>(0.4)</sub> | 5 <sub>±1.3</sub> <sub>(7)</sub> | 0.3 <sub>±0.6</sub> <sub>(0.2)</sub> |
| does not know a second staircase exists | per 100 residents | 22.5 <sub>±4.3</sub> <sub>(31.6)</sub> | 15.7 <sub>±4.4</sub> <sub>(19.4)</sub> | 36.9 <sub>±2.5</sub> <sub>(75.4)</sub> | 22.2 <sub>±2.7</sub> <sub>(59.4)</sub> | 21.5 <sub>±4.4</sub> <sub>(30.4)</sub> | 22.9 <sub>±6.3</sub> <sub>(17.2)</sub> |
| knows the layout, mean | 0–1 | 0.66 <sub>±0.02</sub> | 0.77 <sub>±0.02</sub> | 0.47 <sub>±0.02</sub> | 0.67 <sub>±0.01</sub> | 0.66 <sub>±0.01</sub> | 0.67 <sub>±0.02</sub> |

## What moved most

Ranked by **fold change** in the comparable figure — counts per 100 residents, means as they are — so a building being fuller does not get mistaken for its residents behaving differently, and a halving counts as the same size of move as a doubling.

A change to or from nearly nothing is shown as a bound (`≥`), because dividing by a quantity smaller than its own seed-to-seed spread does not mean anything.

A large change here means the targets were set far apart, nothing more. Whether it matters is a question for the simulation, and which of the underlying parameters deserve the weight is a question for a sensitivity run. Neither has been done.

| building | driver | base → cohort | fold |
|---|---|---|---|
| Accessible building | cannot use the stairs at all | 1.3 → 13.7 | ×10.7 ↑ |
| Students and new tenants | nobody would warn them | 4.7 → 0.8 | ≥×4.7 ↓ |
| Families with children | nobody would warn them | 4.7 → 0.1 | ≥×4.7 ↓ |
| Accessible building | of those, nobody in the flat to help | 1 → 5 | ≥×3.9 ↑ |
| Accessible building | walks with difficulty | 6.7 → 22.2 | ×3.3 ↑ |
| Students and new tenants | gathering, per resident | 8.8 → 3.1 | ×2.8 ↓ |
| Students and new tenants | of those, nobody in the flat to help | 1 → 0.2 | ≥×2.6 ↓ |
| Families with children | of those, nobody in the flat to help | 1 → 0.1 | ≥×2.6 ↓ |
| Students and new tenants | will not leave without something | 17.3 → 7 | ×2.5 ↓ |
| Half the flats empty | nobody would warn them | 4.7 → 1.9 | ≥×2.3 ↓ |
| Mostly elderly | walks with difficulty | 6.7 → 12.8 | ×1.9 ↑ |
| Families with children | in the building | 140.4 → 267.8 | ×1.9 ↑ |
| Half the flats empty | in the building | 140.4 → 75 | ×1.9 ↓ |
| Students and new tenants | does not know a second staircase exists | 22.5 → 36.9 | ×1.6 ↑ |
| Half the flats empty | of those, nobody in the flat to help | 1 → 0.3 | ≥×1.6 ↓ |
| Mostly elderly | nobody would warn them | 4.7 → 3.1 | ×1.5 ↓ |

## What the cohorts strained

A cohort can ask for a building the plan or the arithmetic cannot provide. Those are findings, not faults — and they are the reason the targets are stated rather than assumed.

- **Students and new tenants**: P003 (Walking speed - under 18) matched no persona — its applies_to is almost certainly wrong: age_years < 18 and mobility != wheelchair

## Gaps left open

| building | gap | per run |
|---|---|---|
| (base) | a wheelchair user with nobody in the flat who could help | 1.4 |
| Mostly elderly | a wheelchair user with nobody in the flat who could help | 1.5 |
| Students and new tenants | a wheelchair user with nobody in the flat who could help | 1.0 |
| Families with children | a wheelchair user with nobody in the flat who could help | 1.0 |
| Accessible building | a wheelchair user with nobody in the flat who could help | 7.0 |
| Half the flats empty | a wheelchair user with nobody in the flat who could help | 1.0 |

## Reading this honestly

- A cohort is a **question**, not a measurement. The base building's targets come from the census and the literature; a cohort's come from the team, and its rows say `basis = team` for exactly that reason.
- Most of what you see here is the arithmetic you set up. If you halve a cohort's mean tenure and the parameter rows assign familiarity by tenure band, mean familiarity falls — that is a weighted average, not a result. The rows worth a second look are the ones where a consequence appears in a quantity the cohort never named.
- Mobility is conditioned on age, so a cohort that only moves the age distribution still moves the walking-difficulty share. That is the model working, not a second assumption.
- Nothing here is an evacuation time. Feeding these populations to the simulation is what turns a difference in drivers into a difference in outcome, and the size of that step is the open question.
