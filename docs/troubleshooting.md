# Troubleshooting

| Problem | Fix |
|---|---|
| `/verify-engineering` doesn't show up | Check the folder path: it must be `.../skills/verify-engineering/SKILL.md`, not one level deeper. Restart the agent session. |
| Installed as a Claude Code plugin, but `/verify-engineering` doesn't exist | Plugin skills are namespaced: `/verify-engineering:verify-engineering`. |
| `python3: command not found` | Install Python 3.9+. On Windows, use `py` or `python` in place of `python3`. |
| `test_integrity_scan.py` says "not a git repository" | Run it from inside the repo, pass `--repo <path>`, or compare two folders with `--before old/ --after new/`. |
| Scanner flags something that is fine | It's a triage tool. The agent confirms every hit by reading the code. If the change is justified (for example, a real requirement change), the report says so. |
| `mutation_probe.py` exits with code 2 | Your tests already fail before any mutation. Fix or report that first. The probe only works on a green suite. |
| Mutation probe is slow | Lower `--max`, use a faster test command (`-x`, a single test file), or point `--target` at one file. |
| `diff_harness.py` shows 0% match | Usually the two commands read input differently (one file vs line-by-line). Try `--mode each`, and check that both commands work on their own. |
| Agent wants to install packages | That's by design: it must ask first. Say yes or no. The core workflow needs only Python and git. |
| Report says NOT VERIFIED a lot | Something could not run (no test command, missing toolchain). Give the agent the test command, or install the toolchain, and rerun. |
