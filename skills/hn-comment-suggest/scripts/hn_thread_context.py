#!/usr/bin/env python3
"""Read bounded public HN thread context with the Python standard library.

Usage: python hn_thread_context.py 'https://news.ycombinator.com/item?id=8863'
       python hn_thread_context.py 8863 --limit 12 --format json
The helper does not log in, post, vote, or retry failed reads.
"""

import argparse
import html
import json
import sys
import time
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.client import HTTPException
from io import TextIOWrapper
from typing import Any, Literal, Protocol, TypedDict
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

API = 'https://hacker-news.firebaseio.com/v0'
OUTPUT_ENCODING = 'utf-8'
MAX_ANCESTORS = 20
MAX_LINKS = 12
MAX_TEXT_CHARS = 3000
READ_ERRORS = (OSError, HTTPException, ValueError)


JsonRecord = dict[str, Any]
AncestryStopReason = Literal['missing_parent', 'cycle', 'limit', 'fetch_error']


class ExtractedText(TypedDict):
    """Describe plain source text and its public links."""

    text: str
    links: list[str]


class BriefItem(TypedDict):
    """Describe public item context for a research result."""

    id: int
    type: str | None
    by: str | None
    created_utc: str | None
    title: str
    url: str | None
    hn_url: str
    parent_id: int | None
    kids_count: int
    dead: bool
    deleted: bool
    text: str
    links_in_text: list[str]


class ItemReader(Protocol):
    """Read public item records for thread analysis."""

    def get(self, item_id: int, /) -> JsonRecord | None:
        """Return a public item or a missing-record result."""
        ...


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ('p', 'br', 'div', 'blockquote', 'pre'):
            self.parts.append('\n')
        if tag == 'a':
            for key, value in attrs:
                if (
                    key == 'href'
                    and value
                    and value.startswith(('https://', 'http://'))
                    and len(self.links) < MAX_LINKS
                ):
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in ('p', 'div', 'blockquote', 'pre'):
            self.parts.append('\n')

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def extract_text(value: str | None, max_chars: int = MAX_TEXT_CHARS) -> ExtractedText:
    """Extract bounded text and links without changing code indentation."""
    parser = _TextParser()
    parser.feed(value or '')
    cleaned = ''.join(parser.parts).strip('\n')
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + ' [truncated]'
    return {'text': cleaned, 'links': list(dict.fromkeys(parser.links))}


def parse_item_id(value: str) -> int:
    """Parse a positive item ID or an official HN item URL."""
    if str(value).isdigit() and int(value) > 0:
        return int(value)
    parsed = urlparse(value)
    if (
        parsed.scheme != 'https'
        or parsed.hostname != 'news.ycombinator.com'
        or parsed.path.rstrip('/') != '/item'
    ):
        raise ValueError(
            'Pass a positive HN item ID '
            'or an https://news.ycombinator.com/item?id=... URL'
        )
    args = parse_qs(parsed.query)
    ids = args.get('id', [])
    if len(ids) != 1 or not ids[0].isdigit() or int(ids[0]) <= 0:
        raise ValueError('HN URL needs one positive numeric id= value')
    return int(ids[0])


def iso(value: int | float | None) -> str | None:
    """Format an available Unix timestamp in UTC."""
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat() if value else None


def brief(item: JsonRecord) -> BriefItem:
    """Extract bounded text and public context from one item."""
    body = extract_text(item.get('text'))
    item_id = int(item['id'])
    return {
        'id': item_id,
        'type': item.get('type'),
        'by': item.get('by'),
        'created_utc': iso(item.get('time')),
        'title': html.unescape(item.get('title') or ''),
        'url': item.get('url'),
        'hn_url': f'https://news.ycombinator.com/item?id={item_id}',
        'parent_id': item.get('parent'),
        'kids_count': len(item.get('kids') or []),
        'dead': bool(item.get('dead')),
        'deleted': bool(item.get('deleted')),
        'text': body['text'],
        'links_in_text': body['links'],
    }


class HNReader:
    """Read and cache public HN items without account access."""

    def __init__(self, pause: float = 0.06) -> None:
        self.cache: dict[int, JsonRecord | None] = {}
        self.pause = pause

    def get(self, id_: int) -> JsonRecord | None:
        """Return one cached or newly fetched public item."""
        item_id = int(id_)
        if item_id in self.cache:
            return self.cache[item_id]
        request = Request(
            f'{API}/item/{item_id}.json',
            headers={
                'User-Agent': 'hn-comment-suggest-readonly/1.0 (research)',
                'Accept': 'application/json',
            },
        )
        with urlopen(request, timeout=12) as response:
            record = json.load(response)
        self.cache[item_id] = record
        if self.pause:
            time.sleep(self.pause)
        return record


