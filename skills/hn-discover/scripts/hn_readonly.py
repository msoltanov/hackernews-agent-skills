#!/usr/bin/env python3
"""Read the official Hacker News public API without third-party dependencies.

The helper does not post, vote, log in, or write HN content.
It limits the number of reads.
"""

import argparse
import datetime as dt
import html
import json
import sys
import time
from html.parser import HTMLParser
from http.client import HTTPException
from io import TextIOWrapper
from typing import Any, TypedDict
from urllib.request import Request, urlopen

API = 'https://hacker-news.firebaseio.com/v0'
OUTPUT_ENCODING = 'utf-8'
REQUEST_TIMEOUT = 12
MAX_TEXT_CHARS = 3000
MAX_RECORDS = 25
FETCH_ERRORS = (OSError, HTTPException, ValueError)
FEEDS = {
    'top': 'topstories',
    'new': 'newstories',
    'best': 'beststories',
    'ask': 'askstories',
    'show': 'showstories',
    'jobs': 'jobstories',
}


JsonRecord = dict[str, Any]


class ItemInfo(TypedDict):
    """Describe one public HN item for research output."""

    id: int | None
    type: str | None
    title: str
    by: str | None
    created_utc: str | None
    score: int | None
    comments: int | None
    url: str | None
    hn_url: str
    dead: bool
    deleted: bool
    parent_id: int | None
    text: str
    text_truncated: bool


