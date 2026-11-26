# Design：005_conclusion

## Context

Section V 已有 W、X、Y（`[TBD]`）、Z 四段；原本 Discussion 的限制已併入 Z（精簡）與 IV-V（效度威脅）。

## Goals / Non-Goals

**Goals:** 四段各自簡短；X 以已證明的性質而非實驗數字說明優勢。

**Non-Goals:** 不引入正文沒出現過的新主張。

## Decisions

1. **X 引用 Proposition 1、2**：在實驗前就能具體說明優勢，且不需要數字。
2. **Y 只複述 Section IV 的數字**：實驗完成後由 004_experiments 的結果填入。
3. **Z 列三項未來工作**：佇列優先排序、ATT&CK for ICS（IoT/OT）、真實 SOC 部署的信任研究。

## Risks / Trade-offs

- [Y 與 IV 數字不一致] → 填寫 Y 時直接引用 Table VI 的值，並在任務中比對。
