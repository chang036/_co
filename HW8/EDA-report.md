# IC 設計的 EDA 是什麼？

**實作報告｜2026-10-29｜veryl2chip IDE + hack-computer HDL｜瀏覽器 / WebAssembly**

> 從一個 FIFO、一個 16 位元加法器，到一顆 RISC-V SoC：用實際操作走過模擬、驗證、合成、佈局、繞線、時序與位元流，理解 EDA 如何把「想法」變成「可製造的電路」。

---

## 摘要

EDA（Electronic Design Automation，電子設計自動化）不是單一軟體，而是一條把 RTL（硬體描述）轉換成 FPGA 位元流或 ASIC GDSII 版圖的工具鏈。本報告先在 veryl2chip IDE 操作 256×8 FIFO，完成 RTL 模擬、四種實作全面驗證、iCE40 FPGA 佈局繞線與 ASIC 標準元件流程；再用 hack-computer 的 Nand2Tetris HDL 模擬器與迷你 EDA 操作 Inc16；最後用 RV32I / RISC-V SoC 觀察「放不下」的資源檢查與虛擬板燒錄。量測結果顯示：同一份 FIFO 在 FPGA 是 60 個 LUT4、48.3 MHz、25.9 pJ/cycle，在 ASIC 是 166 個標準元件、493.9 MHz、0.70 pJ/cycle。EDA 的價值，就是讓這些取捨在做出晶片之前就變成可比較的數字。

---

## 1. EDA 是什麼：一句話與一個比喻

**一句話：** EDA 是硬體的編譯器、測試框架、排版軟體與量測儀器的總和。它把「我想要什麼功能」翻譯成「哪一顆閘放在哪裡、用哪一層金屬連起來」，並在做出來之前告訴你「這樣會不會太慢、太熱、太大、放不下」。

| 軟體開發的類比 | IC / FPGA 的對應 | 轉換了什麼 |
|---|---|---|
| 原始碼 | RTL（Veryl / Verilog / VHDL） | 人的意圖 → 可解析的時序邏輯描述 |
| 編譯器 | 邏輯合成（logic synthesis） | RTL → 與製程無關的閘級網表 |
| 單元測試 | testbench、assertion、形式驗證 | 檢查功能是否正確 |
| 連結器 / 最佳化 | 技術映射（technology mapping） | 通用閘 → LUT4、標準元件、BRAM / SRAM |
| 排版引擎 | 佈局與繞線（placement & routing） | 邏輯連接 → 實際座標與金屬線 |
| 效能分析器 | STA、功耗、IR drop、DRC / LVS | 「能不能跑、會不會燒、能不能做」 |
| 執行檔 | 位元流 / GDSII | 可載入 FPGA，或送進晶圓廠 |

關鍵差異：**軟體編譯失敗可以重編，晶片做錯通常不能重來。** 一組先進製程光罩動輒數百萬到數千萬美元，因此 EDA 不只是讓設計變快，更是讓錯誤在便宜的時候就被抓到。

---

## 2. 為什麼 IC 設計離不開 EDA

1. **規模**：一個 256×8 FIFO 用通用閘描述就是 8,660 個元件；一顆 RV32I 核心合成後是 9,151 個閘、5,337 個 LUT4、1,056 個 DFF。人腦無法逐一手算。
2. **成本**：FPGA 燒錯可以重燒；ASIC 光罩做錯，損失的是整套光罩與數個月產能。驗證與簽核本質上是在把錯誤提前。
3. **物理限制**：速度、功耗、面積、良率互相拉扯。排緊可以縮短線長，卻可能造成壅塞與 IR drop；提高時脈可以變快，卻可能讓功耗與時序餘裕惡化。
4. **設計空間**：同一份 RTL 可以放進 FPGA，也可以做成 ASIC。哪個才對？要靠 EDA 把 **PPA（Performance / Power / Area）** 量出來再選。

**PPA** 是所有 IC 設計取捨的共同語言：Performance（Fmax / 關鍵路徑）、Power（功耗 / 每週期能量）、Area（面積）。EDA 的工作，就是讓這三個數字在每個階段都「看得見」。

---

## 3. IC 設計流程與 EDA 工具鏈

```text
共用前端
規格/架構 → RTL 設計 → 功能模擬 → 邏輯合成 → 通用閘網表
                                              ├─ FPGA：技術映射 → 佈局 → 繞線 → STA → 位元流
                                              └─ ASIC：標準元件映射 → 佈局+CTS → 繞線 → 簽核 → GDSII
驗證與分析貫穿全程：testbench · assertion · coverage · 形式等價 · 閘級模擬 · STA · 功耗/IR · DRC/LVS
```

### 3.1 前端與後端

