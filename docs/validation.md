# Host validation log

| Check | Result | How |
|---|---|---|
| Agent Skills spec: frontmatter, name rules, description ≤ 1024, SKILL.md < 500 lines, referenced files exist | **PASS** | `tests/test_skill_spec.py` |
| Claude Code plugin + marketplace manifests | **PASS** | `claude plugin validate .` → "Validation passed" (Claude Code 2.1.260) |
| Skill workflow followed end to end by an agent in Claude Code | **PASS** | 3 benchmark runs (one per batch) read and followed `SKILL.md`, ran the scripts and returned reports ([`benchmark/results/`](../benchmark/results/)) |
| `/verify-engineering` slash invocation in a live Claude Code session | **NOT VERIFIED** | Not yet run interactively |
| Cursor Agent loading the skill from `.cursor/skills/` | **NOT VERIFIED** | Not yet run |
| Codex | **NOT VERIFIED** | Not yet run |
| `npx skills add iamshantanubose/receipts` | **NOT VERIFIED** | Not yet run against the published repository |
| Test suite on Python 3.9 and 3.13 (macOS) | **PASS** | `python -m pytest -q tests` |

If you try an unverified host, please file a "Host verification report" issue with the result.
