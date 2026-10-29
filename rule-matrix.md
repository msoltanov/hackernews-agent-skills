# HN rules and project checks

The [source register](sources.md) records the official evidence for these decisions.

| Check | Project action | Basis |
| --- | --- | --- |
| AI content | Provide research and critique without HN-ready text or automated publication. | [Guidelines][guidelines], [team note][team-note] |
| Intellectual depth | Identify what readers can learn and assess the evidence. | [Welcome][welcome], [Guidelines][guidelines] |
| Original source | Find the original paper, post, project, or repository. | [Guidelines][guidelines] |
| Title | Flag misleading wording, hype, or departures from the factual original for human review. | [Guidelines][guidelines] |
| Video/PDF | Flag a missing `[video]` or `[pdf]` title indicator. | [Guidelines][guidelines] |
| Reposts | Check prior attention and dates without guaranteeing eligibility after a fixed interval. | [FAQ][faq], [Guidelines][guidelines] |
| Promotion | Assess the balance of self-promotion and useful participation. | [Guidelines][guidelines] |
| Show HN | Check substantial personal work, reader access, and author availability. | [Show HN][show-hn] |
| Ask HN | Explain text submission with the URL field blank, without drafting a question. | [FAQ][faq] |
| Jobs | Route eligible ordinary job ads to the monthly hiring thread. | [FAQ][faq], [Lists][lists] |
| Votes and comments | Reject solicitation, vote rings, and automated engagement. | [Guidelines][guidelines], [FAQ][faq] |
| Comments | Critique substance, evidence, and civility without replacement wording. | [Guidelines][guidelines], [Welcome][welcome] |
| Comment angles | Identify evidence, tradeoffs, factual checks, and open questions for human authorship. | [Guidelines][guidelines], [Welcome][welcome] |
| Moderation | Distinguish flagged, dead, and deleted items. | [FAQ][faq] |
| Karma and rank | Preserve uncertainty about anti-abuse systems and account restrictions. | [FAQ][faq] |
| Active threads | Check age and status before assessing reply availability. | [FAQ][faq] |
| Lists | Select a relevant view rather than relying only on the front page. | [Lists][lists] |
| API | Bound public reads and label incomplete information. | [API][api] |

A small number of reposts can be acceptable after roughly one year without significant attention.
This interval does not guarantee eligibility.
Deletion followed by reposting is not an acceptable attention strategy.

Show HN excludes landing pages, signup-only teasers, and minor releases.
Readers need work they can try, and the author must be available to discuss it.

HN closes threads to new comments after two weeks or when the submission is killed.
Public API fields do not guarantee reply access.
Flat karma or a low rank does not establish an account ban.
The `showdead` setting can reveal dead items but does not restore deleted content.

## Output boundary

The agent can return summaries, lists, factual tables, logic checks, citations, and research questions.
It must not turn those findings into a comment, title, or submission for direct publication on HN.
The agent can analyze a human-written draft without editing it.

[guidelines]: https://news.ycombinator.com/newsguidelines.html
[team-note]: https://news.ycombinator.com/item?id=22336638
[welcome]: https://news.ycombinator.com/newswelcome.html
[faq]: https://news.ycombinator.com/newsfaq.html
[show-hn]: https://news.ycombinator.com/showhn.html
[lists]: https://news.ycombinator.com/lists
[api]: https://github.com/HackerNews/API
