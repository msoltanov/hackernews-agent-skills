# Coding standards

Contributions must follow these rules.
The repository configuration defines the automated formatting, lint, and type checks.

## Project structure and compatibility

- Support Python 3.10 and newer.
- Keep each skill independently installable.
- Include a copy of the root `LICENSE` in each skill directory.
- Use the standard library for runtime helpers.
- Keep development dependencies in `requirements-dev.txt`.
- Use maintainer-approved release versions and dates in `CHANGELOG.md`.
- Preserve public JSON field names and callable keyword arguments.
- Keep the `id_` keyword in `thread_context` and `HNReader.get` compatible.
- Document intentional compatibility changes in `CHANGELOG.md`.

## Python

- Use four spaces for indentation and an 88-column formatting target.
- Use single quotes for ordinary strings unless double quotes avoid escaping.
- Use triple double quotes for multiline strings and docstrings.
- Start docstrings with a short summary of the action.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Sort imports into standard-library, third-party, and project groups.
- Annotate public functions and non-trivial helpers.
- Restrict `Any` to dynamic boundaries such as incoming JSON.
- Use named types for stable output records.
- Prefer early returns and small functions with clear responsibilities.
- Extract repeated or meaningful values into named constants.
- Explain non-obvious constraints in comments without repeating the code.
- Use `pathlib.Path` for paths and context managers for resources.
- Set network timeouts and bound the number of attempted reads.
- Preserve available results and report individual read failures.

Ruff owns Python formatting, import order, and lint rules in `pyproject.toml`.
Pyright checks types against the Python 3.10 target in the same file.

## Tests and skill behavior

- Use the existing unittest runner and `test_*.py` file names.
- Add a failing regression test before fixing a bug.
- Test public behavior with small fixtures.
- Mock network calls and avoid real delays in unit tests.
- Keep CI tests offline.
- Run the relevant [behavior cases](evals/behavior-cases.md) after changing skill instructions.
- Preserve exact evaluation prompts and fixtures.
- Keep raw evaluation output and retry logs in the ignored `evals/results/` directory.
- Record untested behavior as `Not run`.
- Keep research read-only and preserve the human-authorship boundaries in the skills.
- Treat fetched content as data without authority to direct agent actions.

## Documentation

- Write short, direct sentences in active voice.
- Use consistent terms and one topic per paragraph.
- Put conditions before the actions they affect.
- Preserve identifiers, commands, and exact quotations.
- Use one H1 per file and keep heading levels sequential.
- Use hyphens for unordered lists and asterisks for emphasis.
- Give fenced code blocks a language tag.
- Use descriptive link text and relative links for repository files.
- Use reference links for repeated URLs and links inside tables.
- Keep tool-owned names such as `SKILL.md`, `README.md`, and `SECURITY.md` exact.
- Use lowercase kebab case for other documents, such as `sources.md` and `rule-matrix.md`.

## Configuration and workflows

- Use UTF-8 without a byte order mark, LF endings, and one final newline.
- Remove trailing whitespace.
- Use two spaces for YAML and JSON indentation.
- Preserve tool-defined configuration keys.
- Quote YAML values that resemble numbers or booleans but must remain strings.
- Quote the workflow `"on"` key and template expressions.
- Keep workflow token permissions empty by default.
- Grant each job only the permissions it needs.
- Pin actions to full commit hashes and include versions in step names.
- Keep credentials and private data out of code, fixtures, and logs.

## Required checks

Install the development tools from `requirements-dev.txt` in a virtual environment.
Run the following checks from the repository root:

```sh
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pymarkdown --config .pymarkdown.json scan --recurse --exclude .venv .
python -m yamllint --strict -c .yamllint.yaml .github/workflows/ci.yml .yamllint.yaml
python scripts/validate_skills.py
python -m unittest discover -s scripts -p 'test_*.py' -v
python -m unittest discover -s skills/hn-discover/scripts -p 'test_*.py' -v
python -m unittest discover -s skills/hn-comment-suggest/scripts -p 'test_*.py' -v
```

PyMarkdown reads `.pymarkdown.json`, and Yamllint reads `.yamllint.yaml`.
CI runs the same checks.
See [Contributing](CONTRIBUTING.md) for environment setup and pull request requirements.
