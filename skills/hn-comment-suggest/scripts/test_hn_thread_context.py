"""Run offline checks for bounded thread context and source text."""

import json
import unittest
from http.client import IncompleteRead
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch
from urllib.error import URLError

from hn_thread_context import (
    HNReader,
    JsonRecord,
    extract_text,
    main,
    parse_item_id,
    render_md,
    thread_context,
)


class MockReader:
    def __init__(self) -> None:
        self.items: dict[int, JsonRecord] = {
            1: {
                'id': 1,
                'type': 'story',
                'title': 'What is faster?',
                'url': 'https://example.com/test',
                'kids': [2, 3],
            },
            2: {
                'id': 2,
                'type': 'comment',
                'parent': 1,
                'by': 'a',
                'text': '<p>Initial claim &amp; detail.</p>',
                'kids': [4],
            },
            3: {
                'id': 3,
                'type': 'comment',
                'parent': 1,
                'by': 'b',
                'text': '<p>Different point.</p>',
            },
            4: {
                'id': 4,
                'type': 'comment',
                'parent': 2,
                'by': 'c',
                'text': '<p>Deep comment.</p>',
                'kids': [5],
            },
            5: {
                'id': 5,
                'type': 'comment',
                'parent': 4,
                'by': 'd',
                'text': '<p>Too deep.</p>',
            },
        }

    def get(self, item_id: int) -> JsonRecord | None:
        return self.items.get(item_id)


