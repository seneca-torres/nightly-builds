from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable


MONTH_PATTERN = (
    r"January|February|March|April|May|June|July|August|September|October|November|December"
)
ROLE_TERMS = [
    "Head Coach",
    "Assistant Coach",
    "Offensive Coordinator",
    "Defensive Coordinator",
    "Special Teams Coordinator",
    "Recruiting Coordinator",
    "Athletic Director",
    "Quarterbacks Coach",
    "Wide Receivers Coach",
    "Running Backs Coach",
    "Linebackers Coach",
    "Secondary Coach",
]
SCHOOL_SUFFIXES = [
    "University",
    "College",
    "State",
    "Tech",
    "Academy",
    "High School",
]
SCHOOL_ALIASES = [
    "Alabama",
    "Arkansas",
    "Auburn",
    "Clemson",
    "Duke",
    "Florida",
    "Georgia",
    "LSU",
    "Miami",
    "Michigan",
    "Ohio State",
    "Oklahoma",
    "Ole Miss",
    "Oregon",
    "Tennessee",
    "Texas",
    "USC",
]


@dataclass(frozen=True)
class Entity:
    kind: str
    label: str
    normalized: str


def slugify(value: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return lowered or "untitled-note"


def infer_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:80]
    return "Untitled Note"


def normalize_date(raw: str) -> str:
    cleaned = raw.strip().replace(",", "")
    formats = ["%B %d %Y", "%B %Y", "%m/%d/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if fmt == "%B %Y":
                return parsed.strftime("%Y-%m")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def dedupe(entities: Iterable[Entity]) -> list[Entity]:
    seen: set[tuple[str, str]] = set()
    result: list[Entity] = []
    for entity in entities:
        key = (entity.kind, entity.normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(entity)
    return result


def detect_dates(text: str) -> list[Entity]:
    pattern = re.compile(
        rf"\b(?:{MONTH_PATTERN}) \d{{1,2}}, \d{{4}}\b|\b(?:{MONTH_PATTERN}) \d{{4}}\b|\b\d{{1,2}}/\d{{1,2}}/\d{{2,4}}\b"
    )
    return [
        Entity("date", match.group(0), normalize_date(match.group(0)))
        for match in pattern.finditer(text)
    ]


def detect_roles(text: str) -> list[Entity]:
    entities: list[Entity] = []
    for role in ROLE_TERMS:
        pattern = re.compile(rf"\b{re.escape(role)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            entities.append(Entity("role", match.group(0), role))
    return entities


def detect_schools(text: str) -> list[Entity]:
    entities: list[Entity] = []
    suffix_pattern = "|".join(re.escape(suffix) for suffix in SCHOOL_SUFFIXES)
    school_pattern = re.compile(
        rf"\b(?:[A-Z][A-Za-z&.-]+(?:\s+[A-Z][A-Za-z&.-]+){{0,3}})\s+(?:{suffix_pattern})\b"
    )
    for match in school_pattern.finditer(text):
        entities.append(Entity("school", match.group(0), match.group(0)))
    for alias in SCHOOL_ALIASES:
        pattern = re.compile(rf"\b{re.escape(alias)}\b")
        for match in pattern.finditer(text):
            entities.append(Entity("school", match.group(0), alias))
    return entities


def detect_coaches(text: str) -> list[Entity]:
    entities: list[Entity] = []
    patterns = [
        re.compile(r"\bCoach\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"),
        re.compile(
            r"\b(?:Head Coach|Assistant Coach|Offensive Coordinator|Defensive Coordinator|Athletic Director|Quarterbacks Coach|Wide Receivers Coach|Running Backs Coach|Linebackers Coach)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        ),
        re.compile(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s+(?:head coach|assistant coach|offensive coordinator|defensive coordinator|athletic director)\b",
            re.IGNORECASE,
        ),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            name = match.group(1)
            entities.append(Entity("coach", name, name))
    return entities


def detect_entities(text: str) -> list[Entity]:
    return dedupe(
        [
            *detect_coaches(text),
            *detect_schools(text),
            *detect_dates(text),
            *detect_roles(text),
        ]
    )


def entity_sort_key(entity: Entity) -> tuple[int, str]:
    order = {"coach": 0, "school": 1, "date": 2, "role": 3}
    return (order.get(entity.kind, 99), entity.normalized.lower())


def apply_backlinks(text: str, entities: Iterable[Entity]) -> str:
    linked = text
    ordered = sorted(entities, key=lambda item: len(item.label), reverse=True)
    for entity in ordered:
        target = entity.normalized
        label = entity.label
        escaped = re.escape(label)
        pattern = re.compile(rf"(?<!\[\[){escaped}(?![^\[]*\]\])")
        replacement = f"[[{target}]]" if label == target else f"[[{target}|{label}]]"
        linked = pattern.sub(replacement, linked)
    return linked


def build_frontmatter(title: str, source: str, entities: Iterable[Entity]) -> str:
    grouped: dict[str, list[str]] = {"coaches": [], "schools": [], "dates": [], "roles": []}
    key_map = {
        "coach": "coaches",
        "school": "schools",
        "date": "dates",
        "role": "roles",
    }
    for entity in sorted(entities, key=entity_sort_key):
        grouped[key_map[entity.kind]].append(entity.normalized)

    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'source: "{source}"',
        "tags:",
        "  - broadcaster-notes",
    ]
    for key, values in grouped.items():
        lines.append(f"{key}:")
        if values:
            for value in values:
                lines.append(f'  - "{value}"')
        else:
            lines.append("  -")
    lines.append("---")
    return "\n".join(lines)


def convert_text(text: str, title: str | None = None, source: str = "plain-text") -> str:
    note_title = title or infer_title(text)
    entities = detect_entities(text)
    frontmatter = build_frontmatter(note_title, source, entities)
    body = apply_backlinks(text.strip(), entities)
    return f"{frontmatter}\n\n# {note_title}\n\n{body}\n"


def write_markdown(text: str, output_dir: Path, title: str | None = None, source: str = "plain-text") -> Path:
    note_title = title or infer_title(text)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slugify(note_title)}.md"
    output_path.write_text(convert_text(text, title=note_title, source=source), encoding="utf-8")
    return output_path