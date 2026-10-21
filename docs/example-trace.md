# From the literature to a number the model acts on

Engine: **FireEgress 3D** (`fire_egress_3d`) · 151 residents

**34 of 42 chains reach the engine.** A chain is one heuristic, through the persona field it writes, through an effect that consumes that field, to a canonical output and the engine's own name for it.

The label on a chain is its **weakest link**. A value read off a sourced distribution at a quantile decided by an invented ordering is INVENTED — reporting it as SOURCED would launder a guess into a citation.

| end-to-end evidence | chains |
|---|---|
| SOURCED | 2 |
| ESTIMATE | 20 |
| INVENTED | 12 |

## Chains that reach the engine

| heuristic | writes | effect | how | output | engine field | weakest link |
|---|---|---|---|---|---|---|
| `P001` Walking speed - working-age adult | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **SOURCED** |
| `P005` Walking speed - ambulatory difficulty | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **SOURCED** |
| `P002` Walking speed - 65 and over | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **ESTIMATE** |
| `P003` Walking speed - under 18 | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **ESTIMATE** |
| `P004` Walking speed - wheelchair | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **ESTIMATE** |
| `P006` Carrying or handling a pet | `base_speed` | `E010` | carries it across | walk_speed_mps | `base_speed` | **ESTIMATE** |
| `P010` Milling - baseline | `mill_tendency` | `E001` | weighs it +1 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P011` Milling - a new tenant has fewer people to confer with | `mill_tendency` | `E001` | weighs it +1 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P012` Milling - living alone | `mill_tendency` | `E001` | weighs it +1 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P020` Seeks a second cue before moving | `seeks_confirmation` | `E001` | weighs it +0.8 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P021` Seeks a second cue - poor alarm | `seeks_confirmation` | `E001` | weighs it +0.8 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P022` Compliance with instructions | `authority_compliance` | `E001` | weighs it -0.7 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P022` Compliance with instructions | `authority_compliance` | `E030` | weighs it -0.2 | smoke_turnback_m | `smoke_limit_m` | **ESTIMATE** |
| `P023` Altruism | `altruism` | `E001` | weighs it +0.3 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P030` Knows the building - new tenant | `floorplan_familiarity` | `E030` | weighs it +0.4 | smoke_turnback_m | `smoke_limit_m` | **ESTIMATE** |
| `P030` Knows the building - new tenant | `floorplan_familiarity` | `E040` | weighs it +0.8 | tries_alternate_route | `tries_other_stair` | **ESTIMATE** |
| `P031` Knows the building - one to five years | `floorplan_familiarity` | `E030` | weighs it +0.4 | smoke_turnback_m | `smoke_limit_m` | **ESTIMATE** |
| `P031` Knows the building - one to five years | `floorplan_familiarity` | `E040` | weighs it +0.8 | tries_alternate_route | `tries_other_stair` | **ESTIMATE** |
| `P032` Knows the building - five years or more | `floorplan_familiarity` | `E030` | weighs it +0.4 | smoke_turnback_m | `smoke_limit_m` | **ESTIMATE** |
| `P032` Knows the building - five years or more | `floorplan_familiarity` | `E040` | weighs it +0.8 | tries_alternate_route | `tries_other_stair` | **ESTIMATE** |
| `P040` Hears the alarm - good alarm | `alarm_audible` | `E001` | weighs it -1.2 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P041` Hears the alarm - poor alarm | `alarm_audible` | `E001` | weighs it -1.2 | premovement_time_s | `delay_s` | **ESTIMATE** |
| `P022` Compliance with instructions | `authority_compliance` | `E020` | weighs it +0.4 | queue_patience_s | `patience_s` | **INVENTED** |
| `P026` Risk tolerance | `risk_tolerance` | `E020` | weighs it -1 | queue_patience_s | `patience_s` | **INVENTED** |
| `P026` Risk tolerance | `risk_tolerance` | `E030` | weighs it +1 | smoke_turnback_m | `smoke_limit_m` | **INVENTED** |
| `P026` Risk tolerance | `risk_tolerance` | `E040` | weighs it +0.6 | tries_alternate_route | `tries_other_stair` | **INVENTED** |
| `P027` Risk tolerance - 65 and over | `risk_tolerance` | `E020` | weighs it -1 | queue_patience_s | `patience_s` | **INVENTED** |
| `P027` Risk tolerance - 65 and over | `risk_tolerance` | `E030` | weighs it +1 | smoke_turnback_m | `smoke_limit_m` | **INVENTED** |
| `P027` Risk tolerance - 65 and over | `risk_tolerance` | `E040` | weighs it +0.6 | tries_alternate_route | `tries_other_stair` | **INVENTED** |
| `P033` Knows a second staircase exists - new tenant | `knows_second_stair` | `E041` | gates on it | tries_alternate_route | `tries_other_stair` | **INVENTED** |
| `P034` Knows a second staircase exists - established resident | `knows_second_stair` | `E041` | gates on it | tries_alternate_route | `tries_other_stair` | **INVENTED** |
| `P036` False alarms lived through - one to five years | `prior_false_alarms` | `E001` | weighs it +0.06 | premovement_time_s | `delay_s` | **INVENTED** |
| `P037` False alarms lived through - five years or more | `prior_false_alarms` | `E001` | weighs it +0.06 | premovement_time_s | `delay_s` | **INVENTED** |
| `P038` Fire safety training | `fire_safety_training` | `E001` | weighs it -0.5 | premovement_time_s | `delay_s` | **INVENTED** |

