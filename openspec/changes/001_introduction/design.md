# Design：001_introduction

## Context

Section I 已有 G（兩段）、H、I、J、K（含 M1–M5 與三項貢獻條列）、L，每段有 A2Z 註解。

## Goals / Non-Goals

**Goals:** H 比摘要的 B 更具體並以研究問題結尾；I 與 II. Related Work 的四類分類一致。

**Non-Goals:** 不在 Introduction 展開個別文獻細節（留給 M）。

## Decisions

1. **G 用三個來源的數據（國安局、Mandiant、IBM）**：分別支撐規模、潛伏時間與成本，數字依 `my_ref/README.md`。
2. **I 的四類順序 = 由簡到繁**：ML 分級 → 領域知識 → LLM Agent → 人因，與 A2Z「from old to new, simple to complex」一致。
3. **J 的每個不足都要在 SWOT 表（O）找得到**：讓 J 與 002_related_work 的 O 互相對應。

## Risks / Trade-offs

- [Introduction 過長擠壓頁數] → G 與 J 各維持一段；細節移到 Related Work。
