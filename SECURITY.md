# Security policy

## Supported versions
Only the latest release receives fixes.

## Reporting a vulnerability
Please report security problems privately through GitHub: **Security → Report a vulnerability** on this repository
(private vulnerability reporting). Do not open a public issue for them.

Useful details: the affected script or skill instruction, the version or commit, steps to reproduce, and the impact.
Expect a first reply within 7 days.

## Scope
In scope:
- the bundled scripts (`test_integrity_scan.py`, `diff_harness.py`, `mutation_probe.py`), for example a way to make the mutation
  probe write outside its temporary copy, or path or argument injection;
- instructions in `SKILL.md` or `references/` that would lead an agent to take an unsafe action, for example following
  instructions embedded in the repository under review.

Out of scope: the code that the skill is asked to verify, and the behaviour of the host agent itself.

## What the skill does and does not enforce
The skill's guardrails are instructions to an AI agent. They do not sandbox anything. Running a project's tests, the mutation
probe or the differential harness executes that project's code with your permissions. Keep your host's permission prompts on, and
review changes from untrusted contributors only inside a container or VM.