class HNCommentSkillTest(unittest.TestCase):
    def test_unicode_output_uses_utf8_for_redirected_streams(self) -> None:
        record = {'id': 1, 'type': 'story', 'title': 'Launch \U0001f680', 'kids': []}
        for output_format in ('json', 'markdown'):
            with self.subTest(output_format=output_format):
                with (
                    BytesIO() as buffer,
                    TextIOWrapper(buffer, encoding='cp1252') as output,
                    patch('hn_thread_context.HNReader.get', return_value=record),
                    patch('sys.stdout', output),
                ):
                    status = main(['1', '--format', output_format])
                    output.flush()
                    rendered = buffer.getvalue().decode('utf-8')

                self.assertEqual(status, 0)
                self.assertIn('Launch \U0001f680', rendered)
                if output_format == 'json':
                    self.assertEqual(
                        json.loads(rendered)['root']['title'], record['title']
                    )

    def test_invalid_item_returns_argument_error_without_reads(self) -> None:
        for value in ('hey', '0', 'http://news.ycombinator.com/item?id=8863'):
            with self.subTest(value=value):
                with (
                    patch('hn_thread_context.HNReader.get') as read_item,
                    patch('sys.stderr', new_callable=StringIO),
                    self.assertRaises(SystemExit) as error,
                ):
                    main([value])

                self.assertEqual(error.exception.code, 2)
                read_item.assert_not_called()

    def test_thread_context_preserves_item_id_keyword(self) -> None:
        context = thread_context(id_=1, reader=MockReader())

        self.assertEqual(context['root']['id'], 1)

    def test_reader_preserves_item_id_keyword(self) -> None:
        with patch('hn_thread_context.urlopen') as open_url:
            open_url.return_value.__enter__.return_value = BytesIO(b'{"id":1}')

            result = HNReader(pause=0).get(id_=1)

        self.assertEqual(result, {'id': 1})

    def test_id_parsing(self) -> None:
        self.assertEqual(parse_item_id('8863'), 8863)
        self.assertEqual(
            parse_item_id('https://news.ycombinator.com/item?id=8863&foo=bar'), 8863
        )
        for invalid in (
            '0',
            'https://other.com/item?id=8863',
            'http://news.ycombinator.com/item?id=8863',
            'https://news.ycombinator.com/item',
            'hey',
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_item_id(invalid)

    def test_extract_text(self) -> None:
        parsed = extract_text(
            '<p>Hi &amp; bye</p><p>Next <a href="https://example.com">link</a></p>'
        )
        self.assertIn('Hi & bye', parsed['text'])
        self.assertIn('Next link', parsed['text'])
        self.assertEqual(parsed['links'], ['https://example.com'])

    def test_focus_chain_and_bounded_replies(self) -> None:
        context = thread_context(4, limit=2, depth=2, reader=MockReader())
        self.assertEqual(context['root']['id'], 1)
        self.assertEqual(
            [item['id'] for item in context['ancestors_root_to_focus']], [1, 2, 4]
        )
        self.assertEqual(context['sample_size'], 2)
        self.assertEqual([item['id'] for item in context['sampled_replies']], [5, 3])
        self.assertIn('Root', render_md(context))

    def test_depth_and_truncation(self) -> None:
        context = thread_context(1, limit=1, depth=3, reader=MockReader())
        self.assertEqual(context['sample_size'], 1)
        self.assertTrue(context['sample_truncated'])
        self.assertEqual(context['sampled_replies'][0]['id'], 2)

    def test_missing_item(self) -> None:
        context = thread_context(999, reader=MockReader())
        self.assertIn('error', context)

    def test_missing_replies_consume_fetch_budget(self) -> None:
        reader = MockReader()
        reader.items = {1: {'id': 1, 'type': 'story', 'kids': [2, 3, 4]}}
        calls: list[int] = []
        original_get = reader.get
        reader.get = lambda item_id: calls.append(item_id) or original_get(item_id)

        context = thread_context(1, limit=1, reader=reader)

        self.assertEqual(calls, [1, 2])
        self.assertEqual(context['sample_size'], 0)
        self.assertTrue(context['sample_truncated'])

    def test_deep_ancestry_does_not_claim_a_comment_is_root(self) -> None:
        reader = MockReader()
        reader.items = {1: {'id': 1, 'type': 'story'}}
        reader.items.update(
            {
                item_id: {'id': item_id, 'type': 'comment', 'parent': item_id - 1}
                for item_id in range(2, 26)
            }
        )

        context = thread_context(25, reader=reader)

        self.assertIsNone(context['root'])
        self.assertFalse(context['ancestry_complete'])
        self.assertEqual(context['ancestry_stop_reason'], 'limit')
        self.assertIn('Root unavailable', render_md(context))

    def test_missing_or_cyclic_ancestry_is_explicit(self) -> None:
        for parent, reason in ((99, 'missing_parent'), (2, 'cycle')):
            with self.subTest(reason=reason):
                reader = MockReader()
                reader.items = {2: {'id': 2, 'type': 'comment', 'parent': parent}}

                context = thread_context(2, reader=reader)

                self.assertIsNone(context['root'])
                self.assertFalse(context['ancestry_complete'])
                self.assertEqual(context['ancestry_stop_reason'], reason)

    def test_complete_ancestry_is_explicit(self) -> None:
        context = thread_context(4, reader=MockReader())

        self.assertTrue(context['ancestry_complete'])
        self.assertIsNone(context['ancestry_stop_reason'])

    def test_samples_siblings_below_an_ancestor(self) -> None:
        reader = MockReader()
        reader.items = {
            1: {'id': 1, 'type': 'story', 'kids': [2]},
            2: {'id': 2, 'type': 'comment', 'parent': 1, 'kids': [3, 4]},
            3: {'id': 3, 'type': 'comment', 'parent': 2},
            4: {'id': 4, 'type': 'comment', 'parent': 2},
        }

        context = thread_context(3, reader=reader)

        self.assertEqual([item['id'] for item in context['sampled_replies']], [4])
        self.assertFalse(context['sample_truncated'])

    def test_reply_failure_keeps_successful_context(self) -> None:
        reader = MockReader()
        original_get = reader.get

        def get(item_id: int) -> JsonRecord | None:
            if item_id == 2:
                raise URLError('temporary failure')
            return original_get(item_id)

        reader.get = get
        context = thread_context(1, limit=2, reader=reader)

        self.assertEqual([item['id'] for item in context['sampled_replies']], [3])
        self.assertEqual(context['fetch_errors'][0]['id'], 2)
        self.assertTrue(context['sample_truncated'])
        self.assertIn('temporary failure', render_md(context))

    def test_ancestor_failure_keeps_focus(self) -> None:
        reader = MockReader()
        original_get = reader.get

        def get(item_id: int) -> JsonRecord | None:
            if item_id == 2:
                raise URLError('temporary failure')
            return original_get(item_id)

        reader.get = get
        context = thread_context(4, reader=reader)

        self.assertEqual(context['focus']['id'], 4)
        self.assertIsNone(context['root'])
        self.assertFalse(context['ancestry_complete'])
        self.assertEqual(context['ancestry_stop_reason'], 'fetch_error')
        self.assertEqual(context['fetch_errors'][0]['id'], 2)

    def test_response_read_failure_keeps_successful_context(self) -> None:
        for failure in (
            IncompleteRead(b'{', 5),
            ConnectionResetError('connection reset'),
        ):
            with self.subTest(failure=type(failure).__name__):
                reader = MockReader()
                with patch.object(
                    reader,
                    'get',
                    side_effect=[reader.items[1], failure, reader.items[3]],
                ):
                    context = thread_context(1, limit=2, reader=reader)

                self.assertEqual(
                    [item['id'] for item in context['sampled_replies']], [3]
                )
                self.assertEqual(context['fetch_errors'][0]['id'], 2)

                with (
                    patch('hn_thread_context.thread_context', return_value=context),
                    patch('sys.stdout', new_callable=StringIO),
                ):
                    self.assertEqual(main(['1']), 1)

    def test_entities_decode_once(self) -> None:
        parsed = extract_text('<p>Write &amp;lt;div&amp;gt;.</p>')

        self.assertEqual(parsed['text'], 'Write &lt;div&gt;.')

    def test_preformatted_code_preserves_indentation(self) -> None:
        parsed = extract_text(
            '<pre><code>    if ready:\n        run()\n\n        done()</code></pre>'
        )

        self.assertEqual(
            parsed['text'], '    if ready:\n        run()\n\n        done()'
        )

    def test_initial_network_failure_returns_nonzero(self) -> None:
        with (
            patch('hn_thread_context.HNReader.get', side_effect=URLError('offline')),
            patch('sys.stderr', new_callable=StringIO) as errors,
        ):
            self.assertEqual(main(['1']), 1)

        self.assertIn('offline', errors.getvalue())

    def test_partial_context_returns_nonzero(self) -> None:
        for items in (
            {1: {'id': 1, 'type': 'story', 'kids': [2]}},
            {1: {'id': 1, 'type': 'comment', 'parent': 1}},
        ):
            with self.subTest(items=items):
                reader = MockReader()
                reader.items = items
                context = thread_context(1, reader=reader)

                with (
                    patch('hn_thread_context.thread_context', return_value=context),
                    patch('sys.stdout', new_callable=StringIO) as output,
                ):
                    self.assertEqual(main(['1']), 1)

                self.assertTrue(output.getvalue())

    def test_planned_sample_truncation_returns_success(self) -> None:
        context = thread_context(1, limit=1, reader=MockReader())

        with (
            patch('hn_thread_context.thread_context', return_value=context),
            patch('sys.stdout', new_callable=StringIO),
        ):
            self.assertEqual(main(['1']), 0)


if __name__ == '__main__':
    unittest.main()
