# Wroteassembler.py
#!/usr/bin/env python3
"""Hack 組譯器（nand2tetris Project 6）

將 Hack 組合語言（.asm）翻譯成 16 位元機器碼（.hack）。

用法：
    python assembler.py add/Add.asm
    python assembler.py add/Add.asm max/Max.asm
    python assembler.py add          # 組譯資料夾內所有 .asm

支援：
    - A 指令：@value（十進位常數或符號）
    - C 指令：dest=comp;jump
    - 標籤：  (LABEL)
    - 註解：  // ...
    - 預定義符號：R0-R15、SP、LCL、ARG、THIS、THAT、SCREEN、KBD
    - 未定義符號會從 RAM[16] 開始自動配置
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 符號表
# ---------------------------------------------------------------------------

PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,
}
PREDEFINED_SYMBOLS.update({f"R{i}": i for i in range(16)})

# 符號允許的字元：字母、數字、底線、點、錢號、冒號；不可用數字開頭
SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")
MAX_ADDRESS = 32767  # 16 位元指令中位址欄位可表示的最大值


class AsmError(Exception):
    """組譯錯誤，包含來源檔案與行號。"""

    def __init__(self, path: Path, line_no: int, message: str):
        self.path = path
        self.line_no = line_no
        self.message = message
        super().__init__(f"{path}:{line_no}: {message}")


# ---------------------------------------------------------------------------
# 指令編碼表
# ---------------------------------------------------------------------------

DEST_TABLE = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

JUMP_TABLE = {
    "": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

COMP_TABLE = {
    # a = 0
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    # a = 1
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}


# ---------------------------------------------------------------------------
# 剖析器
# ---------------------------------------------------------------------------


class Parser:
    """讀入 .asm，去除註解與空白，保留原始行號以便報錯。"""

    def __init__(self, path: Path):
        self.path = path
        self.instructions: list[tuple[int, str]] = []

        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise AsmError(path, 0, f"無法讀取檔案：{exc}") from exc

        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            code = raw_line.split("//", 1)[0].strip()
            if code:
                self.instructions.append((line_no, code))

    def __iter__(self):
        return iter(self.instructions)


# ---------------------------------------------------------------------------
# 組譯流程
# ---------------------------------------------------------------------------


def validate_symbol(path: Path, line_no: int, symbol: str) -> None:
    if not symbol:
        raise AsmError(path, line_no, "符號不可為空")
    if not SYMBOL_RE.match(symbol):
        raise AsmError(
            path,
            line_no,
            f"無效的符號 {symbol!r}（只能使用字母、數字、_ . $ :，且不可用數字開頭）",
        )


def first_pass(parser: Parser) -> dict[str, int]:
    """紀錄所有 (LABEL) 對應的 ROM 位址。"""
    symbols: dict[str, int] = {}
    rom_address = 0

    for line_no, instruction in parser:
        if instruction.startswith("("):
            if not instruction.endswith(")"):
                raise AsmError(parser.path, line_no, f"標籤格式錯誤：{instruction}")
            label = instruction[1:-1].strip()
            validate_symbol(parser.path, line_no, label)
            if label in PREDEFINED_SYMBOLS:
                raise AsmError(parser.path, line_no, f"不可重新定義預定義符號 {label!r}")
            if label in symbols:
                raise AsmError(parser.path, line_no, f"標籤重複定義：{label!r}")
            symbols[label] = rom_address
        else:
            rom_address += 1
            if rom_address > MAX_ADDRESS + 1:
                raise AsmError(parser.path, line_no, "程式超過 ROM 可定址範圍")

    return symbols


def encode_a_instruction(
    path: Path, line_no: int, instruction: str, symbols: dict[str, int], next_ram: int
) -> tuple[str, int]:
    """將 @value 編碼成 0vvvvvvvvvvvvvvv，回傳 (機器碼, 下一個可用 RAM 位址)。"""
    value_text = instruction[1:].strip()
    if not value_text:
        raise AsmError(path, line_no, "A 指令缺少數值或符號")

    if value_text.isdigit():
        value = int(value_text)
    else:
        validate_symbol(path, line_no, value_text)
        if value_text not in symbols:
            symbols[value_text] = next_ram
            next_ram += 1
        value = symbols[value_text]

    if value > MAX_ADDRESS:
        raise AsmError(path, line_no, f"位址 {value} 超出範圍（最大 {MAX_ADDRESS}）")

    return format(value, "016b"), next_ram


def encode_c_instruction(path: Path, line_no: int, instruction: str) -> str:
    """將 dest=comp;jump 編碼成 111accccccdddjjj。"""
    code = re.sub(r"\s+", "", instruction)  # 容許 "D = M" 之類的寫法
    if "=" in code:
        dest_text, comp_text = code.split("=", 1)
    else:
        dest_text, comp_text = "", code

    if ";" in comp_text:
        comp_text, jump_text = comp_text.split(";", 1)
    else:
        jump_text = ""

    if "=" in comp_text or ";" in jump_text:
        raise AsmError(path, line_no, f"C 指令格式錯誤：{instruction}")

    try:
        dest_bits = DEST_TABLE[dest_text]
    except KeyError:
        raise AsmError(path, line_no, f"無效的 dest：{dest_text!r}") from None

    try:
        comp_bits = COMP_TABLE[comp_text]
    except KeyError:
        raise AsmError(path, line_no, f"無效的 comp：{comp_text!r}") from None

    try:
        jump_bits = JUMP_TABLE[jump_text]
    except KeyError:
        raise AsmError(path, line_no, f"無效的 jump：{jump_text!r}") from None

    return f"111{comp_bits}{dest_bits}{jump_bits}"


def assemble_file(source: Path, output: Path | None = None) -> Path:
    """組譯單一 .asm 檔案，回傳輸出的 .hack 路徑。"""
    source = source.resolve()
    if not source.is_file():
        raise AsmError(source, 0, "找不到檔案")
    if source.suffix.lower() != ".asm":
        raise AsmError(source, 0, "輸入檔案的副檔名必須是 .asm")

    parser = Parser(source)
    symbols = dict(PREDEFINED_SYMBOLS)
    symbols.update(first_pass(parser))

    next_ram = 16
    machine_code: list[str] = []

    for line_no, instruction in parser:
        if instruction.startswith("("):
            continue  # 標籤不產生機器碼

        if instruction.startswith("@"):
            binary, next_ram = encode_a_instruction(
                source, line_no, instruction, symbols, next_ram
            )
        else:
            binary = encode_c_instruction(source, line_no, instruction)

        machine_code.append(binary)

    if output is None:
        output = source.with_suffix(".hack")

    try:
        output.write_text("\n".join(machine_code) + "\n", encoding="utf-8")
    except OSError as exc:
        raise AsmError(source, 0, f"無法寫入 {output}：{exc}") from exc

    return output


def collect_sources(paths: list[str]) -> list[Path]:
    sources: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            found = sorted(path.glob("*.asm"))
            if not found:
                raise SystemExit(f"資料夾 {path} 中沒有 .asm 檔案")
            sources.extend(found)
        elif path.is_file():
            sources.append(path)
        else:
            raise SystemExit(f"找不到檔案或資料夾：{path}")
    return sources


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(
        description="Hack 組譯器：將 .asm 編譯成 .hack（nand2tetris Project 6）"
    )
    cli.add_argument("paths", nargs="+", help=".asm 檔案或包含 .asm 的資料夾")
    cli.add_argument(
        "-o", "--output", help="輸出檔名（僅適用於單一輸入檔案）"
    )
    args = cli.parse_args(argv)

    sources = collect_sources(args.paths)
    if args.output and len(sources) != 1:
        cli.error("--output 只能搭配單一輸入檔案使用")

    failed = 0
    for source in sources:
        try:
            output = Path(args.output) if args.output else None
            result = assemble_file(source, output)
            print(f"組譯成功：{source} -> {result}")
        except AsmError as exc:
            failed += 1
            print(f"組譯失敗：{exc}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
