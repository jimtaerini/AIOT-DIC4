# Proposal：000_abstract

## Why

摘要是 ICEIB 2027 審稿者最先讀到、也是 2027-03-01 摘要投稿時唯一送出的內容。它必須依 2020 A-Z SOP 的 **A–F**（`my_ref/A2Z outline example.pdf`）組成，且每個數字都要能在 `my_ref/README.md` 找到。

## What Changes

- 規範 `iceib-paper/main.tex`（與 `main.txt`）中 `abstract` 環境的 A–F 六段內容與順序：
  - **A** SOC 告警與外洩成本壓力；**B** ML 缺攻擊鏈脈絡、LLM 漏判與過早結案、自動化自滿；**C** AI SOC Analyst Agent；**D** ReAct Planner + `IsSufficient` + GBDT/SHAP + ATT&CK/NIST RAG + 證據融合與升級；**E** GUIDE（707,108 起事件、5,769 個組織）與 ExCyTIn-Bench、四個 baseline；**F** 實驗結果（目前 `[TBD]`）。
- 規範摘要後的 Index Terms。

## Capabilities

### New Capabilities

- `abstract-a-to-f`：摘要的 A–F 完整性與順序、長度、Findings 的誠實性與 Index Terms。

### Modified Capabilities

（無）

## Impact

- 檔案：`iceib-paper/main.tex`、`iceib-paper/main.txt`。
- 依據：`my_ref/A2Z outline example.pdf`（A–F）、`my_ref/README.md`（A–F 核心論證）。
- 摘要投稿期限 2027-03-01；F 段需要 E1 結果。
