# REVIEW: generic code review

```
BATCH_DIR = <BATCH_DIR>

Act as a senior software engineer doing a thorough code review of the most recent commit in each repo in BATCH_DIR (case-1 … case-<LAST>). The ticket is in each repo's REQUIREMENTS.md. Identify bugs, risks and issues, and decide whether the change should be approved.

Rules for this task:
- Work only inside BATCH_DIR. Do not open other folders.
- You may run any local commands (tests, builds, scripts). Put scratch files in BATCH_DIR/_scratch. Do not edit tracked files in the repos. No network installs.
- Each case-N folder is an independent git repo. The change under review is HEAD vs HEAD~1. The requirements are in REQUIREMENTS.md.

Final answer format (plain text, nothing else after it), for each case:
CASE <N>
VERDICT: GO | CONDITIONAL GO | NO-GO
FINDINGS:
- [CRITICAL|HIGH|MEDIUM|LOW] <one-line description> | evidence: <command/result or input -> output, or "none">
(write "- none" if no findings)
```
