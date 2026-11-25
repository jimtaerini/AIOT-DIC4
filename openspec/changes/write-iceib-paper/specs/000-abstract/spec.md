# Spec Delta：000-abstract

## Purpose

定義論文摘要必須依 A2Z SOP 的 A–F 六段組成，讓讀者在一段文字內看到動機、挑戰、解法、方法、實驗與發現。

## ADDED Requirements

### Requirement: A–F 六段結構
摘要 SHALL 依序包含 A Attention Getter（動機與數據）、B But（挑戰）、C Cure（提出的方案）、D Development（方法設計）、E Experiments（資料集與比較對象）、F Findings（結果），每段以 `% [A2Z:<字母>]` 標記。

#### Scenario: 檢查摘要結構
- **WHEN** 檢查 `abstract` 環境中的標記
- **THEN** 依序出現 A、B、C、D、E、F 六個標記

### Requirement: 摘要長度
摘要 MUST 為單一段落，不超過 250 個英文字，且不得包含引用編號、數學式或縮寫未定義的專有名詞。

#### Scenario: 字數過長
- **WHEN** 摘要超過 250 字
- **THEN** 摘要需刪減到 250 字以內

### Requirement: Findings 只寫已驗證的結果
F Findings MUST 只陳述 `004-experiment` 已報告的結果；實驗完成前 SHALL 以 `[TBD]` 標示，不得寫入預期或推測的數字。

#### Scenario: 實驗尚未完成
- **WHEN** E1 的結果檔尚不存在
- **THEN** F 段落保留 `[TBD]`，不出現任何漏判率或 F1 數字

#### Scenario: 實驗完成
- **WHEN** E1 結果已寫入 IV. Experiment
- **THEN** F 段落的數字與 IV. Experiment 的表格一致

### Requirement: 關鍵字
摘要之後 SHALL 有 Index Terms，列出 5–8 個英文關鍵字，涵蓋 SOC、alert triage、LLM agent、MITRE ATT&CK 與 human-in-the-loop。

#### Scenario: 檢查關鍵字
- **WHEN** 檢查 `IEEEkeywords` 環境
- **THEN** 列出 5–8 個關鍵字，且包含上述五個主題
