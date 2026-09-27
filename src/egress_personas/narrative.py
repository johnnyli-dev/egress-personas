"""The text card, rendered from the structured blocks.

Deterministic on purpose: the same snapshot and seed must give the same words, so
there is no model call here. A card is assembled from clauses that each read one or
two fields, so it can never assert something the persona does not carry.

The card is what an LLM agent would be conditioned on, and what a human reads to
judge whether the sampler is producing people or noise.
"""

from __future__ import annotations

from typing import Any

BANDS = {
    "0_17": "a child", "18_34": "in their twenties or early thirties",
    "35_49": "in their late thirties or forties", "50_64": "in their fifties or sixties",
    "65_74": "in their late sixties or early seventies", "75_plus": "in their late seventies or older",
}
MOBILITY = {
    "none": "",
    "ambulatory_difficulty": "walk with difficulty and tire on stairs",
    "walker_cane": "use a walker or a cane, so stairs are slow and tiring",
    "wheelchair": "use a wheelchair and cannot use the stairs at all",
}
ROLE = {
    "head": "heads the household", "partner": "is a partner in the household",
    "child": "is a child of the household",
    "parent": "is an older parent living with the household",
    "lodger": "shares the flat", "carer": "lives in to help another member",
    "other": "lives there",
}


def _years(v: float | None) -> str:
    if v is None:
        return "an unrecorded length of time"
    if v < 1:
        return "less than a year"
    if v < 2:
        return "about a year"
    return f"{int(round(v))} years"


def _band(x: float | None, low: str, mid: str, high: str) -> str:
    if x is None:
        return mid
    return low if x < 0.34 else (mid if x < 0.67 else high)


def _finish(parts: list[str], person: Any, housemates: list[Any]) -> str:
    """The closing clauses every card ends with: the moment, and who they know."""
    sit = person.situation
    if sit.get("present") is False:
        parts.append("They are not in the building when the fire starts.")
        return " ".join(parts)
    if sit.get("asleep"):
        parts.append("At the moment the fire starts they are asleep.")
    elif sit.get("activity") == "out_of_flat":
        parts.append("At the moment the fire starts they are out in the shared space "
                     "of their floor.")
    else:
        parts.append("At the moment the fire starts they are awake at home.")
    if sit.get("alarm_audible") is False:
        parts.append("The alarm cannot be heard where they are.")
    if person.commitments:
        names = []
        for c in person.commitments:
            what = c.get("what") or c.get("kind") or "something"
            names.append(what if what.startswith("the ") else f"the {what}")
        parts.append(f"They will not leave without {' and '.join(names)}.")
    knocks = sum(1 for t in person.ties if t["kind"] == "knock")
    phones = sum(1 for t in person.ties if t["kind"] == "phone")
    chat = any(t["kind"] == "group_chat" for t in person.ties)
    social: list[str] = []
    if knocks:
        social.append(f"{knocks} neighbour{'s' if knocks > 1 else ''} they would "
                      f"knock for")
    if phones:
        social.append(f"{phones} {'people' if phones > 1 else 'person'} in the "
                      f"building they would phone")
    if chat:
        social.append("the building group chat")
    if social:
        parts.append(f"They have {', '.join(social)}.")
    elif not housemates:
        parts.append("They know nobody else in the building.")
    return " ".join(parts)


def render(person: Any, household: Any, everyone: list[Any]) -> str:
    """One paragraph. Reads only fields the persona actually has."""
    ident, body, sit = person.identity, person.body, person.situation
    age = ident.get("age_years")
    parts: list[str] = []

    name = ident.get("name")
    age_text = str(age) if age is not None else BANDS.get(
        ident.get("age_band"), "an adult")
    subject = f"{name}, {age_text}," if name else f"A resident of {age_text}"
    if not name:
        subject = f"Somebody of {age_text}"
    parts.append(
        f"{subject} has lived in {sit.get('unit', 'the building')} for "
        f"{_years(ident.get('tenure_years'))} and "
        f"{ROLE.get(ident.get('household_role'), 'lives there')}."
    )

    mob = MOBILITY.get(body.get("mobility", "none"), "")
    if mob:
        parts.append(f"They {mob}.")

    housemates = [q for q in everyone if q.household == person.household and q is not person]
    if housemates:
        kids = [q for q in housemates if (q.identity.get("age_years") or 99) < 18]
        others = len(housemates) - len(kids)
        bits = []
        if others:
            bits.append(f"{others} other adult{'s' if others > 1 else ''}")
        if kids:
            bits.append(f"{len(kids)} child{'ren' if len(kids) > 1 else ''}")
        parts.append(f"They share the flat with {' and '.join(bits)}.")
    else:
        parts.append("They live alone.")

    fam = person.knowledge.get("floorplan_familiarity")
    second = person.knowledge.get("knows_second_stair")
    know = _band(fam, "barely know the building's layout",
                 "know the building reasonably well", "know the building well")
    stair = person.knowledge.get("habitual_stair")
    tail = ""
    if second is False:
        tail = ", and do not know there is a second staircase"
    elif stair in ("north", "south"):
        tail = f", and take the {stair} stair by habit"
    parts.append(f"They {know}{tail}.")

    false_alarms = person.knowledge.get("prior_false_alarms")
    if false_alarms:
        parts.append(
            f"{'One false alarm' if false_alarms == 1 else f'{false_alarms} false alarms'} "
            f"here already, so a bell alone does not mean much to them."
        )

    d = person.dispositions
    if (age or 99) < 12:
        parts.append("They are too young to decide anything for themselves and will go "
                     "wherever the adults in the flat take them.")
        return _finish(parts, person, housemates)
    mill = _band(d.get("mill_tendency"), "tend to act rather than confer",
                 "will usually check with somebody before acting",
                 "will look for information and talk to people before moving")
    alt = _band(d.get("altruism"), "and look after themselves first",
                "and would help if asked", "and would go out of their way to help others")
    parts.append(f"They {mill}, {alt}.")

    if d.get("leadership", 0) >= 0.67:
        parts.append("In a corridor full of unsure neighbours, this is who starts giving directions.")

    return _finish(parts, person, housemates)
