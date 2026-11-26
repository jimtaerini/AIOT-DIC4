# Spec Delta：introduction-g-to-l

## Purpose

確保 I. Introduction 依 2020 A-Z SOP 的 G–L 組成，從現況、挑戰、文獻分類與評論，推到本研究的貢獻與文章結構。

## ADDED Requirements

### Requirement: G General 現況
Introduction SHALL 以 G 段開頭，用有引用的數據說明攻擊規模、潛伏時間與外洩成本，並說明 TP / BP / FP 分級。

#### Scenario: 數字有引用
- **WHEN** 檢查 `% [A2Z:G]` 段落
- **THEN** 每個數字都附有 `\cite`，且與 `my_ref/README.md` 一致

### Requirement: H However 挑戰與研究問題
H 段 SHALL 說明告警疲勞、LLM 漏判與過早結案、自動化自滿，並明確寫出研究問題。

#### Scenario: 檢查研究問題
- **WHEN** 檢查 `% [A2Z:H]` 段落
- **THEN** 段落以斜體寫出研究問題

### Requirement: I In literature 四類文獻
I 段 SHALL 將相關研究分為 ML 分級、領域知識整合、LLM Agent、SOC 人因四類，各有至少一個引用。

#### Scenario: 檢查分類
- **WHEN** 檢查 `% [A2Z:I]` 段落
- **THEN** 四類都被提及並各有引用

### Requirement: J Judgement 評論
J 段 SHALL 為每一類方法寫出至少一個優點與一個不足，並指出缺少「何時交給人」的設計。

#### Scenario: 檢查評論
- **WHEN** 檢查 `% [A2Z:J]` 段落
- **THEN** 四類都有優點與不足

### Requirement: K Keypoint 貢獻
K 段 SHALL 說明 M1–M5 設計精神與 novelty，並以條列列出至少三項貢獻。

#### Scenario: 檢查貢獻
- **WHEN** 檢查 `% [A2Z:K]` 段落
- **THEN** 有 `itemize` 條列至少三項貢獻

### Requirement: L List the organization
Introduction SHALL 以 L 段結尾，以 `\ref` 依序說明 II 到 V。

#### Scenario: 檢查章節引用
- **WHEN** 檢查 `% [A2Z:L]` 段落
- **THEN** `sec:related`、`sec:design`、`sec:exp`、`sec:concl` 都被 `\ref`
