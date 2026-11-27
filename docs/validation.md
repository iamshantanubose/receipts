# Host validation log

| Check | Result | How |
|---|---|---|
| Agent Skills spec: frontmatter, name rules, description ≤ 1024, SKILL.md < 500 lines, referenced files exist | **PASS** | `tests/test_skill_spec.py` |
| Claude Code plugin + marketplace manifests | **PASS** | `claude plugin validate .` → "Validation passed" (Claude Code 2.1.260) |
| Skill workflow followed end to end by an agent in Claude Code | **PASS** | 3 benchmark runs (one per batch) read and followed `SKILL.md`, ran the scripts and returned reports ([`benchmark/results/`](../benchmark/results/)) |
| `/verify-engineering` slash invocation in a live Claude Code session | **PASS** | Claude Code 2.1.260, skill installed in a project's `.claude/skills/`, run on a copy of `demos/b-weakened-tests` as a git commit (`/verify-engineering audit the last commit against REQUIREMENTS.md`). The skill chose DEEP mode, ran the test-integrity scan (6 findings), the old-vs-new comparison, the mutation probe and an independent second pass, and returned NO-GO with the three behaviour defects and the weakened tests. Plugin route (`/verify-engineering:verify-engineering`) not yet run |
| Cursor Agent loading the skill from `.cursor/skills/` | **NOT VERIFIED** | Not yet run |
| Codex | **NOT VERIFIED** | Not yet run |
| `npx skills add iamshantanubose/receipts` | **NOT VERIFIED** | Not yet run against the published repository |
| Test suite on Python 3.9 and 3.13 (macOS) | **PASS** | `python -m pytest -q tests` |

If you try an unverified host, please file a "Host verification report" issue with the result.
