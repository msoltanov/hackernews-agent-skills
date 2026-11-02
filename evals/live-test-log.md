# Live test log

This log records manual tests of the skills in real agent hosts.
The [behavior cases](behavior-cases.md) define the synthetic evaluations.
Live tests use real HN data, so their results can change over time.
Raw conversation output is not committed.

## 2026-11-02: claude.ai and Claude Code

- Host: claude.ai web, with code execution.
  The model was not recorded.
- Network: the claude.ai egress proxy blocked `hacker-news.firebaseio.com` until the maintainer allowed the domain under **Settings > Capabilities**.
- Inputs: live HN lists, public Show HN and essay URLs, and the maintainer's own HN account.
  Account details are not recorded here.
- Reviewer: the maintainer, against each skill's `SKILL.md` rules.

### Results by skill

| Skill | Tested release | Result | Finding | Fixed in |
| --- | --- | --- | --- | --- |
| `hn-discover` | v1.0.0 | Fail | Used stale web search and did not run the helper. Fallback disclosure was correct. | v1.0.1 |
| `hn-discover` | v1.0.1 | Fail | The helper ran, but the egress proxy blocked the API. It first ran from the wrong directory. | v1.0.2 |
| `hn-discover` | v1.0.2 | Pass | Read live `best`, `top`, and `new` lists. Read metadata only and said so. | — |
| `hn-comment-review` | v1.0.2 | Pass | It treated thread age as the only closure check. Minor gap, no change. | — |
| `hn-digest` | v1.0.2 | Pass | Web fetch refused every article URL, so source checks were not done. The skill disclosed this. | v1.0.7, not yet retested |
| `hn-account-health` | v1.0.2 | Fail | Read the API through web fetch, hit the website rate limit, and may have guessed the account. | v1.0.3 |
| `hn-account-health` | v1.0.3 | Pass | Asked for the account and read the API through the helper. Karma and age were missing from helper output. | v1.0.4, not yet retested |
| `hn-comment-suggest` | v1.0.2 | Fail | Angles were paste-ready questions. Earlier commenters had no permalinks. It retried a rate-limited website. | v1.0.3 |
| `hn-comment-suggest` | v1.0.3 | Pass | Topic-note angles, comment permalinks, and helper reads. Minor: four discussed points instead of three. | — |
| `hn-source-review` | v1.0.2 | Fail | No prior discussion section, age counted as a fault, and one unlinked outside fact. | v1.0.3 |
| `hn-source-review` | v1.0.3 | Pass | Prior discussion with the search method. The age and link rules were not exercised. | — |
| `hn-submission-check` | v1.0.2 | Fail | Returned the undeclared decision `Not applicable` for an item already on HN. | v1.0.3 |
| `hn-submission-check` | v1.0.3 | Fail | Told the user to write a new title instead of keeping the original title. | v1.0.4 |
| `hn-submission-check` | v1.0.4 | Pass | Told the user to keep the original title. The `Already live` decision was not exercised. | — |

### Packaging

| Check | Result |
| --- | --- |
| claude.ai accepts the skill zips, including the `license` frontmatter key | Pass |
| Claude Code installs the plugin from the marketplace in a clean home directory (v1.0.4 and v1.0.6) | Pass, 7 skills loaded |

### Open retests

- `hn-account-health`: check that karma and the creation date appear (v1.0.4).
- `hn-digest`: check the title-search fallback when web fetch refuses an article URL (v1.0.7).
- `hn-submission-check`: check the `Already live` decision with an item already on HN.
- `hn-source-review`: check the age and link rules with a source older than one year.
