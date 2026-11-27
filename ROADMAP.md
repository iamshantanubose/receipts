# Roadmap

Open work, in priority order. Contributions and reports are welcome (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## Verification of hosts
- [x] Confirm `/verify-engineering` in a live Claude Code session.
- [ ] Confirm the plugin route (`/verify-engineering:verify-engineering`).
- [ ] Confirm Cursor loads the skill from `.cursor/skills/` and `~/.claude/skills/`.
- [ ] Confirm Codex loads it from `.agents/skills/`.
- [ ] Confirm `npx skills add iamshantanubose/receipts` for each host.

Status per host is tracked in [docs/validation.md](docs/validation.md).

## A benchmark that can separate approaches
The first run ([benchmark/results/RESULTS.md](benchmark/results/RESULTS.md)) showed no measurable detection advantage: the cases
were too easy. The next run needs:
- [ ] larger, multi-file repositories;
- [ ] vague or partly missing requirements;
- [ ] weaker or cheaper models as well as strong ones;
- [ ] repeated trials, one case per agent session;
- [ ] a blinded scorer;
- [ ] the current `SKILL.md` and scripts.

## Tools
- [ ] Windows: run the scripts and the Python demos in CI on `windows-latest`.
- [ ] Scanner: language-aware parsing for Go, Java/Kotlin and C# test files.
- [ ] Differential harness: optional, documented normalisation rules (timestamps, IDs, key order).

## Known limitations
See [docs/compatibility.md](docs/compatibility.md). Most importantly: the skill's safety rules are instructions to an AI agent and
do not enforce anything by themselves. Keep host permission prompts on.
