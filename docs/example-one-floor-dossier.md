# One floor, in full

Floor 14 of the 27-storey tower · scenario `one_floor` · seed 1234

**7 residents in 4 households across 4 flats.** Every number below is followed from the literature to the value, so the model can be checked by hand rather than taken on trust.

- run `blake2b128:26a6334a088bc1bd02e09ff2c1199ddf`
- snapshot `blake2b128:e16d680150fed9799a5c06f9ffa5db00`
- engine mapping: **FireEgress 3D** (`fire_egress_3d`)

## Read this before the numbers

**At this size the distributions are not reproduced, and are not meant to be.** Seven draws cannot recover a curve fitted to 149 observations. The conformance figures below are printed for completeness and should be discounted; they are the reason to build the whole tower when you want the distributions to mean something, and this when you want to audit where they came from.

Three labels appear throughout, and they are the point of the exercise:

- **SOURCED** — a citation was read and supports this value.
- **ESTIMATE** — reasoned from an adjacent finding, but not measured.
- **INVENTED** — no measurement exists; the model needs a number.

## The floor

| flat | residents | household | pet |
|---|---|---|---|
| **14A** | P0000 (38, female), P0001 (41, male), P0002 (3, female) | HH-14A | yes |
| **14B** | P0003 (39, female) | HH-14B | no |
| **14C** | P0004 (49, male) | HH-14C | yes |
| **14D** | P0005 (40, male), P0006 (34, female, wheelchair) | HH-14D | no |

Seed tiles come from the floorplan drawing and are marked *estimate*: the simulation infers flats from walls and doors rather than naming them, so the A–D letters are annotations on a drawing, not an index anything verified.

## Where the composition came from

Every demographic target the sampler aimed at, with what it rests on. `basis` says the kind of evidence: `acs` and `sipp` are census surveys, `estimate` is reasoned, `team` is a figure somebody chose to ask a question with.

