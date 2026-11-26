# Spec Delta：abstract-a-to-f

## Purpose

確保論文摘要依 2020 A-Z SOP 的 A–F 六段組成，讓讀者在一段文字內看到動機、挑戰、解法、方法、實驗與發現。

## ADDED Requirements

### Requirement: A–F 六段結構
摘要 SHALL 依序涵蓋 A Attention Getter、B But、C Cure、D Development、E Experiments、F Findings，每段前以 `% [A2Z:<字母>]` 註解標記。

#### Scenario: 檢查順序
- **WHEN** 執行 `python3 iceib-paper/check_a2z.py`
- **THEN** A、B、C、D、E、F 都存在且依序出現

### Requirement: 摘要長度與內容
摘要 MUST 為單一段落、不超過 250 個英文字，且不得包含引用編號。

#### Scenario: 字數過長
- **WHEN** 檢查腳本回報摘要超過 250 字
- **THEN** 摘要需刪減到 250 字以內

### Requirement: 領域事實一致
摘要中的數字與主張 MUST 與 `my_ref/README.md` 一致。

#### Scenario: 檢查資料規模
- **WHEN** 摘要提到 GUIDE 的事件數與組織數
- **THEN** 數字為 707,108 起事件與 5,769 個組織

### Requirement: Findings 不得捏造
F Findings MUST 只陳述 IV. Experiment 已報告的結果；實驗完成前 SHALL 以 `[TBD]` 標示或改寫為不含數字的敘述。

#### Scenario: 實驗尚未完成
- **WHEN** E1 結果檔不存在
- **THEN** F 段不出現任何漏判率、升級率或 F1 數字

### Requirement: Index Terms
摘要之後 SHALL 有 `IEEEkeywords`，列出 5–8 個關鍵字，涵蓋 SOC、alert triage、LLM agent、MITRE ATT&CK 與 human-in-the-loop。

#### Scenario: 檢查關鍵字
- **WHEN** 檢查 `IEEEkeywords` 環境
- **THEN** 有 5–8 個關鍵字且涵蓋上述主題
