# Step 3 — 两遍自校验（Validate）

Progress: `输入与定位 → 蒸馏 → [两遍自校验] → 终门与交付`

**Read (input):** step 2 落下的整条记录；输入清单（Preservation 的走查对面）。
**Write (output):** 修补后的记录；`assumptions` / `open_questions`；`verdict` 两段。

每次 create 或 update 之后都要扫这两遍，再交付。

## Pass 1 — Coherence（对 Spec Law 1–6 与 8）

1. 逐条过 Spec Law 1–6、8：`intent` + `success` 是否成对、`intent` 是否说了 WHAT、每条 constraint 是否真淘汰设计、non-goals 是否至少一条、success signal 是否可测、CAP ID 是否稳定唯一（退役的**留条目、标 `retired: true`**，不删）、句子是否都承载内容。
2. 判弱但**输入支持得住**的 → 就地修，不发明输入里没有的内容。
3. **未经直接确认的裁量** → 落 `assumptions[]`，一条一句讲清依据。
4. **修不了的缺口** → 落 `open_questions[]`，写成一个人能直接回答的问句（如「离线播放是否在 CAP-2 范围内？」）。
5. 稀疏输入的路径选择（express / guided，含无头默认）写在 `verdict.coherence` **段末一句**——它是 Pass 1 的输入判定，不是独立字段。

## Pass 2 — Preservation（对 Spec Law 7）

拿 step 1 的输入清单，**逐条声明**走一遍：

- load-bearing 的 → 确认它落进了内核某字段或某条 `artifacts`；
- 只在前置材料里、产物中确实找不到落点的 → 补落（能补则补）；
- **纯包装性内容**（仪式性套话、过程叙事、上游的过程元数据）→ 明确丢弃，并把丢掉的东西写进 `verdict.preservation.dropped`，一条一句。

**不许静默丢弃。** `dropped` 是这次丢弃的留痕位——它让丢弃成为决定而不是疏漏；写了就是交代清楚了，空列表表示确实没有丢弃。

## 落 verdict

```yaml
verdict:
  coherence: <Pass 1 判决一段；稀疏输入时末尾加一句 express|guided 的选择>
  preservation:
    dropped: [<wrapper-only 内容，一条一句；无则空列表>]
    note: <Pass 2 走查结论一段：逐了多少条声明、丢弃了几条>
```

交互式：把判决给用户过一眼，`assumptions` / `open_questions` 逐条摆出来。无头：判决留在产物里，调用方（或其下游）从 `verdict` 读。

## 播报与下一步

一句话：两遍判决结果、修了几处、`assumptions` / `open_questions` 各几条。

读全并照做 `./04-finish.md`。