| target | value | basis | source |
|---|---|---|---|
| occupancy.persons_per_flat | `1.66` persons | estimate | [ACS B11016](https://data.census.gov/table/ACSDT1Y2024.B11016) |
| household_size.1 | `40.65` share | acs | [ACS B11016](https://data.census.gov/table/ACSDT1Y2024.B11016) |
| household_size.2 | `32.67` share | acs | [ACS B11016](https://data.census.gov/table/ACSDT1Y2024.B11016) |
| household_size.3 | `12.12` share | acs | [ACS B11016](https://data.census.gov/table/ACSDT1Y2024.B11016) |
| household_size.4plus | `14.57` share | acs | [ACS B11016](https://data.census.gov/table/ACSDT1Y2024.B11016) |
| age_band.0_17 | `0.12` share | estimate | — |
| age_band.18_34 | `0.27` share | acs | — |
| age_band.35_49 | `0.24` share | estimate | — |
| age_band.50_64 | `0.19` share | estimate | — |
| age_band.65_74 | `0.11` share | estimate | — |
| age_band.75_plus | `0.07` share | estimate | — |
| sex.female | `0.50` share | estimate | — |
| sex.male | `0.50` share | estimate | — |
| mobility.wheelchair | `0.013` share | sipp | SIPP wheelchair use |
| mobility.ambulatory_difficulty@18_64 | `0.038` share | acs | [ACS B18105](https://data.census.gov/table/ACSDT1Y2024.B18105) |
| mobility.ambulatory_difficulty@65_plus | `0.182` share | acs | [ACS B18105](https://data.census.gov/table/ACSDT1Y2024.B18105) |
| absence.share | `0.06` share | estimate | — |
| pet.share | `0.25` share | estimate | — |
| tenure.lt_1 | `0.18` share | estimate | — |
| tenure.1_5 | `0.37` share | estimate | — |
| tenure.5_plus | `0.45` share | estimate | — |

## The residents

For each: who they are, then every persona field with the heuristic that set it, then every quantity the simulation receives with the chain that produced it.

### P0000 — Mother of a small child, with a cat · hand-authored case `C03`

`14A` · floor 14 · head · 6 years here · asleep

> Mother of a small child, with a cat, 38, has lived in 14A for 6 years and heads the household. They share the flat with 1 other adult and 1 child. They know the building well, and take the north stair by habit. 5 false alarms here already, so a bell alone does not mean much to them. They will look for information and talk to people before moving, and would go out of their way to help others. In a corridor full of unsure neighbours, this is who starts giving directions. At the moment the fire starts they are asleep. They will not leave without the cat and the toddler. They have the building group chat.

*Why this case exists: Two floors above the fire with a toddler to carry and a cat that hides. Gathering time, not walking speed, decides this household's outcome.*

**Will not leave without** the cat (+60 s), the toddler (+120 s).

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **1.032** | `P001` set then `P006` mul | trunc_normal(1.20, 0.24, 0.50, 2.00) · const(0.90) | SOURCED/ESTIMATE | Bohannon 2008, SFPE / Fruin |
| `body.patience_s` | **73.4** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **yes** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.7** | `case` set *(pinned)* | — | ESTIMATE | — |
| `dispositions.authority_compliance` | **0.573** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.75** | `case` set *(pinned)* | — | ESTIMATE | — |
| `dispositions.mill_tendency` | **0.833** | `P010` set | trunc_normal(0.70, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.risk_tolerance` | **0.488** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.262** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.floorplan_familiarity` | **0.85** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.habitual_stair` | **north** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.knows_second_stair` | **yes** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.prior_false_alarms` | **5** | `P037` set | uniform(1, 8) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **363.2** s | `delay_s` | `E001` quantile: score +1.751 → 93% of 7 → Pre-movement, good alarm  [mill_tendency 0.833×+1, seeks_confirmation 0.262×+0.8, prior_false_alarms 5×+0.06, altruism 0.7×+0.3, commitments 2×+0.9, authority_compliance 0.573×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **1.032** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **42.9** s | `patience_s` | `E020` quantile: score -0.259 → 7% of 7 → Patience behind a blockage  [risk_tolerance 0.488×-1, authority_compliance 0.573×+0.4] | INVENTED |
| Visibility at which they turn back | **14.16** m | `smoke_limit_m` | `E030` quantile: score +0.713 → 93% of 7 → Visibility at which people turn back  [risk_tolerance 0.488×+1, floorplan_familiarity 0.85×+0.4, authority_compliance 0.573×-0.2] | ESTIMATE |
| Tries another route after turning back | **yes**  | `tries_other_stair` | `E040` quantile: score +0.973 → 93% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.488×+0.6, floorplan_familiarity 0.85×+0.8] | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **180** s | *this engine has nowhere to put it* | `E060` sum: 2 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **north**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **3** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 93% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 7% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 93% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 93% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- group chat → the building chat (strength 0.114)
- household → P0001 in 14A (strength 1.0)
- household → P0002 in 14A (strength 1.0)

### P0001 — Her partner · hand-authored case `C04`

`14A` · floor 14 · partner · 6 years here · asleep

> Her partner, 41, has lived in 14A for 6 years and is a partner in the household. They share the flat with 1 other adult and 1 child. They know the building well, and take the north stair by habit. One false alarm here already, so a bell alone does not mean much to them. They will look for information and talk to people before moving, and would help if asked. At the moment the fire starts they are asleep. They will not leave without the pet. They have 1 neighbour they would knock for, 2 people in the building they would phone.

*Why this case exists: The second adult in C03's flat. Whether the household waits for each other is the thing to watch.*

**Will not leave without** pet (+45 s).

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.827** | `P001` set then `P006` mul | trunc_normal(1.20, 0.24, 0.50, 2.00) · const(0.90) | SOURCED/ESTIMATE | Bohannon 2008, SFPE / Fruin |
| `body.patience_s` | **79.7** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **yes** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.6** | `case` set *(pinned)* | — | ESTIMATE | — |
| `dispositions.authority_compliance` | **0.441** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.4** | `case` set *(pinned)* | — | ESTIMATE | — |
| `dispositions.mill_tendency` | **0.877** | `P010` set | trunc_normal(0.70, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.risk_tolerance` | **0.319** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.366** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.floorplan_familiarity` | **0.8** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.habitual_stair` | **north** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.knows_second_stair` | **yes** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.prior_false_alarms` | **1** | `P037` set | uniform(1, 8) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **180** s | `delay_s` | `E001` quantile: score +0.801 → 79% of 7 → Pre-movement, good alarm  [mill_tendency 0.877×+1, seeks_confirmation 0.366×+0.8, prior_false_alarms 1×+0.06, altruism 0.6×+0.3, commitments 1×+0.9, authority_compliance 0.441×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.827** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **48.6** s | `patience_s` | `E020` quantile: score -0.143 → 21% of 7 → Patience behind a blockage  [risk_tolerance 0.319×-1, authority_compliance 0.441×+0.4] | INVENTED |
| Visibility at which they turn back | **2.18** m | `smoke_limit_m` | `E030` quantile: score +0.551 → 64% of 7 → Visibility at which people turn back  [risk_tolerance 0.319×+1, floorplan_familiarity 0.8×+0.4, authority_compliance 0.441×-0.2] | ESTIMATE |
| Tries another route after turning back | **no**  | `tries_other_stair` | `E040` quantile: score +0.831 → 64% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.319×+0.6, floorplan_familiarity 0.8×+0.8] | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **45** s | *this engine has nowhere to put it* | `E060` sum: 1 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **north**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **5** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 79% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 21% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 64% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 64% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- household → P0000 in 14A (strength 1.0)
- household → P0002 in 14A (strength 1.0)
- knock → P0006 in 14D (strength 0.386)
- phone → P0004 in 14C (strength 0.991)
- phone → P0006 in 14D (strength 0.762)

### P0002 — Their toddler · hand-authored case `C05`

`14A` · floor 14 · child · 3 years here · asleep

> Their toddler, 3, has lived in 14A for 3 years and is a child of the household. They share the flat with 2 other adults. They barely know the building's layout, and do not know there is a second staircase. They are too young to decide anything for themselves and will go wherever the adults in the flat take them. At the moment the fire starts they are asleep.

*Why this case exists: Three years old. Cannot evacuate alone under any circumstances, and sets the household's pace.*

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.759** | `P003` set then `P006` mul | trunc_normal(0.95, 0.20, 0.40, 1.50) · const(0.90) | ESTIMATE | SFPE / Fruin, [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `body.patience_s` | **55.5** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **yes** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.146** | `P023` set | trunc_normal(0.32, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.authority_compliance` | **0.43** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0** | `case` set *(pinned)* | — | ESTIMATE | — |
| `dispositions.mill_tendency` | **0.653** | `P010` set | trunc_normal(0.70, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.risk_tolerance` | **0.188** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.55** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.floorplan_familiarity` | **0.05** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.habitual_stair` | **none** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.knows_second_stair` | **no** | `case` set *(pinned)* | — | ESTIMATE | — |
| `knowledge.prior_false_alarms` | **0** | `case` set *(pinned)* | — | ESTIMATE | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **35.3** s | `delay_s` | `E001` quantile: score -0.364 → 36% of 7 → Pre-movement, good alarm  [mill_tendency 0.653×+1, seeks_confirmation 0.55×+0.8, prior_false_alarms 0×+0.06, altruism 0.146×+0.3, commitments 0×+0.9, authority_compliance 0.43×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.759** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **65.7** s | `patience_s` | `E020` quantile: score -0.016 → 64% of 7 → Patience behind a blockage  [risk_tolerance 0.188×-1, authority_compliance 0.43×+0.4] | INVENTED |
| Visibility at which they turn back | **0** m | `smoke_limit_m` | `E030` quantile: score +0.122 → 7% of 7 → Visibility at which people turn back  [risk_tolerance 0.188×+1, floorplan_familiarity 0.05×+0.4, authority_compliance 0.43×-0.2] | ESTIMATE |
| Tries another route after turning back | **no**  | `tries_other_stair` | `E040` quantile: score +0.153 → 7% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.188×+0.6, floorplan_familiarity 0.05×+0.8] then `E041` gate: knows_second_stair == False | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **0** s | *this engine has nowhere to put it* | `E060` sum: 0 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **none**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **2** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 36% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 64% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 7% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 7% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- household → P0000 in 14A (strength 1.0)
- household → P0001 in 14A (strength 1.0)

### P0003 — 39-year-old female

`14B` · floor 14 · head · 0.5 years here · asleep

> Somebody of 39 has lived in 14B for less than a year and heads the household. They live alone. They barely know the building's layout, and do not know there is a second staircase. They will usually check with somebody before acting, and look after themselves first. At the moment the fire starts they are asleep. They have the building group chat.

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.968** | `P001` set | trunc_normal(1.20, 0.24, 0.50, 2.00) | SOURCED | Bohannon 2008, SFPE / Fruin |
| `body.patience_s` | **50** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **no** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.199** | `P023` set | trunc_normal(0.32, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.authority_compliance` | **0.495** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.461** | `P024` set then `P025` add | trunc_normal(0.30, 0.18, 0.00, 1.00) · const(0.15) | ESTIMATE/INVENTED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.mill_tendency` | **0.424** | `P010` set then `P011` mul then `P012` mul | trunc_normal(0.70, 0.18, 0.00, 1.00) · const(0.65) · const(0.85) | SOURCED/ESTIMATE | NIST NCSTAR 1-7, [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.risk_tolerance` | **0.14** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.394** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `P038` set | bernoulli(0.10) | INVENTED | — |
| `knowledge.floorplan_familiarity` | **0.262** | `P030` set | trunc_normal(0.35, 0.15, 0.00, 1.00) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.habitual_stair` | **south** | `P035` set | categorical(north, south) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.knows_second_stair` | **no** | `P033` set | bernoulli(0.45) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **3.4** s | `delay_s` | `E001` quantile: score -0.748 → 7% of 7 → Pre-movement, good alarm  [mill_tendency 0.424×+1, seeks_confirmation 0.394×+0.8, altruism 0.199×+0.3, commitments 0×+0.9, authority_compliance 0.495×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.968** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **71.4** s | `patience_s` | `E020` quantile: score +0.058 → 79% of 7 → Patience behind a blockage  [risk_tolerance 0.14×-1, authority_compliance 0.495×+0.4] | INVENTED |
| Visibility at which they turn back | **0** m | `smoke_limit_m` | `E030` quantile: score +0.146 → 21% of 7 → Visibility at which people turn back  [risk_tolerance 0.14×+1, floorplan_familiarity 0.262×+0.4, authority_compliance 0.495×-0.2] | ESTIMATE |
| Tries another route after turning back | **no**  | `tries_other_stair` | `E040` quantile: score +0.294 → 21% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.14×+0.6, floorplan_familiarity 0.262×+0.8] then `E041` gate: knows_second_stair == False | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **0** s | *this engine has nowhere to put it* | `E060` sum: 0 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **south**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **1** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 7% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 79% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 21% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 21% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- group chat → the building chat (strength 0.352)

### P0004 — 49-year-old male

`14C` · floor 14 · head · 3.1 years here · asleep

> Somebody of 49 has lived in 14C for 3 years and heads the household. They live alone. They know the building well, and do not know there is a second staircase. 3 false alarms here already, so a bell alone does not mean much to them. They will usually check with somebody before acting, and would help if asked. At the moment the fire starts they are asleep. They will not leave without the pet. They have 1 neighbour they would knock for, 2 people in the building they would phone, the building group chat.

**Will not leave without** pet (+45 s).

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.883** | `P001` set then `P006` mul | trunc_normal(1.20, 0.24, 0.50, 2.00) · const(0.90) | SOURCED/ESTIMATE | Bohannon 2008, SFPE / Fruin |
| `body.patience_s` | **47.8** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **yes** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.592** | `P023` set | trunc_normal(0.32, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.authority_compliance` | **0.803** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.422** | `P024` set then `P025` add | trunc_normal(0.30, 0.18, 0.00, 1.00) · const(0.15) | ESTIMATE/INVENTED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.mill_tendency` | **0.66** | `P010` set then `P012` mul | trunc_normal(0.70, 0.18, 0.00, 1.00) · const(0.85) | SOURCED/ESTIMATE | NIST NCSTAR 1-7, [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.risk_tolerance` | **0.136** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.787** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `P038` set | bernoulli(0.10) | INVENTED | — |
| `knowledge.floorplan_familiarity` | **0.855** | `P031` set | trunc_normal(0.65, 0.15, 0.00, 1.00) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.habitual_stair` | **north** | `P035` set | categorical(north, south) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.knows_second_stair` | **no** | `P034` set | bernoulli(0.85) | INVENTED | — |
| `knowledge.prior_false_alarms` | **3** | `P036` set | uniform(0, 3) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **106.4** s | `delay_s` | `E001` quantile: score +0.785 → 64% of 7 → Pre-movement, good alarm  [mill_tendency 0.66×+1, seeks_confirmation 0.787×+0.8, prior_false_alarms 3×+0.06, altruism 0.592×+0.3, commitments 1×+0.9, authority_compliance 0.803×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.883** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **77.1** s | `patience_s` | `E020` quantile: score +0.185 → 93% of 7 → Patience behind a blockage  [risk_tolerance 0.136×-1, authority_compliance 0.803×+0.4] | INVENTED |
| Visibility at which they turn back | **0.97** m | `smoke_limit_m` | `E030` quantile: score +0.317 → 50% of 7 → Visibility at which people turn back  [risk_tolerance 0.136×+1, floorplan_familiarity 0.855×+0.4, authority_compliance 0.803×-0.2] | ESTIMATE |
| Tries another route after turning back | **no**  | `tries_other_stair` | `E040` quantile: score +0.766 → 50% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.136×+0.6, floorplan_familiarity 0.855×+0.8] then `E041` gate: knows_second_stair == False | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **45** s | *this engine has nowhere to put it* | `E060` sum: 1 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **north**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **4** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 64% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 93% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 50% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 50% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- group chat → the building chat (strength 0.362)
- knock → P0006 in 14D (strength 0.632)
- phone → P0001 in 14A (strength 0.991)
- phone → P0005 in 14D (strength 0.688)

### P0005 — 40-year-old male

`14D` · floor 14 · head · 0.3 years here · asleep

> Somebody of 40 has lived in 14D for less than a year and heads the household. They share the flat with 1 other adult. They barely know the building's layout, and do not know there is a second staircase. They will usually check with somebody before acting, and look after themselves first. At the moment the fire starts they are asleep. They have 1 person in the building they would phone.

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.911** | `P001` set | trunc_normal(1.20, 0.24, 0.50, 2.00) | SOURCED | Bohannon 2008, SFPE / Fruin |
| `body.patience_s` | **52.9** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **yes** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.073** | `P023` set | trunc_normal(0.32, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.authority_compliance` | **0.729** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.514** | `P024` set then `P025` add | trunc_normal(0.30, 0.18, 0.00, 1.00) · const(0.15) | ESTIMATE/INVENTED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.mill_tendency` | **0.537** | `P010` set then `P011` mul | trunc_normal(0.70, 0.18, 0.00, 1.00) · const(0.65) | SOURCED/ESTIMATE | NIST NCSTAR 1-7, [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `dispositions.risk_tolerance` | **0.362** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.598** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `P038` set | bernoulli(0.10) | INVENTED | — |
| `knowledge.floorplan_familiarity` | **0.199** | `P030` set | trunc_normal(0.35, 0.15, 0.00, 1.00) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.habitual_stair` | **south** | `P035` set | categorical(north, south) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.knows_second_stair` | **no** | `P033` set | bernoulli(0.45) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **16** s | `delay_s` | `E001` quantile: score -0.673 → 21% of 7 → Pre-movement, good alarm  [mill_tendency 0.537×+1, seeks_confirmation 0.598×+0.8, altruism 0.073×+0.3, commitments 0×+0.9, authority_compliance 0.729×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.911** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **60** s | `patience_s` | `E020` quantile: score -0.070 → 50% of 7 → Patience behind a blockage  [risk_tolerance 0.362×-1, authority_compliance 0.729×+0.4] | INVENTED |
| Visibility at which they turn back | **0** m | `smoke_limit_m` | `E030` quantile: score +0.296 → 36% of 7 → Visibility at which people turn back  [risk_tolerance 0.362×+1, floorplan_familiarity 0.199×+0.4, authority_compliance 0.729×-0.2] | ESTIMATE |
| Tries another route after turning back | **no**  | `tries_other_stair` | `E040` quantile: score +0.376 → 36% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.362×+0.6, floorplan_familiarity 0.199×+0.8] then `E041` gate: knows_second_stair == False | ESTIMATE |
| Can use stairs | **yes**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **0** s | *this engine has nowhere to put it* | `E060` sum: 0 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **south**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **2** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 21% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 50% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 36% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 36% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- household → P0006 in 14D (strength 1.0)
- phone → P0004 in 14C (strength 0.688)

### P0006 — 34-year-old female

`14D` · floor 14 · partner · 12 years here · asleep

> Somebody of 34 has lived in 14D for 12 years and is a partner in the household. They use a wheelchair and cannot use the stairs at all. They share the flat with 1 other adult. They know the building well, and take the south stair by habit. 3 false alarms here already, so a bell alone does not mean much to them. They will look for information and talk to people before moving, and would help if asked. At the moment the fire starts they are asleep. They have 2 neighbours they would knock for, 1 person in the building they would phone, the building group chat.

**Persona fields, and the heuristic behind each**

| field | value | heuristic | drawn from | how sure | source |
|---|---|---|---|---|---|
| `body.base_speed` | **0.734** | `P004` set | trunc_normal(0.68, 0.20, 0.30, 1.10) | ESTIMATE | SFPE / Fruin |
| `body.patience_s` | **46.1** | `P007` set | uniform(40, 80) | INVENTED | — |
| `body.tries_other_stair` | **no** | `P008` set | bernoulli(0.23) | ESTIMATE | — |
| `dispositions.altruism` | **0.378** | `P023` set | trunc_normal(0.32, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.authority_compliance` | **0.469** | `P022` set | trunc_normal(0.60, 0.20, 0.00, 1.00) | ESTIMATE | Kuligowski NIST TN 1632 |
| `dispositions.leadership` | **0.244** | `P024` set | trunc_normal(0.30, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.mill_tendency` | **0.75** | `P010` set | trunc_normal(0.70, 0.18, 0.00, 1.00) | SOURCED | NIST NCSTAR 1-7 |
| `dispositions.risk_tolerance` | **0.282** | `P026` set | trunc_normal(0.40, 0.18, 0.00, 1.00) | INVENTED | — |
| `dispositions.seeks_confirmation` | **0.749** | `P020` set | trunc_normal(0.55, 0.20, 0.00, 1.00) | ESTIMATE | NIST NCSTAR 1-7, Team self-elicitation 2026 |
| `knowledge.fire_safety_training` | **no** | `P038` set | bernoulli(0.10) | INVENTED | — |
| `knowledge.floorplan_familiarity` | **0.95** | `P032` set | trunc_normal(0.85, 0.12, 0.00, 1.00) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.habitual_stair` | **south** | `P035` set | categorical(north, south) | ESTIMATE | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |
| `knowledge.knows_second_stair` | **yes** | `P034` set | bernoulli(0.85) | INVENTED | — |
| `knowledge.prior_false_alarms` | **3** | `P037` set | uniform(1, 8) | INVENTED | — |
| `situation.alarm_audible` | **yes** | `P040` set | bernoulli(0.98) | SOURCED | [Proulx 1995](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0) |

**What FireEgress 3D receives**

| model input | value | engine field | how it was arrived at | how sure |
|---|---|---|---|---|
| Pre-movement time | **63.5** s | `delay_s` | `E001` quantile: score +0.114 → 50% of 7 → Pre-movement, good alarm  [mill_tendency 0.75×+1, seeks_confirmation 0.749×+0.8, prior_false_alarms 3×+0.06, altruism 0.378×+0.3, commitments 0×+0.9, authority_compliance 0.469×-0.7, fire_safety_training 0×-0.5, alarm_audible 1×-1.2] | ESTIMATE |
| Walking speed on the level | **0.734** m/s | `base_speed` | `E010` direct: from base_speed | SOURCED |
| Patience behind a blockage | **54.3** s | `patience_s` | `E020` quantile: score -0.094 → 36% of 7 → Patience behind a blockage  [risk_tolerance 0.282×-1, authority_compliance 0.469×+0.4] | INVENTED |
| Visibility at which they turn back | **5.07** m | `smoke_limit_m` | `E030` quantile: score +0.568 → 79% of 7 → Visibility at which people turn back  [risk_tolerance 0.282×+1, floorplan_familiarity 0.95×+0.4, authority_compliance 0.469×-0.2] | ESTIMATE |
| Tries another route after turning back | **yes**  | `tries_other_stair` | `E040` quantile: score +0.929 → 79% of 7 → Tries the other staircase after turning back  [risk_tolerance 0.282×+0.6, floorplan_familiarity 0.95×+0.8] | ESTIMATE |
| Can use stairs | **no**  | `can_use_stairs` | `E050` direct: from can_use_stairs | SOURCED |
| Gathering time | **0** s | *this engine has nowhere to put it* | `E060` sum: 0 commitment(s) × delay_s | ESTIMATE |
| Habitual route | **south**  | *this engine has nowhere to put it* | `E080` direct: from habitual_stair | ESTIMATE |
| Neighbours they would warn | **5** count | *this engine has nowhere to put it* | `E090` direct: from ties | ESTIMATE |

Where those came from, when the value was read off a published distribution:

| model input | this resident | reference distribution | fitted by |
|---|---|---|---|
| Pre-movement time | 50% of the floor | Pre-movement, good alarm — weibull(102.475, 0.767) | [Lovreglio et al. 2019](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf) |
| Patience behind a blockage | 36% of the floor | Patience behind a blockage — uniform(40.0, 80.0) | — |
| Visibility at which they turn back | 79% of the floor | Visibility at which people turn back — empirical_curve() | — |
| Tries another route after turning back | 79% of the floor | Tries the other staircase after turning back — bernoulli(0.23) | — |

**Who they would reach**

- group chat → the building chat (strength 0.165)
- household → P0005 in 14D (strength 1.0)
- knock → P0001 in 14A (strength 0.386)
- knock → P0004 in 14C (strength 0.632)
- phone → P0001 in 14A (strength 0.762)

## Conformance at this size, and why to discount it

| published distribution | mean | what seven residents produced |
|---|---|---|
| Pre-movement time | 119.807 s | 109.686 s |
| Patience behind a blockage | 60.0 s | 60.0 s |
| Visibility at which they turn back | 3.252 m | 3.197 m |

The gaps are sampling noise, not error. The mechanism assigns each resident a rank and reads the value off the published curve at that point, which reproduces the curve exactly in the limit and approximately nowhere near it. On the full tower of 151 these land within 1%.

## What the generator flagged

- case C01: unit '18C' is not in this plan; skipped
- case C02: unit '6B' is not in this plan; skipped
- case C06: unit '21D' is not in this plan; skipped
- case C07: unit '12B' is not in this plan; skipped
- case C08: unit '9A' is not in this plan; skipped
- P002 (Walking speed - 65 and over) matched no persona — its applies_to is almost certainly wrong: age_years >= 65 and mobility != wheelchair
- P005 (Walking speed - ambulatory difficulty) matched no persona — its applies_to is almost certainly wrong: mobility in [ambulatory_difficulty, walker_cane]
- P027 (Risk tolerance - 65 and over) matched no persona — its applies_to is almost certainly wrong: age_years >= 65

## Every source behind this floor

10 of the 15 sources on the Sheet were used by the numbers above.

- **ACS B11016** — US Census Bureau, American Community Survey, table B11016 (household type by household size), San Francisco. [https://data.census.gov/table/ACSDT1Y2024.B11016](https://data.census.gov/table/ACSDT1Y2024.B11016)
  - *What it gives us:* San Francisco households of 1 / 2 / 3 / 4-or-more people are 40.65 / 32.67 / 12.12 / 14.57 percent.
  - *Caveat:* Five-and-more folded into four. Flats in large buildings hold fewer people than the city average, which is why the occupancy target here is stated per flat and the size weights are tilted to match it.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **ACS B18105** — US Census Bureau, American Community Survey, table B18105 (ambulatory difficulty by age). [https://data.census.gov/table/ACSDT1Y2024.B18105](https://data.census.gov/table/ACSDT1Y2024.B18105)
  - *What it gives us:* Ambulatory difficulty runs about 3.8 percent among adults aged 35-64 and about 18.2 percent among those 65 and over.
  - *Caveat:* This is the share the workbook's 'mobility impaired' category actually matches - not the much smaller wheelchair share.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **Bohannon 2008** — Bohannon, R. (2008). Comfortable and maximum walking speed of adults aged 20-79 years: reference values and determinants.
  - *What it gives us:* Comfortable adult walking speed about 1.20 m/s with a standard deviation near 0.24 m/s.
  - *Caveat:* Citation carried from the project's evidence ledger; the standard deviation matters here because it is the spread this registry samples.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **Kuligowski NIST TN 1632** — Kuligowski, E. (2009). The process of human behavior in fires. NIST Technical Note 1632.
  - *What it gives us:* Sets out the perception-interpretation-decision-action model the TTS side of this project is built on.
  - *Caveat:* URL not yet recorded.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **Lovreglio et al. 2019** — Lovreglio, R., Kuligowski, E., Gwynne, S. and Boyce, K. (2019). A pre-evacuation database for use in egress simulations. Fire Safety Journal 105, 107-128. [https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf](https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf)
  - *What it gives us:* Fitted residential pre-evacuation distributions: good-alarm cluster Weibull scale 102.475 s shape 0.767 (n=149); poor-alarm or real-fire cluster Weibull scale 724.617 s shape 0.978 (n=78).
  - *Caveat:* The lognormal rows of the same table are internally inconsistent between units; use the Weibull or gamma rows. Citation carried from the project's evidence ledger.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **NIST NCSTAR 1-7** — Averill, J. et al. (2005). Occupant behavior, egress, and emergency communications. NIST NCSTAR 1-7, World Trade Center Investigation.
  - *What it gives us:* About 70% of occupants milled - sought information or conferred - before evacuating. 30-34% helped others; 23-32% searched for others. Cues such as smoke made people leave slower, not faster, because they triggered sense-making first.
  - *Caveat:* An office population, so group and family effects transfer poorly to a residential tower. URL not yet recorded.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **Proulx 1995** — Proulx, G. (1995). Evacuation time and movement in apartment buildings. Fire Safety Journal 24(3), 229-246. [https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0](https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0)
  - *What it gives us:* Four apartment drills. Alarm audibility dominated time to start (169 s audible vs 515 s poor). 62% evacuated in groups, mostly pairs or threes, at the slowest member's pace. Residents chose familiar stairs over the nearest.
  - *Caveat:* Announced drills in 6-7 storey buildings, so a real fire is likely slower. Citation carried from the project's evidence ledger; not yet read first-hand for this registry.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **SFPE / Fruin** — SFPE Handbook of Fire Protection Engineering, movement chapters, following Fruin's pedestrian planning work.
  - *What it gives us:* Able-bodied adults walk about 1.19-1.25 m/s on the level; older adults are markedly slower; children are slower; assisted occupants much slower.
  - *Caveat:* Named in a comment on the team's first workbook. Edition, chapter and page still to be pinned down.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **SIPP wheelchair use** — US Census Bureau, Survey of Income and Program Participation, wheelchair and mobility device use.
  - *What it gives us:* About 1.3 percent of the adult population uses a wheelchair.
  - *Caveat:* URL not yet recorded.
  - *Not yet read first-hand for this registry* — the citation was carried from the project's existing evidence ledger.
- **Team self-elicitation 2026** — Fire on Floor 12 - what do I do? First-person walkthrough by the project team, three positions relative to the fire floor.
  - *What it gives us:* Below the fire: alarm-only cue, assume a false alarm, check the hallway, the phone and the building group chat before leaving. On the fire floor: multi-sensory cues, alert the household, call 999/911 while moving, take the far stair. Above: cues delayed, contact people in the building, consider knocking on neighbours, shelter and seal if the stair is not clear.
  - *Caveat:* Recorded in context.md section 5. This is the only source for the building group chat as a warning channel, which is why those rows are INVENTED rather than ESTIMATE.
