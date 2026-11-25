# Spec Delta：paper-format

## Purpose

定義 ICEIB 2027 論文的整體格式：IEEE conference 版面、固定的章節順序、頁數與語言限制、A2Z 寫作標記，以及原始檔必須可以編譯。

## ADDED Requirements

### Requirement: IEEE conference 版面
論文 SHALL 使用 IEEEtran 的 conference 模式（雙欄），原始檔為 `ICEIB paper/main.tex`，並可用 pdfLaTeX 編譯。

#### Scenario: 編譯論文
- **WHEN** 在 Overleaf 或 TeX Live 以 pdfLaTeX 編譯 `main.tex`
- **THEN** 產生雙欄 PDF，編譯記錄沒有錯誤（error）

### Requirement: 固定章節順序
論文 SHALL 依序包含：Abstract、Index Terms、I. Introduction、II. Related Work、III. Proposed Design、IV. Experiment、V. Conclusion、References；不得有其他編號章節。Acknowledgment 為選用的不編號章節。

#### Scenario: 檢查章節
- **WHEN** 列出 `main.tex` 中所有 `\section`
- **THEN** 依序恰好是 Introduction、Related Work、Proposed Design、Experiment、Conclusion（Acknowledgment 除外）

### Requirement: ICEIB 投稿限制
論文 MUST 以英文撰寫，編譯後的頁數 MUST 介於 4 到 8 頁（含參考文獻）。

#### Scenario: 頁數超過
- **WHEN** 編譯後的 PDF 超過 8 頁
- **THEN** 論文不得投稿，需先刪減內容

#### Scenario: 頁數不足
- **WHEN** 編譯後的 PDF 少於 4 頁
- **THEN** 論文不得投稿，需先補足內容

### Requirement: A2Z 標記
每個依 A2Z SOP 撰寫的段落、表格、圖或演算法 SHALL 在原始檔中以 LaTeX 註解 `% [A2Z:<代號>]` 標示其對應字母（例如 `% [A2Z:A]`、`% [A2Z:PG]`）；標記只出現在註解中，不得出現在 PDF。

#### Scenario: 檢查標記完整
- **WHEN** 執行 A2Z 標記檢查
- **THEN** A–O、PA–PM、Q–Z 每個代號至少出現一次，且依 SOP 順序排列

#### Scenario: 檢查 PDF
- **WHEN** 搜尋編譯後的 PDF 文字
- **THEN** 不會出現 `[A2Z:` 字樣

### Requirement: 作者資訊
投稿版 MUST 填入每位作者的英文姓名、系所、學校、城市與 email，不得留下範本佔位文字。

#### Scenario: 投稿前檢查
- **WHEN** 原始檔仍含 `Author Name` 或 `[University]` 等佔位文字
- **THEN** 論文不得投稿
