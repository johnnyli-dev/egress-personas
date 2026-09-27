"""What a persona is: the closed registry of fields, and the closed registry of
attributes a Parameters row may filter on.

Two registries, deliberately separate:

* `FIELDS` — what a Parameters row may *write*. Adding a parameter that adjusts an
  existing field costs nothing; adding a genuinely new field costs one entry here.
* `ATTRS` — what a Parameters row may *read* in `applies_to`. Nothing in `ATTRS` is
  writable by a Parameters row. That is the rule that keeps composition order from
  leaking into filter results: if a filter could read a half-composed field, the
  answer would depend on the order rows happened to be applied in.

Fields in the `body` block carry the simulation's own names
(FireEgress-3dsim, crates/fe-core/src/agent.rs:257-275) so that the loader reserved
by its roadmap item 3.2 needs no translation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: `default = INHERIT` means: leave the field out of the JSON entirely, so the
#: simulation's own sourced rules decide it. This is the reason a sheet that knows
#: nothing about, say, stair recovery cannot silently flatten a fitted distribution.
INHERIT = "inherit"

BLOCKS = ("identity", "body", "situation", "knowledge", "dispositions")


@dataclass(frozen=True)
class FieldSpec:
    path: str
    dtype: str  # float | int | bool | enum | str
    unit: str = ""
    default: Any = INHERIT
    lo: float | None = None
    hi: float | None = None
    decimals: int | None = None
    vocab: str = ""
    what: str = ""


def _f(path, unit="", default=INHERIT, lo=None, hi=None, decimals=4, what=""):
    return FieldSpec(path, "float", unit, default, lo, hi, decimals, "", what)


def _unit01(path, default, what):
    return FieldSpec(path, "float", "0-1", default, 0.0, 1.0, 3, "", what)


#: Every field a Parameters row may write, keyed by dotted path.
FIELDS: dict[str, FieldSpec] = {s.path: s for s in [
    # --- body: the numbers the simulation acts on ------------------------------
    _f("body.base_speed", "m/s", INHERIT, 0.1, 2.5, 3,
       "Free walking speed on the level, before crowding and smoke."),
    _f("body.congestion_sensitivity", "factor", INHERIT, 0.0, 5.0, 3,
       "How strongly a crowd ahead pushes this person's route choice away."),
    _f("body.stair_fatigue_rate", "per storey", INHERIT, 0.0, 1.0, 5,
       "Tiredness gained per storey descended."),
    _f("body.stair_recovery_rate", "per s", INHERIT, 0.0, 1.0, 5,
       "Tiredness shed per second of rest."),
    _f("body.patience_s", "s", INHERIT, 0.0, 1800.0, 1,
       "Seconds stuck behind a blockage before giving up on a staircase."),
    _f("body.smoke_limit_m", "m", INHERIT, 0.0, 30.0, 2,
       "Visibility below which this person turns back. 0 means never."),
    _f("body.medical_events_per_hour", "per h", INHERIT, 0.0, 1.0, 9,
       "Rate of an incapacitating cardiac event while evacuating."),
    _f("body.fed_tolerance", "factor", INHERIT, 0.1, 5.0, 3,
       "Individual multiplier on the smoke dose this person can take."),
    _f("body.delay_s", "s", INHERIT, 0.0, 7200.0, 1,
       "Pre-movement time. Left absent unless a sourced row sets it: the "
       "simulation fits this from data and a point value would be a regression."),
    FieldSpec("body.tries_other_stair", "bool", "", INHERIT, None, None, None, "",
              "On turning back, tries the other staircase rather than going home."),

    # --- knowledge: what they know about the building (wayfinding) -------------
    _unit01("knowledge.floorplan_familiarity", 0.5,
            "How well they know the building's routes, 0 a first-day visitor, 1 a caretaker."),
    FieldSpec("knowledge.habitual_stair", "enum", "", "none", None, None, None, "stair",
              "The staircase they use by habit, which they will reach for under stress."),
    FieldSpec("knowledge.knows_second_stair", "bool", "", False, None, None, None, "",
              "Whether they know a second staircase exists at all."),
    FieldSpec("knowledge.prior_false_alarms", "int", "count", 0, 0, 50, None, "",
              "False alarms lived through here. Raises the bar for believing this one."),
    FieldSpec("knowledge.fire_safety_training", "bool", "", False, None, None, None, "",
              "Any drill or training, which shows up as faster interpretation."),

    # --- dispositions: the decision tendencies that drive TTS ------------------
    _unit01("dispositions.mill_tendency", 0.7,
            "Tendency to seek information and confer before acting, rather than leave. "
            "NIST found about 70% of WTC occupants milled."),
    _unit01("dispositions.seeks_confirmation", 0.5,
            "Need for a second cue — a neighbour, a siren, an announcement — before moving."),
    _unit01("dispositions.authority_compliance", 0.6,
            "Willingness to do what an alarm, an announcement or a firefighter says."),
    _unit01("dispositions.altruism", 0.3,
            "Willingness to spend their own time helping or warning others."),
    _unit01("dispositions.risk_tolerance", 0.4,
            "Willingness to enter a route they can see is degraded."),
    _unit01("dispositions.leadership", 0.3,
            "Tendency to direct others rather than follow."),

    # --- situation: one writable field; the rest is the sampler's --------------
    FieldSpec("situation.alarm_audible", "bool", "", True, None, None, None, "",
              "Whether the alarm can be heard where this person is. Proulx found "
              "audibility the single largest driver of pre-movement time."),
]}

#: Fields the sampler owns and a Parameters row may not write. Kept here so the
#: validator can give a better message than "unknown target".
SAMPLER_OWNED = frozenset({
    "identity.age_years", "identity.sex", "identity.household_role",
    "identity.tenure_years", "body.mobility", "body.can_use_stairs",
    "body.limiting_condition", "situation.unit", "situation.floor_label",
    "situation.sim_floor", "situation.home_tile", "situation.present",
    "situation.asleep", "situation.activity",
})


@dataclass(frozen=True)
class AttrSpec:
    name: str
    dtype: str
    vocab: str = ""
    what: str = ""


#: Everything `applies_to` may read. All sampler-owned or scenario-level, never
#: written by a Parameters row.
ATTRS: dict[str, AttrSpec] = {a.name: a for a in [
    AttrSpec("age_years", "int", "", "Age in years."),
    AttrSpec("age_band", "enum", "age_band", "Age bucket, derived from age_years."),
    AttrSpec("sex", "enum", "sex", "Recorded sex."),
    AttrSpec("sim_agent_type", "enum", "sim_agent_type",
             "The simulation's occupant class, derived from age and mobility."),
    AttrSpec("mobility", "enum", "mobility", "Mobility category."),
    AttrSpec("household_role", "enum", "household_role", "Role within the flat."),
    AttrSpec("household_size", "int", "", "People in this flat."),
    AttrSpec("tenure_years", "float", "", "Years lived in the building."),
    AttrSpec("present", "bool", "", "Whether they are in the building at t=0."),
    AttrSpec("asleep", "bool", "", "Whether they are asleep at t=0."),
    AttrSpec("has_pet", "bool", "", "Whether this flat keeps a pet."),
    AttrSpec("has_children", "bool", "", "Whether this flat holds anyone under 18."),
    AttrSpec("lives_alone", "bool", "", "Household of one."),
    AttrSpec("unit", "str", "", "Unit label, e.g. 4A."),
    AttrSpec("unit_letter", "enum", "unit_letter", "Unit letter within the floor."),
    AttrSpec("floor_label", "int", "", "Floor as the building names it (no 13)."),
    AttrSpec("sim_floor", "int", "", "Floor as the simulation indexes it."),
    AttrSpec("on_fire_floor", "bool", "", "Whether the fire starts on their floor."),
    AttrSpec("above_fire", "bool", "", "Whether they are above the fire floor."),
    AttrSpec("time_of_day", "enum", "time_of_day", "Scenario setting."),
    AttrSpec("alarm_quality", "enum", "alarm_quality", "Scenario setting."),
]}


@dataclass
class Persona:
    """One occupant. Blocks are plain dicts so a field is addressable by path."""

    key: str
    id: str = ""
    index: int = -1
    identity: dict[str, Any] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    situation: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, Any] = field(default_factory=dict)
    dispositions: dict[str, Any] = field(default_factory=dict)
    commitments: list[dict[str, Any]] = field(default_factory=list)
    ties: list[dict[str, Any]] = field(default_factory=list)
    household: str = ""
    household_index: int | None = None
    case_id: str = ""
    narrative: str = ""
    #: Fields pinned by a Cases row: never overwritten, recorded in provenance.
    pinned: set[str] = field(default_factory=set)

    def get(self, path: str, default: Any = None) -> Any:
        block, _, name = path.partition(".")
        return getattr(self, block, {}).get(name, default)

    def set(self, path: str, value: Any) -> None:
        block, _, name = path.partition(".")
        getattr(self, block)[name] = value

    def has(self, path: str) -> bool:
        block, _, name = path.partition(".")
        return name in getattr(self, block, {})
