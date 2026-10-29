# Changelog

## v1.0

- Each standalone skill includes the complete MIT license notice.
- The standalone account evaluation checks inspection guidance without live requests.
- Thread guidance states the two-week and killed-submission closure rules explicitly.
- CLI output uses UTF-8 for Unicode text in pipes and redirected files.
- Invalid thread arguments return exit code `2` before public API reads.
- Submission rejection gates use the declared `Not a fit` decision.
- Reply budgets count failed and missing reads.
- Incomplete thread ancestry returns an unknown root and an explicit reason.
- Thread samples include sibling branches below known ancestors.
- Source text preserves literal entities and code indentation.
- Discovery output includes bounded item bodies and truncation markers.
- Failed reads preserve partial results and report item-level errors.
- Missing targets and failed reads return a nonzero exit code.
- Metadata checks reject malformed and non-string values, with offline regression tests.
- Standalone skills define source trust boundaries and fallbacks for unavailable tools.
- Manual evaluation cases cover instruction safety, missing tools, and uncertain evidence.
- Seven research-first Agent Skills for Hacker News.
- Read-only public API helpers for feeds, users, items, and bounded thread context.
- Offline unit tests and skill metadata checks.
- MIT license, contribution and security policies, and GitHub Actions CI.
- Official HN policy source register and rule matrix.

The project includes no automated posting, voting, commenting, or account control.
