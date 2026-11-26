# Design：006_references

## Context

論文有 24 筆 `\bibitem`，全部被引用；作者區塊仍為佔位文字；Overleaf 編譯為 6 頁。`check_a2z.py` 以結束碼區分：0 可投稿、1 結構問題、2 仍有 `[TBD]` 或作者佔位文字。

## Goals / Non-Goals

**Goals:** 一個指令就能判斷是否可投稿。

**Non-Goals:** 不改用 BibTeX（Overleaf 單檔編譯較簡單）。

## Decisions

1. **使用內嵌 `thebibliography`**：不需 `.bib` 檔，`main.tex` 單檔即可在 Overleaf 編譯。
2. **中文文獻翻譯標題並註明 (in Chinese)**：國安局報告依此處理。
3. **整份論文的格式規則放在此變更**：IEEEtran、章節順序、頁數、作者、`main.txt` 同步都是投稿前最後確認的項目；章節內容規則放在 000–005。
4. **`main.txt` 為 `main.tex` 的逐位元組副本**：與參考專案一致；檢查腳本比對 SHA-256。

## Risks / Trade-offs

- [ICEIB 2027 guideline 公布後有新規定（例如匿名審查）] → 屆時新增 `007_xxx` 變更。
