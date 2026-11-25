# Spec Delta：004-experiment

## Purpose

定義 IV. Experiment 必須依 A2Z SOP 的 Q–V 組成，並確保每個實驗數字都能追溯到實驗結果檔，實驗完成前不會出現推測的數據。

## ADDED Requirements

### Requirement: Q Quality and Quantity 指標
IV. Experiment SHALL 以 Q 段定義實驗規模（資料集、事件數、抽樣數）與指標：Macro-F1、各類 Precision / Recall、TP 漏判率、人工升級率、ATT&CK 對應 Precision / Recall、報告品質評分與成本。

#### Scenario: 檢查指標定義
- **WHEN** 檢查 `% [A2Z:Q]` 段落
- **THEN** TP 漏判率與人工升級率都有明確定義

### Requirement: R Related methods 比較方法
R 段 SHALL 列出比較對象：多數類別、Detector 歷史誤報率規則、純 GBDT、純 LLM（無知識庫），以及消融設定。

#### Scenario: 檢查比較方法
- **WHEN** 檢查 `% [A2Z:R]` 段落
- **THEN** 四個 baseline 與三種消融設定都被列出

### Requirement: S Setup 實驗設定
S 段 SHALL 說明資料集（GUIDE、ExCyTIn-Bench）、實測的資料特性、依事件／組織／時間的切分方式，以及實作環境。

#### Scenario: 檢查資料切分
- **WHEN** 檢查 `% [A2Z:S]` 段落
- **THEN** 寫明以 OrgId 與 IncidentId 為鍵切分，以避免資料洩漏

### Requirement: T Tuning 參數
T 段 SHALL 列出調整的參數（w_ml、w_llm、τ、τ_safety、工具預算 B、R5 門檻）與調整範圍，並說明只在驗證集上調整。

#### Scenario: 檢查調參
- **WHEN** 檢查 `% [A2Z:T]` 段落
- **THEN** 每個參數都有範圍或候選值，且寫明不使用測試集調參

### Requirement: U Useful results 結果
U 段 SHALL 以表格與圖報告 E1–E5 與消融實驗的結果，包含漏判率對升級率的取捨曲線。

#### Scenario: 結果表
- **WHEN** 檢查 `% [A2Z:U]` 標記
- **THEN** 至少有 E1 結果表與取捨曲線圖

### Requirement: V Verify 驗證有效性
V 段 SHALL 根據 U 的結果說明提出的方法是否優於比較方法、在什麼情況下失效，並討論對效度的威脅。

#### Scenario: 檢查驗證段
- **WHEN** 檢查 `% [A2Z:V]` 段落
- **THEN** 段落同時寫出優勢、失效情況與至少一項效度威脅

### Requirement: 數據可追溯
IV. Experiment 中每個實驗數字 MUST 來自 `experiments/results/` 下的結果檔；結果檔不存在時 MUST 以 `[TBD]` 標示，不得填入預期或推測的數字。

#### Scenario: 實驗尚未完成
- **WHEN** 某個實驗的結果檔不存在
- **THEN** 該表格欄位顯示 `[TBD]`

#### Scenario: 投稿前檢查
- **WHEN** 原始檔仍含 `[TBD]`
- **THEN** 論文不得投稿
