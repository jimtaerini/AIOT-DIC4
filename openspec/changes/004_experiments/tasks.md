# Tasks

## 1. 撰寫 Experiment（Q–V，實驗前可完成的部分）

- [x] 1.1 撰寫 Q 與實驗設計表，驗證：`% [A2Z:Q]` 段落引用 Section III 的 MR、ER 定義
- [x] 1.2 撰寫 R，驗證：四個 baseline 與三種消融都被列出
- [x] 1.3 撰寫 S 與 GUIDE profile 表，驗證：數字與 `my_ref/README.md` 相同，寫明依 `OrgId` + `IncidentId` 切分
- [x] 1.4 撰寫 T，驗證：每個參數都有候選值，寫明只用驗證集
- [x] 1.5 建立 U 的結果表骨架（`[TBD]`），驗證：Table VI 可編譯
- [x] 1.6 撰寫 V 的效度威脅，驗證：至少四項威脅（匿名化資料、LLM 幻覺、評分主觀、刪 log 攻擊）

## 2. 填入結果（依賴 `build-soc-triage-agent`）

- [ ] 2.1 以 E1 結果填入 Table VI 並畫 MR–ER 曲線，驗證：每個數字對應 `experiments/results/` 中的值
- [ ] 2.2 填入 E2–E5 與消融結果並完成 V 的有效性結論，驗證：Section IV 不再有 `[TBD]`

## 3. 同步與檢查

- [x] 3.1 執行檢查，驗證：`check_a2z.py` 回報 Q–V 齊全且順序正確，`main.txt` 與 `main.tex` 相同
