# Spec Delta：006-references

## Purpose

定義論文參考文獻的格式與完整性：使用 IEEE 引用格式，每篇文獻都被引用，每個引用都有對應文獻。

## ADDED Requirements

### Requirement: IEEE 引用格式
References SHALL 使用 IEEE 格式（作者縮寫名、標題加引號、期刊或會議斜體、卷期頁、年份，有 DOI 時附 DOI），以英文撰寫；非英文文獻 SHALL 翻譯標題並註明原文語言。

#### Scenario: 非英文文獻
- **WHEN** 引用國安局的中文報告
- **THEN** 文獻條目使用英文標題，並註明 (in Chinese)

### Requirement: 引用完整性
每個 `\bibitem` MUST 在正文中至少被 `\cite` 一次，每個 `\cite` 的鍵 MUST 有對應的 `\bibitem`。

#### Scenario: 未被引用的文獻
- **WHEN** 某個 `\bibitem` 在正文中沒有被引用
- **THEN** 刪除該條目或在正文中加入引用

#### Scenario: 編譯檢查
- **WHEN** 編譯論文
- **THEN** 編譯記錄沒有 undefined citation 警告

### Requirement: 文獻來源一致
論文中的文獻 SHALL 以 `docs/proposal.md` §6 References 為來源；新增的文獻 MUST 同時補進 `docs/proposal.md` §6。

#### Scenario: 新增文獻
- **WHEN** 論文新增一篇 `docs/proposal.md` 沒有的文獻
- **THEN** 同一次修改也把該文獻加入 `docs/proposal.md` §6
