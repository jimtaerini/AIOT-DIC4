# Proposal：004_experiments

## Why

IV. Experiment 決定論文主張是否成立，也是最容易出現捏造數據的地方。依 2020 A-Z SOP 需涵蓋 **Q–V**；目前尚未執行任何實驗，所有結果必須保持 `[TBD]`，直到能追溯到 `AIOT-DIC3-ProjectRefactor/experiments/results/` 的結果檔。

## What Changes

- 規範 Section IV 的 Q–V：**Q** E1–E5 與消融、TP 漏判率（MR）與升級率（ER）等指標與抽樣規模；**R** 四個 baseline 與三種消融；**S** GUIDE 與 ExCyTIn-Bench、實測資料特性、依事件／組織／時間切分、實作環境；**T** 調參範圍與只用驗證集；**U** 結果表與 MR–ER 曲線；**V** 有效性驗證與效度威脅。
- 規範結果數字的可追溯性。

## Capabilities

### New Capabilities

- `experiments-q-to-v`：Experiment 的 Q–V 結構、指標定義、資料切分、調參與結果可追溯性。

### Modified Capabilities

（無）

## Impact

- 檔案：`iceib-paper/main.tex`、`iceib-paper/main.txt`（Section IV、Table IV–VI）。
- 相依：`AIOT-DIC3-ProjectRefactor/openspec/changes/build-soc-triage-agent`（E1–E5 與消融的實作）。
- 依據：`my_ref/A2Z outline example.pdf`（Q–V）、`my_ref/README.md`（資料與實驗）。