- **前端**關心「邏輯對不對」：RTL 撰寫、功能模擬、邏輯合成、形式驗證。輸出與製程無關的閘級網表。
- **後端**關心「物理上做不做得到」：把閘對應到真正的標準元件或 FPGA 資源，安排位置、拉線、插入時脈樹，最後做時序、功耗、DRC / LVS 簽核。

兩者不是單向。後端發現「這條路徑太慢」時，會回頭要求前端改微架構（pipeline、拆組合邏輯），或要求合成工具換映射策略。這種來回就是**設計空間探索**。

### 3.2 FPGA 與 ASIC 的差異

| 面向 | FPGA | ASIC |
|---|---|---|
| 實作方式 | 可程式化 LUT、正反器、BRAM、DSP | 固定功能標準元件與 SRAM 巨集，經光罩製造 |
| 製造成本 | 無光罩成本（NRE 低），晶片本身較貴 | 光罩與設計 NRE 極高，量大時單位成本低 |
| 效能 / 功耗 | 較低 Fmax、較高功耗 | 較高 Fmax、較低功耗 |
| 彈性 | 可重複燒錄、現場更新 | 製造後功能固定，改版等於重新流片 |
| 典型流程 | 合成 → 技術映射 → 佈局 → 繞線 → 位元流 | 合成 → DFT → 佈局 → CTS → 繞線 → 簽核 → GDSII |
| 適合 | 原型、驗證、少量多樣、教學 | 大量生產、效能 / 功耗 / 面積敏感產品 |

本報告的 FIFO 把差異量化出來：同一份 RTL、同一組測試，FPGA 版本 48.3 MHz、25.9 pJ/cycle；ASIC 版本 493.9 MHz、0.70 pJ/cycle。但 ASIC 需要光罩與固定元件庫，FPGA 則可以立刻重燒。

---

## 4. 本次使用的軟體與操作環境

| 工具 | 角色 | 位置 |
|---|---|---|
| **veryl2chip IDE** | Rust / WebAssembly 的完整數位 EDA：Veryl 編輯器、事件驅動模擬器、邏輯合成、iCE40 / ECP5 FPGA 流程、ASIC 標準元件流程（含 SKY130）、STA、功耗、虛擬 iCEBreaker | <https://ccc-eda.github.io/veryl2chip/web/dist/index.html> |
| **hack-computer HDL** | JavaScript 版 Nand2Tetris 工具鏈：HDL 模擬、階層電路圖、迷你 EDA（MicroSyn + MicroPnR） | <https://ccc-js.github.io/hack-computer/dist/hdl.html> |
| **Cornell ECE 5745** | 產業級 ASIC 課程參照：前端 / 後端 / 自動化流程、合成與實體設計演算法、Synopsys / Cadence、OpenLANE | <https://www.csl.cornell.edu/courses/ece5745/handouts.html> |

**操作環境：** Windows 11 + Chromium 架構瀏覽器（Chrome 152 / Electron 44）。兩套工具都不需要安裝、不需要伺服器；veryl2chip 的模擬器、合成器、佈局繞線器全部以 WebAssembly 在工作執行緒中執行。操作包含按「▶ 測試」、按「✔ 全面驗證」、切換七／九個合成階段、按「⚡ 虛擬板」燒錄，以及讀取狀態列與細節面板的數字。

---

## 5. 實作一：FIFO 256×8 的完整流程

### 5.1 設計與 testbench

256×8 同步 FIFO，資料在 `i_pop` 的下一拍出現，記憶體以同步讀取推斷成 block RAM。核心包含讀寫指標、計數器、full / empty 控制。

```veryl
module Fifo #(
    param ADDR_W: u32 = 8,
    param DATA_W: u32 = 8,
) (
    i_clk  : input  clock        ,
    i_rst  : input  reset        ,
    i_push : input  logic        ,
    i_data : input  logic<DATA_W>,
    i_pop  : input  logic        ,
    o_data : output logic<DATA_W>,
    o_empty: output logic        ,
    o_full : output logic        ,
    o_count: output logic<ADDR_W + 1>,
) {
    var mem  : logic<DATA_W> [1 << ADDR_W];
    var wp   : logic<ADDR_W>;
    var rp   : logic<ADDR_W>;
    var count: logic<ADDR_W + 1>;
    var rdata: logic<DATA_W>;

    let do_push: logic = i_push && (count != (1 << ADDR_W));
    let do_pop : logic = i_pop  && (count != 0);

    always_ff (i_clk) {
        if do_push { mem[wp] = i_data; }
        if do_pop  { rdata   = mem[rp]; }
    }

    always_ff {
        if_reset { wp = 0; rp = 0; count = 0; }
        else {
            if do_push { wp = wp + 1; }
            if do_pop  { rp = rp + 1; }
            if do_push && !do_pop      { count = count + 1; }
            else if do_pop && !do_push { count = count - 1; }
        }
    }

    assign o_data  = rdata;
    assign o_count = count;
    assign o_empty = count == 0;
    assign o_full  = count == (1 << ADDR_W);
}
```

