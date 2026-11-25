# Design：撰寫 ICEIB 2027 學術論文

## Context

- 動機見 `proposal.md` — Why。
- 現況：`ICEIB paper/main.tex` 已有完整初稿（IEEEtran、約 6–7 頁），內容來自 `docs/proposal.md`、`DESIGN.md`、`docs/project-core.md`；章節為 Introduction、Related Work、Proposed、Experimental Setup、Results、Discussion、Conclusion，沒有 A2Z 標記，結果欄位為 `[TBD]`。
- 已上傳至 Overleaf（專案 ID `6b064f4bd40bb166a2b1f0f2`），兩邊沒有同步。
- 本機沒有 TeX Live；ICEIB 2027 的 guideline 頁面仍顯示 pending，目前已知規定只有：英文、全文 4–8 頁、EI 索引（IEEE 領域）。
- 寫作 SOP：`myref/A2Z outline example.pdf`（文字版 `myref/A2Z outline example.md`）。

## Goals / Non-Goals

**Goals:**
- 每個 A2Z 代號都能在原始檔中定位到對應段落，可用腳本自動檢查。
- 實驗前就能產出可編譯、可審閱的完整論文，實驗後只需填入數字。

**Non-Goals:**
- 不在本變更中執行實驗；數據來自 `build-soc-triage-agent`。
- 不製作簡報、海報或 Engineering Proceedings 的 Word 版本。
- 不設定 Overleaf 與 GitHub 的自動同步。

## Decisions

### D1：章節標題採用使用者指定的名稱，內容採用 A2Z 字母
A2Z SOP 的章節名稱是 Proposed Scheme 與 Simulation；使用者要求 Proposed Design 與 Experiment。本專題的評估是在真實資料集上的實驗而不是模擬，因此採用 **III. Proposed Design** 與 **IV. Experiment**，內容仍依 PA–PM 與 Q–V 組織。

### D2：A2Z 以 LaTeX 註解標記，不放進 PDF
替代方案：(a) 用 `\paragraph{A. Attention Getter}` 顯示在 PDF；(b) 定義可切換的巨集。學術論文不應出現寫作骨架，(a) 不可行；(b) 增加複雜度。採用 `% [A2Z:<代號>]` 註解：PDF 乾淨，原始檔可 grep，並以檢查腳本驗證順序與完整性。

### D3：初稿章節的重新歸屬
| 初稿 | 新位置 |
|---|---|
| Experimental Setup（資料、切分、baseline、實作） | IV. Experiment：S、R、Q |
| Results（E1 表、取捨曲線、E2–E5、消融） | IV. Experiment：U |
| Discussion（自動化 vs. 協作、規則 vs. ML） | IV. Experiment：V |
| Discussion — Limitations | V. Conclusion：Z（精簡）＋ IV. Experiment：V（效度威脅） |
| Illustrative Walk-Through | III：PJ |

### D4：PM 數學性質
採用可直接由 Algorithm 1–2 推導的命題，避免依賴實驗：
- **命題 1（門檻單調性）**：固定其他參數，令 A(τ) 為自動結案（AUTO_TRIAGED）的事件集合。若 τ₁ ≤ τ₂，則 A(τ₂) ⊆ A(τ₁)；因為 TP 漏判只可能發生在自動結案且標籤不是 TP 的事件，TP 漏判率對 τ 單調不增，人工升級率對 τ 單調不減。
- **命題 2（高風險安全性）**：若事件觸發高風險規則，則該事件必定被升級；因此任何觸發 R1–R5 的真實攻擊都不會被自動結案。
兩者證明都只需要升級條件式 (2) 的定義。

### D5：O 的 4×5 SWOT 表
4 列 = 四類研究；5 欄 = Representative works、S、W、O、T。O（Opportunities）寫本研究可以補上的機會，T（Threats）寫該類方法在實務上的風險。表格放在 II. Related Work 結尾，與 AIDA 比較表並存；若頁數超過 8 頁，先刪減 AIDA 比較表並把重點併入 N 段。

### D6：A2Z 檢查腳本
新增 `ICEIB paper/check_a2z.py`（只用 Python 標準函式庫）：讀取 `main.tex`，抽出 `% [A2Z:<代號>]`，檢查 A–O、PA–PM、Q–Z 全部出現且第一次出現的順序符合 SOP；同時回報 `[TBD]`、作者佔位文字，以及未被引用的 `\bibitem` 與沒有對應文獻的 `\cite`。腳本以非零結束碼表示「不可投稿」。

### D7：編譯驗證
以 Overleaf 為主要編譯環境（`main.tex` 修改後重新上傳或貼上），頁數與編譯錯誤以 Overleaf 的 PDF 與 log 為準；本機若之後安裝 TeX Live，可改用 `latexmk -pdf`。

## Risks / Trade-offs

- [加入 SWOT 表、命題與證明後超過 8 頁] → 依序刪減：AIDA 比較表、PJ 範例縮短、GUIDE profile 表改為正文一句話。
- [實驗在全文期限前無法完成] → 摘要階段（2027-03-01）只需摘要；全文期限前未完成的實驗從 U 移除並在 Z 說明，不保留 `[TBD]`。
- [Overleaf 與本機 `main.tex` 分歧] → 以 repo 中的 `main.tex` 為唯一來源，Overleaf 只用來編譯。
- [ICEIB 2027 guideline 公布後有額外規定（例如字型、版權頁）] → 公布後新增一個 change 修改 `007-format`。

## Open Questions

- 作者的英文姓名、系所與學校（投稿前由組員提供，不影響其他任務）。
- 投稿時是否需要匿名審查（guideline 頁面公布後確認；若需要，投稿版暫時移除作者區塊）。
