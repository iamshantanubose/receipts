# Troubleshooting

| Problem | Fix |
|---|---|
| `/verify-engineering` doesn't show up | Check the folder path: it must be `.../skills/verify-engineering/SKILL.md`, not one level deeper and not flattened into `skills/` itself. Restart the agent session. |
| Installed as a Claude Code plugin, but `/verify-engineering` doesn't exist | Plugin skills are namespaced: `/verify-engineering:verify-engineering`. |
| `python3: command not found` | Install Python 3.9+. On Windows, use `py` or `python` in place of `python3`. |
| `test_integrity_scan.py` says "not a git repository" | Run it from inside the repo, pass `--repo <path>`, or compare two folders with `--before old/ --after new/` (git must still be installed). |
| `unknown git ref 'main'` | The base branch has another name (`master`, `develop`) or isn't fetched. Pass the right one to `--base`. |
| Scanner flags something that is fine | It's a triage tool. The agent confirms every hit by reading the code. If the change is justified (for example, a real requirement change), the report says so. |
| `mutation_probe.py` exits 2: "fails BEFORE any mutation" | Your tests already fail in the temporary copy. Fix or report that first. The probe only works on a green suite. |
| `mutation_probe.py` exits 2: "no mutation points found" | The target has no comparisons, arithmetic, booleans or 0/1 literals to change, so nothing was tested. Pick another file. This is never a pass. |
| "commands run without a shell" | Neither script uses a shell. Put pipes, `&&` or redirects in a small script and pass the script. |
| Mutation probe is slow | Lower `--max`, use a faster test command (`-x`, a single test file), or point `--target` at one file. |
| `diff_harness.py` shows 0% match | Usually the two commands read input differently (one file vs line by line). Try `--mode each`, and check that both commands work on their own. |
| Agent wants to install packages | That's by design: it must ask first. Say yes or no. The core workflow needs only Python and git. |
| Report says NOT VERIFIED a lot | Something could not run (no test command, missing toolchain). Give the agent the test command, or install the toolchain, and rerun. |
