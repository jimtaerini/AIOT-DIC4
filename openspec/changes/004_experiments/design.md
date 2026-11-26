# Design：004_experiments

## Context

Section IV 已依 Q–V 寫成六個小節；Table IV（實驗設計）、Table V（GUIDE 實測 profile）、Table VI（E1 結果，全部 `[TBD]`）。A2Z 稱此章為 Simulation，本論文以真實資料集評估，因此章名為 Experiment。

## Goals / Non-Goals

**Goals:** 實驗前就能完成 Q、R、S、T 與 V 的效度威脅；實驗後只需填入 U 與 V 的結果。

**Non-Goals:** 不在本變更執行實驗。

## Decisions

1. **MR 與 ER 用 Section III 的定義**：與 Proposition 1 共用符號，T 段的 τ 掃描因此保證得到單調曲線。
2. **T 的候選值為規劃值**：w_ml ∈ {0.5, 0.6, 0.7, 0.8}、τ_safety ∈ {0.2, 0.3, 0.4}、B ∈ {5, 10, 15}、R5 門檻 ∈ {3, 4, 5}、τ ∈ [0.50, 0.95] 間隔 0.05；可在實驗開始前調整。
3. **結果填寫規則**：每個數字必須能在 `experiments/results/` 找到；全文投稿前仍未完成的實驗從 U 刪除並在 Conclusion 說明，而不是保留 `[TBD]`。

## Risks / Trade-offs

- [全文期限前無法完成所有實驗] → 依 E1 → E2 → E5 → E3 → E4 優先順序執行（同 `build-soc-triage-agent`）。
- [GUIDE 單一廠商、匿名化] → V 段列為效度威脅，並以組織切分與 ExCyTIn-Bench 部分緩解。