testbench `TestFifo` 檢查：重設後為空、push 三個位元組、依序 pop 出 `0x11 / 0x22 / 0x33`、清空後再填滿 256 筆、滿了之後不能再 push。

### 5.2 功能模擬：0.07 秒的第一次把關

| 指標 | 數值 |
|---|---|
| testbench | 1 個通過（`TestFifo ✓ PASS`） |
| 模擬時間 | 0.07 s |
| 引擎啟動 / 編譯 | 281 ms（WebAssembly 背景執行緒） |
| 錯誤 / 警告 | 0 / 0 |

這個階段只證明「RTL 行為符合 testbench」，還沒有證明「合成後也一樣」，更沒有證明「放得進晶片、跑得到目標頻率」。

### 5.3 全面驗證：四種實作，同一個答案

veryl2chip 的「✔ 全面驗證」把同一個 testbench 跑在四種實作上。這是對合成工具最直接的不信任測試：**如果合成器有 bug，四份結果就會不一致。**

| 實作 | 規模（介面顯示） | TestFifo | 意義 |
|---|---|---|---|
| RTL（Veryl） | 1 個 FIFO 模組 | ✓ PASS | 行為基準 |
| 通用閘（generic gates） | 8,660 個元件 | ✓ PASS | 合成後仍是同一個邏輯 |
| iCE40（LUT4 / DFF / BRAM） | 86 個元件 | ✓ PASS | 對應 FPGA 資源後仍正確 |
| ASIC 標準元件 | 151 個元件 | ✓ PASS | 對應標準元件庫後仍正確 |

量測位置：「測試結果」面板的驗證矩陣；耗時 6.3 秒。註：驗證矩陣的標準元件計數（151）與 ASIC 合成視圖的 166 個標準元件來自不同視圖，計數方式可能含記憶體／邊界元件，照實呈現，不強行視為同一數字。

> **為什麼 8,660 個閘會變成 86 個 iCE40 元件？** 因為「閘」和「FPGA 元件」不是同一種東西。通用閘網表把 256×8 記憶體拆成大量正反器與多工器；iCE40 映射時，整塊記憶體被收進 **1 個 SB_RAM40_4K**，其餘控制邏輯才用 LUT4 與 DFF 實現。**元件數不能跨技術直接比較**，必須在同一個製程／元件庫裡看 PPA。

### 5.4 FPGA 實現：60 個 LUT4、1 個 BRAM

切到「FPGA → ⑤ Placement 退火」，工具完成技術映射、佈局與繞線：

| 指標 | 數值 |
|---|---|
| LUT4 | 60 |
| DFF | 25 |
| Fmax | 48.3 MHz（關鍵路徑 20.70 ns） |
| 邏輯單元 | 61 LC（iCE40UP5K 的 1.2%） |
| 記憶體 | 1 × SB_RAM40_4K |
| 繞線 | 632 個可程式開關（pip） |
| 能量 / 功耗 | 25.9 pJ/cycle；@48.3 MHz 約 1.340 mW（靜態 0.090 mW） |

FPGA 的面積是「固定晶片」，設計只佔 61 個 LC，所以真正的成本是「這顆 FPGA 多少錢」，而不是「這 61 個 LC 多少面積」。

### 5.5 ASIC 實現：166 個標準元件、493.9 MHz

切到「ASIC · vlib → ⑨ Power + IR Drop」，同一份 RTL 被映射到自製的 vlib 標準元件庫（約 130 nm 等級的教學模型），再經過列式佈局、時脈樹、繞線、STA 與功耗分析：

| 指標 | 數值 |
|---|---|
| 標準元件 | 166（含 25 個 DFF） |
| Fmax | 493.9 MHz（關鍵路徑 2.02 ns） |
| 面積 | 元件 7,828.0 µm²；晶粒 98×96 µm；利用率 82% |
| 繞線 | 7.39 mm 金屬線、1,804 個 via |
| 每週期能量 | 0.70 pJ |
| 功耗 @48.3 MHz | 0.0341 mW（漏電 0.0003 mW） |

**能量花在哪裡？** ASIC 的每週期能量分解（總和約 0.70 pJ）：

| 來源 | 每週期能量 | 占比 | 說明 |
|---|---:|---:|---|
| 訊號 net | 0.282 pJ | 40.3% | 元件之間的金屬線充放電 |
| 時脈樹 | 0.258 pJ | 36.9% | 時脈要驅動所有正反器 |
| 元件內部 | 0.149 pJ | 21.3% | 閘本身的切換 |
| SRAM | 0.010 pJ | 1.4% | 記憶體存取 |

