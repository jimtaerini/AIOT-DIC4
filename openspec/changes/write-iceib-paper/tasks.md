# Tasks

> 規格見 `specs/`，做法見 `design.md`。論文原始檔為 `ICEIB paper/main.tex`；編譯以 Overleaf（專案 `6b064f4bd40bb166a2b1f0f2`）為準。

## 1. 參考資料與檢查工具

- [x] 1.1 將 A2Z SOP 放入 `myref/`（PDF 與文字版），驗證：`myref/A2Z outline example.pdf` 與 `.md` 存在
- [x] 1.2 實作 `ICEIB paper/check_a2z.py`（D6），驗證：對目前尚無標記的 `main.tex` 執行時，以非零結束碼列出缺少的代號
- [x] 1.3 在 README 加入論文與 `myref/` 的說明及檢查指令，驗證：README 中的指令照抄可執行

## 2. 格式與章節骨架（paper-format）

- [x] 2.1 將章節改為 Introduction、Related Work、Proposed Design、Experiment、Conclusion，並依 D3 搬移初稿內容，驗證：`grep '\\section' main.tex` 依序只出現這五個（Acknowledgment 除外）
- [x] 2.2 在 Overleaf 編譯，驗證：無 error，PDF 為 4–8 頁

## 3. Abstract 與 Introduction（paper-abstract、paper-introduction）

- [x] 3.1 依 A–F 改寫摘要並加標記，驗證：`check_a2z.py` 回報 A–F 齊全，摘要 ≤ 250 字
- [x] 3.2 依 G–L 改寫 Introduction 並加標記，驗證：`check_a2z.py` 回報 G–L 齊全且順序正確；L 段以 `\ref` 提及 II–V

## 4. Related Work（paper-related-work）

- [x] 4.1 依 M 整理四個小節並加標記，驗證：四個小節各有 `% [A2Z:M]`
- [x] 4.2 撰寫 N 段（新趨勢、研究缺口、與 AIDA 的差異），驗證：`% [A2Z:N]` 段落引用比較表
- [x] 4.3 新增 O 的 4×5 SWOT 表（D5），驗證：表格 4 列 × 5 欄，J 段的每個不足都出現在 W 或 T 欄

## 5. Proposed Design（paper-proposed-design）

- [x] 5.1 撰寫 PA–PC 開頭小節，驗證：依序出現 PA、PB、PC 標記
- [x] 5.2 為 PD–PI 既有內容（架構、模組、架構圖、證據蒐集、分級、知識、演算法）加上標記並補齊 PE 的八模組清單，驗證：`check_a2z.py` 回報 PD–PI 齊全且順序正確
- [x] 5.3 將範例移為 PJ，並寫明 illustrative，驗證：融合計算 (0.46, 0.45, 0.09) 與 (0.70, 0.15, 0.15) 平均得 (0.58, 0.30, 0.12)
- [x] 5.4 撰寫 PK（關鍵貢獻）與 PL（銜接 IV. Experiment），驗證：PL 段以 `\ref` 指向 Experiment
- [ ] 5.5 撰寫 PM 的命題 1、2 與證明（D4），驗證：證明只使用 Algorithm 1–2 與式 (1)(2) 已定義的符號，並由一位組員獨立檢查

## 6. Experiment（paper-experiment）

- [x] 6.1 撰寫 Q（規模與指標定義）、R（baseline 與消融）、S（資料、切分、實作），驗證：`check_a2z.py` 回報 Q、R、S 齊全；TP 漏判率與升級率有明確定義
- [x] 6.2 撰寫 T（參數與範圍，只在驗證集調參），驗證：w_ml、w_llm、τ、τ_safety、B、R5 門檻都有範圍
- [x] 6.3 建立 U 的結果表與取捨曲線骨架，未完成的欄位以 `[TBD]` 標示，驗證：E1 表與曲線圖存在且可編譯
- [x] 6.4 撰寫 V（優勢、失效情況、效度威脅），實驗前先寫效度威脅，驗證：`% [A2Z:V]` 段落至少含一項效度威脅
- [ ] 6.5 （依賴 `build-soc-triage-agent` 的 E1–E5 與消融）以 `experiments/results/` 的結果填入 U 與 V，驗證：每個數字可對應到結果檔中的值，`main.tex` 中不再有 `[TBD]`

## 7. Conclusion 與 References（paper-conclusion、paper-references）

- [x] 7.1 依 W–Z 改寫 Conclusion 並加標記，驗證：`check_a2z.py` 回報 W–Z 齊全；Z 段含限制與至少兩項未來工作
- [x] 7.2 檢查引用完整性與 IEEE 格式，驗證：`check_a2z.py` 回報沒有未被引用的 `\bibitem` 與缺少文獻的 `\cite`，Overleaf log 沒有 undefined citation

## 8. 投稿前整體檢查

- [ ] 8.1 填入作者英文姓名、系所、學校與 email，驗證：`check_a2z.py` 不再回報作者佔位文字
- [ ] 8.2 最終檢查，驗證：`check_a2z.py` 結束碼為 0，Overleaf 編譯無 error 且為 4–8 頁，PDF 中搜尋不到 `[A2Z:`

## Workflow follow-up

- 2027-03-01 前透過 ICEIB 線上系統投稿摘要；2027-04-20 前投稿全文。
- ICEIB 2027 guideline 公布後，確認是否需要匿名審查或其他格式規定，必要時新增 change 修改 `paper-format`。
- 全文投稿後封存本變更（`openspec archive write-iceib-paper`）。
