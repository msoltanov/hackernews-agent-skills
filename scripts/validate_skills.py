#!/usr/bin/env python3
"""Check Agent Skills metadata without third-party dependencies.

This is a focused structural check for the simple YAML used in this repository,
not a full YAML parser or replacement for an Agent Skills host's own validation.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
FIELD = re.compile(r'([a-z][a-z0-9-]*):[ \t]+(.*)\Z')
CONTROL_CHARACTERS = re.compile(r'[\x00-\x1f\x7f-\x9f]')
NONSTRING_VALUES = {
    'null',
    '~',
    'true',
    'false',
    'yes',
    'no',
    'on',
    'off',
    'y',
    'n',
    '.nan',
    '.inf',
    '+.inf',
    '-.inf',
}


def parse_scalar(value: str) -> str:
    """Parse a supported single-line YAML string."""
    if not value or CONTROL_CHARACTERS.search(value):
        raise ValueError('expected a single-line string')
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str) or CONTROL_CHARACTERS.search(parsed):
            raise ValueError('expected a single-line string')
        return parsed
    if value.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", value):
            raise ValueError('invalid single-quoted string')
        return value[1:-1].replace("''", "'")
    if (
        value[0] in "-?:,[]{}#&*!|>'%@`"
        or re.search(r':(?:\s|$)|\s#', value)
        or value.lower() in NONSTRING_VALUES
        or re.match(r'[-+]?(?:[0-9]|\.[0-9])', value)
    ):
        raise ValueError('unsupported plain scalar; use a quoted string')
    return value


def check_skill(path: Path) -> list[str]:
    """Return metadata and structure errors for one skill."""
    errors: list[str] = []
    body = path.read_text(encoding='utf-8')
    if not body.startswith('---\n'):
        return [f'{path}: missing opening frontmatter delimiter']
    lines = body.splitlines()
    try:
        closing = lines.index('---', 1)
    except ValueError:
        return [f'{path}: invalid/empty frontmatter or instructions']
    if not '\n'.join(lines[closing + 1 :]).strip():
        return [f'{path}: invalid/empty frontmatter or instructions']
    metadata: dict[str, str] = {}
    for raw in lines[1:closing]:
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        field = FIELD.fullmatch(raw)
        if not field:
            errors.append(f'{path}: unsupported frontmatter line: {raw!r}')
            continue
        key, value = field.groups()
        if key in metadata:
            errors.append(f'{path}: duplicate frontmatter key {key!r}')
        try:
            metadata[key] = parse_scalar(value.strip())
        except ValueError as exc:
            errors.append(f'{path}: invalid {key}: {exc}')
    name = metadata.get('name', '')
    description = metadata.get('description', '')
    if not NAME.fullmatch(name) or len(name) > 64:
        errors.append(f'{path}: invalid name {name!r}')
    elif path.parent.name != name:
        errors.append(f'{path}: name must match directory {path.parent.name!r}')
    if not 1 <= len(description) <= 1024:
        errors.append(f'{path}: description length must be 1..1024')
    return errors


def main() -> int:
    """Check the seven bundled skills without network access."""
    files = sorted((ROOT / 'skills').glob('*/SKILL.md'))
    if len(files) != 7:
        print(f'Expected 7 skills; found {len(files)}', file=sys.stderr)
        return 1
    problems = [error for path in files for error in check_skill(path)]
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    print(f'Validated {len(files)} Agent Skills (metadata and structure).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
