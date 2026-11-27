# Host validation log

| Check | Result | How |
|---|---|---|
| Agent Skills spec: frontmatter, name rules, description ≤ 1024, SKILL.md < 500 lines, referenced files exist | **PASS** | `tests/test_skill_spec.py` |
| Claude Code plugin + marketplace manifests | **PASS** | `claude plugin validate .` → "Validation passed" (Claude Code 2.1.260) |
| Skill workflow executed by Claude Code agents | **PASS** | 4 benchmark runs (one per batch): fresh Claude Code subagents (Sonnet) read and followed `SKILL.md`, ran the scripts, and returned reports (`benchmark/results/`). That is part of 12 benchmark runs in total |
| `/verify-engineering` slash invocation in a live Claude Code session | **NOT VERIFIED** | The headless `claude -p` run failed at authentication on the test machine |
| Cursor Agent loading the skill from `.cursor/skills/` | **NOT VERIFIED** | `cursor-agent -p` needs a login on the test machine |
| Codex | **NOT VERIFIED** | Codex CLI not installed on the test machine |
| `npx skills add` installer | **NOT VERIFIED** before first publish (needs the public GitHub repo) |

Please report results for unverified hosts in an issue.