## Chains that stop short

Each of these is a heuristic that currently changes nothing the engine does. That is worth knowing per row rather than in aggregate: some are waiting on the engine, and some on a number nobody has published.

| heuristic | writes | stops because |
|---|---|---|
| `P008` Tries the other staircase after turning back | `tries_other_stair` | no effect reads this field, so it changes nothing a model acts on |
| `P025` Leadership - head of household | `leadership` | no effect reads this field, so it changes nothing a model acts on |
| `P035` Habitual staircase | `habitual_stair` | No route-habit bias is modelled. |
| `P007` Patience behind a blockage | `patience_s` | no effect reads this field, so it changes nothing a model acts on |
| `P024` Leadership | `leadership` | no effect reads this field, so it changes nothing a model acts on |
| `P030` Knows the building - new tenant | `floorplan_familiarity` | the output has no published reference distribution, so the effect has nothing to read a value off |
| `P031` Knows the building - one to five years | `floorplan_familiarity` | the output has no published reference distribution, so the effect has nothing to read a value off |
| `P032` Knows the building - five years or more | `floorplan_familiarity` | the output has no published reference distribution, so the effect has nothing to read a value off |

## Did the published distributions survive?

The quantile mechanism claims the persona decides the ordering while the literature keeps the shape. This is that claim, measured.

| output | reference | published mean | realized | |
|---|---|---|---|---|
| premovement_time_s | `premovement_good` | 119.807 | 119.274 s | ok |
| queue_patience_s | `queue_patience` | 60.0 | 60.0 s | ok |
| smoke_turnback_m | `smoke_turnback` | 3.252 | 3.252 m | ok |

## What FireEgress 3D cannot use

Outputs the compiler produces that this engine has nowhere to put. Listed rather than dropped, so the gap is attributable to the engine rather than looking like a gap in the model.

- **gather_time_s** — AgentState::Gathering exists in the enum and is never entered (fsm.rs:11); belongings.rs is a doc-only stub.
- **preferred_route** — No route-habit bias is modelled.
- **route_confusion** — perception.stair_confusion_chance is global, not per agent (rules.rs:692). docs/sources/B_behaviour.md recommends making it per-agent, which is what this would feed.
- **warns_n_neighbours** — groups.rs is a doc-only stub; warning across households is not modelled.
