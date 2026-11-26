# Spec Delta：related-work-m-to-o

## Purpose

確保 II. Related Work 依 2020 A-Z SOP 的 M–O 組成：依類別展開文獻、指出新趨勢與 novelty，並以 4×5 SWOT 表歸納。

## ADDED Requirements

### Requirement: M Methods 四類小節
II. Related Work SHALL 以四個小節展開 ML 分級、領域知識整合、LLM Agent、SOC 人因，每個小節有 `% [A2Z:M]` 標記並說明代表研究的做法與主要數據。

#### Scenario: 檢查小節
- **WHEN** 列出 Section II 的前四個 `\subsection`
- **THEN** 各對應一類研究並有 `% [A2Z:M]`

### Requirement: N New proposed 研究缺口
N 段 SHALL 說明新趨勢與研究缺口，並以表格比較本研究與 AIDA。

#### Scenario: 檢查缺口
- **WHEN** 檢查 `% [A2Z:N]` 段落
- **THEN** 段落列出研究缺口並 `\ref` 比較表

### Requirement: O Organize SWOT 4×5
O SHALL 提供 4 列資料 × 5 欄（Representative works、Strengths、Weaknesses、Opportunities、Threats）的表格，含 `\caption` 與 `\label`。

#### Scenario: 檢查 SWOT 表
- **WHEN** 檢查 `% [A2Z:O]` 標記的表格
- **THEN** 表格為四類研究 × 五欄

#### Scenario: 與 J 一致
- **WHEN** 比對 Introduction 的 J 段與 SWOT 表
- **THEN** J 提到的每個不足都出現在 Weaknesses 或 Threats 欄
