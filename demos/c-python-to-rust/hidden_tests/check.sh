#!/usr/bin/env bash
# Ground truth for scenario C: the flawed port must diverge from legacy; the control must match 100%.
# Needs bash and cargo. PYTHON selects the interpreter (default: python3). Builds go to a temp folder.
set -u
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
H=../../skills/verify-engineering/scripts/diff_harness.py
WORK="$(mktemp -d "${TMPDIR:-/tmp}/scenario-c.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
cargo build -q --release --manifest-path rust_port/Cargo.toml --target-dir "$WORK/flawed" &&
  cargo build -q --release --manifest-path control_rust/Cargo.toml --target-dir "$WORK/control" || exit 2
CORPUS="$WORK/corpus.tsv"
cat hidden_tests/hidden_corpus.tsv hidden_tests/big_ints.tsv > "$CORPUS"
"$PY" hidden_tests/gen_corpus.py 5000 11 >> "$CORPUS"
"$PY" "$H" --old "$PY legacy_python/normalize.py" --new "$WORK/flawed/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
flawed=$?
"$PY" "$H" --old "$PY legacy_python/normalize.py" --new "$WORK/control/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
control=$?
echo "flawed_port_exit=$flawed (expect 1)  control_exit=$control (expect 0)"
[ "$flawed" = 1 ] && [ "$control" = 0 ]
