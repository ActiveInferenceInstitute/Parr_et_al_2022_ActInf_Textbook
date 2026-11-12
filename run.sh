#!/usr/bin/env bash
# Single gate entry point. Every arm is exactly the command GitHub Actions runs
# (.github/workflows/ci.yml calls these arms, it does not repeat their commands).
#
#   ./run.sh --list        name and exact command of every arm
#   ./run.sh <arm> [...]   run one or more arms
#   ./run.sh fast          lint + plaintext + docs (no Julia, no network)
#   ./run.sh full          every arm
#
# Arms: lint, plaintext, docs, vfe, gnn, fast, full, report.
# Wall times and gate facts: docs/_generated/GATES.md (regenerate with ./run.sh report).
set -euo pipefail
cd "$(dirname "$0")"

command_for() {
  case "$1" in
    lint)      echo 'python3 scripts/lint_sources.py' ;;
    plaintext) echo 'python3 scripts/clean_plaintext.py' ;;
    docs)      echo 'python3 scripts/check_docs.py' ;;
    vfe)       echo 'julia Chapters/test_vfe.jl' ;;
    gnn)       echo 'python3 scripts/check_gnn_conformance.py' ;;
    fast)      echo './run.sh lint && ./run.sh plaintext && ./run.sh docs' ;;
    full)      echo './run.sh lint && ./run.sh plaintext && ./run.sh docs && ./run.sh vfe && ./run.sh gnn' ;;
    report)    echo 'python3 scripts/gate_report.py' ;;
    *)         return 1 ;;
  esac
}

arms() {
  printf '%s\n' lint plaintext docs vfe gnn fast full report
}

usage() {
  cat <<'EOF'
usage: ./run.sh --list | ./run.sh <arm> [<arm> ...]

arms:
  lint       tracked Python compiles, tracked JSON/notebooks parse
  plaintext  plaintext integrity invariant (report only, writes nothing)
  docs       relative links resolve, docs/ pages reachable from the index
  vfe        Julia VFE regression suite
  gnn        pinned GNN conformance check (needs network)
  fast       lint + plaintext + docs
  full       every arm above
  report     rewrite docs/_generated/GATES.md with measured arm wall times
EOF
}

if [ "${1:-}" = "--list" ]; then
  for arm in $(arms); do
    printf '%s\t%s\n' "$arm" "$(command_for "$arm")"
  done
  exit 0
fi

if [ "$#" -eq 0 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 2
fi

for arm in "$@"; do
  if ! command="$(command_for "$arm")"; then
    echo "run.sh: unknown arm '$arm'" >&2
    echo "run.sh: known arms: $(arms | tr '\n' ' ')" >&2
    exit 2
  fi
  echo "== $arm: $command" >&2
  bash -c "$command"
done
