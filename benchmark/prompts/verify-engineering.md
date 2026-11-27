# VERIFY: the verify-engineering skill, audit only

```
BATCH_DIR = <BATCH_DIR>
SKILL FILE (read it first and follow it exactly; its references/ and scripts/ are in the same folder): <SKILL_DIR>/SKILL.md

Task: the most recent commit in each repo in BATCH_DIR (case-1 … case-<LAST>) implements the ticket in its REQUIREMENTS.md. Using the skill above (audit only), determine whether each change is complete, correct and ready to merge.

Rules for this task:
- Work only inside BATCH_DIR (and read-only access to the skill folder named above). Do not open other folders.
- You may run any local commands (tests, builds, scripts). Put scratch files in BATCH_DIR/_scratch. Do not edit tracked files in the repos. No network installs.
- Each case-N folder is an independent git repo. The change under review is HEAD vs HEAD~1. The requirements are in REQUIREMENTS.md.
- Skip writing a full report file per case; the final answer below is the report for this task.

Final answer format (plain text, nothing else after it), for each case:
CASE <N>
VERDICT: GO | CONDITIONAL GO | NO-GO
FINDINGS:
- [CRITICAL|HIGH|MEDIUM|LOW] <one-line description> | evidence: <command/result or input -> output, or "none">
(write "- none" if no findings)
```
