# HW8｜IC 設計的 EDA 是什麼？

本目錄是 HW8 的完整報告包。報告以「實際操作 EDA 軟體」為核心，先說明 EDA 的定義與 IC 設計流程，再用三個設計走過模擬、驗證、合成、佈局、繞線、時序與位元流，最後用量到的數字討論 EDA 的價值、產業版圖與課程對照。

> 操作日期：2026-10-29  
> 使用工具：veryl2chip IDE、hack-computer HDL  
> 執行環境：瀏覽器（WebAssembly），免安裝

---

## 報告檔案

| 檔案 | 說明 |
|---|---|
| [`EDA-report.html`](./EDA-report.html) | **主要版本**。含封面、目錄、流程圖、量測表格與比較圖表，適合直接用瀏覽器閱讀。 |
| [`EDA-report.pdf`](./EDA-report.pdf) | 由 HTML 列印產生的 PDF，共 27 頁，適合列印或繳交。 |
| [`EDA-report.md`](./EDA-report.md) | Markdown 版，方便再編輯、複製段落或放進其他文件。 |

建議先開 HTML 版；若要繳交紙本或 PDF，直接使用 `EDA-report.pdf`。

---

## 主題

**IC 設計的 EDA 是什麼？**

報告要回答的不是「EDA 有哪些軟體」，而是：

- EDA 在 IC 設計流程中到底扮演什麼角色？
- 一顆電路從 RTL 到 FPGA 位元流／ASIC 版圖，中間經過哪些轉換？
- 為什麼同一份 RTL，在 FPGA 與 ASIC 上的速度、功耗、面積差這麼多？
- EDA 如何讓「放不下」、「太慢」、「太耗電」在做出晶片之前就被發現？

---

## 實際操作內容

### 1. FIFO 256×8（veryl2chip IDE）

- 執行 `TestFifo` testbench：**1 PASS**、0.07 秒、0 錯誤 / 0 警告
- 「✔ 全面驗證」：RTL、通用閘、iCE40、ASIC 標準元件 **4 種實作全部一致**
- FPGA 流程（iCE40UP5K）：**60 LUT4、25 DFF、61 LC、1 個 BRAM、Fmax 48.3 MHz**
- ASIC 流程（vlib）：**166 個標準元件、Fmax 493.9 MHz、每週期 0.70 pJ**
- 實際切換 ①～⑦（FPGA）與 ①～⑨（ASIC）階段，讀取佈局、繞線、STA、功耗與 FPGA vs ASIC 比較頁

### 2. Inc16（hack-computer HDL）

- 載入 Nand2Tetris 的 `Inc16`，執行 `.tst`：4 組測資全部通過
- 「檢視電路圖」：`Inc16 → Add16 → FullAdder → Nand` 的階層
- 「合成 LUT」迷你 EDA：**224 個閘 → 60 個 LUT4**；ASIC 視圖為 **174 個標準元件**

### 3. RISC-V CPU（veryl2chip IDE）

- 單週期 RV32I：**9,151 個閘、5,337 LUT4、1,056 DFF**
- 佈局失敗訊息：需要 **5,441 LC**（iCE40UP5K 只有 5,280）、**167 I/O**（封裝只有 39）
- 改用 RISC-V SoC：**1,164 LUT4、232 DFF、Fmax 17.0 MHz**，2 個 testbench 通過
- 燒進虛擬 iCEBreaker：位元流 **1,227 LC**，LED 顯示 `0011 0111` = **55**（Fibonacci(10)）

---

## 關鍵數據

| 項目 | 數值 |
|---|---|
| FIFO 模擬 | 1 PASS，0.07 s |
| FIFO 全面驗證 | 4 / 4 種實作一致，6.3 s |
| FIFO FPGA | 60 LUT4、25 DFF、61 LC、48.3 MHz、25.9 pJ/cycle |
| FIFO ASIC | 166 cells、493.9 MHz、0.70 pJ/cycle |
| Inc16 FPGA | 224 閘 → 60 LUT4、23.0 MHz |
| Inc16 ASIC | 174 cells、319.2 µm²、約 81 MHz |
| RV32I 單週期 | 5,337 LUT4；需要 5,441 LC / 167 IO，放不下 |
| RISC-V SoC | 1,164 LUT4、232 DFF、17.0 MHz；LED = 55 |

完整數據、量測位置與注意事項見報告的「附錄 A.2 量測總表」。

