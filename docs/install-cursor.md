# Install in Cursor

Cursor reads Agent Skills (`SKILL.md`) from `.cursor/skills/` and `.agents/skills/` (project) and from
`~/.cursor/skills/` and `~/.agents/skills/` (user). It also reads `~/.claude/skills/`, so if you already
installed the skill for Claude Code, Cursor sees it too.

## Option 1: one command
```bash
npx skills add iamshantanubose/verify-engineering -a cursor -g
```

## Option 2: manual copy
```bash
git clone https://github.com/iamshantanubose/verify-engineering.git
mkdir -p ~/.cursor/skills
cp -R verify-engineering/skills/verify-engineering ~/.cursor/skills/
```
For one project only, copy it into `<project>/.cursor/skills/` instead.

## Use it
In Agent chat, type `/` and pick **verify-engineering**, or ask *"verify my last change with verify-engineering"*.

Cursor does not have the same subagent tool as Claude Code. The skill then does a **cold read** instead: it
re-derives the expected behaviour from the requirements before it reads the implementation.