def get_json(path: str) -> Any:
    """Read a JSON value from the public HN API."""
    request = Request(
        f'{API}/{path}.json',
        headers={
            'User-Agent': 'hn-skills-readonly/1.0 (personal educational research)',
            'Accept': 'application/json',
        },
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.load(response)


def iso_date(unix_time: int | float | None) -> str | None:
    """Format an available Unix timestamp in UTC."""
    if not unix_time:
        return None
    return dt.datetime.fromtimestamp(unix_time, tz=dt.timezone.utc).strftime(
        '%Y-%m-%dT%H:%M:%SZ'
    )


def strip_markup(value: str | None) -> str:
    """Decode a title without rendering HTML."""
    return html.unescape(value or '').replace('\n', ' ').strip()


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ('p', 'br', 'div', 'blockquote', 'pre'):
            self.parts.append('\n')

    def handle_endtag(self, tag: str) -> None:
        if tag in ('p', 'div', 'blockquote', 'pre'):
            self.parts.append('\n')

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def info(item: JsonRecord | None) -> ItemInfo | None:
    """Extract bounded body text and public item metadata."""
    if not item:
        return None
    item_id = item.get('id')
    parser = _TextParser()
    parser.feed(item.get('text') or '')
    text = ''.join(parser.parts).strip('\n')
    return {
        'id': item_id,
        'type': item.get('type'),
        'title': strip_markup(item.get('title')),
        'by': item.get('by'),
        'created_utc': iso_date(item.get('time')),
        'score': item.get('score'),
        'comments': item.get('descendants'),
        'url': item.get('url'),
        'hn_url': f'https://news.ycombinator.com/item?id={item_id}',
        'dead': bool(item.get('dead', False)),
        'deleted': bool(item.get('deleted', False)),
        'parent_id': item.get('parent'),
        'text': text[:MAX_TEXT_CHARS],
        'text_truncated': len(text) > MAX_TEXT_CHARS,
    }


def fetch_items(
    ids: list[int],
    limit: int,
    pause: float = 0.07,
    errors: list[JsonRecord] | None = None,
) -> list[ItemInfo | None]:
    """Read selected items and retain errors without retrying."""
    results: list[ItemInfo | None] = []
    errors = errors if errors is not None else []
    for item_id in ids[:limit]:
        try:
            item = get_json(f'item/{int(item_id)}')
            if item:
                results.append(info(item))
            else:
                errors.append({'id': item_id, 'error': 'Item not found'})
        except FETCH_ERRORS as exc:
            errors.append({'id': item_id, 'error': str(exc)})
        if pause:
            time.sleep(pause)
    return results


def run_feed(feed: str, limit: int) -> JsonRecord:
    """Read a bounded sample from an official feed."""
    ids = get_json(FEEDS[feed]) or []
    errors: list[JsonRecord] = []
    items = fetch_items(ids, limit, errors=errors)
    return {
        'feed': feed,
        'source': f'{API}/{FEEDS[feed]}.json',
        'items': items,
        'fetch_errors': errors,
        'incomplete': bool(errors),
    }


def run_item(item_id: int, replies: int) -> JsonRecord:
    """Read an item and a bounded sample of its direct replies."""
    item = get_json(f'item/{item_id}')
    if not item:
        return {'error': 'Item not found', 'id': item_id}
    errors: list[JsonRecord] = []
    children = fetch_items(item.get('kids', []), replies, errors=errors)
    return {
        'item': info(item),
        'first_level_replies': children,
        'fetch_errors': errors,
        'incomplete': bool(errors),
        'note': (
            'Comment trees and moderation state may be incomplete. '
            'Read the HN thread for full context.'
        ),
    }


def run_user(username: str, limit: int) -> JsonRecord:
    """Read a public profile and a bounded activity sample."""
    user = get_json(f'user/{username}')
    if not user:
        return {'error': 'Public user data not found', 'username': username}
    ids = user.get('submitted', [])
    errors: list[JsonRecord] = []
    items = fetch_items(ids, limit, errors=errors)
    return {
        'username': user.get('id'),
        'created_utc': iso_date(user.get('created')),
        'public_karma': user.get('karma'),
        'recent_items': items,
        'fetch_errors': errors,
        'incomplete': bool(errors),
        'note': (
            'API data cannot determine why a post was flagged '
            'or whether an account is restricted.'
        ),
    }


def render(result: JsonRecord, fmt: str) -> str:
    """Render a research result as JSON or Markdown."""
    if fmt == 'json':
        return json.dumps(result, ensure_ascii=False, indent=2)
    header = f'# HN: {result.get("feed", result.get("username", "item"))}'
    lines = [header, '', 'Read-only research. Not HN posting text.', '']
    if 'error' in result:
        return '\n'.join([*lines, f'Error: {result["error"]}'])
    if 'item' in result:
        objects = [result['item'], *result.get('first_level_replies', [])]
    else:
        objects = result.get('items', result.get('recent_items', []))
    for item in objects:
        label = item['title'] or f'{item["type"] or "item"} #{item["id"]}'
        lines.append(f'- **{label}** — {item["hn_url"]}')
        lines.append(
            f'  - source: {item["url"] or "(not supplied)"}; '
            f'date: {item["created_utc"] or "?"}; by: {item["by"] or "?"}; '
            f'score: {item["score"]}; replies: {item["comments"]}; '
            f'dead: {item["dead"]}; deleted: {item["deleted"]}'
        )
        if item.get('text'):
            lines.append('  - text:')
            lines.extend(f'    {line}' for line in item['text'].splitlines())
        if item.get('text_truncated'):
            lines.append('  - Body truncated.')
    if result.get('incomplete'):
        lines.extend(['', 'Incomplete result: some records could not be read.'])
        lines.extend(
            f'- Item {error["id"]}: {error["error"]}'
            for error in result.get('fetch_errors', [])
        )
    if result.get('note'):
        lines.extend(['', result['note']])
    return '\n'.join(lines)


def positive_limit(value: str) -> int:
    """Parse a record limit within the supported range."""
    number = int(value)
    if not 1 <= number <= MAX_RECORDS:
        raise argparse.ArgumentTypeError(f'limit must be 1..{MAX_RECORDS}')
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse discovery, item, and account command arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='command', required=True)
    for command in ('feed', 'item', 'user'):
        command_parser = subcommands.add_parser(command)
        command_parser.add_argument(
            '--format', choices=('markdown', 'json'), default='markdown'
        )
        command_parser.add_argument(
            '--limit',
            type=positive_limit,
            default=10,
            help=f'max {MAX_RECORDS} requests for individual records',
        )
        if command == 'feed':
            command_parser.add_argument(
                '--list', choices=tuple(FEEDS), default='top', dest='feed'
            )
        elif command == 'item':
            command_parser.add_argument('id', type=int)
        else:
            command_parser.add_argument('username')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run a read-only command and report incomplete results."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding=OUTPUT_ENCODING)

    args = parse_args(argv)
    try:
        if args.command == 'feed':
            result = run_feed(args.feed, args.limit)
        elif args.command == 'item':
            result = run_item(args.id, args.limit)
        else:
            result = run_user(args.username, args.limit)
        print(render(result, args.format))
        return 1 if 'error' in result or result.get('incomplete') else 0
    except FETCH_ERRORS as exc:
        print(f'Unable to read HN public API: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
