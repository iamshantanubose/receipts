# Compatibility matrix

| Host | Install path | Invocation | Independent subagent | Status |
|---|---|---|---|---|
| Claude Code (CLI, desktop, IDE) | `~/.claude/skills/` or `.claude/skills/`, or as a plugin | `/verify-engineering` (plugin: `/verify-engineering:verify-engineering`) | Yes (Task/Agent tool) | Manifest validated; workflow executed by Claude Code agents. Slash invocation not yet verified live (see `docs/validation.md`) |
| Cursor | `~/.cursor/skills/`, `.cursor/skills/`, `.agents/skills/` (also reads `~/.claude/skills/`) | `/` menu, or ask in plain language | Cold-read fallback | Documented, **not yet verified live** |
| OpenAI Codex | `~/.agents/skills/`, `.agents/skills/` | `$verify-engineering` or `/skills` | Cold-read fallback | Documented, **not tested** |
| Other Agent Skills hosts | any folder the host scans for `SKILL.md` | host-specific | Depends | Uses only the 4 standard frontmatter fields (`name`, `description`, `license`, `metadata`) |

| Requirement | Version |
|---|---|
| Python (scripts) | 3.9+ (standard library only; CI tests 3.9 and 3.13) |
| git | any recent version |
| Rust toolchain | only for the Rust migration demo |
| pytest | only to run this repo's own test suite and the Python demos |

## Known limitations
- `test_integrity_scan.py` and `mutation_probe.py` are pattern-based and language-agnostic. They are fast triage, not a replacement for a full mutation tool (mutmut, cargo-mutants, Stryker, PIT) or for careful review.
- The mutation probe copies the project to a temp folder and runs your test command there. Projects that need absolute paths, running services or large build caches may need `--root` / `--test` adjustments.
- `diff_harness.py` compares stdout. For HTTP services, wrap each version in a small CLI or script that sends the request and prints the response.
- Verification quality still depends on the model and on how clear the requirements are. Missing requirements become NOT VERIFIED or PROPOSED, never invented facts.
- A GO verdict is evidence-based confidence, not proof of correctness.