0.282 + 0.258 + 0.149 + 0.010 = 0.699 pJ，與顯示的 0.70 pJ 相符。這說明在深次微米設計裡，**「線」與「時脈」往往比「閘」更耗能**；這也是後端要花大量時間做 placement、CTS 與繞線最佳化的原因。

### 5.6 FPGA vs ASIC：把取捨變成數字

| 指標 | FPGA（iCE40UP5K） | ASIC（vlib 標準元件） |
|---|---|---|
| 實作 | LUT4 + DFF + BRAM（可重燒） | 標準元件 + SRAM 巨集（需流片） |
| 邏輯資源 | 61 LC（1.2%）、25 DFF、0 CARRY | 166 個元件、25 DFF |
| 記憶體 | 1 × SB_RAM40_4K | 1 × SRAM 巨集 |
| 面積 | 固定晶片（5,280 LC / 30 BRAM） | 元件 7,828 µm²；晶粒 98×96 µm；利用率 82% |
| 繞線 | 632 個 pip | 7.39 mm 金屬線、1,804 個 via |
| 關鍵路徑 | 20.70 ns | 2.02 ns |
| Fmax | 48.3 MHz | 493.9 MHz（×10.2） |
| 每週期能量 | 25.9 pJ | 0.70 pJ（÷37） |
| 功耗 @48.3 MHz | 1.340 mW（靜態 0.090） | 0.0341 mW（漏電 0.0003） |

> 資料來源：「⇄ FPGA vs ASIC 比較」頁面，2026-10-29。ASIC 使用 vlib 教學用標準元件庫，數字是此流程模型的估計，不是商業 signoff 或實際晶片量測。

### 5.7 這一輪學到什麼

同一份 125 行的 FIFO，在四個抽象層級都通過同一個 testbench，卻有完全不同的成本結構：通用閘 8,660 個元件、FPGA 86 個元件（1 個 BRAM）、ASIC 166 個元件（1 個 SRAM）。**EDA 的價值不是「把電路畫出來」，而是讓這些差異可以被量測、被比較、被選擇。**

---

## 6. 實作二：Inc16 與迷你 EDA

### 6.1 HDL 模擬與階層電路圖

`Inc16` 的 HDL 只有一行真正的工作：把 `Add16` 的第一個加數接 `in`，第二個加數第 0 位接 `true`、其餘接 `false`。

```hdl
CHIP Inc16 {
    IN in[16];
    OUT out[16];

    PARTS:
    Add16(a=in, b[0]=true, b[1..15]=false, out=out);
}
```

按「執行」後，`.tst` 的輸出全部符合 `.cmp`：

| in（二進位） | out（二進位） | 十進位意義 |
|---|---|---|
| `0000 0000 0000 0000` | `0000 0000 0000 0001` | 0 → 1 |
| `1111 1111 1111 1111` | `0000 0000 0000 0000` | 65535 → 0（溢位） |
| `0000 0000 0000 0101` | `0000 0000 0000 0110` | 5 → 6 |
| `1111 1111 1111 1011` | `1111 1111 1111 1100` | 65531 → 65532 |

按「檢視電路圖」可以看到階層：`Inc16` 內含一個 `Add16`，`b[0]` 綁 `true`、`b[1..15]` 綁 `false`。可以一路點進 `Add16`、`FullAdder`，直到最底層的 `Nand` 與 `DFF`。**「階層」是硬體設計控制複雜度的第一個工具。**

### 6.2 迷你 EDA：224 個閘 → 60 個 LUT4

按「合成 LUT」後，畫面顯示七個階段：① RTL→Logic、② Logic Netlist、③ Tech-indep Syn、④ LUT4 Techmap、⑤ Placement、⑥ Routing、⑦ STA，並可切換 FPGA / ASIC 後端。

| 指標 | FPGA 視圖 | ASIC 視圖 |
|---|---|---|
| 技術映射 | 60 LUT4 + 0 DFF | 174 標準元件（NAND2×65、AOI21×16、INV×78、MUX2×15） |
| 面積 / 佈局 | 10×10 格子、利用率 0.60、32 I/O | 319.2 µm²、66 列 |
| 繞線 | 總線長 78（畫面單位） | 1,705.3 µm |
| 時序 | 43.50 ns → 23.0 MHz | 約 81 MHz |
| 原始閘數 | 224 | 224 |

| 階段 | 做什麼 |
|---|---|
| ① RTL→Logic | 解析 HDL、建階層、展開 `Inc16 → Add16 → 全加器` |
| ② Logic Netlist | 每個行為變成 AND / XOR / NOT / DFF（224 個閘） |
| ③ Tech-indep Syn | 化簡、常數傳播，去掉重複與沒用到的邏輯 |
| ④ 技術映射 | FPGA：60 個 LUT4；ASIC：174 個標準元件 |
| ⑤ 佈局 | 決定元件位置，縮短連線（退火演算法） |
| ⑥ 繞線 | 用可程式開關或金屬層連接 |
| ⑦ 時序 | 找關鍵路徑，算 Fmax |

