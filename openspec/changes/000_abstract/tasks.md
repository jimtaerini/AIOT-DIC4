# Tasks

## 1. 撰寫摘要（A–F）

- [x] 1.1 依 A–F 撰寫單一段落摘要並加 `% [A2Z:A]`–`% [A2Z:F]`，驗證：`check_a2z.py` 回報 A–F 齊全且順序正確
- [x] 1.2 控制長度並移除引用，驗證：`check_a2z.py` 回報摘要 ≤ 250 字（目前 187 字），`abstract` 環境內沒有 `\cite`
- [x] 1.3 對照 `my_ref/README.md` 檢查數字，驗證：E 段的 707,108 與 5,769 與 README 相同
- [x] 1.4 撰寫 Index Terms，驗證：7 個關鍵字，涵蓋 SOC、alert triage、LLM agent、MITRE ATT&CK、human-in-the-loop
- [ ] 1.5 （依賴 E1）以 IV. Experiment 的結果改寫 F，驗證：F 的數字與 E1 結果表（`tab:e1`）一致，摘要中不再有 `[TBD]`

## 2. 同步與檢查

- [x] 2.1 同步 `main.txt` 與 `main.tex`，驗證：`check_a2z.py` 回報兩檔 SHA-256 相同
