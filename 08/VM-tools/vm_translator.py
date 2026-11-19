#!/usr/bin/env python3
"""nand2tetris VM translator (projects 7 & 8).

Translates .vm files into a single Hack assembly .asm file.

Usage:
    python vm_translator.py <file.vm | directory> [-o output.asm]
                           [--bootstrap | --no-bootstrap]

If a directory is given, all *.vm files inside are translated into
<directory name>.asm.  Bootstrap code (SP = 256; call Sys.init 0) is emitted
automatically when the input contains a Sys.vm file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ARITHMETIC = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
SEGMENT_BASE = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
POINTER_BASE = {"0": "THIS", "1": "THAT"}

# Scratch registers reserved by this translator.
FRAME = "R13"  # holds the caller's frame base in 'return'
RETADDR = "R14"  # holds the return address in 'return'
ADDR = "R13"  # holds a computed target address in push/pop


class CodeWriter:
    def __init__(self, filename: str, bootstrap: bool) -> None:
        self.filename = filename
        self.lines: list[str] = []
        self.current_function = ""
        self.counter = 0  # global, so labels never collide across files

    # ------------------------------------------------------------------ utils
    def emit(self, *lines: str) -> None:
        self.lines.extend(lines)

    def a(self, value: object) -> str:
        return f"@{value}"

    def unique(self, tag: str) -> str:
        self.counter += 1
        return f"{self.filename}${tag}.{self.counter}"

    def scoped(self, label: str) -> str:
        prefix = self.current_function or self.filename
        return f"{prefix}${label}"

    def static_symbol(self, index: str) -> str:
        return f"{self.filename}.{index}"

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8", newline="\n")

    # -------------------------------------------------------------- bootstrap
    def write_bootstrap(self) -> None:
        self.emit(
            "// bootstrap: SP = 256",
            self.a(256),
            "D=A",
            self.a("SP"),
            "M=D",
        )
        self.write_call("Sys.init", 0, bootstrap=True)

    # ------------------------------------------------------------ arithmetic
    def write_arithmetic(self, command: str) -> None:
        if command in {"add", "sub", "and", "or"}:
            op = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}[command]
            self.emit(
                f"// {command}",
                self.a("SP"),
                "M=M-1",
                "A=M",
                "D=M",  # D = y (the value that was popped)
                self.a("SP"),
                "A=M-1",  # x is now at SP-1
                f"M={op}",
            )
        elif command in {"neg", "not"}:
            op = "-M" if command == "neg" else "!M"
            self.emit(
                f"// {command}",
                self.a("SP"),
                "A=M-1",  # top of stack is at SP-1
                f"M={op}",
            )
        else:  # eq, gt, lt
            jump = {"eq": "JNE", "gt": "JLE", "lt": "JGE"}[command]
            false_label = self.unique(f"{command}_false")
            end_label = self.unique(f"{command}_end")
            self.emit(
                f"// {command}",
                self.a("SP"),
                "M=M-1",
                "A=M",
                "D=M",  # D = y
                self.a("SP"),
                "M=M-1",
                "A=M",
                "D=M-D",  # D = x - y
                self.a(false_label),
                f"D;{jump}",
                self.a("SP"),
                "A=M",
                "M=-1",
                self.a(end_label),
                "0;JMP",
                f"({false_label})",
                self.a("SP"),
                "A=M",
                "M=0",
                f"({end_label})",
                "",
                self.a("SP"),
                "M=M+1",
            )

    # ----------------------------------------------------------- memory access
    def write_push(self, segment: str, index: str) -> None:
        self.emit(f"// push {segment} {index}")
        if segment == "constant":
            self.emit(self.a(index), "D=A")
        elif segment == "static":
            self.emit(self.a(self.static_symbol(index)), "D=M")
        elif segment == "temp":
            self.emit(self.a(5 + int(index)), "D=M")
        elif segment == "pointer":
            self.emit(self.a(POINTER_BASE[index]), "D=M")
        else:
            self.emit(self.a(index), "D=A", self.a(SEGMENT_BASE[segment]), "A=D+M", "D=M")

        self.emit(
            self.a("SP"),
            "A=M",
            "M=D",
            self.a("SP"),
            "M=M+1",
        )

    def write_pop(self, segment: str, index: str) -> None:
        self.emit(f"// pop {segment} {index}")
        if segment == "static":
            target = self.static_symbol(index)
        elif segment == "temp":
            target = 5 + int(index)
        elif segment == "pointer":
            target = POINTER_BASE[index]
        else:
            self.emit(self.a(index), "D=A", self.a(SEGMENT_BASE[segment]), "D=D+M")
            target = ADDR

        if segment in {"static", "temp", "pointer"}:
            self.emit(self.a(target), "D=A")
        # else: D already holds the computed address (LCL/ARG/THIS/THAT + index)
        self.emit(
            self.a(ADDR),
            "M=D",
            self.a("SP"),
            "M=M-1",
            "A=M",
            "D=M",
            self.a(ADDR),
            "A=M",
            "M=D",
        )

    # -------------------------------------------------------------- branching
    def write_label(self, label: str) -> None:
        self.emit(f"// label {label}", f"({self.scoped(label)})")

    def write_goto(self, label: str) -> None:
        self.emit(
            f"// goto {label}",
            self.a(self.scoped(label)),
            "0;JMP",
        )

    def write_if_goto(self, label: str) -> None:
        self.emit(
            f"// if-goto {label}",
            self.a("SP"),
            "M=M-1",
            "A=M",
            "D=M",
            self.a(self.scoped(label)),
            "D;JNE",
        )

    # --------------------------------------------------------------- functions
    def write_function(self, name: str, n_locals: str) -> None:
        self.current_function = name
        self.emit(f"// function {name} {n_locals}", f"({name})")
        for _ in range(int(n_locals)):
            self.emit(self.a("SP"), "A=M", "M=0", self.a("SP"), "M=M+1")

    def write_call(self, name: str, n_args: str | int, bootstrap: bool = False) -> None:
        return_label = self.unique("ret")
        self.emit(
            f"// call {name} {n_args}",
            self.a(return_label),
            "D=A",
            self.a("SP"),
            "A=M",
            "M=D",
            self.a("SP"),
            "M=M+1",
        )

        for segment in ("LCL", "ARG", "THIS", "THAT"):
            self.emit(self.a(segment), "D=M", self.a("SP"), "A=M", "M=D", self.a("SP"), "M=M+1")

        # ARG = SP - nArgs - 5
        self.emit(
            self.a("SP"),
            "D=M",
            self.a(n_args),
            "D=D-A",
            self.a(5),
            "D=D-A",
            self.a("ARG"),
            "M=D",
            # LCL = SP
            self.a("SP"),
            "D=M",
            self.a("LCL"),
            "M=D",
            self.a(name),
            "0;JMP",
            f"({return_label})",
        )
        if bootstrap:
            self.emit("")

    def write_return(self) -> None:
        # FRAME = LCL; RET = *(FRAME - 5)
        self.emit(
            "// return",
            self.a("LCL"),
            "D=M",
            self.a(FRAME),
            "M=D",
            self.a(5),
            "A=D-A",
            "D=M",
            self.a(RETADDR),
            "M=D",
            # *ARG = pop()
            self.a("SP"),
            "M=M-1",
            "A=M",
            "D=M",
            self.a("ARG"),
            "A=M",
            "M=D",
            # SP = ARG + 1
            self.a("ARG"),
            "D=M+1",
            self.a("SP"),
            "M=D",
        )

        # Restore THAT, THIS, ARG, LCL from the saved frame.
        for offset, segment in ((1, "THAT"), (2, "THIS"), (3, "ARG"), (4, "LCL")):
            self.emit(
                self.a(FRAME),
                "D=M",
                self.a(offset),
                "A=D-A",
                "D=M",
                self.a(segment),
                "M=D",
            )

        self.emit(self.a(RETADDR), "A=M", "0;JMP", "")


def parse(line: str) -> list[str] | None:
    line = line.split("//", 1)[0].strip()
    return line.split() if line else None


def translate_files(files: list[Path], bootstrap: bool) -> CodeWriter:
    writer = CodeWriter(files[0].stem, bootstrap)
    if bootstrap:
        writer.write_bootstrap()

    for path in files:
        # static variables are file-scoped: switch the symbol prefix per file,
        # while keeping one shared counter so all generated labels stay unique.
        writer.filename = path.stem
        for raw in path.read_text(encoding="utf-8").splitlines():
            tokens = parse(raw)
            if not tokens:
                continue
            op = tokens[0]
            if op in ARITHMETIC:
                writer.write_arithmetic(op)
            elif op == "push":
                writer.write_push(tokens[1], tokens[2])
            elif op == "pop":
                writer.write_pop(tokens[1], tokens[2])
            elif op == "label":
                writer.write_label(tokens[1])
            elif op == "goto":
                writer.write_goto(tokens[1])
            elif op == "if-goto":
                writer.write_if_goto(tokens[1])
            elif op == "function":
                writer.write_function(tokens[1], tokens[2])
            elif op == "call":
                writer.write_call(tokens[1], tokens[2])
            elif op == "return":
                writer.write_return()
            else:
                raise ValueError(f"Unknown VM command in {path.name}: {raw!r}")
        writer.lines.append("")
    return writer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="a .vm file or a directory of .vm files")
    parser.add_argument("-o", "--output", type=Path, help="explicit output .asm path")
    bootstrap = parser.add_mutually_exclusive_group()
    bootstrap.add_argument("--bootstrap", dest="bootstrap", action="store_true", default=None,
                           help="force bootstrap code")
    bootstrap.add_argument("--no-bootstrap", dest="bootstrap", action="store_false",
                           help="do not emit bootstrap code")
    args = parser.parse_args(argv)

    path = args.path.resolve()
    if path.is_dir():
        files = sorted(
            (f for f in path.glob("*.vm")),
            key=lambda f: (f.stem != "Sys", f.name.lower()),
        )
        if not files:
            parser.error(f"no .vm files in {path}")
        out = args.output or path / f"{path.name}.asm"
        want_bootstrap = args.bootstrap if args.bootstrap is not None else any(
            f.stem == "Sys" for f in files
        )
    elif path.is_file() and path.suffix == ".vm":
        files = [path]
        out = args.output or path.with_suffix(".asm")
        want_bootstrap = args.bootstrap if args.bootstrap is not None else path.stem == "Sys"
    else:
        parser.error(f"expected a .vm file or a directory, got {path}")

    writer = translate_files(files, want_bootstrap)
    writer.save(out)
    print(f"{out}  ({len(writer.lines)} lines, bootstrap={want_bootstrap})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
