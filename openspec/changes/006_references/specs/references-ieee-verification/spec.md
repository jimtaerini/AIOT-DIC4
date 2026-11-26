# Spec Delta：references-ieee-verification

## Purpose

確保參考文獻符合 IEEE 格式且引用完整，並在投稿前確認整份論文符合 ICEIB 2027 的格式與誠實性要求。

## ADDED Requirements

### Requirement: IEEE 引用格式
References SHALL 使用 IEEE 格式並以英文撰寫；非英文文獻 SHALL 翻譯標題並註明 (in Chinese)。

#### Scenario: 中文文獻
- **WHEN** 檢查國安局報告的條目
- **THEN** 標題為英文並註明 (in Chinese)

### Requirement: 引用完整性
每個 `\bibitem` MUST 至少被 `\cite` 一次，每個 `\cite` 的鍵 MUST 有對應的 `\bibitem`。

#### Scenario: 檢查引用
- **WHEN** 執行 `python3 iceib-paper/check_a2z.py`
- **THEN** 不回報未被引用的 `\bibitem` 或缺少文獻的 `\cite`

### Requirement: 文獻來源一致
論文新增的文獻 MUST 同時加入 `AIOT-DIC3-ProjectRefactor/docs/proposal.md` §6。

#### Scenario: 新增文獻
- **WHEN** 論文新增一篇 proposal.md 沒有的文獻
- **THEN** 同一次修改也更新 proposal.md §6

### Requirement: IEEE 版面與章節順序
論文 SHALL 使用 IEEEtran conference 模式，編號章節依序為 Introduction、Related Work、Proposed Design、Experiment、Conclusion。

#### Scenario: 檢查章節
- **WHEN** 執行檢查腳本
- **THEN** 章節清單與上述順序相同

### Requirement: 頁數與語言
論文 MUST 以英文撰寫，Overleaf 編譯後為 4 到 8 頁且沒有 error。

#### Scenario: 頁數超過
- **WHEN** PDF 超過 8 頁
- **THEN** 論文不得投稿

### Requirement: main.txt 同步
`iceib-paper/main.txt` MUST 與 `iceib-paper/main.tex` 逐位元組相同。

#### Scenario: 檢查同步
- **WHEN** 執行檢查腳本
- **THEN** 回報兩檔 SHA-256 相同

### Requirement: 投稿阻礙
投稿版 MUST 不含 `[TBD]` 與作者佔位文字（例如 `Author Name`、`[University]`）。

#### Scenario: 仍有阻礙
- **WHEN** 檢查腳本結束碼為 2
- **THEN** 論文不得投稿
