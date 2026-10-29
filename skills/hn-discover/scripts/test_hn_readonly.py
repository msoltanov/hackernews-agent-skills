"""Run offline discovery checks without network access."""

import contextlib
import io
import json
import unittest
from http.client import IncompleteRead
from unittest.mock import MagicMock, patch

import hn_readonly as hn


class TestReadOnlyHelper(unittest.TestCase):
    def test_info_flags_are_separate(self) -> None:
        value = hn.info(
            {'id': 42, 'title': 'A &amp; B', 'type': 'story', 'time': 0, 'dead': True}
        )
        assert value is not None
        self.assertEqual(value['title'], 'A & B')
        self.assertTrue(value['dead'])
        self.assertFalse(value['deleted'])
        self.assertEqual(value['hn_url'], 'https://news.ycombinator.com/item?id=42')

    @patch.object(hn, 'get_json')
    def test_feed_is_read_only(self, request: MagicMock) -> None:
        request.side_effect = [
            [1, 2],
            {'id': 1, 'title': 'One'},
            {'id': 2, 'title': 'Two', 'deleted': True},
        ]
        data = hn.run_feed('new', 2)
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(request.call_count, 3)
        self.assertTrue(data['items'][1]['deleted'])

    @patch.object(hn, 'get_json', return_value=None)
    def test_missing_user_is_not_a_ban_claim(self, _request: MagicMock) -> None:
        self.assertEqual(
            hn.run_user('nobody', 4)['error'], 'Public user data not found'
        )

    def test_arg_range(self) -> None:
        with self.assertRaises(SystemExit):
            hn.parse_args(['feed', '--limit', '999'])

    def test_json_render(self) -> None:
        self.assertIn('"feed": "top"', hn.render({'feed': 'top', 'items': []}, 'json'))


