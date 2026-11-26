# Spec Delta：experiments-q-to-v

## Purpose

確保 IV. Experiment 依 2020 A-Z SOP 的 Q–V 組成，且每個實驗數字都能追溯到結果檔，實驗完成前不出現推測的數據。

## ADDED Requirements

### Requirement: Q 指標與規模
Section IV SHALL 以 Q 定義實驗、抽樣規模與指標，並以 Section III 的定義使用 MR 與 ER。

#### Scenario: 檢查指標
- **WHEN** 檢查 `% [A2Z:Q]` 段落
- **THEN** MR 與 ER 都被定義或引用其定義

### Requirement: R 比較方法
R 段 SHALL 列出四個 baseline（多數類別、Detector 誤報率規則、純 GBDT、純 LLM）與三種消融。

#### Scenario: 檢查比較方法
- **WHEN** 檢查 `% [A2Z:R]` 段落
- **THEN** 四個 baseline 與三種消融都被列出

### Requirement: S 實驗設定
S 段 SHALL 說明資料集、與 `my_ref/README.md` 一致的實測特性，以及以 `OrgId` + `IncidentId` 為鍵的切分。

#### Scenario: 檢查切分
- **WHEN** 檢查 `% [A2Z:S]` 段落
- **THEN** 寫明依事件切分並另做組織與時間切分

### Requirement: T 參數調整
T 段 SHALL 列出每個參數的候選值或範圍，並寫明只在驗證集調整。

#### Scenario: 檢查調參
- **WHEN** 檢查 `% [A2Z:T]` 段落
- **THEN** w_ml、τ_safety、B、R5 門檻與 τ 都有範圍

### Requirement: U 結果與 V 驗證
U SHALL 以表格與 MR–ER 曲線報告結果；V SHALL 說明優勢、失效情況與至少一項效度威脅。

#### Scenario: 檢查效度威脅
- **WHEN** 檢查 `% [A2Z:V]` 段落
- **THEN** 至少列出一項效度威脅

### Requirement: 數據可追溯
Section IV 的每個實驗數字 MUST 來自 `AIOT-DIC3-ProjectRefactor/experiments/results/` 的結果檔；結果不存在時 MUST 標示 `[TBD]`。

#### Scenario: 實驗尚未完成
- **WHEN** 結果檔不存在
- **THEN** 對應欄位顯示 `[TBD]`，不得出現推測數字
