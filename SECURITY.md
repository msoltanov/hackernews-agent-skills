# Security

The bundled helpers read only the public Hacker News API.
They do not use accounts, cookies, credentials, posting APIs, or write endpoints.
They require no third-party runtime packages.
See [Privacy](PRIVACY.md) for data handling.

## Supported versions

| Version | Supported |
| --- | --- |
| Latest `v1.x` release | Yes |
| Older releases | No |

Security fixes go into the next release.
Update to the latest release before you report a problem.

## Scope

These problems are in scope:

- A helper sends a request to a host other than `hacker-news.firebaseio.com`.
- A helper sends credentials, cookies, or local file contents.
- A helper writes outside standard output, or the zip build script writes outside its output directory.
- Skill instructions let untrusted source text cause commands, secret access, account actions, or publication.
- A skill produces publication-ready HN text, automated posting, vote coordination, or moderation evasion.

These problems are out of scope:

- Problems in Hacker News, the Hacker News API, or the agent host.
- Model behavior that the skill instructions already prohibit, unless you can repeat it with a specific prompt.

## Vulnerability reports

Do not publish exploit details or secrets in a public issue.
Use GitHub private vulnerability reporting on this repository.
If that feature is not available, contact the maintainer through a private contact method on their GitHub profile.

Include these details:

- The affected skill or helper and the release version.
- The prompt, input, or command that shows the problem.
- The observed result and the expected result.

The maintainer replies on a best-effort basis.
After a fix is released, the changelog records it.

Do not upload HN cookies, session tokens, private moderation correspondence, or other sensitive account data to issues or pull requests.
