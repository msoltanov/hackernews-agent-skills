# Contributing

Contributions can fix bugs and improve documentation, rule checks, tests, and read-only research tools.

## Development setup

Create a local virtual environment:

```sh
python -m venv .venv
```

On Linux or macOS, activate it with this command:

```sh
. .venv/bin/activate
```

On Windows PowerShell, activate it with this command:

```powershell
.venv\Scripts\Activate.ps1
```

Install the development tools:

```sh
python -m pip install -r requirements-dev.txt
```

Follow the project rules in [Coding standards](coding-standards.md) for code, documentation, tests, and workflows.

## Local checks

The helpers and offline tests require Python 3.10 or newer.
They need no third-party runtime packages.

```sh
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pymarkdown --config .pymarkdown.json scan --recurse --exclude .venv .
python -m yamllint --strict -c .yamllint.yaml .github/workflows/ci.yml .github/workflows/release.yml .yamllint.yaml
python scripts/validate_skills.py
python scripts/check_versions.py
python -m unittest discover -s scripts -p 'test_*.py' -v
python -m unittest discover -s skills/hn-discover/scripts -p 'test_*.py' -v
python -m unittest discover -s skills/hn-comment-suggest/scripts -p 'test_*.py' -v
```

The metadata checker supports flat, single-line string values.
It rejects YAML blocks, collections, tags, aliases, and implicit non-string values.
Use single quotes with doubled apostrophes, or double quotes with JSON escapes.
Quote values that contain a colon followed by a space or an inline comment marker.
The checker does not replace the agent host's format checks.

For instruction changes, run the relevant [manual behavior cases](evals/behavior-cases.md).
Record the model, host, response, attempted tool calls, and result.
Keep cases that did not run marked `Not run`.
Keep raw run output in the ignored `evals/results/` directory.
Include a short result summary in the pull request.

## Pull requests

1. Describe the problem and resulting behavior.
2. For a rule change, cite the relevant official HN policy, FAQ section, or API documentation.
3. Keep each skill portable, with valid frontmatter and no required agent-specific service.
4. If an integration is agent-specific, make it optional.
5. Add offline tests for changed script behavior.
6. Mock network responses rather than contacting HN from CI.
7. Bound public reads and avoid unnecessary requests.
8. Keep credentials, hidden endpoints, API keys, and private user data outside the repository.
9. Do not add automated posting, voting, comments, flags, account evasion, or engagement solicitation.
10. Do not add generated HN comments or submissions for publication.
11. Distinguish public observations and moderation inferences from official policy.

## Packaging checks

Run these checks when you change skill metadata, manifests, or packaging:

```sh
python scripts/build_skill_zips.py
claude plugin validate . --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

The zip build writes one claude.ai upload zip per skill to `dist/`.
Each skill description must have 200 characters or less.
The `icon` field in `.claude-plugin/plugin.json` sets the plugin icon.
The icon is a square PNG of 1024 pixels.

## Releases

Maintainers make releases from `main`.

1. Update the version in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
2. Update the version in `README.md`.
3. Add the changes to `CHANGELOG.md`.
4. Merge these changes into `main`.
5. Push a tag with the same version, for example `v1.0.0`.

The tag starts the release workflow.
The workflow stops if the tag does not match the version in every file.
Run `python scripts/check_versions.py --tag v1.0.0` with your tag before you push it.
The workflow builds the skill zips and attaches them to a GitHub release.
Do not change a tag after you push it.

## Issues

Include public item IDs, expected behavior, observed behavior, and reproduction steps.
Do not share passwords, session cookies, API tokens, private messages, or unpublished personal data.
Report vulnerabilities privately as [Security](SECURITY.md) describes.

## License

By contributing, you agree your contribution is provided under the repository's MIT License.
This project is independent of Hacker News and Y Combinator.
