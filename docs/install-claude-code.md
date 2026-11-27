# Install in Claude Code

Takes about 2 minutes. You need Claude Code, git and Python 3.9+.

## Option 1: one command (recommended)
```bash
npx skills add iamshantanubose/receipts -a claude-code -g
```
`-g` installs it for all your projects (`~/.claude/skills/`). Leave out `-g` to install it only in the current project (`.claude/skills/`).

## Option 2: as a Claude Code plugin
Inside Claude Code:
```
/plugin marketplace add iamshantanubose/receipts
/plugin install verify-engineering@verify-engineering
```
Plugin skills are namespaced, so you invoke it as `/verify-engineering:verify-engineering`. Plain language also works.

## Option 3: manual copy
```bash
git clone https://github.com/iamshantanubose/receipts.git
mkdir -p ~/.claude/skills
cp -R receipts/skills/verify-engineering ~/.claude/skills/
```

## Use it
```
/verify-engineering
/verify-engineering deep
/verify-engineering standard fix
/verify-engineering quick src/payments/
```
Or just ask: *"verify the last change before I merge"* or *"check this migration is behaviour-identical"*.

In Claude Code the skill hands the challenge stage to a fresh subagent, so the verifier does not
inherit the implementing agent's assumptions.

## Check it is installed
Start Claude Code and type `/verify`. `verify-engineering` should appear in the menu. You can also ask: *"What skills do you have?"*