> 資料來源：hack-computer `hdl.html` 的「合成 LUT」浮層，2026-10-29。此為教學用簡化模型（MicroSyn / MicroPnR），數字用於理解流程，不應與商用 signoff 直接比較。

> **為什麼 LUT4 的數量不是「224 ÷ 4」？** 因為一個 LUT4 不是「4 個閘」，而是**一張 16 位元的真值表**：任何 4 個輸入的布林函數都可以用它實現。合成器把邏輯切成 4 輸入的切集（cut），再把每個切集的真值表燒進 LUT。ASIC 則沒有 LUT，必須用 NAND2、INV、AOI21 等標準元件重新組出同樣的函數，所以又是另一組數字。

---

## 7. 實作三：RISC-V CPU 與「放不下」

### 7.1 單週期 RV32I：功能對，但放不進 FPGA

選擇「RV32I 單週期 CPU」範例，直接跳到 FPGA 的 ⑤ Placement。合成結果是 **9,175 → 9,151 個閘、5,337 個 LUT4、1,056 個 DFF**；接著佈局繞線回報：

```text
佈局繞線失敗：design does not fit: needs 5441 LCs (the device has 5280)
and 167 IO pins (the package has 39)
```

iCE40UP5K-SG48 只有 5,280 個 LC、39 個 I/O 腳。這個核心的暫存器檔用正反器實現，再加上單週期 CPU 的資料路徑，結果**超出 161 個 LC，且 I/O 需求遠超封裝腳數**。工具沒有把錯誤留到燒錄或上電才發生，而是在佈局階段就明確拒絕，並建議改用「RISC-V SoC（FPGA）」範例或 ASIC 流程。

**這一幕就是 EDA 的價值。** 「放不下」不是設計者的疏忽，而是**架構與資源的衝突**。EDA 把衝突量化成兩個數字（5,441 > 5,280、167 > 39），讓設計者可以在改架構（多週期、把暫存器／記憶體放進 BRAM）、換晶片（更大的 FPGA）、或改流程（走 ASIC）之間做選擇。

### 7.2 RISC-V SoC：把記憶體放進 BRAM 就放得下

改用 multi-cycle 的 `RiscvSoc`：暫存器檔與記憶體改用同步讀取的 RAM，推斷成 block RAM；程式 ROM 也放在 BRAM。

| 指標 | 數值 |
|---|---|
| 合成後閘數 | 2,463（原始 11,969） |
| LUT4 / DFF | 1,164 / 232 |
| Fmax | 17.0 MHz（板子時脈 12 MHz，有餘裕） |
| 測試 | `TestRiscvCore`、`TestRiscvSoc` 都 PASS，0.19 s |

按「⚡ 虛擬板」後，工具合成、佈局繞線、產生位元流並燒錄：

```text
RiscvSoc　位元流：1227 LC，Fmax 17.0 MHz ≥ 12 MHz ✓
接線：CLK↔i_clk　BTN_N↔i_rst　P1A1↔o_led[0] … P1A10↔o_led[7]
```

虛擬板上的 8 顆 LED 最後顯示為 **1 1 1 0 1 1 0 0**（LED0→LED7），也就是二進位 `0011 0111` = `0x37` = **55**，正好是測試程式計算的 Fibonacci(10)。

### 7.3 從「放不下」到「跑起來」：架構決策被 EDA 推動

- **單週期 → 多週期**：減少每個時脈的組合邏輯與資料路徑，換取較低的資源與較高的 Fmax 餘裕。
- **暫存器 → BRAM**：把 32×32 的暫存器檔與記憶體放進 block RAM，LUT4 用量從 5,337 降到 1,164。
- **程式 ROM 常數化**：合成器把只被這個程式用到的硬體移除（未用的暫存器、移位器、byte load 等）。
- **位元流驗證**：Fmax 17.0 MHz ≥ 12 MHz，才敢說「這顆設計可以在這塊板子上跑」。

**RTL 只是提案，EDA 才是把提案變成可執行承諾的過程。**

---

## 8. 從操作看 EDA 的五個價值

