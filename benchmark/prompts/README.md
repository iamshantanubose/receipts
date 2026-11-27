# Benchmark prompts

These are the exact prompts used in the run reported in `../results/`. Only the paths were replaced with
placeholders:

- `<BATCH_DIR>`: a batch folder made by `../build_cases.py` (`OUT_DIR/flawed` or `OUT_DIR/controls`)
- `<LAST>`: `5` for the flawed batch, `3` for the controls batch
- `<SKILL_DIR>`: a copy of `skills/verify-engineering/` the agent can read

Each prompt went to a fresh agent session with no conversation history and with shell access. One agent
reviewed one whole batch. Every prompt ends with the same answer format (`output-format.md`), so the reports
can be compared line by line.

| Approach | Prompt |
|---|---|
| SELF: self-review | [`self-review.md`](self-review.md) |
| REVIEW: generic code review | [`generic-review.md`](generic-review.md) |
| VERIFY: this skill, audit only | [`verify-engineering.md`](verify-engineering.md) |

The K3 rerun (after the control port was fixed) used the controls prompt on a batch that held only the
rebuilt K3 case, as `case-1`.
