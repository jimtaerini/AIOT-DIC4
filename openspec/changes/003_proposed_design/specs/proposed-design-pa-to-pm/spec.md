# Spec Delta：proposed-design-pa-to-pm

## Purpose

確保 III. Proposed Design 依 2020 A-Z SOP 的 PA–PM 組成，且架構、規則與演算法與 `my_ref/README.md` 一致。

## ADDED Requirements

### Requirement: PA–PC 目標、背景與理由
Section III SHALL 以 PA、PB、PC 三段開頭，分別說明設計目標、背景與解法有效的原因。

#### Scenario: 檢查開頭
- **WHEN** 檢查 Section III 第一個小節
- **THEN** 依序出現 `% [A2Z:PA]`、`% [A2Z:PB]`、`% [A2Z:PC]`

### Requirement: PD–PG 架構與架構圖
論文 SHALL 說明典範轉移（PD）、列出八個模組（PE）及其功能（PF），並提供架構圖與圖說（PG）。

#### Scenario: 檢查架構圖
- **WHEN** 檢查 `% [A2Z:PG]` 標記的圖
- **THEN** 圖中出現 ①–⑧ 八個模組且正文 `\ref` 該圖

### Requirement: PH–PI 做法與演算法
論文 SHALL 說明 `IsSufficient` 的 C1–C3、分級方法與 R1–R5（PH），並以融合式、升級條件與兩個演算法呈現流程（PI），內容與 `my_ref/README.md` 一致。

#### Scenario: 檢查演算法
- **WHEN** 檢查 `% [A2Z:PI]` 標記
- **THEN** 有兩個 `algorithm` 環境與升級條件式

### Requirement: PJ 示意範例
論文 SHALL 用一個事件走完流程，標明數值為 illustrative，且計算正確。

#### Scenario: 檢查計算
- **WHEN** 以 w_ml = w_llm = 0.5 融合 (0.46, 0.45, 0.09) 與 (0.70, 0.15, 0.15)
- **THEN** 結果為 (0.58, 0.30, 0.12)

### Requirement: PK–PL 關鍵點與實驗銜接
論文 SHALL 摘要設計關鍵點（PK），並說明下一章如何評估（PL），以 `\ref` 指向 Section IV。

#### Scenario: 檢查銜接
- **WHEN** 檢查 `% [A2Z:PL]` 段落
- **THEN** 段落 `\ref{sec:exp}`

### Requirement: PM 數學性質
論文 SHALL 提供至少一個命題與完整證明，證明 MUST 只使用式 (1)(2) 與 Algorithm 1–2 已定義的符號，不依賴實驗結果。

#### Scenario: 檢查命題
- **WHEN** 檢查 `% [A2Z:PM]` 標記
- **THEN** 有 `proposition` 與 `IEEEproof` 環境