def thread_context(
    id_: int,
    limit: int = 12,
    depth: int = 2,
    reader: ItemReader | None = None,
) -> JsonRecord:
    """Read bounded thread context and report missing evidence."""
    item_id = id_
    reader = reader or HNReader()
    focus = reader.get(item_id)
    if not focus:
        return {'error': 'HN item not found', 'item_id': item_id}

    chain = [focus]
    ancestor_ids = {int(focus['id'])}
    ancestry_stop_reason: AncestryStopReason | None = None
    fetch_errors: list[JsonRecord] = []
    while chain[-1].get('type') == 'comment':
        if not chain[-1].get('parent'):
            ancestry_stop_reason = 'missing_parent'
            break
        parent_id = int(chain[-1]['parent'])
        if parent_id in ancestor_ids:
            ancestry_stop_reason = 'cycle'
            break
        if len(chain) >= MAX_ANCESTORS:
            ancestry_stop_reason = 'limit'
            break
        try:
            ancestor = reader.get(parent_id)
        except READ_ERRORS as exc:
            fetch_errors.append({'id': parent_id, 'error': str(exc)})
            ancestry_stop_reason = 'fetch_error'
            break
        if not ancestor:
            fetch_errors.append({'id': parent_id, 'error': 'HN item not found'})
            ancestry_stop_reason = 'missing_parent'
            break
        chain.append(ancestor)
        ancestor_ids.add(parent_id)
    chain.reverse()
    ancestry_complete = ancestry_stop_reason is None
    root = chain[0] if ancestry_complete else None

    queue: deque[tuple[int, int]] = deque()
    for ancestor in reversed(chain):
        queue.extend(
            (item, 1)
            for item in (ancestor.get('kids') or [])
            if item not in ancestor_ids
        )
    sample: list[BriefItem] = []
    deeper_reply_ids: set[int] = set()
    seen = set(ancestor_ids)
    reply_fetches = 0
    while queue and reply_fetches < limit:
        child_id, current_depth = queue.popleft()
        if child_id in seen:
            continue
        seen.add(child_id)
        reply_fetches += 1
        try:
            child = reader.get(child_id)
        except READ_ERRORS as exc:
            fetch_errors.append({'id': child_id, 'error': str(exc)})
            continue
        if not child:
            fetch_errors.append({'id': child_id, 'error': 'HN item not found'})
            continue
        sample.append(brief(child))
        if current_depth < depth:
            queue.extend(
                (item, current_depth + 1) for item in (child.get('kids') or [])
            )
        elif child.get('kids'):
            deeper_reply_ids.update(child['kids'])

    return {
        'focus': brief(focus),
        'root': brief(root) if root else None,
        'ancestors_root_to_focus': [brief(item) for item in chain],
        'ancestry_complete': ancestry_complete,
        'ancestry_stop_reason': ancestry_stop_reason,
        'sampled_replies': sample,
        'sample_size': len(sample),
        'sample_truncated': (
            any(item_id not in seen for item_id, _ in queue)
            or bool(deeper_reply_ids - seen)
            or bool(fetch_errors)
            or not ancestry_complete
        ),
        'fetch_errors': fetch_errors,
        'note': (
            'Partial public API sample. Read the original article separately '
            'and inspect full HN context before deciding on an angle. '
            'Never paste AI-generated text into HN.'
        ),
    }


def render_md(value: JsonRecord) -> str:
    """Render available thread evidence and errors as Markdown."""
    if 'error' in value:
        return f'Error: {value["error"]}'

    def display(item: BriefItem) -> str:
        subject = item.get('title') or (f'Comment #{item["id"]}')
        lines = [f'### {subject} — {item["hn_url"]}']
        lines.append(
            f'by {item["by"] or "?"} · {item["created_utc"] or "?"} · '
            f'dead={item["dead"]} · deleted={item["deleted"]}'
        )
        if item.get('url'):
            lines.append(f'Original source: {item["url"]}')
        if item.get('text'):
            lines.append(item['text'])
        if item.get('links_in_text'):
            lines.append('Links: ' + ', '.join(item['links_in_text']))
        return '\n'.join(lines)

    root_text = (
        display(value['root'])
        if value['root']
        else 'Root unavailable: ancestry is incomplete.'
    )
    lines = [
        '# Read-only HN thread context',
        '',
        '## Root',
        root_text,
        '',
        '## Focus and parent chain',
    ]
    lines.extend(display(item) for item in value['ancestors_root_to_focus'])
    if not value['ancestry_complete']:
        lines.append(f'Ancestry incomplete: {value["ancestry_stop_reason"]}')
    lines.extend(['', '## Sample replies'])
    lines.extend(display(item) for item in value['sampled_replies'])
    if value['fetch_errors']:
        lines.extend(['', '## Fetch errors'])
        lines.extend(
            f'Item #{error["id"]}: {error["error"]}' for error in value['fetch_errors']
        )
    lines.extend(
        [
            '',
            f'Sampled: {value["sample_size"]} · '
            f'More replies not sampled: {value["sample_truncated"]}',
            value['note'],
        ]
    )
    return '\n\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the thread reader and report incomplete ancestry or failed reads."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding=OUTPUT_ENCODING)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'item',
        type=parse_item_id,
        help='HN item ID or https://news.ycombinator.com/item?id=... URL',
    )
    parser.add_argument('--limit', type=int, default=12, help='reply fetches, 1..25')
    parser.add_argument('--depth', type=int, default=2, help='nested reply depth, 1..3')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 25 or not 1 <= args.depth <= 3:
        parser.error('--limit must be 1..25 and --depth 1..3')
    try:
        result = thread_context(args.item, args.limit, args.depth)
    except READ_ERRORS as exc:
        print(f'Unable to read public HN item: {exc}', file=sys.stderr)
        return 1
    print(
        json.dumps(result, indent=2, ensure_ascii=False)
        if args.format == 'json'
        else render_md(result)
    )
    return (
        1
        if (
            'error' in result
            or result['fetch_errors']
            or not result['ancestry_complete']
        )
        else 0
    )


if __name__ == '__main__':
    sys.exit(main())