1. **正確性：四種實作，一個答案。** FIFO 的全面驗證把同一個 testbench 跑在 RTL、通用閘、iCE40、標準元件上，4/4 一致。合成器也是軟體，也會有 bug；用同一組測試驗證合成前後，是最實際的交叉檢查。
2. **可實現性：在編譯期就說「放不下」。** RV32I 單週期核心需要 5,441 LC（只有 5,280）、167 I/O（只有 39）。EDA 在佈局階段就明確拒絕，避免把錯誤帶到板子或光罩。
3. **量化：把 PPA 取捨變成表格。** FIFO 的 FPGA / ASIC 比較把「哪個比較好」拆成邏輯資源、記憶體、面積、繞線、關鍵路徑、Fmax、能量、功耗。工程決策的前提是可比較的數字。
4. **生產力：瀏覽器裡的分鐘級迭代。** 模擬 0.07 秒、四種實作驗證 6.3 秒、RISC-V SoC 佈局繞線約 40 秒、虛擬板燒錄與開機在分鐘內完成。
5. **透明性：每一個階段都可以點進去看。** LUT 真值表、標準元件位置、繞線 net、關鍵路徑延遲、退火佈局過程。教學工具把黑盒子打開，讓學習者看見演算法如何改變結果。

**限制也要知道：** 本報告的 ASIC 數字來自 vlib 教學模型（veryl2chip 另支援 SKY130 開放 PDK），不是商業 signoff；hack-computer 的 MicroSyn / MicroPnR 也是簡化版。真實 tapeout 需要 foundry 的 PDK、Liberty / SPEF / SDC、商用 STA 與 DRC / LVS 工具，以及 silicon validation。

---

## 9. EDA 的產業版圖與發展趨勢

| 類別 | 代表工具 / 公司 | 角色 |
|---|---|---|
| 商用三大 EDA | Synopsys、Cadence、Siemens EDA | 前端合成、模擬、形式驗證、後端佈局繞線、STA、DFT、PCB / 封裝 |
| 物理分析 / 多物理 | Ansys、Keysight、Silvaco | 熱、電磁、電源完整性、TCAD、元件模擬 |
| 開源前端 | Verilator、Icarus Verilog、Yosys、ghdl | 模擬、合成、形式 / 等價檢查 |
| 開源後端 | nextpnr、OpenROAD、OpenLANE、Magic、KLayout | FPGA / ASIC 佈局繞線、DRC / LVS、GDSII |
| 開源 PDK | SkyWater SKY130、GF180MCU | 讓學界與小團隊也能跑完整 ASIC 流程 |
| 瀏覽器 / 教學 | veryl2chip、hack-computer | 免安裝、視覺化、適合課程與原型 |

**四個趨勢：**

1. **雲端與瀏覽器化**：把模擬器、合成器、佈局繞線器編譯成 WebAssembly，讓 EDA 從「工作站授權」變成「開網址就能跑」。
2. **開源流程成熟**：Yosys + nextpnr + OpenROAD + SKY130 已經可以做出可運作的晶片；Cornell ECE 5745 也把 OpenLANE 放進課程。開源不是要取代商用 signoff，而是降低學習與原型門檻。
3. **AI 輔助設計**：機器學習用於佈局預測、繞線壅塞預測、設計空間探索、測試生成與驗證覆蓋率；大型語言模型也開始協助產生 RTL 與 testbench，但驗證與簽核仍然是人與工具的責任。
4. **Chiplet 與先進封裝**：設計拆成多顆 chiplet，EDA 要處理 die-to-die 介面、封裝繞線、熱與電源整合。

**對台灣的意義：** 台灣是全球晶圓代工與 IC 設計重鎮，EDA 是生態系的共同語言。理解 EDA 不只是會操作一套軟體，而是理解從規格、RTL、驗證、佈局到量產的整條價值鏈。

---

## 10. 與 Cornell ECE 5745 課程的對照

Cornell 的 **ECE 5745: Complex Digital ASIC Design** 把主題拆成 HDL、CMOS 元件與電路、全客戶設計、自動化方法、ASIC 與 custom 的差距、封裝／電源／時脈／I/O、測試與驗證、合成演算法、實體設計演算法等；實作包含前端、後端、自動化流程、TinyRV2 加速器、SRAM 產生器與 OpenLANE。

| ECE 5745 的主題 | 本報告的對應操作 | 補充 |
|---|---|---|
| Topic 1：Hardware Description Languages | Veryl / Nand2Tetris HDL 撰寫與模擬 | RTL 是設計的原始碼，語意與時序必須精確 |
| Topic 5：Automated Design Methodologies | FIFO / Inc16 / RISC-V SoC 的合成與實現 | 自動化把設計者從手繪閘級電路中解放 |
| Topic 8：Testing and Verification | testbench、`$assert`、四種實作全面驗證 | 驗證不是跑一次，而是交叉檢查與覆蓋率 |
| Topic 12：Synthesis Algorithms | 224 閘 → 60 LUT4、8,660 閘 → 86 元件 | 化簡、切集、技術映射決定最終 PPA |
| Topic 13：Physical Design Automation | Placement、Routing、CTS、STA、功耗 / IR | 物理限制讓「邏輯對」變成「做出來也對」 |
| Section 1–3：Front-end / Back-end / Flow | veryl2chip 的七／九階段流程 | 前端與後端不是先後，而是反覆迭代 |
| Tutorial 4：Synopsys / Cadence ASIC Tools | 本報告用開源／教學工具替代 | 商用工具做 signoff，教學工具做理解 |

