"""Run offline checks for the claude.ai zip builder."""

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

import build_skill_zips as builder


class BuildSkillZipsTest(unittest.TestCase):
    def build(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(['--output', str(output)]), 0)
        return output

    def test_each_skill_folder_is_the_zip_root(self) -> None:
        output = self.build()
        skills = sorted(
            path.parent.name for path in (builder.ROOT / 'skills').glob('*/SKILL.md')
        )
        self.assertEqual(sorted(path.stem for path in output.glob('*.zip')), skills)
        for name in skills:
            with self.subTest(skill=name):
                with zipfile.ZipFile(output / f'{name}.zip') as bundle:
                    names = bundle.namelist()
                self.assertIn(f'{name}/SKILL.md', names)
                self.assertIn(f'{name}/LICENSE', names)
                self.assertTrue(all(entry.startswith(f'{name}/') for entry in names))
                self.assertFalse(any('__pycache__' in entry for entry in names))

    def test_output_is_reproducible(self) -> None:
        first = self.build()
        second = self.build()
        for archive in sorted(first.glob('*.zip')):
            with self.subTest(archive=archive.name):
                self.assertEqual(
                    archive.read_bytes(), (second / archive.name).read_bytes()
                )


if __name__ == '__main__':
    unittest.main()
