# Spec Delta：conclusion-w-to-z

## Purpose

確保 V. Conclusion 依 2020 A-Z SOP 的 W–Z 組成，回顧研究、強調優勢與成果，並說明限制與未來工作。

## ADDED Requirements

### Requirement: W 回顧
Section V SHALL 以 W 段開頭，以 2–3 句回顧挑戰與提出的方案。

#### Scenario: 檢查 W
- **WHEN** 檢查 `% [A2Z:W]` 段落
- **THEN** 同時提到挑戰與方案

### Requirement: X 優勢
X 段 SHALL 說明至少一個適用情境與一個優勢。

#### Scenario: 檢查 X
- **WHEN** 檢查 `% [A2Z:X]` 段落
- **THEN** 有適用情境與優勢，且引用已證明的性質

### Requirement: Y 成果一致
Y 段的數字 MUST 與 Section IV 相同；實驗完成前以 `[TBD]` 標示。

#### Scenario: 比對數字
- **WHEN** 比對 Y 段與 Table VI
- **THEN** 每個數字都相同

### Requirement: Z 結論與未來工作
Z 段 SHALL 說明問題如何被解決、主要限制，並列出至少兩項未來工作。

#### Scenario: 檢查 Z
- **WHEN** 檢查 `% [A2Z:Z]` 段落
- **THEN** 有限制與至少兩項未來工作