兩者最大的差異在**準確度與規模**：ECE 5745 用商用工具與真實 PDK，處理可以下線的設計；本報告用瀏覽器工具，處理可以理解的設計。但兩者要建立的直覺一樣：**設計者必須知道每個階段在做什麼、會引入什麼限制、以及如何用數字判斷好壞。**

---

## 11. 結論

**EDA 是 IC 設計的「實現層」。** 它接收人類寫下的 RTL，經過模擬、合成、映射、佈局、繞線、時序與功耗分析，最後輸出位元流或 GDSII。它不只是畫圖或模擬，而是一套把「功能意圖」轉換成「物理現實」的工具鏈與方法學。

這次實作印象最深的是**抽象層級的落差**：一個 256×8 FIFO，在通用閘是 8,660 個元件，在 FPGA 是 86 個元件（1 個 BRAM），在 ASIC 是 166 個標準元件（1 個 SRAM）。同一個行為，不同的實現，Fmax 從 48.3 MHz 跳到 493.9 MHz，每週期能量從 25.9 pJ 降到 0.70 pJ。

另一個印象是**失敗的價值**：單週期 RV32I 核心因為 5,441 > 5,280 個 LC、167 > 39 個 I/O 而「放不下」。這個失敗不是挫折，而是 EDA 最有用的功能之一：它讓設計者在花錢之前就知道架構與資源的衝突，然後用多週期、BRAM、換晶片或改流程來解決。最後 RISC-V SoC 以 1,164 個 LUT4、17.0 MHz 的位元流在虛擬板上亮出 LED = 55，完成了從 RTL 到實際運行的閉環。

所以，**IC 設計的 EDA 是什麼？** 它是把「我想要一顆會算 Fibonacci 的晶片」變成「這顆晶片在 17 MHz 下、用 1,227 個邏輯單元、可以燒進這塊板子」的那一整套工具、資料與方法。沒有它，現代晶片的複雜度無法被管理；有了它，設計者才能在速度、功耗、面積與成本之間，做出有根據的選擇。

> **給第一次接觸 EDA 的人：** 不要從「記住所有工具名稱」開始。先從一個小設計（FIFO 或 Inc16）走一次完整流程：寫 RTL → 跑 testbench → 看波形 → 合成 → 看閘／LUT → 佈局繞線 → 看 Fmax。當你看到同一份程式碼變成不同的元件、不同的數字，你就會真正理解 EDA 在做什麼。

---

## 附錄 A：重現步驟

1. **FIFO**：開啟 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=fifo> → 按「▶ 測試」→ 按「✔ 全面驗證」→ 在「看電路」選 `FPGA` 與「⑤ Placement 退火」→ 再選 `ASIC · vlib` 與「⑨ Power + IR Drop」→ 最後選「⇄ FPGA vs ASIC 比較」。
2. **Inc16**：開啟 <https://ccc-js.github.io/hack-computer/dist/hdl.html> → 章節選「02 加法器/ALU」→ 晶片選 `../02/Inc16` → 按「執行」→ 按「檢視電路圖」→ 按「合成 LUT」→ 切換 FPGA / ASIC 視圖。
3. **RISC-V**：開啟 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=rv32i&stage=place>，觀察「放不下」訊息；再開 <https://ccc-eda.github.io/veryl2chip/web/dist/index.html#ex=soc&stage=place> → 按「▶ 測試」→ 按「⚡ 虛擬板」→ 看 LED。
4. **命令列（可選）**：veryl2chip 也提供 `v2c`：`cargo install veryl2chip-sim veryl2chip-eda`，即可用 `v2c sim / synth / fpga / asic / gatesim` 重跑類似流程。

## 附錄 B：量測總表

