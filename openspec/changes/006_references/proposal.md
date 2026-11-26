# Proposal：006_references

## Why

References 是最後一個章節，也是投稿前整體驗證的最後關卡：IEEE 引用格式、引用完整性，以及整份論文是否符合 ICEIB 2027 的投稿條件（IEEEtran、章節順序、4–8 頁、作者資訊、A2Z 標記、`main.txt` 與 `main.tex` 一致、沒有 `[TBD]`）。

## What Changes

- 規範 `thebibliography` 的 IEEE 格式與 `\cite` / `\bibitem` 一一對應，文獻來源與 `AIOT-DIC3-ProjectRefactor/docs/proposal.md` §6 一致。
- 規範投稿前的整體檢查：`python3 iceib-paper/check_a2z.py` 結束碼為 0，Overleaf 編譯無 error 且為 4–8 頁。

## Capabilities

### New Capabilities

- `references-ieee-verification`：IEEE 引用格式與完整性，以及投稿前的整份論文驗證。

### Modified Capabilities

（無）

## Impact

- 檔案：`iceib-paper/main.tex`、`iceib-paper/main.txt`（References、作者區塊、整份論文）、`iceib-paper/check_a2z.py`。
- 依據：IEEE reference style、ICEIB 2027 投稿規定（英文、4–8 頁）、`AIOT-DIC3-ProjectRefactor/docs/proposal.md` §6。
- 期限：摘要 2027-03-01、全文 2027-04-20。
