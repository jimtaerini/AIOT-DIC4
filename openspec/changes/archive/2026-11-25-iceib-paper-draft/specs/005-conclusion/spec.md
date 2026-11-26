# Spec Delta：005-conclusion

## Purpose

定義 V. Conclusion 必須依 A2Z SOP 的 W–Z 組成，回顧研究、強調方法的優勢與成果，最後說明限制與未來工作。

## ADDED Requirements

### Requirement: W What proposed 回顧
V. Conclusion SHALL 以 W 段開頭，用 2–3 句回顧研究動機、挑戰與提出的方案。

#### Scenario: 檢查 W 段
- **WHEN** 檢查 `% [A2Z:W]` 段落
- **THEN** 段落同時提到挑戰與提出的方案

### Requirement: X eXcel 優勢
X 段 SHALL 說明方法最適合的情境（例如大量告警、證據不完整、高風險攻擊鏈）以及相對既有方法的優勢。

#### Scenario: 檢查 X 段
- **WHEN** 檢查 `% [A2Z:X]` 段落
- **THEN** 段落至少寫出一個適用情境與一個優勢

### Requirement: Y Yields 成果
Y 段 SHALL 簡述實驗的主要數據，數字 MUST 與 IV. Experiment 一致；實驗完成前以 `[TBD]` 標示。

#### Scenario: 數字一致
- **WHEN** 比對 Y 段與 IV. Experiment 的表格
- **THEN** 每個數字都相同

### Requirement: Z Zen 結論與未來工作
Z 段 SHALL 強調問題獲得怎樣的解決與研究貢獻，並列出主要限制與至少兩項未來工作。

#### Scenario: 檢查 Z 段
- **WHEN** 檢查 `% [A2Z:Z]` 段落
- **THEN** 段落包含限制與至少兩項未來工作