---

## 報告大綱

1. EDA 是什麼：一句話與一個比喻
2. 為什麼 IC 設計離不開 EDA
3. IC 設計流程與 EDA 工具鏈（前端 / 後端、FPGA / ASIC）
4. 本次使用的軟體與操作環境
5. 實作一：FIFO 256×8 的完整流程
6. 實作二：Inc16 與迷你 EDA
7. 實作三：RISC-V CPU 與「放不下」
8. 從操作看 EDA 的五個價值
9. EDA 的產業版圖與發展趨勢
10. 與 Cornell ECE 5745 課程的對照
11. 結論
12. 附錄：重現步驟、量測總表、名詞對照、參考資料

---

## 如何重現

### FIFO

1. 開啟 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=fifo>
2. 按「▶ 測試」
3. 按「✔ 全面驗證」
4. 「看電路」選 `FPGA` →「⑤ Placement 退火」
5. 再選 `ASIC · vlib` →「⑨ Power + IR Drop」
6. 最後選「⇄ FPGA vs ASIC 比較」

### Inc16

1. 開啟 <https://ccc-js.github.io/hack-computer/dist/hdl.html>
2. 章節選「02 加法器/ALU」→ 晶片選 `../02/Inc16`
3. 按「執行」→「檢視電路圖」→「合成 LUT」
4. 切換 FPGA / ASIC 視圖

### RISC-V

1. 開啟 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=rv32i&stage=place>，觀察「放不下」訊息
2. 再開 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=soc&stage=place>
3. 按「▶ 測試」→「⚡ 虛擬板」→ 看 LED

### 命令列（可選）

```sh
cargo install veryl2chip-sim veryl2chip-eda
v2c sim --vcd wave.vcd design.veryl
v2c fpga --pcf pins.pcf --bin design.bin design.veryl
v2c asic --pdk sky130 --gds design.gds design.veryl
```

---

## 環境與版本

- 作業系統：Windows 11
- 瀏覽器：Chromium 架構（Chrome 152 / Electron 44）
- veryl2chip：線上 IDE（Rust 核心編譯為 WebAssembly）
- hack-computer：零依賴 ESM，Node ≥ 20（本報告只用瀏覽器版）
- 操作日期：2026-10-29

---

## 注意事項

- 本報告的 ASIC 數字來自 veryl2chip 的 **vlib 教學用標準元件庫**（約 130 nm 等級的模型），適合理解流程與 PPA 趨勢，**不等同商用 signoff 或實際晶片量測**。
- veryl2chip 另支援 SKY130 開放 PDK；真實 tapeout 仍需 foundry PDK、Liberty / SPEF / SDC、商用 STA 與 DRC / LVS 工具，以及 silicon validation。
- hack-computer 的 MicroSyn / MicroPnR 也是教學用簡化模型，數字用於理解流程，不應與商用工具直接比較。
- 報告中的 FIFO 驗證矩陣顯示標準元件 151 個、ASIC 合成視圖顯示 166 個，兩者來自不同視圖，計數方式可能含記憶體／邊界元件，報告中已照實標註。

---

## 參考資料

1. veryl2chip IDE：<https://ccc-eda.github.io/veryl2chip/web/dist/index.html>
2. veryl2chip GitHub：<https://github.com/ccc-eda/veryl2chip/>
3. veryl2chip 教學（繁體中文）：<https://github.com/ccc-eda/veryl2chip/blob/main/tutorial/README.tw.md>
4. hack-computer HDL 模擬器：<https://ccc-js.github.io/hack-computer/dist/hdl.html>
5. hack-computer GitHub：<https://github.com/ccc-js/hack-computer>
6. Cornell ECE 5745 Handouts：<https://www.csl.cornell.edu/courses/ece5745/handouts.html>
7. Cornell ECE 5745 課程單元：<https://cornell-ece5745.github.io/>
8. Veryl 官方網站：<https://veryl-lang.org/>
9. Yosys / nextpnr / OpenROAD / OpenLANE：<https://yosyshq.net/yosys/>、<https://www.openroad.net/>

---

## 目錄結構

```text
HW8/
├── README.md          ← 本檔案
├── EDA-report.html    ← 主要報告（建議先看）
├── EDA-report.pdf     ← 列印 / 繳交版（27 頁）
└── EDA-report.md      ← Markdown 版
```
