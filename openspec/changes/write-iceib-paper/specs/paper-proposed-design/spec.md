# Spec Delta：paper-proposed-design

## Purpose

定義 III. Proposed Design 必須依 A2Z SOP 的 PA–PM 組成，讓讀者從目標、架構、元件、演算法、範例一路讀到貢獻與數學性質。

## ADDED Requirements

### Requirement: PA–PC 目標、背景與解法
III. Proposed Design SHALL 以 PA（設計目標）、PB（設計依據的背景與聚焦）、PC（解法及其有效的原因）開頭，三者各以 `% [A2Z:PA]`、`% [A2Z:PB]`、`% [A2Z:PC]` 標記。

#### Scenario: 檢查開頭
- **WHEN** 檢查 III. Proposed Design 的第一個小節
- **THEN** 依序出現 PA、PB、PC 標記

### Requirement: PD–PG 架構、元件、功能與架構圖
論文 SHALL 說明設計如何結合 ML、領域知識與 LLM（PD），列出八個模組（PE），說明各模組的功能（PF），並提供一張架構圖與圖說（PG）。

#### Scenario: 檢查架構圖
- **WHEN** 檢查 `% [A2Z:PG]` 標記的圖
- **THEN** 圖中出現八個模組，且正文以 `\ref` 引用該圖

### Requirement: PH–PI 做法與演算法
論文 SHALL 說明系統如何達成設計目標（PH），並以兩個演算法（SOC Triage Agent、FuseEvidence）呈現元件互動與流程（PI）。

#### Scenario: 檢查演算法
- **WHEN** 檢查 `% [A2Z:PI]` 標記
- **THEN** 有兩個 `algorithm` 環境，且證據足夠性條件與升級條件都被定義

### Requirement: PJ 範例
論文 SHALL 用一個事件範例走完整個流程，並明確標示範例數值為示意，不是實驗結果。

#### Scenario: 檢查範例
- **WHEN** 檢查 `% [A2Z:PJ]` 段落
- **THEN** 段落寫明數值為 illustrative，且融合計算結果正確

### Requirement: PK–PL 貢獻與實驗銜接
論文 SHALL 摘要設計的關鍵貢獻（PK），並說明下一章如何評估這些設計（PL）。

#### Scenario: 檢查銜接
- **WHEN** 檢查 `% [A2Z:PL]` 段落
- **THEN** 段落以 `\ref` 指向 IV. Experiment

### Requirement: PM 數學性質
論文 SHALL 以至少一個命題與證明說明升級機制的性質，例如提高門檻 τ 時 TP 漏判率不會增加；命題 MUST 可由演算法定義直接推導，不得依賴實驗結果。

#### Scenario: 檢查命題
- **WHEN** 檢查 `% [A2Z:PM]` 標記
- **THEN** 有一個命題與完整證明，且證明只使用演算法中已定義的符號
