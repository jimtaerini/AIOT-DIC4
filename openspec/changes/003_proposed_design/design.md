# Design：003_proposed_design

## Context

Section III 已依 PA–PM 寫成七個小節，含 TikZ 架構圖、R1–R5 表、兩個演算法、示意範例與兩個命題。

## Goals / Non-Goals

**Goals:** 每個 P 字母都有對應段落；範例計算正確；證明只用已定義的符號。

**Non-Goals:** 不提供實驗數據支撐的主張（留給 004_experiments）。

## Decisions

1. **PE 與 PF 合併為一段**：八個模組各配一個功能，避免重複列舉；兩個標記都放在該段。
2. **PG 圖用 TikZ 內嵌**：Overleaf 不需額外圖檔。
3. **PM 選可直接推導的命題**：Proposition 1：τ₁ ≤ τ₂ ⇒ A(τ₂) ⊆ A(τ₁)，所以 TP 漏判率不增、升級率不減。Proposition 2：觸發 R1–R5 的事件必定升級。兩者只依賴式 (2) 與 Algorithm 2，不依賴實驗。
4. **PJ 數值明確標為 illustrative**：(0.46, 0.45, 0.09) 與 (0.70, 0.15, 0.15) 以 0.5 權重得 (0.58, 0.30, 0.12)。

## Risks / Trade-offs

- [證明錯誤會損害可信度] → 由一位組員獨立檢查（任務 2.2）。
