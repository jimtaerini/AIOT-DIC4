# Design：002_related_work

## Context

Section II 已有四個 M 小節、N 小節與 Table I（AIDA 比較）、O 小節與 Table II（SWOT，`table*` 跨雙欄）。

## Goals / Non-Goals

**Goals:** M 依由簡到繁排序；O 的 SWOT 與 Introduction 的 J 互相對應。

**Non-Goals:** 不重製 `docs/proposal.md` 的完整 8 欄文獻彙整表（篇幅不足）。

## Decisions

1. **SWOT 為 4 列 × 5 欄**：4 列 = 四類研究；5 欄 = Representative works、Strengths、Weaknesses、Opportunities、Threats（A2Z「SWOT 列表 4x5 table」）。Opportunities 寫本研究可補上的機會。
2. **SWOT 用 `table*`**：五欄文字在單欄放不下。
3. **保留 AIDA 比較表於 N**：AIDA 是最接近的研究；若超過 8 頁，此表最先被刪，重點併入 N 段文字。

## Risks / Trade-offs

- [`table*` 浮動位置造成版面空白] → 以 `[t]` 放頁首，Overleaf 檢查位置。
