# Skills

Claude Code skills collection by [ivanzzeth](https://github.com/ivanzzeth).

## Install

```bash
npx skills add ivanzzeth/skills
```

Or install a specific skill:

```bash
npx skills add https://github.com/ivanzzeth/skills/tree/main/skills/<skill-name>
```

## Structure

```
skills/
├── <skill-name>/
│   └── SKILL.md       # Skill definition with YAML frontmatter
└── README.md
```

Each `SKILL.md` requires at minimum:

```yaml
---
name: skill-name          # kebab-case, 1-64 chars
description: Brief description of what this skill does and when to use it
---

Detailed instructions in Markdown...
```

## Development

### Create a new skill

```bash
npx skills init <skill-name>
```

### Test locally

```bash
npx skills add ./skills/<skill-name>
```

### Validate

```bash
npx skills validate ./skills/<skill-name>
```

## Publishing to skills.sh

Skills are automatically indexed on [skills.sh](https://skills.sh) when users install them via `npx skills add`. The leaderboard ranks skills by install count across three views: **All Time**, **Trending (24h)**, and **Hot**. No manual submission or approval is needed.

## License

MIT