class TestReadOnlyRegressions(unittest.TestCase):
    def test_unicode_output_uses_utf8_for_redirected_streams(self) -> None:
        record = {'id': 1, 'type': 'story', 'title': 'Launch \U0001f680', 'kids': []}
        for output_format in ('json', 'markdown'):
            with self.subTest(output_format=output_format):
                with (
                    io.BytesIO() as buffer,
                    io.TextIOWrapper(buffer, encoding='cp1252') as output,
                    patch.object(hn, 'get_json', return_value=record),
                    contextlib.redirect_stdout(output),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    status = hn.main(['item', '1', '--format', output_format])
                    output.flush()
                    rendered = buffer.getvalue().decode('utf-8')

                self.assertEqual(status, 0)
                self.assertIn('Launch \U0001f680', rendered)
                if output_format == 'json':
                    self.assertEqual(
                        json.loads(rendered)['item']['title'], record['title']
                    )

    @patch.object(hn, 'get_json', return_value=None)
    def test_missing_item_returns_failure(self, _request: MagicMock) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hn.main(['item', '999']), 1)

    @patch.object(hn, 'get_json', return_value=None)
    def test_missing_user_returns_failure(self, _request: MagicMock) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(hn.main(['user', 'nobody']), 1)

    def test_item_body_preserves_literal_entities_and_code_indentation(self) -> None:
        item = hn.info(
            {
                'id': 42,
                'type': 'comment',
                'text': (
                    '<p>Literal &amp;lt;tag&amp;gt;</p>'
                    '<pre><code>if ready:\n    work()</code></pre>'
                ),
            }
        )
        assert item is not None
        self.assertIn('Literal &lt;tag&gt;', item.get('text', ''))
        self.assertIn('if ready:\n    work()', item.get('text', ''))
        self.assertIn('Literal &lt;tag&gt;', hn.render({'item': item}, 'markdown'))

    def test_item_body_is_bounded_and_marked(self) -> None:
        item = hn.info({'id': 42, 'text': 'x' * 4000})
        assert item is not None
        self.assertTrue(item.get('text_truncated', False))
        self.assertLessEqual(len(item['text']), 3000)
        self.assertIn('truncated', hn.render({'item': item}, 'markdown'))

    def test_preformatted_body_keeps_first_line_indentation(self) -> None:
        item = hn.info(
            {'id': 42, 'text': '<pre><code>    first\n    second</code></pre>'}
        )
        assert item is not None
        self.assertEqual(item['text'], '    first\n    second')

    @patch.object(hn.time, 'sleep')
    @patch.object(hn, 'get_json')
    def test_feed_retains_successes_after_individual_failure(
        self, request: MagicMock, _sleep: MagicMock
    ) -> None:
        request.side_effect = [
            [1, 2, 3],
            {'id': 1, 'title': 'One'},
            TimeoutError('timed out'),
            {'id': 3, 'title': 'Three'},
        ]
        data = hn.run_feed('top', 3)
        self.assertEqual([item['id'] for item in data['items']], [1, 3])
        self.assertTrue(data.get('incomplete', False))
        self.assertEqual(data['fetch_errors'], [{'id': 2, 'error': 'timed out'}])
        self.assertEqual(request.call_count, 4)
        self.assertIn('Incomplete', hn.render(data, 'markdown'))
        self.assertIn('timed out', hn.render(data, 'markdown'))

    def test_feed_retains_successes_after_response_read_failure(self) -> None:
        for failure in (
            IncompleteRead(b'{', 5),
            ConnectionResetError('connection reset'),
        ):
            with self.subTest(failure=type(failure).__name__):
                responses = [[1, 2, 3], {'id': 1}, failure, {'id': 3}]
                with (
                    patch.object(hn, 'get_json', side_effect=responses),
                    patch.object(hn.time, 'sleep'),
                ):
                    data = hn.run_feed('top', 3)
                self.assertEqual([item['id'] for item in data['items']], [1, 3])
                self.assertTrue(data['incomplete'])
                self.assertEqual(data['fetch_errors'][0]['id'], 2)

    @patch.object(hn.time, 'sleep')
    @patch.object(hn, 'get_json')
    def test_missing_child_is_reported_without_exceeding_budget(
        self, request: MagicMock, _sleep: MagicMock
    ) -> None:
        request.side_effect = [[1, 2, 3], None, {'id': 2}]
        data = hn.run_feed('top', 2)
        self.assertEqual([item['id'] for item in data['items']], [2])
        self.assertEqual(request.call_count, 3)
        self.assertTrue(data.get('incomplete', False))
        self.assertEqual(data['fetch_errors'], [{'id': 1, 'error': 'Item not found'}])

    @patch.object(hn.time, 'sleep')
    @patch.object(hn, 'get_json')
    def test_partial_item_returns_failure_with_parent_body(
        self, request: MagicMock, _sleep: MagicMock
    ) -> None:
        request.side_effect = [
            {'id': 1, 'type': 'story', 'text': '<p>Ask body</p>', 'kids': [2]},
            TimeoutError('timed out'),
        ]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(hn.main(['item', '1', '--format', 'json']), 1)
        data = json.loads(output.getvalue())
        self.assertEqual(data['item']['text'], 'Ask body')
        self.assertTrue(data['incomplete'])

    @patch.object(hn.time, 'sleep')
    @patch.object(hn, 'get_json')
    def test_user_retains_profile_after_child_failure(
        self, request: MagicMock, _sleep: MagicMock
    ) -> None:
        request.side_effect = [
            {'id': 'alice', 'karma': 42, 'submitted': [1]},
            TimeoutError('timed out'),
        ]
        data = hn.run_user('alice', 1)
        self.assertEqual(data['public_karma'], 42)
        self.assertEqual(data['recent_items'], [])
        self.assertTrue(data['incomplete'])

    @patch.object(hn, 'get_json', side_effect=TimeoutError('root timed out'))
    def test_root_failure_has_no_success_output(self, _request: MagicMock) -> None:
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(hn.main(['feed']), 1)
        self.assertEqual(output.getvalue(), '')
        self.assertIn('root timed out', errors.getvalue())

    @patch.object(hn, 'urlopen')
    def test_transport_uses_public_api_get_with_timeout(
        self, open_url: MagicMock
    ) -> None:
        open_url.return_value.__enter__.return_value = io.BytesIO(b'{"id":42}')
        self.assertEqual(hn.get_json('item/42'), {'id': 42})
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(
            request.full_url, 'https://hacker-news.firebaseio.com/v0/item/42.json'
        )
        self.assertEqual(open_url.call_args.kwargs['timeout'], 12)


if __name__ == '__main__':
    unittest.main()
