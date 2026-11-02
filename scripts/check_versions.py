#!/usr/bin/env python3
"""Check that every release version in the repository is the same.

The plugin manifest, the marketplace entry, the README version line, and the
newest CHANGELOG heading must name one version. With ``--tag``, the git tag
must be that version with a ``v`` prefix.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r'\d+\.\d+\.\d+\Z')
README_VERSION = re.compile(r'^Version: `v(\S+)`\.$', re.MULTILINE)
CHANGELOG_VERSION = re.compile(r'^## v(\S+)$', re.MULTILINE)


def read_json(path: Path) -> dict:
    """Return a JSON object from a file."""
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path}: expected a JSON object')
    return data


def collect_versions(root: Path) -> dict[str, str]:
    """Return each version source and the version it names."""
    plugin = read_json(root / '.claude-plugin' / 'plugin.json')
    marketplace = read_json(root / '.claude-plugin' / 'marketplace.json')
    name = plugin.get('name')
    entries = [
        entry
        for entry in marketplace.get('plugins', [])
        if isinstance(entry, dict) and entry.get('name') == name
    ]
    if len(entries) != 1:
        raise ValueError(f'marketplace.json must list plugin {name!r} once')
    readme = README_VERSION.search((root / 'README.md').read_text(encoding='utf-8'))
    changelog = CHANGELOG_VERSION.search(
        (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    )
    if not readme:
        raise ValueError('README.md has no "Version: `vX.Y.Z`." line')
    if not changelog:
        raise ValueError('CHANGELOG.md has no "## vX.Y.Z" heading')
    return {
        'plugin.json': str(plugin.get('version')),
        'marketplace.json': str(entries[0].get('version')),
        'README.md': readme.group(1),
        'CHANGELOG.md': changelog.group(1),
    }


def check(root: Path, tag: str | None = None) -> list[str]:
    """Return version errors for the repository at ``root``."""
    try:
        versions = collect_versions(root)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    errors = [
        f'{source}: {version!r} is not X.Y.Z'
        for source, version in versions.items()
        if not SEMVER.match(version)
    ]
    if len(set(versions.values())) != 1:
        found = ', '.join(f'{source} {version}' for source, version in versions.items())
        errors.append(f'versions differ: {found}')
    expected = f'v{versions["plugin.json"]}'
    if tag is not None and tag != expected:
        errors.append(f'tag {tag!r} does not match version {expected!r}')
    return errors


def main(argv: list[str] | None = None) -> int:
    """Check the repository versions and print the result."""
    parser = argparse.ArgumentParser(description='Check release versions.')
    parser.add_argument('--tag', help='git tag to compare, for example v1.0.7')
    args = parser.parse_args(argv)
    errors = check(ROOT, args.tag)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Release versions match.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
