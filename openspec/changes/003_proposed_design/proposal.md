# Proposal：003_proposed_design

## Why

III. Proposed Design 是論文的核心，要讓讀者從目標一路讀到演算法與數學性質。依 2020 A-Z SOP，需涵蓋 **PA–PM**，所有架構與規則依 `my_ref/README.md`（①–⑧、`IsSufficient` C1–C3、R1–R5、融合與升級條件）。

## What Changes

- 規範 Section III 的 PA–PM：PA 目標、PB 背景、PC 解法理由；PD 典範轉移（單一判斷 → 證據融合與升級）、PE/PF 八模組與功能、PG 架構圖；PH 證據蒐集／分級／領域知識與 R1–R5 表；PI 式 (1)(2) 與 Algorithm 1、2；PJ 示意範例；PK 關鍵點、PL 銜接實驗；PM Proposition 1（門檻單調性）與 Proposition 2（高風險安全性）及證明。

## Capabilities

### New Capabilities

- `proposed-design-pa-to-pm`：Proposed Design 的 PA–PM 完整性、架構與演算法一致性、範例與證明的正確性。

### Modified Capabilities

（無）

## Impact

- 檔案：`iceib-paper/main.tex`、`iceib-paper/main.txt`（Section III、Fig. 1、Table III、Algorithm 1–2、式 (1)(2)、Proposition 1–2）。
- 依據：`my_ref/A2Z outline example.pdf`（PA–PM）、`my_ref/README.md`、`AIOT-DIC3-ProjectRefactor/DESIGN.md` §3–§9。