| 項目 | 數值 | 來源 / 備註 |
|---|---|---|
| FIFO 模擬 | 1 個 testbench PASS，0.07 s，0 錯誤 / 0 警告 | 「測試結果」面板 |
| FIFO 全面驗證 | 1 個 testbench × 4 種實作全部一致，6.3 s | 「✔ 全面驗證」 |
| FIFO 通用閘 / iCE40 / 標準元件 | 8,660 / 86 / 151 個元件 | 驗證矩陣 |
| FIFO FPGA | 60 LUT4、25 DFF、61 LC（1.2%）、1 BRAM、632 pips、20.70 ns、48.3 MHz | FPGA ⑤；狀態列 |
| FIFO ASIC | 166 cells、25 DFF、7,828 µm²、98×96 µm、82%、7.39 mm、1,804 via、2.02 ns、493.9 MHz | ASIC ⑨；比較頁 |
| FIFO 能量 / 功耗 | FPGA 25.9 pJ、1.340 mW；ASIC 0.70 pJ、0.0341 mW（@48.3 MHz） | 比較頁 |
| Inc16 HDL | 4 組測資全部通過（0→1、65535→0、5→6、65531→65532） | hack-computer「執行」 |
| Inc16 FPGA | 224 閘 → 60 LUT4 + 0 DFF、10×10、util 0.60、32 I/O、43.50 ns、23.0 MHz | 「合成 LUT」FPGA |
| Inc16 ASIC | 174 cells（NAND2 65 / AOI21 16 / INV 78 / MUX2 15）、319.2 µm²、66 列、1,705.3 µm、約 81 MHz | 「合成 LUT」ASIC |
| RV32I 單週期 | 9,175→9,151 閘、5,337 LUT4、1,056 DFF；需要 5,441 LC / 167 IO，放不下 | FPGA ⑤ 失敗訊息 |
| RISC-V SoC | 11,969→2,463 閘、1,164 LUT4、232 DFF、17.0 MHz；2 個 testbench PASS | FPGA ⑤；測試結果 |
| RISC-V SoC 位元流 | 1,227 LC、Fmax 17.0 MHz ≥ 12 MHz；LED = 0b00110111 = 55 | 虛擬板 |

## 附錄 C：名詞對照

| 名詞 | 意思 |
|---|---|
| RTL | Register-Transfer Level，暫存器轉移層級；用時脈與暫存器描述電路行為，是合成工具的輸入。 |
| Testbench | 用來測試設計的「測試電路」：產生時脈、餵輸入、檢查輸出。 |
| Synthesis | 邏輯合成：把 RTL 轉成閘級網表，並做化簡與最佳化。 |
| Technology mapping | 技術映射：把通用閘對應到特定製程的 LUT、標準元件或記憶體。 |
| Placement / Routing | 佈局／繞線：決定元件位置，再用金屬線或可程式開關連接。 |
| CTS | Clock Tree Synthesis，時脈樹合成：把時脈均勻送到所有正反器，控制 skew。 |
| STA | Static Timing Analysis，靜態時序分析：不跑模擬，用延遲模型檢查 setup / hold。 |
| PPA | Performance、Power、Area：效能、功耗、面積。 |
| DRC / LVS | Design Rule Check / Layout Versus Schematic：檢查版圖是否符合製程規則、是否與電路一致。 |
| PDK | Process Design Kit：製程廠提供的設計套件（元件模型、規則、Liberty 等）。 |
| DFT / ATPG | Design for Test / Automatic Test Pattern Generation：讓晶片可被測試，並自動產生測試向量。 |
| GDSII | 積體電路版圖的交換格式，是送給晶圓廠的「施工圖」。 |
| Bitstream | FPGA 的設定檔：每個 LUT 的真值表與每個繞線開關的開關狀態。 |
| LUT4 | 4 輸入查表：16 位元真值表，可實現任意 4 輸入布林函數。 |
| DFF | D 型正反器：時脈邊緣觸發的 1 位元儲存元件。 |
| BRAM / SRAM | FPGA 的塊狀記憶體 / ASIC 的靜態隨機存取記憶體巨集。 |
| Tapeout | 送片：把 GDSII 送進晶圓廠製作光罩並生產。 |
| NRE | Non-Recurring Engineering，一次性工程成本（光罩、設計、驗證）。 |

## 參考資料

1. veryl2chip IDE（線上版）。<https://ccc-eda.github.io/veryl2chip/web/dist/index.html>（2026-10-29 操作）
2. veryl2chip GitHub：README、tutorial、veryl-eda 文件。<https://github.com/ccc-eda/veryl2chip/>
3. veryl2chip 教學：從零開始用 Veryl 設計數位電路。<https://github.com/ccc-eda/veryl2chip/blob/main/tutorial/README.tw.md>
4. hack-computer HDL 模擬器。<https://ccc-js.github.io/hack-computer/dist/hdl.html>（2026-10-29 操作）
5. hack-computer GitHub：Nand2Tetris 全工具鏈＋RISC-V 後端。<https://github.com/ccc-js/hack-computer>
6. Cornell ECE 5745: Complex Digital ASIC Design — Handouts。<https://www.csl.cornell.edu/courses/ece5745/handouts.html>
7. Cornell ECE 5745：ASIC Tool Front-End / Back-End / Automated Flow 課程單元。<https://cornell-ece5745.github.io/>
8. Veryl 官方網站。<https://veryl-lang.org/>
9. Yosys / nextpnr / OpenROAD / OpenLANE 開源工具鏈。<https://yosyshq.net/yosys/>、<https://www.openroad.net/>
