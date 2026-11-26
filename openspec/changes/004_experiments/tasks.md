# Tasks

## 1. 撰寫 Experiment（Q–V，實驗前可完成的部分）

- [x] 1.1 撰寫 Q 與實驗設計表，驗證：`% [A2Z:Q]` 段落引用 Section III 的 MR、ER 定義
- [x] 1.2 撰寫 R，驗證：四個 baseline 與三種消融都被列出
- [x] 1.3 撰寫 S 與 GUIDE profile 表，驗證：數字與 `my_ref/README.md` 相同，寫明依 `OrgId` + `IncidentId` 切分
- [x] 1.4 撰寫 T，驗證：每個參數都有候選值，寫明只用驗證集
- [x] 1.5 建立 U 的結果表骨架（`[TBD]`），驗證：Table VI 可編譯
- [x] 1.7 撰寫 V 的「規則與資料的落差」發現（R1 在 GUIDE 上觸發 15%、TP 比例 7.0% 低於基準 20.4%；規則維持不變並作為發現報告），驗證：數字與 `e1e_rules_escalation.json` 相同
- [x] 1.6 撰寫 V 的效度威脅，驗證：至少四項威脅（匿名化資料、LLM 幻覺、評分主觀、刪 log 攻擊）

## 2. 填入結果（依賴 `build-soc-triage-agent`）

- [x] 2.1a 以 E1 非 LLM 結果填入 Table VI 前三列（多數類別、Detector 規則、GBDT）與 IV-E 的組織／時間切分說明，驗證：數字與 `AIOT-DIC3-ProjectRefactor/experiments/results/e1_results.json` 相同
- [x] 2.1b 以不含 LLM 的信心升級與 R1–R5 結果畫出 Fig. 2 的 MR–ER 曲線，並在 Table VI 新增「GBDT + escalation」列，驗證：座標與數字和 `experiments/results/e1e_curve.csv`、`e1e_rules_escalation.json` 相同
- [ ] 2.1c 以純 LLM baseline 與完整 Agent（含 LLM 融合）的結果填入 Table VI 最後兩列並在 Fig. 2 加上 Agent 曲線，驗證：每個數字對應 `experiments/results/` 中的值
- [ ] 2.2 填入 E2–E5 與消融結果並完成 V 的有效性結論，驗證：Section IV 不再有 `[TBD]`

## 3. 同步與檢查

- [x] 3.1 執行檢查，驗證：`check_a2z.py` 回報 Q–V 齊全且順序正確，`main.txt` 與 `main.tex` 相同
