# Contributing

Thanks for helping. Issues and pull requests are both welcome.

## Most useful right now
- **Host verification reports.** Did the skill load and run in Cursor, Codex, or the Claude Code plugin route? Use the
  "Host verification report" issue template. See [docs/validation.md](docs/validation.md) for what is still unverified.
- **Scanner misses and false alarms.** A minimal before/after pair that `test_integrity_scan.py` gets wrong is the best bug report.
- **Harder benchmark cases.** See [ROADMAP.md](ROADMAP.md) and [benchmark/README.md](benchmark/README.md).

## Development
```bash
python3 -m pip install pytest
python3 -m pytest -q tests      # the Rust demo test also needs cargo and bash; it is skipped without them
```
- The scripts use the Python standard library only and must keep working on Python 3.9.
- Every behaviour change to a script needs a regression test in `tests/`.
- Keep `SKILL.md` short (it is loaded into the agent's context). Details belong in `references/`.
- Docs use British English (behaviour, authorised, normalise). Code identifiers stay as they are.

## Releases
Bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and the `SKILL.md` metadata, add a
`CHANGELOG.md` entry (`tests/test_skill_spec.py` checks they agree), then build the zip with `python3 tools/build_release.py`.
