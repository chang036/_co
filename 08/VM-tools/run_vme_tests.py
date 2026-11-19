#!/usr/bin/env python3
"""Run every project 7/8 VM Emulator test script (*VME.tst).

The bundled VM Emulator has a parser quirk: leading tabs before `label` or
`function` break label resolution.  For those files we run a cleaned copy
in a temp directory, leaving the official project files untouched.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = [ROOT / "projects" / "7", ROOT / "projects" / "8"]
VME = ROOT / "tools" / "VMEmulator.bat"


def clean_source(path: Path, dest_dir: Path) -> Path:
    """Copy a .vm file, trimming leading whitespace on label/function lines."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("label ", "function ")):
            line = stripped
        lines.append(line)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return dest


def main() -> int:
    tests = [
        t for project in PROJECTS
        for t in sorted(project.rglob("*VME.tst"))
    ]
    failed = []
    with tempfile.TemporaryDirectory(prefix="nand2tetris-vme-") as tmp:
        for t in tests:
            target = t
            if t.name == "NestedCallVME.tst":
                work = Path(tmp) / "NestedCall"
                work.mkdir(exist_ok=True)
                for f in t.parent.iterdir():
                    if f.suffix in {".vm", ".cmp"}:
                        shutil.copy2(f, work / f.name)
                for vm in work.glob("*.vm"):
                    clean_source(vm, work)
                shutil.copy2(t, work / t.name)
                target = work / t.name

            r = subprocess.run([str(VME), str(target)], capture_output=True, text=True)
            out = r.stdout + r.stderr
            ok = r.returncode == 0 and "Comparison ended successfully" in out
            print(f"[{'PASS' if ok else 'FAIL'}] {t.parent.name}/{t.name}")
            if not ok:
                failed.append((t, out.strip()))

    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    for t, out in failed:
        print(f"\n--- {t} ---\n{out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
