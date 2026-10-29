# Official source register

The project reviewed these sources on 2026-10-29.
HN pages define the policy claims.
The Agent Skills specification defines the skill format.

## Policy and mechanics

- [HN Guidelines][guidelines] define submission relevance, original sources, title integrity, media labels, promotion, reposts, and civil discussion.
  They prohibit solicited engagement, generated or AI-edited text, and automated posting.
- [HN FAQ][faq] explains ranking, karma, Ask HN, Show HN, visibility, moderation labels, reposts, jobs, account controls, and thread closure.
  It also covers IP restrictions and request volume.
- [HN Lists][lists] indexes `front`, `pool`, `invited`, `highlights`, `shownew`, `asknew`, `best`, `bestcomments`, `active`, and new-account lists.
  Other views include `classic`, `leaders`, `topcolors`, `whoishiring`, and `launches`.
- [HN Welcome][welcome] describes intellectual depth, learning, civil discussion, and meaningful replies.
- [Show HN Guidelines][show-hn] require substantial personal projects that readers can try.
  Landing pages, blogs, newsletters, and vote requests do not qualify.
  Easy access without signup is preferred.
- [HN Formatting][formatting] explains paragraphs, italics, code, and links.
  Links in text submissions do not become active.
- [HN team Show HN note][team-note], updated 2026-03-28, rejects even small LLM edits to published HN text.
  It also describes backstory, demo access, and honest presentation.

## Data and format

- [Official HN API][api] defines public item and user data.
  The `dead` and `deleted` fields do not explain the full moderation context.
- [Agent Skills specification][specification] defines skill directories and `SKILL.md` frontmatter with `name` and `description`.

## Priority of evidence

1. Use HN policy pages for conduct and eligibility.
2. Use the HN FAQ for mechanics.
3. Use public API fields for item observations, without inferring moderator intent.
4. Use community interpretations only as context.

Never present guesses about ranking or moderation as official policy.
`hn-comment-suggest` uses this register and a bounded read-only helper for thread context.
The project does not provide AI-generated or AI-edited HN post text.
Links provide evidence, not authorization to act.

[guidelines]: https://news.ycombinator.com/newsguidelines.html
[faq]: https://news.ycombinator.com/newsfaq.html
[lists]: https://news.ycombinator.com/lists
[welcome]: https://news.ycombinator.com/newswelcome.html
[show-hn]: https://news.ycombinator.com/showhn.html
[formatting]: https://news.ycombinator.com/formatdoc
[team-note]: https://news.ycombinator.com/item?id=22336638
[api]: https://github.com/HackerNews/API
[specification]: https://agentskills.io/specification
