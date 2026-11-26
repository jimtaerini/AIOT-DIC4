# Tasks

## 1. 參考文獻

- [x] 1.1 以 IEEE 格式整理 24 筆文獻，驗證：國安局報告為英文標題並註明 (in Chinese)
- [x] 1.2 檢查引用完整性，驗證：`check_a2z.py` 回報 24 個 `\bibitem` 與 24 個被引用的鍵，無缺漏

## 2. 格式與同步

- [x] 2.1 確認 IEEEtran 與章節順序，驗證：`check_a2z.py` 回報五個章節依序正確
- [x] 2.2 在 Overleaf 編譯，驗證：6 頁、無 error（2026-11-25 使用者回報）
- [x] 2.3 在檢查腳本加入 `main.txt` / `main.tex` SHA-256 比對，驗證：兩檔相同時回報 identical，不同時結束碼為 1

## 3. 投稿前檢查

- [ ] 3.1 填入四位作者的英文姓名、系所、學校、城市與 email，驗證：`check_a2z.py` 不再回報作者佔位文字
- [ ] 3.2 最終檢查，驗證：`check_a2z.py` 結束碼為 0，Overleaf 編譯為 4–8 頁且無 error
