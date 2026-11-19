# nand2tetris VM Translator（Project 7 + 8）

`vm_translator.py` 將 Jack 虛擬機（VM）程式翻譯成 Hack 組合語言（`.asm`）。
支援 project 7 的堆疊運算 / 記憶體區段，以及 project 8 的程式流程與函式呼叫。

## 用法

```powershell
# 翻譯單一 .vm 檔
python vm_translator.py projects/7/StackArithmetic/SimpleAdd/SimpleAdd.vm

# 翻譯整個資料夾（裡面所有 .vm 合成一個 .asm）
python vm_translator.py projects/8/FunctionCalls/FibonacciElement

# 指定輸出檔名
python vm_translator.py projects/7/... -o MyOutput.asm

# 強制 / 關閉 bootstrap（預設：資料夹內有 Sys.vm 才自動加）
python vm_translator.py <path> --bootstrap
python vm_translator.py <path> --no-bootstrap
```

若輸入是資料夾，輸出檔名為 `<資料夾名>.asm`，放在同一個資料夾。
`Sys.vm` 存在時會自動加上 bootstrap：

```
@256
D=A
@SP
M=D
...  // call Sys.init 0
```

## 支援的 VM 指令

| 類別 | 指令 |
| --- | --- |
| 算術邏輯 | `add sub neg eq gt lt and or not` |
| 記憶體 | `push/pop constant local argument this that temp pointer static` |
| 流程控制 | `label goto if-goto` |
| 函式 | `function call return` |

## 實作重點

- 堆疊top在 `RAM[SP-1]`；二元運算先 pop 到 D，再把結果寫回 `SP-1`，不改 SP。
- `eq/gt/lt` 用 `x-y` 搭配 `JNE/JLE/JGE` 產生 `0` 或 `-1`。
- 區段基底：`local→LCL`、`argument→ARG`、`this→THIS`、`that→THAT`；
  `temp→RAM[5+index]`、`pointer→THIS/THAT`、`static→<檔名>.<index>`。
- label 以 `function$label` 限定範圍，跨檔案也不會碰撞；比較與返回標籤用全域計數器。
- `call`：push 返回位址 → 存 LCL/ARG/THIS/THAT → `ARG = SP - nArgs - 5` → `LCL = SP` → 跳到函式。
- `return`：由 `LCL` 取 frame，取回返回位址，回寫 `ARG`，`SP = ARG + 1`，再還原 THAT/THIS/ARG/LCL。
- `R13` 當 frame/位址暫存器，`R14` 存返回位址。

## 測試

一鍵重新翻譯並跑完 project 7、8 所有 `.tst`（CPU Emulator，驗證 `.asm`）：

```powershell
python run_vm_tests.py
```

一鍵跑完所有 `*VME.tst`（VM Emulator，直接驗證 `.vm`）：

```powershell
python run_vme_tests.py
```

`run_vme_tests.py` 會自動避開內建 VM Emulator 對 `label`/`function` 行首 tab 的解析 bug
（NestedCall 的 `Sys.vm`），使用暫存副本執行，不更動官方測試檔。

目前兩邊結果都是 **11 / 11 通過**（BasicTest、PointerTest、StaticTest、SimpleAdd、StackTest、
FibonacciElement、NestedCall、SimpleFunction、StaticsTest、BasicLoop、FibonacciSeries）。
