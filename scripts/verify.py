#!/usr/bin/env python3
"""Canonical VeloBid verification entrypoint."""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "velobid-verify/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def assert_contains(name: str, body: str, needle: str) -> None:
    if needle not in body:
        raise RuntimeError(f"{name} missing expected text: {needle}")


def run_unit_tests() -> None:
    print("== Unit Tests ==", flush=True)
    run([sys.executable, "-m", "pytest", "tests/test_validation.py"])


def run_live_checks(backend_url: str, frontend_url: str | None) -> None:
    print("== Live Checks ==", flush=True)

    backend_checks: list[tuple[str, str, str | None]] = [
        ("backend meta", f"{backend_url.rstrip('/')}/api/v1/meta", None),
        ("backend health", f"{backend_url.rstrip('/')}/api/v1/health", None),
        ("backend root", f"{backend_url.rstrip('/')}/", "VeloBid"),
    ]

    for name, url, needle in backend_checks:
        try:
            status, body = fetch(url)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{name} unreachable at {url}: {exc}") from exc

        if status >= 400:
            raise RuntimeError(f"{name} returned HTTP {status} at {url}")
        if needle:
            assert_contains(name, body, needle)
        print(f"PASS  {name} -> {url}", flush=True)

    if frontend_url:
        url = frontend_url.rstrip("/") + "/"
        try:
            status, body = fetch(url)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"frontend unreachable at {url}: {exc}") from exc

        if status >= 400:
            raise RuntimeError(f"frontend returned HTTP {status} at {url}")
        assert_contains("frontend root", body, "VeloBid")
        print(f"PASS  frontend root -> {url}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VeloBid verification checks.")
    parser.add_argument("--live", action="store_true", help="Run live HTTP smoke checks.")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend-url", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_unit_tests()

    if args.live:
        run_live_checks(args.backend_url, args.frontend_url)

    print("== Done ==", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
