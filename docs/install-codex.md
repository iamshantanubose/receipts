# Install in OpenAI Codex (documented, not yet tested)

Codex's documentation says it loads Agent Skills from `.agents/skills/` (from the current folder up to the repo root)
and from `~/.agents/skills/`. The skill uses only the portable `SKILL.md` format, so it should work, but it has
**not been tested in Codex yet** (see [compatibility.md](compatibility.md)). If you try it, please file a
"Host verification report" issue with the result.

```bash
npx skills add iamshantanubose/receipts -a codex -g
# or manually:
git clone https://github.com/iamshantanubose/receipts.git
mkdir -p ~/.agents/skills && cp -R receipts/skills/verify-engineering ~/.agents/skills/
```
Invoke it with `$verify-engineering`, or pick it from `/skills`.
