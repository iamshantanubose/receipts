# Install in OpenAI Codex (documented, not yet tested by us)

Codex's documentation says it loads Agent Skills from `.agents/skills/` (from the current folder up to the repo root)
and from `~/.agents/skills/`. The skill uses only the portable `SKILL.md` format, so it should work.
We have **not yet tested it in Codex** (see `compatibility.md`). If you try it, please open an issue with the result.

```bash
npx skills add iamshantanubose/receipts -a codex -g
# or manually:
git clone https://github.com/iamshantanubose/receipts.git
mkdir -p ~/.agents/skills && cp -R receipts/skills/verify-engineering ~/.agents/skills/
```
Invoke it with `$verify-engineering`, or pick it from `/skills`.
