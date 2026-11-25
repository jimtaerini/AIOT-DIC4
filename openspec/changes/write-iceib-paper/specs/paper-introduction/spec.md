# Spec Delta：paper-introduction

## Purpose

定義 I. Introduction 必須依 A2Z SOP 的 G–L 組成，從現況、挑戰、文獻分類與評論，一路推到本研究的設計精神、貢獻與文章結構。

## ADDED Requirements

### Requirement: G General 現況
Introduction SHALL 以 G 段開頭，用有引用的數據說明攻擊規模、潛伏時間與外洩成本，並說明 SOC 分級（TP / BP / FP）的工作內容與 IoT / OT 告警如何進入 SOC。

#### Scenario: 檢查 G 段
- **WHEN** 檢查 `% [A2Z:G]` 標記的段落
- **THEN** 每個數字都附有引用

### Requirement: H However 挑戰
H 段 SHALL 比摘要的 B 段更詳細地說明告警疲勞、LLM 漏判與過早結案、自動化自滿，並以一句話提出研究問題。

#### Scenario: 檢查研究問題
- **WHEN** 檢查 `% [A2Z:H]` 段落
- **THEN** 段落以斜體或明確句型寫出研究問題

### Requirement: I In literature 文獻分類
I 段 SHALL 將相關研究分為四大類（ML 分級、LLM Agent、領域知識整合、SOC 人因），依由舊到新、由簡到繁的順序簡述，細節留給 II. Related Work。

#### Scenario: 檢查分類
- **WHEN** 檢查 `% [A2Z:I]` 段落
- **THEN** 四類研究都被提及並各有至少一個引用

### Requirement: J Judgement 評論
J 段 SHALL 評論四類方法各自的優點與不足，並指出它們共同缺少「何時該交給人」的設計。

#### Scenario: 檢查評論
- **WHEN** 檢查 `% [A2Z:J]` 段落
- **THEN** 每一類方法都有至少一個優點與一個不足

### Requirement: K Keypoint 貢獻
K 段 SHALL 說明設計精神（M1–M5 五個核心思維）與 novelty，並以條列列出系統、方法、實驗三項貢獻。

#### Scenario: 檢查貢獻
- **WHEN** 檢查 `% [A2Z:K]` 段落
- **THEN** 有一個條列清單，列出至少三項貢獻

### Requirement: L List the organization
Introduction SHALL 以 L 段結尾，依序說明 II 到 V 各章節的內容，並使用 `\ref` 引用章節編號。

#### Scenario: 檢查文章結構段
- **WHEN** 檢查 `% [A2Z:L]` 段落
- **THEN** II、III、IV、V 四個章節都以 `\ref` 被提及
