# Proposal：撰寫 ICEIB 2027 學術論文

## Why

本專題要投稿 ICEIB 2027（7th International Conference on Electronic Communications, Internet of Things and Big Data，2027 年 4 月 23–25 日，淡江大學）。目前 `ICEIB paper/main.tex` 只有一份初稿：章節是 Abstract、Introduction、Related Work、Proposed、Experimental Setup、Results、Discussion、Conclusion，與我們要的六段結構不同，段落也沒有依照本組的 A2Z 寫作 SOP（[`myref/A2Z outline example.pdf`](../../../myref/A2Z%20outline%20example.pdf)）逐字母組織。投稿期限是摘要 2027-03-01、全文 2027-04-20，需要一份可追蹤、可驗收的寫作規格，讓論文內容、格式與實驗數據都能逐項檢查。

## What Changes

- 將論文固定為七個部分：Abstract、I. Introduction、II. Related Work、III. Proposed Design、IV. Experiment、V. Conclusion、References，使用 IEEE conference（IEEEtran）格式並符合 ICEIB 投稿規定（英文、4–8 頁）。
- 每個部分依 A2Z SOP 組織：Abstract A–F、Introduction G–L、Related Work M–O、Proposed Design PA–PM、Experiment Q–V、Conclusion W–Z，並在 LaTeX 原始檔以註解標記每段對應的字母，方便檢查與交接。
- 將初稿的 Experimental Setup、Results、Discussion 併入 IV. Experiment（Q–V），限制與未來工作併入 V. Conclusion（Z）。**BREAKING**：初稿的章節編號與標題會改變。
- Related Work 新增 A2Z「O」要求的 4×5 SWOT 歸納表；Proposed Design 新增 PM 的數學性質與證明。
- 實驗數據一律來自 `build-soc-triage-agent` 的實驗結果檔；實驗完成前以 `[TBD]` 標示，不得填入推測數字。
- 新增 `myref/`：存放寫作參考資料（A2Z SOP 的 PDF 與文字版）。

## Capabilities

### New Capabilities

- `000-abstract`：摘要的 A–F 六段內容與關鍵字。
- `001-introduction`：引言的 G–L 內容（現況、挑戰、文獻分類、評論、貢獻、文章結構）。
- `002-related-work`：相關研究的 M–O 內容，含 4×5 SWOT 歸納表。
- `003-proposed-design`：系統設計的 PA–PM 內容（目標、架構、圖、演算法、範例、貢獻、數學性質）。
- `004-experiment`：實驗的 Q–V 內容（指標、比較方法、設定、參數、結果、驗證），以及數據來源的誠實性。
- `005-conclusion`：結論的 W–Z 內容（回顧、優勢、成果、結論與未來工作）。
- `006-references`：IEEE 引用格式與引用完整性。
- `007-format`：ICEIB / IEEE 格式、章節順序、頁數、語言、A2Z 標記慣例與可編譯性（跨章節）。

> 能力名稱以 `00N-` 編號，順序與論文章節一致；`007-format` 為跨所有章節的格式規格。

### Modified Capabilities

（無。既有變更 `build-soc-triage-agent` 的規格不變；本變更只引用它的實驗結果。）

## Impact

- **文件**：改寫 `ICEIB paper/main.tex`；新增 `myref/A2Z outline example.pdf` 與其文字版 `myref/A2Z outline example.md`；README 加入論文與 `myref/` 的說明。
- **相依**：IV. Experiment 的數據依賴 `build-soc-triage-agent` 的任務（E1–E5、消融）；實驗未完成前，論文仍可完成其他部分並編譯。
- **工具**：LaTeX 編譯使用 Overleaf 專案（ID `6b064f4bd40bb166a2b1f0f2`）或本機 TeX Live；新增一個檢查 A2Z 標記的腳本。
- **期限**：摘要 2027-03-01、全文 2027-04-20、最終版 2027-06-30。
