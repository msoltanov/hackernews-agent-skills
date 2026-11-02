#!/usr/bin/env python3
"""Build one claude.ai upload zip per skill.

Each archive holds the skill folder at its root, as claude.ai requires:
``hn-discover.zip`` contains ``hn-discover/SKILL.md``. Entries use a fixed
timestamp and sorted order, so the same sources give the same bytes.
"""

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
EXCLUDED_DIRECTORIES = {'__pycache__', '.pytest_cache', '.ruff_cache'}
EXCLUDED_SUFFIXES = {'.pyc', '.pyo'}


def skill_files(skill: Path) -> list[Path]:
    """Return the files to package for one skill, in sorted order."""
    files = []
    for path in sorted(skill.rglob('*')):
        relative = path.relative_to(skill)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in EXCLUDED_SUFFIXES:
            files.append(path)
    return files


def build_zip(skill: Path, output: Path) -> Path:
    """Write ``<output>/<skill>.zip`` with the skill folder at its root."""
    archive = output / f'{skill.name}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in skill_files(skill):
            name = f'{skill.name}/{path.relative_to(skill).as_posix()}'
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, path.read_bytes())
    return archive


def main(argv: list[str] | None = None) -> int:
    """Build zips for every skill under ``skills/``."""
    parser = argparse.ArgumentParser(description='Build claude.ai skill zips.')
    parser.add_argument(
        '--output', type=Path, default=ROOT / 'dist', help='output directory'
    )
    args = parser.parse_args(argv)
    skills = sorted(path.parent for path in (ROOT / 'skills').glob('*/SKILL.md'))
    if not skills:
        print('No skills found.', file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        print(build_zip(skill, args.output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
