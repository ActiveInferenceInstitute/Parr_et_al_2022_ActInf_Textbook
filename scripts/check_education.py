#!/usr/bin/env python3
"""Check this actual member checkout using an explicitly selected courses producer.

COURSES_ROOT (or --courses-root) must provide the producer's explicit repo_root
check_member API. There is no installed-package, sibling-layout or symlink fallback,
no local schema validator, and no producer generation or provisioning step.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent
MEMBER_ID = "Parr_et_al_2022_ActInf_Textbook"
MEMBER_REPOSITORY = f"ActiveInferenceInstitute/{MEMBER_ID}"
_PRODUCER_MODULE = "_textbook_education_producer"


def courses_root(explicit: str | Path | None = None) -> Path:
    value = explicit if explicit is not None else os.environ.get("COURSES_ROOT")
    if value is None or not str(value).strip():
        raise ValueError("COURSES_ROOT or --courses-root is required; qualify the courses producer first")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"courses checkout is unavailable: {root}")
    return root


@contextmanager
def _producer(root: Path) -> Iterator[ModuleType]:
    package = root / "software" / "src" / "education_contract"
    entrypoint = package / "__init__.py"
    if not entrypoint.is_file():
        raise ValueError(f"courses producer is unavailable: {entrypoint}")
    if _PRODUCER_MODULE in sys.modules:
        raise RuntimeError("an education producer check is already active")
    spec = importlib.util.spec_from_file_location(
        _PRODUCER_MODULE, entrypoint, submodule_search_locations=[str(package)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load courses producer from {entrypoint}")
    producer = importlib.util.module_from_spec(spec)
    saved_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.modules[_PRODUCER_MODULE] = producer
    try:
        spec.loader.exec_module(producer)
        yield producer
    finally:
        for name in tuple(sys.modules):
            if name == _PRODUCER_MODULE or name.startswith(_PRODUCER_MODULE + "."):
                del sys.modules[name]
        sys.dont_write_bytecode = saved_bytecode


def check_education(source_root: Path, member_checkout: Path) -> dict:
    source_root = courses_root(source_root)
    member_checkout = member_checkout.expanduser().resolve()
    canonical_schema = source_root / "specs" / "education" / "schema.json"
    with _producer(source_root) as producer:
        registry = producer.load_registry(source_root / "specs" / "education" / "contract.json")
        members = [
            member for member in registry.members
            if member.id == MEMBER_ID and member.repository == MEMBER_REPOSITORY
        ]
        if len(members) != 1:
            raise ValueError(f"courses registry must identify exactly one {MEMBER_REPOSITORY} member")
        member = members[0]
        signature = inspect.signature(producer.check_member)
        if "repo_root" not in signature.parameters:
            raise ValueError(
                "courses check_member must expose the explicit repo_root API; "
                "qualify the updated producer first (no fallback)"
            )
        signature.bind(None, member, canonical_schema=canonical_schema, repo_root=member_checkout)
        state = producer.check_member(
            None, member, canonical_schema=canonical_schema, repo_root=member_checkout
        )
        return {
            "schema": "textbook-education-check/v1",
            "courses_root": str(source_root),
            "member_checkout": str(member_checkout),
            "member_id": state.id,
            "repository": state.repository,
            "state": state.state,
            "detail": state.detail,
            "ok": state.state == producer.ADOPTED and not state.issues,
            "declared_bundles": list(state.bundles),
            "issues": [
                {"code": issue.code, "location": issue.location, "message": issue.message}
                for issue in state.issues
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--courses-root", help="explicit courses source checkout; otherwise COURSES_ROOT")
    parser.add_argument("--member-checkout", type=Path, default=ROOT, help="actual member checkout to validate")
    args = parser.parse_args(argv)
    try:
        receipt = check_education(courses_root(args.courses_root), args.member_checkout)
    except (OSError, ValueError, TypeError, RuntimeError, ImportError, AttributeError, SyntaxError) as error:
        print(f"education: {error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
