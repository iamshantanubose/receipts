#!/usr/bin/env bash
# Ground truth for scenario C: the flawed port must diverge from legacy; the control must match 100%.
set -u
cd "$(dirname "$0")/.."
H=../../skills/verify-engineering/scripts/diff_harness.py
(cd rust_port && cargo build -q --release) && (cd control_rust && cargo build -q --release) || exit 2
CORPUS="$(mktemp -t scenario-c-corpus.XXXXXX)"
cat hidden_tests/hidden_corpus.tsv hidden_tests/big_ints.tsv > "$CORPUS"
python3 hidden_tests/gen_corpus.py 5000 11 >> "$CORPUS"
python3 "$H" --old "python3 legacy_python/normalize.py" --new "rust_port/target/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
flawed=$?
python3 "$H" --old "python3 legacy_python/normalize.py" --new "control_rust/target/release/normalize" \
  --inputs "$CORPUS" --max-examples 0 >/dev/null
control=$?
echo "flawed_port_exit=$flawed (expect 1)  control_exit=$control (expect 0)"
[ "$flawed" = 1 ] && [ "$control" = 0 ]
