#!/usr/bin/env bash
# Single gate entry point. GitHub Actions calls its configured arms unchanged.
# The education arm additionally requires an explicitly qualified COURSES_ROOT.
#
#   ./run.sh --list        name and exact command of every arm
#   ./run.sh <arm> [...]   run one or more arms
#   ./run.sh fast          lint + tests + plaintext + docs (no Julia, no network)
#   ./run.sh full          all validation arms (COURSES_ROOT and GNN prerequisites required)
#
# Arms: lint, tests, plaintext, docs, education, vfe, gnn, fast, full, report.
# Wall times and gate facts: docs/_generated/GATES.md (regenerate with ./run.sh report).
set -euo pipefail
cd "$(dirname "$0")"

command_for() {
  case "$1" in
    lint)      echo 'python3 scripts/lint_sources.py' ;;
    tests)     echo 'python3 -m unittest scripts.test_clean_plaintext scripts.test_check_gnn_conformance scripts.test_check_docs scripts.test_check_education.AdapterTests' ;;
    plaintext) echo 'python3 scripts/clean_plaintext.py' ;;
    docs)      echo 'python3 scripts/check_docs.py' ;;
    education) echo 'python3 -m unittest scripts.test_check_education.MemberContractTests && python3 scripts/check_education.py' ;;
    vfe)       echo 'julia Chapters/test_vfe.jl' ;;
    gnn)       echo 'python3 scripts/check_gnn_conformance.py' ;;
    fast)      echo './run.sh lint && ./run.sh tests && ./run.sh plaintext && ./run.sh docs' ;;
    full)      echo './run.sh lint && ./run.sh tests && ./run.sh plaintext && ./run.sh docs && ./run.sh education && ./run.sh vfe && ./run.sh gnn' ;;
    report)    echo 'python3 scripts/gate_report.py' ;;
    *)         return 1 ;;
  esac
}

arms() {
  printf '%s\n' lint tests plaintext docs education vfe gnn fast full report
}

usage() {
  cat <<'EOF'
usage: ./run.sh --list | ./run.sh <arm> [<arm> ...]

arms:
  lint       tracked Python compiles, tracked JSON/notebooks parse
  tests      hermetic cleaner, GNN, Markdown and education-admission regressions
  plaintext  plaintext integrity invariant (report only, writes nothing)
  docs       relative links resolve, docs/ pages reachable from the index
  education  real producer/member controls + actual member check; COURSES_ROOT required
  vfe        Julia VFE regression suite
  gnn        pinned GNN conformance check (needs network)
  fast       lint + tests + plaintext + docs
  full       every validation arm above (including explicit education prerequisite)
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
