"""Run offline checks for the release version checker."""

import json
import tempfile
import unittest
from pathlib import Path

import check_versions as checker


class CheckVersionsTest(unittest.TestCase):
    def make_repo(
        self,
        plugin: str = '1.2.3',
        marketplace: str = '1.2.3',
        readme: str = '1.2.3',
        changelog: str = '1.2.3',
    ) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        manifests = root / '.claude-plugin'
        manifests.mkdir()
        (manifests / 'plugin.json').write_text(
            json.dumps({'name': 'sample', 'version': plugin}), encoding='utf-8'
        )
        (manifests / 'marketplace.json').write_text(
            json.dumps(
                {
                    'name': 'market',
                    'plugins': [
                        {'name': 'other', 'version': '9.9.9'},
                        {'name': 'sample', 'version': marketplace},
                    ],
                }
            ),
            encoding='utf-8',
        )
        (root / 'README.md').write_text(
            f'# Sample\n\nVersion: `v{readme}`.\n', encoding='utf-8'
        )
        (root / 'CHANGELOG.md').write_text(
            f'# Changelog\n\n## v{changelog}\n\n- Change.\n\n## v0.0.1\n',
            encoding='utf-8',
        )
        return root

    def test_matching_versions_pass(self) -> None:
        self.assertEqual(checker.check(self.make_repo()), [])

    def test_matching_tag_passes(self) -> None:
        self.assertEqual(checker.check(self.make_repo(), 'v1.2.3'), [])

    def test_each_mismatched_source_fails(self) -> None:
        for field in ('plugin', 'marketplace', 'readme', 'changelog'):
            with self.subTest(source=field):
                root = self.make_repo(**{field: '1.2.4'})
                self.assertTrue(checker.check(root))

    def test_wrong_tag_fails(self) -> None:
        errors = checker.check(self.make_repo(), 'v1.2.4')
        self.assertTrue(any('tag' in error for error in errors))

    def test_tag_without_prefix_fails(self) -> None:
        self.assertTrue(checker.check(self.make_repo(), '1.2.3'))

    def test_non_semver_fails(self) -> None:
        root = self.make_repo('1.2', '1.2', '1.2', '1.2')
        self.assertTrue(checker.check(root))

    def test_missing_readme_line_fails(self) -> None:
        root = self.make_repo()
        (root / 'README.md').write_text('# Sample\n', encoding='utf-8')
        self.assertTrue(checker.check(root))

    def test_repository_versions_match(self) -> None:
        self.assertEqual(checker.check(checker.ROOT), [])


if __name__ == '__main__':
    unittest.main()
