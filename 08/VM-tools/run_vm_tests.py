#!/usr/bin/env python3
"""Regenerate every project 7/8 .asm and run the official CPU emulator tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = [ROOT / "projects" / "7", ROOT / "projects" / "8"]
TOOLS = ROOT / "tools"
CLASSPATH = ";".join([
    "bin/classes",
    "bin/lib/Hack.jar",
    "bin/lib/HackGUI.jar",
    "bin/lib/Simulators.jar",
    "bin/lib/SimulatorsGUI.jar",
    "bin/lib/Compilers.jar",
])


def main() -> int:
    dirs = [
        d for project in PROJECTS
        for d in sorted(project.rglob("*"))
        if d.is_dir() and any(d.glob("*.vm"))
    ]
    for d in dirs:
        subprocess.run(
            [sys.executable, str(ROOT / "vm_translator.py"), str(d)],
            check=True, capture_output=True, text=True,
        )

    tests = [
        t for project in PROJECTS
        for t in sorted(project.rglob("*.tst"))
        if "VME" not in t.name
    ]
    failed = []
    for t in tests:
        result = subprocess.run(
            ["java", "-classpath", CLASSPATH, "CPUEmulatorMain", str(t)],
            cwd=TOOLS, capture_output=True, text=True,
        )
        ok = result.returncode == 0 and "Comparison ended successfully" in result.stdout
        print(f"[{'PASS' if ok else 'FAIL'}] {t.parent.name}/{t.name}")
        if not ok:
            failed.append((t, result.stdout + result.stderr))

    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    for t, output in failed:
        print(f"\n--- {t} ---\n{output}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
