# Privacy

This policy covers the `hn-agent-skills` plugin and the seven skills in this repository.
The project checked it on 2026-11-02.

## Data collection

The project collects no personal data.
It has no server, analytics, telemetry, cookies, or accounts.
The maintainer receives no data from your use of the skills.

## Network requests

The optional Python helpers send read-only requests to the public [Hacker News API][api] at `hacker-news.firebaseio.com`.
A request contains only the item ID, username, or list name that you or the agent supplies.
The helpers send no credentials, cookies, or tokens.
The API operator's own policies apply to these requests.

## Agent host

The skills run inside an agent host, such as Claude Code, claude.ai, or the Claude API.
The host processes your prompts, files, and outputs under its own privacy policy.
This project does not control that processing.

## Local files

The helpers write output only to standard output.
The zip build script writes only to the output directory that you select.

## Contact

For privacy questions, open an issue in the [repository][issues].
Do not include passwords, session cookies, API tokens, or private messages.

[api]: https://github.com/HackerNews/API
[issues]: https://github.com/msoltanov/hackernews-agent-skills/issues
