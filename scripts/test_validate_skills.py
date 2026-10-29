"""Run offline checks for supported skill metadata."""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_skills as validator


class SkillMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'sample' / 'SKILL.md'
        self.path.parent.mkdir()

    def write_skill(self, metadata: str, instructions: str = 'Instructions.') -> None:
        self.path.write_text(
            f'---\n{metadata}\n---\n{instructions}\n', encoding='utf-8'
        )

    def test_current_scalar_format_is_valid(self) -> None:
        self.write_skill(
            "name: sample\ndescription: Review the user's source.\nlicense: MIT"
        )
        self.assertEqual(validator.check_skill(self.path), [])

    def test_empty_block_description_is_rejected(self) -> None:
        self.write_skill('name: sample\ndescription: |')
        self.assertTrue(validator.check_skill(self.path))

    def test_unquoted_colon_description_is_rejected(self) -> None:
        self.write_skill('name: sample\ndescription: invalid: yaml')
        self.assertTrue(validator.check_skill(self.path))

    def test_mapping_separator_requires_whitespace(self) -> None:
        self.write_skill('name:sample\ndescription:Invalid mapping')
        self.assertTrue(validator.check_skill(self.path))

    def test_nonstring_description_is_rejected(self) -> None:
        for value in (
            'true',
            'false',
            'null',
            '~',
            '123',
            '.nan',
            '.Inf',
            '[one]',
            '{key: value}',
        ):
            with self.subTest(value=value):
                self.write_skill(f'name: sample\ndescription: {value}')
                self.assertTrue(validator.check_skill(self.path))

    def test_unclosed_quotes_are_rejected(self) -> None:
        for value in ('"unfinished', "'unfinished"):
            with self.subTest(value=value):
                self.write_skill(f'name: sample\ndescription: {value}')
                self.assertTrue(validator.check_skill(self.path))

    def test_control_characters_are_rejected(self) -> None:
        for value in ('plain\x00value', "'quoted\x00value'"):
            with self.subTest(value=value):
                self.write_skill(f'name: sample\ndescription: {value}')
                self.assertTrue(validator.check_skill(self.path))

    def test_quoted_strings_allow_colons_and_hashes(self) -> None:
        for value in ('"Review: evidence #1"', "'Review the user''s source: evidence'"):
            with self.subTest(value=value):
                self.write_skill(f'name: sample\ndescription: {value}')
                self.assertEqual(validator.check_skill(self.path), [])

    def test_scalar_with_dashes_does_not_close_frontmatter(self) -> None:
        self.write_skill('name: sample\ndescription: Notes---')
        self.assertEqual(validator.check_skill(self.path), [])

    def test_duplicate_keys_are_rejected(self) -> None:
        self.write_skill('name: sample\ndescription: First\ndescription: Second')
        self.assertTrue(validator.check_skill(self.path))

    def test_directory_name_must_match(self) -> None:
        self.write_skill('name: different\ndescription: Valid description')
        self.assertTrue(validator.check_skill(self.path))

    def test_empty_instructions_are_rejected(self) -> None:
        self.write_skill('name: sample\ndescription: Valid description', '')
        self.assertTrue(validator.check_skill(self.path))

    def test_inline_comment_does_not_count_as_description(self) -> None:
        self.write_skill('name: sample\ndescription: # no value')
        self.assertTrue(validator.check_skill(self.path))

    def test_main_fails_on_invalid_skill(self) -> None:
        root = Path(self.directory.name)
        skills = root / 'skills'
        for index in range(7):
            name = f'sample-{index}'
            directory = skills / name
            directory.mkdir(parents=True)
            description = '|' if index == 0 else 'Valid description'
            (directory / 'SKILL.md').write_text(
                f'---\nname: {name}\ndescription: {description}\n---\nInstructions.\n',
                encoding='utf-8',
            )
        with (
            patch.object(validator, 'ROOT', root),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(validator.main(), 1)


class SkillPackagingTest(unittest.TestCase):
    def test_standalone_copies_include_complete_license(self) -> None:
        expected = (validator.ROOT / 'LICENSE').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory)
            for skill in sorted((validator.ROOT / 'skills').iterdir()):
                if not skill.is_dir():
                    continue
                with self.subTest(skill=skill.name):
                    destination = installed / skill.name
                    shutil.copytree(skill, destination)
                    bundled_license = destination / 'LICENSE'
                    self.assertTrue(
                        bundled_license.is_file(), 'Standalone copy is missing LICENSE'
                    )
                    self.assertEqual(bundled_license.read_bytes(), expected)


if __name__ == '__main__':
    unittest.main()
