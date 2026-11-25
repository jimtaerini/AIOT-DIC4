# Spec Delta：paper-related-work

## Purpose

定義 II. Related Work 必須依 A2Z SOP 的 M–O 組成：依方法類別展開文獻、指出新趨勢與本研究的 novelty，並以 4×5 SWOT 表歸納。

## ADDED Requirements

### Requirement: M Methods 依類別展開
II. Related Work SHALL 以四個小節展開 Introduction 的四類研究，每類由舊到新、由簡到繁排列，並說明代表研究的做法、資料與主要數據。

#### Scenario: 檢查小節
- **WHEN** 列出 II. Related Work 的 `\subsection`
- **THEN** 前四個小節分別對應 ML 分級、LLM Agent、領域知識整合、SOC 人因，各有 `% [A2Z:M]` 標記

### Requirement: N New proposed 新趨勢與定位
N 段 SHALL 說明領域的新趨勢，並明確寫出研究缺口與本研究相對最接近研究（AIDA）的差異。

#### Scenario: 檢查缺口
- **WHEN** 檢查 `% [A2Z:N]` 段落
- **THEN** 段落寫出研究缺口，並引用與 AIDA 的比較表

### Requirement: O Organize 4×5 SWOT 表
O 段 SHALL 提供一個表格：4 列對應四類研究，5 欄依序為 Representative works、Strengths、Weaknesses、Opportunities、Threats。

#### Scenario: 檢查 SWOT 表
- **WHEN** 檢查 `% [A2Z:O]` 標記的表格
- **THEN** 表格恰好有 4 列資料與 5 欄（不含列標題欄），且有 `\caption` 與 `\label`

#### Scenario: SWOT 與評論一致
- **WHEN** 比對 SWOT 表與 Introduction 的 J 段
- **THEN** J 段提到的每個不足都出現在 Weaknesses 或 Threats 欄
