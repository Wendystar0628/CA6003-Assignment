# CA6003 讲解视频方案

本文是视频唯一有效的方案（2026-10-14 版）。它合并了改版方案（单一版式、固定小窗、七部分进度条、主副标题、26 个场景）与用户 2026-10-14 的九条裁定，并保留旧方案中仍然有效的部分。早先的分镜、版式和合并记录已删除，git 历史中可查。

**语言。** 旁白、屏幕文字、主副标题和字幕用英文，其余用中文。

**人名。** 旁白与屏幕文字一律用人名记号，不用字母代号：

| 记号 | 含义 | `team.json` |
|---|---|---|
| `<Name>` | 本场景的讲者 | 本段讲者的 `members[i].name` |
| `<Name:0>` | 治理与集成成员 | `members[0].name` |
| `<Name:1>` | 数据质量与准备成员 | `members[1].name` |
| `<Name:2>` | 探索、标签与偏差成员 | `members[2].name` |
| `<Name:3>` | 建模与结论成员 | `members[3].name` |

规则见第 3 节。

---

## 0 摘要

**核心信息。** “The score is not the finding; what it reveals about the data is.” 分数本身不是发现，分数暴露出的数据问题才是。

**形式与观众。** 观众是课程讲师：本领域专家，但没看过本项目。形式是项目汇报：问题与数据 → 方法与设计 → 证据 → minimal vs systematic → 改进与恶化 → 贡献与反思。

**结构。** 四位成员各讲一段连续录像，顺序为治理 → 数据质量与准备 → 标签与偏差 → 建模与结论。讲者全片只出现在右下角一个固定小窗里。画面上方的七部分进度条承担导航。

```text
第 1 段 <Name:0>  0:00–2:16  01–07  可疑的 0.961 · 团队 · 议程与研究问题 · 队列 · 治理 · NCHS 复现 · 年龄混杂 · 意外发现
第 2 段 <Name:1>  2:16–4:30  08–13  缺失值代码（非显然发现）· 离群值 · 冗余与偏度 · 准备设计 · 意外发现
第 3 段 <Name:2>  4:30–6:51  14–19  Simpson 与 DAG · RQ1 标签 · 未确诊者 · RQ2a 泄漏检查 · 泄漏机制 · 意外发现
第 4 段 <Name:3>  6:51–9:26  20–26  RQ2b minimal vs systematic · 校准 · 分人群 AUC · 消融 · 留出集与回答 · 意外发现 · 收尾
```

**时长。** 全片 **9:26**（566 s），上限 12:00；26 个场景；旁白 1,189 词；扣除静默卡后平均 128 wpm，单场 125–134 wpm（场景 25 为 120，见 7.3 节）。

| 讲者 | 段落 | 时长 | 场景 | 旁白词数 | 平均语速 |
|---|---|---|---|---|---|
| `<Name:0>` 治理与集成 | 0:00–2:16 | 2:16（136 s） | 01–07 | 288 | 128 wpm |
| `<Name:1>` 数据质量与准备 | 2:16–4:30 | 2:14（134 s） | 08–13 | 281 | 128 wpm |
| `<Name:2>` 探索、标签与偏差 | 4:30–6:51 | 2:21（141 s） | 14–19 | 296 | 128 wpm |
| `<Name:3>` 建模与结论 | 6:51–9:26 | 2:35（155 s，≤ 3:00） | 20–26 | 324 | 129 wpm |
| 合计 | 0:00–9:26 | **9:26（566 s）** | 26 | 1,189 | 128 wpm |

### 0.1 关键决定

| # | 决定 | 要点 |
|---|---|---|
| 1 | 唯一版式 | 顶部进度条，64 px 主标题加 34 px 副标题，图区 1728×764，右下固定小窗 384×216（x 1416，y 748）加名签；没有右栏、徽章、全屏或分屏 |
| 2 | 七部分进度条 | Problem & data · Data quality · EDA & preparation · Labels & bias · Experiments · Results & robustness · Reflection；不写 “Part n of 7” |
| 3 | 标题写主题 | 主标题写本页主题，副标题写本页展示什么；结论放进旁白和图内 ≤ 5 词的标注 |
| 4 | 先讲设计 | 场景 02 是议程页：研究问题、同一模型 × 三种数据准备 × 两个评估人群、三个研究问题 |
| 5 | 研究问题编号 | RQ1 Labels → RQ2a Leakage → RQ2b Preparation，在 02 提出，在 24 回答，与揭示顺序一致 |
| 6 | 一人一段 | 每人一段连续录像；切换只在 2:16、4:30、6:51；没有合影，没有回场 |
| 7 | 不出现字母代号 | 屏幕和语音只用真名；名字唯一来源是 `notebooks/final/team.json`；未填时显示 “[Name]”（裁定 8） |
| 8 | 稳健性署名 | 留出集与稳健性核查署 “Robustness checks led by `<Name:1>`”（裁定 1） |
| 9 | 底栏指引 | 保留一行 “Notebook section N.M”（裁定 2） |
| 10 | 代号对照 | 全片只在场景 12 显示一次 “notebook: M0 · M1 · S”（裁定 3） |
| 11 | 第 1 段无段首页 | 由片头卡、团队页和名签介绍（裁定 4） |
| 12 | 节奏 | 每场 125–140 wpm；只在关键数字或揭示后停 0.8–1.5 s；不留超过约 1.5 s 的空白（裁定 5） |
| 13 | 字幕 | 烧录开放字幕，单独的字幕区，最多 2 行 × 42 字符；另出 `.srt` 供 YouTube（裁定 7） |
| 14 | 合成 | 每段场景拼接后整段叠一次讲者录像并烧录字幕，再拼成全片 |
| 15 | 首个交付 | 第 1 段完整成片（占位小窗 + 烧录字幕）先交用户审阅，其余三段按反馈再做（裁定 9） |

---

## 1 目标与约束

**目标。** 一段设计过的项目汇报视频，不是随意谈话。讲师应能看懂项目及其价值：主线连贯，逐层展开，视觉和动效克制专业，旁白与画面同步。

**作业硬性规则（摘自课程 brief）。**

| 规则 | 落实 |
|---|---|
| “12-minute (maximum)”，超出部分不计 | 9:26；排练上限 10:30 |
| “all group members must appear and present” | 四人各一段连续录像，各 2:14–2:35；小窗与名签全程可见 |
| “single continuous video” | 提交一个视频文件；每段一次连续录制；含义待讲师确认（10.6 节、第 15 节） |
| 内容要求：治理、剖析、EDA、准备、对 ML 的影响、非显然发现、minimal vs systematic、贡献与反思 | 逐项对应见 14.1 节 |
| “reasoning, evidence, and interpretation rather than code or model accuracy” | 无代码画面；每个 AUC 后接“这说明什么” |
| 文字简洁 | 每页 1 个主标题 + 1 个副标题 + ≤ 3 个图内标注 |
| YouTube 公开链接 + 组号 | 第 12 节 |

**评分（各 25 %）。**

| 准则 | 核心要求 | 主要抓手 |
|---|---|---|
| Appropriateness | 探索、剖析、清洗、偏差、EDA、评估各阶段的技术与可视化恰当 | 每个场景一张证据图（第 7 节） |
| Correctness & Clarity | 技术正确、解释清楚；**各成员的贡献清楚可分** | 一人一段；名签全程；团队页；段首页；署名行；收尾回顾 |
| Data Interpretation | 统计量、分布、关系；冗余、多重共线、偏度、谬误；有证据的结论 | 06、11、14–16、20–23 |
| Novelty & depth | 问题、准备策略、偏差分析的原创性；用 basic ML 为数据准备决定提供证据 | 被删的 7.0；插补出的 50；识别与筛查之分；模型作为泄漏探测器 |

**其他约束。**
- 每位成员只出现在自己的一段里；任何一帧只出现一位成员。
- 内容可以不与作者一致，用来平衡段长并保持故事顺序；讲他人的工作时，旁白点名，副标题行右端同时显示署名。
- 第 4 段 ≤ 3:00，且包含结尾。
- 不用幻灯片：画面是 HTML/SVG 动画场景加讲者小窗。只用 basic models，不用 LLM。截止 10/18。

---

## 2 内容主线

### 2.1 四条核心信息

| # | 核心信息 | 主证据 | 场景 |
|---|---|---|---|
| 1 | The headline AUC was leakage. Excluding post-diagnosis items is a correct deterioration; median imputation of a skipped question created a label proxy. | 0.961 → 0.828，配对下降 0.131 [−0.148, −0.114]；86 % 未被问及，插补为 50 | 17、18 |
| 2 | The label is a measurement shaped by care. Treatment masks HbA1c, and access to care decides who is diagnosed, so the all-adults AUC mostly measures recognition. | κ 0.70；250 of 819；152 未确诊，+23.2 pp [6.2, 40.1]；0.836 vs 0.781 | 15、16、22 |
| 3 | With the same model, systematic preparation barely moves AUC. Its value is data integrity, and one step had a measurable cost. | +0.008 [0.000, 0.016] vs margin 0.01，inconclusive；1,496 个有效值被保住；Brier +0.074 | 08–12、20–21 |
| 4 | Governance made these claims checkable. | 数据使用协议与最小化；NCHS 复现；事先锁定的假设；内部留出集 | 04、05、07、24 |

### 2.2 汇报结构

| 阶段 | 场景 | 内容 |
|---|---|---|
| 开场 | 01–02 | 可疑的 0.961；团队与分工；问题、设计、三个研究问题 |
| 数据与治理 | 03–07 | 队列与标签；治理；外部复现；混杂；第 1 段的意外 |
| 数据质量与准备 | 08–13 | 先剖析后清洗（非显然发现）；离群值；冗余与偏度；准备设计与三条流水线；第 2 段的意外 |
| 标签与偏差 | 14–16 | Simpson 与 DAG；RQ1 标签一致性；未确诊者与第二个评估人群 |
| 实验 | 17–21 | RQ2a 泄漏检查与机制；第 3 段的意外；RQ2b minimal vs systematic；一个恶化（校准） |
| 结果与稳健性 | 22–24 | 分人群 AUC；prior-care 消融；内部留出集；三个回答 |
| 反思 | 25–26 | 第 4 段的意外；贡献；局限；GenAI；结论 |

每个证据场景按“问题 → 方法 → 证据 → 含义”组织；口述数字 ≤ 3 个，关键效应带区间。标准概念不配比喻。

### 2.3 研究问题

沿用 notebook 1.5 节的编号。notebook 的 RQ2 同时包括泄漏规则和系统准备（假设 H2a 与 H2b），视频拆成 RQ2a 与 RQ2b。RQ3、RQ4 不讲。

| 屏幕文字（02 与 24b 字号、顺序相同） | 揭示 | 旁白中的叫法 |
|---|---|---|
| **RQ1 · Labels:** What do self-report and HbA1c each measure? | 15 | “Research question one: the label.” |
| **RQ2a · Leakage:** Does AUC 0.961 survive excluding post-diagnosis items? | 17 | “The leakage question” |
| **RQ2b · Preparation:** Does systematic beat minimal preparation, same model? | 20 | “Last question: does systematic preparation pay?” |

- 议程页研究问题下方加一行 28 px、墨色 60 % 的小字：“RQ3 (label matrix) and RQ4 (BMI bias): in the notebook”。
- 不用图标；研究问题不常驻画面，导航由进度条承担。
- 24b 的答案行（结论只写在这里，不进标题）：
  - **RQ1 · Labels：** “Self-report records contact with care as well as disease (κ = 0.70)”。不加 ✓：这一问是描述性的，加 ✓ 会被读成“标签可靠”。
  - **RQ2a · Leakage：** “No: AUC 0.961 → 0.828 once post-diagnosis items are excluded”，墨色实心 ✓。
  - **RQ2b · Preparation：** “AUC +0.008 [0.000, 0.016]: inconclusive”，墨色虚线框加 “?”。下面两行账本：“better: 1,496 valid values kept · an honest test on not-yet-diagnosed adults” / “worse: calibration (Brier +0.074)”。

### 2.4 贯穿对象

| 对象 | 出现 | 回收 | 收尾 |
|---|---|---|---|
| 0.961 | 01（钩子） | 17（原位降为 0.828） | 24b（RQ2a 的回答）、25（意外发现） |
| 被删的 HbA1c 7.0 | 08（被划掉） | 09（29 of 721） | 13（意外发现）、24b（“valid values kept”） |
| 152 名未确诊者 | 16（蓝色空心方块） | 19（52 of 100）、22–23（第二个评估人群） | 26b（局限） |

### 2.5 取舍

判断标准：删掉这一项后，观众还能说清核心思想及其理由吗？能，就收起或删除。

| 内容 | 处理 | 场景 | 理由 |
|---|---|---|---|
| 泄漏规则与 naive → minimal → systematic 对照 | 主线 | 12、17 | 删掉就无法解释 0.961 为何不可信 |
| 统一重编码删掉 7.0（1,496 vs 57；29 of 721；6 个翻转） | 主线 | 08–09、13 | 非显然发现；也是“准备的价值在别处”的证据 |
| 确诊年龄被插补成 50，树在它上面分裂 | 主线 | 18 | 泄漏的机制 |
| κ、250 / 819、165、152、+23.2 pp | 主线 | 15–16 | RQ1 的证据 |
| 全体成人 vs 未确诊成人；prior-care −0.016 vs +0.019 | 主线 | 22–23 | 回答“这个分数为谁服务” |
| 类别权重使 Brier 变差 | 主线 | 21 | 作业要求讲恶化，这是最清楚的一例 |
| VIF、偏度、年龄混杂、Simpson | 主线，各一场景 | 06、11、14 | brief 点名；每项只讲“发现 → 决定” |
| HbA1c 离群值 542 / 519 | 主线 | 10 | 离群值是病人，不能删 |
| 公平性：每 100 人 70 vs 52 被检出 | 第 3 段的意外 | 19 | 覆盖 bias analysis，并与 RQ1 相连 |
| 留出集 | 一句话 | 24 | 可信度证据；不念 +0.060 |
| NCHS DB516 复现 | 一句话 + 表 | 05 | 证明调查加权代码没有错 |
| 预注册锁定 | 一句话 | 04、07 | 证明结论不是事后挑选 |
| DAG、中介 | 一句话 | 14 | 谬误的另一种形式 |
| 团队回顾、GenAI 声明 | 一句话 + 卡片 | 26 | 贡献可区分；如实声明 |
| 响应率 34.6 % / 25.7 % | 只说 “low response”，不念数字 | 26 | 与三个研究问题无关 |
| 亚裔 BMI（51.1 % vs 7.2 %）、WHtR | 删除；WHtR 只在 12 留脚注 | — | 探索性，n = 47 |
| 3×3 标签矩阵、RQ3 | 删除，议程页注明在 notebook | — | 区间都跨 0 |
| ADA-lite 基线 | 删除 | — | 留出集没有复现，容易听成“优于 ADA” |
| 缺失机制（OR、IPW、Manski、MNAR） | 删除 | — | 结论是“基本不影响” |
| 置换检验、噪声列、种子、规格曲线、PSU 分组 CV、nested C、设计效应 | 删除 | — | 可信度细节，留在 notebook |
| 树在未确诊人群上的 AUC 0.633 / 0.701 | 删除 | — | 只是描述性探针 |
| 外部评审的六项核查 | 删除 | — | 不上屏、不进旁白（10.3 节） |
| 合影、四人画廊、回场、片尾单人短片 | 删除 | — | 一人一段 |

---

## 3 名字、角色与署名

### 3.1 名字规则（裁定 8）

- **字母 A、B、C、D 永远不出现在视频里**：不出现在屏幕上（名签、团队页、段首页、署名行、收尾回顾、片头片尾卡、字幕），也不出现在语音里。不写 “A”、“Member A”、“<A>”、“Analysis by C”。
- **唯一来源：** `notebooks/final/team.json` 的 `members[].name`（目前是占位值 “A”–“D”）。场景、字幕和合成脚本都从这里读名字，不在任何文件里手写名字。
- **占位：** 名字仍是占位值（单个字母，或含 “[TEAM TO FILL”）时，渲染为 “[Name]”；带职责时写成 “[Name] · Data quality & preparation”。字幕同样显示 “[Name]”。kit 审计在渲染出的文字里发现单独的 A–D 人名时报错。
- **方案里的写法：** 旁白与屏幕文字用 `<Name>`（本场景讲者）和 `<Name:i>`（成员 i）记号；口头自我介绍 “I'm A” 一律写成 “I'm `<Name>`”。
- **组号：** 同理来自 `team.json` 的 `group_number`，未填时显示 “[no.]”。

### 3.2 角色

| 成员 | 名签第 2 行（role） | 段首页 “Owns” 行 | 本人讲的部分 |
|---|---|---|---|
| `<Name:0>` | Governance & integration | governance, data access, reproducibility | Problem & data |
| `<Name:1>` | Data quality & preparation | quality audit, preparation design, robustness checks | Data quality · EDA & preparation |
| `<Name:2>` | Exploration, labels & bias | exploratory analysis, label analysis, fairness audit | Labels & bias · Experiments (leakage check) |
| `<Name:3>` | Modelling & conclusions | experiments, synthesis of conclusions | Experiments · Results & robustness · Reflection |

### 3.3 署名

讲他人的工作时，旁白点名原作者，副标题行右端显示一行署名（28 px 墨色，左侧 2×28 px 墨色竖线，无框）。

| 场景 | 署名行 | 旁白中的点名 |
|---|---|---|
| 06 | Analysis by `<Name:2>` | “In `<Name:2>`'s analysis” |
| 11 | EDA by `<Name:2>` | “`<Name:2>`'s exploration found” |
| 17 | Experiment by `<Name:3>` | “from `<Name:3>`'s experiments” |
| 18 | Experiment by `<Name:3>` | “`<Name:3>`'s shallow decision tree” |
| 20b | Preparation steps by `<Name:1>` | — |
| 21 | Class-weight step by `<Name:1>` | “`<Name:1>`'s class weights” |
| 22 | Population defined by `<Name:2>` | — |
| 24 | **Robustness checks led by `<Name:1>`**（裁定 1） | 不点名 |

### 3.4 自我介绍与交接

| 讲者 | 自我介绍（场景） | 意外发现（场景） | 交接句 |
|---|---|---|---|
| `<Name:0>` | “I'm `<Name>`; I led governance and integration.”（01，团队页） | 3 of 6 hypotheses supported（07） | “Now `<Name:1>` asks whether the data deserve the same trust.” |
| `<Name:1>` | “I'm `<Name>`; I led data quality and preparation.”（08） | 29 HbA1c results erased（13） | “But cleaning cannot fix the label itself. `<Name:2>` shows why.” |
| `<Name:2>` | “I'm `<Name>`; I led exploration, labels and bias.”（14） | 70 vs 52 of 100（19） | “`<Name:3>` takes the last question.” |
| `<Name:3>` | “I'm `<Name>`; I led modelling and conclusions.”（20） | leakage vs preparation（25） | —（第 4 段包含结尾） |

交接时，讲者看着镜头说完交接句，停约 0.5 s；切点落在下一段段首页的第 1 帧。节号只出现在底栏指引里，不念出来。

---

## 4 版式

### 4.1 唯一版式与网格

全片只有一种版式。画布 1920×1080，外边距左右 96 px、上 40 px、下 52 px。

```text
x  96                                                                                 1824
y  40 ┌ Problem & data   Data quality   EDA & preparation   Labels & bias   Experiments ... ┐  74  进度条
y  96 │ Main title (64 px serif)                                                            │ 160
y 172 │ Subtitle (34 px sans)                                    | Analysis by <Name:2>     │ 206
y 224 ┌──────────────────────────── 图区纸面面板 1728×764 ───────────────────────────────────┐
      │ 主区：面板 x 0–1272，y 0–648               副区：面板 x 1296–1728，y 0–408          │
      │                                                   ┌ Presented by <Name> ───────┐    │ 656
      │                                                   └ Data quality & preparation ┘    │ 740
y 872 │ ┌──────────── 字幕区 x 96–1368，y 872–988 ─────────┐ ┌────────────────────────────┐  │ 748
      │ │      Caption line one (Plex Sans, ink)           │ │   小窗 384×216（固定）      │  │
      │ │      Caption line two                            │ └────────────────────────────┘  │ 964
y 988 └─┴──────────────────────────────────────────────────┴──────────────────────────────────┘
y1000   ● reference baseline  ▨ harmed or leaked data  ■ Systematic preparation  □ Not-yet-...   Notebook section 7.5  1028
```

| 区域 | x | y | 尺寸 | 规格 |
|---|---|---|---|---|
| 进度条 | 96–1824 | 40–74 | 1728×34 | 七段；段名 24 px IBM Plex Sans，基线 y 60；4 px 细线在 y 70–74（5.1 节） |
| 主标题 | 96–1824 | 96–160 | 1728×64 | Source Serif 4，64 px，单行 |
| 副标题 | 96–1824 | 172–206 | 1728×34 | IBM Plex Sans 34 px，墨色，单行；有署名时在署名左侧 48 px 处结束 |
| 署名 | 副标题行右端 | 172–206 | 自适应 | 28 px sans，左侧 2×28 px 墨色竖线，无框 |
| 图区纸面面板 | 96–1824 | 224–988 | 1728×764 | 白纸，8 px 圆角，1 px #E3E7EC 边，柔和阴影；面板坐标原点 (96, 224) |
| 主图区 | 96–1368 | 224–872 | 1272×648 | 面板坐标 x 0–1272，y 0–648；证据图放这里 |
| 副图区 | 1392–1824 | 224–632 | 432×408 | 面板坐标 x 1296–1728，y 0–408；小图、图例条、脚注 |
| 字幕区 | 96–1368 | 872–988 | 1272×116 | 面板坐标 x 0–1272，y 648–764；只放字幕（第 8 节） |
| 名签 | 1416–1800 | 656–740 | 384×84 | 两行 28 px：`Presented by <Name>`（semibold）/ role；纸色底，1 px 细边，直角 |
| 小窗 | 1416–1800 | 748–964 | 384×216 | 直角；1 px #E3E7EC 细边画在外侧（1415–1801 × 747–965），由 kit 渲染；无阴影、无动画 |
| 避让区 | 1392–1824 | 632–988 | 432×356 | 小窗与名签外扩 24 px；面板坐标 x 1296–1728，y 408–764 |
| 底栏 | 96–1824 | 1000–1028 | 1728×28 | 左侧图例行（24 px）；右端 notebook 指引（24 px，墨色 60 %，右对齐到 x 1824） |

**禁区。** 图形内容不得进入避让区或字幕区，推近（M9，缩放 ≤ 1.25）后的包围盒也不行。kit 审计会拦截（9.4 节）。

### 4.2 小窗与名签

- **小窗：** 384×216（16:9，画面宽度的 1/5），全片同一坐标。胸像构图下脸高约 97 px。录像尚未完成时，合成用灰色 “camera” 占位块。
- **名签：** 全程常驻，写 “Presented by `<Name>`” 和职责（3.2 节）。
- **切换：** 换讲者只在 2:16、4:30、6:51，都在段首页的第 1 帧。新讲者从第 1 帧起就在小窗里，名签同时换字。

### 4.3 页面类型

网格和小窗不变，面板里放什么分成五种页面，外加两种过渡元素。

| 类型 | 用途 | 面板内容 | 规则 | 场景 |
|---|---|---|---|---|
| **证据页** | 数据讲解 | 一张证据图 | 一页一个主张；口述数字 ≤ 3；内容只在主区和副区 | 03–06、08b–12、14b–18、20b–23 |
| **段首页** | 第 2–4 段的开头 | 第 1 行 56 px serif：`Presented by <Name> · <role>`；第 2 行 28 px 墨色 60 %：`Owns: …`；下面每个部分一行 | 前 1.2 s 静默（进度条在此时切换）；自我介绍句后用 M12 溶解成第一张证据页 | 08a、14a、20a |
| **反思页** | 每段末尾的 “Most unexpected finding” | 正文一行 40 px serif（讲者的反思句）；小图缩到 ≤ 400 px 高放在下方；左下 28 px 墨色 60 % 的交接行 | ≤ 14 s；主标题固定，副标题以讲者名开头 | 07、13、19、25 |
| **议程页** | 开场路线图；24b 的回答版与之呼应 | 栏目名 28 px（墨色 60 %）+ 内容 34 px，左对齐 | 研究问题行的字号、顺序在 02 和 24b 完全相同 | 02、24b |
| **收尾页** | 贡献、局限与 AI、结论 | 角色卡与贡献链；局限标签与 GenAI 卡；一句 56 px 收束语 | 收束语是全片唯一以大字出现的结论 | 26a–c |
| 过渡：**章节卡** | 不换讲者的部分开头 | 舞台色满幅（小窗、名签照常露出）：80 px 部分名、34 px 范围行、28 px 讲者行 | 1.2 s 静止，计入所在场景时长，旁白在其后开口 | 11、17、22 |
| 过渡：**片头卡 / 片尾卡** | 开场 1.5 s、结尾 1.5 s | 片名 88 / 120 px，副标题行 “Basic models as instruments on NHANES 2021–2023” | 片尾卡：七段路线回到画面中央并全部为“已讲完”；底部一行数据来源 | 01a、26d |

**靛蓝只出现一处。** 一帧里，结构靛蓝只用于进度条当前段的填充线。卡片焦点用 M3 的 2 px 墨色描边加“暗其余”。

### 4.4 底栏

**图例行**（左侧，24 px，常驻，只显示已出现过的颜色）：`● reference baseline` · `▨ harmed or leaked data` · `■ Systematic preparation` · `□ Not-yet-diagnosed adults`。

**图例时刻**（颜色第一次出现时，副区一角出现 2–3 s，随后收进底栏；不需要旁白，在停顿处出现，不与数字 callout 同时出现）：

| 颜色 | 首次出现 | 图例条文字 |
|---|---|---|
| 灰 | 03（All adults 末条） | “● grey = reference: all adults” |
| 红 | 08（被误删的单元格、1,496 柱） | “▨ red = harmed or leaked data” |
| 青 | 12（systematic 泳道） | “■ teal = systematic preparation” |
| 蓝 | 16（152 人） | “□ blue = not-yet-diagnosed adults” |

议程页（02）的设计矩阵只用墨色，不提前用语义色。

**Notebook 指引**（右端，纯文字一行，裁定 2）。格式 `Notebook section 7.5`，多节时 `Notebook sections 4.7–4.8`。不写 “§”、结果键名或 notebook 原标题（原标题含 “M0 → M1”、“E-SCREEN” 等代号）。段首页、章节卡、片头卡和片尾卡不显示。下表已逐条对照 `notebooks/final/CA6003_NHANES_Diabetes.ipynb` 的标题。

| 场景 | 指引 | 依据（notebook 标题） | 场景 | 指引 | 依据（notebook 标题） |
|---|---|---|---|---|---|
| 01 | section 7.5 | 7.5 Leak gate（0.961 出处） | 14 | sections 4.7–4.8 | 4.7 Simpson scan；4.8 Causal structure |
| 02 | sections 1.3–1.5 | 1.3 Feature-availability rule；1.4 Evaluation populations；1.5 Research questions | 15 | sections 5.1–5.2 | 5.1 Three labels and their agreement；5.2 Treatment masking |
| 03 | sections 1.1, 3.2 | 1.1 Analysis cohort；3.2 … the sample funnel | 16 | sections 5.3–5.4 | 5.3 What "undiagnosed" means；5.4 Who is undiagnosed |
| 04 | sections 1.8–1.9 | 1.8 Data user agreement；1.9 Data minimisation | 17 | section 7.5 | 7.5 Leak gate |
| 05 | section 4.3 | 4.3 External anchor: NCHS Data Brief 516 | 18 | section 7.5 | 7.5 的 “So what” 讨论树与插补的 50 |
| 06 | sections 4.5–4.6 | 4.5 Age standardisation；4.6 Insurance | 19 | sections 8.2–8.3 | 8.2 Group metrics at the fixed threshold；8.3 Gaps |
| 07 | section 10.2 | 10.2 Hypothesis scoreboard | 20 | sections 7.12, 10.2 | 7.12 Verdicts；10.2.1 H2b in detail |
| 08 | section 3.4 | 3.4 Cost of a blanket recode | 21 | section 7.10 | 7.10 Precision–recall and calibration |
| 09 | section 3.4 | 同上 | 22 | section 7.9 | 7.9 E-ALL vs E-SCREEN |
| 10 | section 3.8 | 3.8 Outliers: a three-layer rule | 23 | section 7.8 | 7.8 Leave-one-block-out |
| 11 | sections 4.9–4.10 | 4.9 Redundancy and collinearity；4.10 Skewness | 24 | sections 9.11, 10.6 | 9.11 Internal hold-out check；10.6 Headline findings |
| 12 | sections 6.2, 6.9 | 6.2 Step catalogue；6.9 Arms | 25 | sections 7.5, 10.2 | 7.5 与 10.2 |
| 13 | section 3.4 | 3.4 | 26 | Notebook: Team and contributions; section 10.9 | 无编号的 “Team and contributions” 与 10.9 Limitations register |

---

## 5 导航与标题

### 5.1 七部分进度条

场景顺序由“一人一段”锁定，所以进度条只往前走。探索性分析分散在 06、11、14：06 留在第 1 部分；11 与准备设计合为第 3 部分；14 归入 “Labels & bias”。

| 段名（进度条与章节卡一字不差） | 场景 | 起止 | 时长 | 讲者 | 开头标识 | rubric 要点 |
|---|---|---|---|---|---|---|
| Problem & data | 01–07 | 0:00–2:16 | 136 s | `<Name:0>` | 片头卡 + 团队页（01） | 问题、设计、队列、治理、外部复现、混杂 |
| Data quality | 08–10 | 2:16–3:19 | 63 s | `<Name:1>` | 段首页（08a） | 剖析、非显然发现、离群值 |
| EDA & preparation | 11–13 | 3:19–4:30 | 71 s | `<Name:1>` | 章节卡（11） | 冗余、多重共线、偏度；准备设计；三条流水线 |
| Labels & bias | 14–16 | 4:30–5:49 | 79 s | `<Name:2>` | 段首页（14a） | 谬误；标签一致性；未确诊者与第二个评估人群 |
| Experiments | 17–21 | 5:49–7:42 | 113 s | `<Name:2>` → `<Name:3>` | 章节卡（17）；段首页（20a）不切换段 | 泄漏检查；minimal vs systematic；恶化 |
| Results & robustness | 22–24 | 7:42–8:48 | 66 s | `<Name:3>` | 章节卡（22） | 分人群表现；消融；留出集；回答研究问题 |
| Reflection | 25–26 | 8:48–9:26 | 38 s | `<Name:3>` | 无章节卡（25 只有 7 s） | 意外发现；贡献；局限；GenAI；结论 |

合计 566 s。

| 项 | 规格 |
|---|---|
| 位置 | x 96–1824，y 40–74 |
| 段名 | 只写部分名，不加序号，不用图标，不用 “§” |
| 段宽 | 段名宽 + 32 px，段间隙 16 px，从 x 96 左对齐；总宽约 1,450 px |
| 细线 | y 70–74，每段一条，与该段同宽 |
| 已讲完 | 段名墨色 60 %，细线墨色 |
| 当前段 | 段名墨色 100 % semibold；细线为结构靛蓝，按本段已用时间从左往右填充（全局时间 t 的纯函数，段起止由 `timeline.json` 求和得到），未填部分为 `--line` |
| 未讲到 | 段名墨色 60 %，细线 `--line` |
| 切换 | 在段首页或章节卡的前 1.2 s 内完成：上一段转为“已讲完”，新段变为 semibold，靛蓝线从新段左端开始填充（0.4 s，M12） |
| 出现 | 场景 02 末尾，议程里的七段路线用 M6（0.9 s）收缩到页顶，之后常驻到 26c；01 与 02 的前约 25 s 没有进度条 |
| 片尾 | 26d 片尾卡上，路线回到画面中央，七段全部为“已讲完” |

### 5.2 主标题与副标题

**主标题。**
- 64 px Source Serif 4，单行，最多约 5 个词。
- 写本页主题，可用标准术语，例如 “Data leakage check”、“Label agreement: self-report vs HbA1c”。
- 可以用问句，但只能说明本页检验什么，不能预设答案。可以：“How good is AUC 0.961?”；不可以：“How did the model cheat?”。
- 不写结论：不用 →、=、≫，不用 “worse”、“removed”、“inconclusive” 这类判定词，不放区间。
- 数字只在它本身就是主题时出现，全片只有 01b 一处。
- 不用内部代号（M0 / M1 / S、E-ALL / E-SCREEN、trap、P 编号、§）；不用人名字母。
- 一个场景一个标题，从头到尾不变。分阶段的场景每个阶段换一次：01（片头、钩子、团队）、08 / 14 / 20（段首页、正文）、24（留出集、回答）、26（贡献、局限、结论、片尾）。

**副标题。** 34 px IBM Plex Sans，单行，最多约 12 个词；比主标题晚 0.3 s 淡入，之后常驻。说明这一页给观众看什么：数据、方法或比较。不写结论，最多一个数字。

**结论的去处：** 旁白，或图内 ≤ 5 词的小标注，例如 17 的 “✓ correct deterioration”、23 的 “? inconclusive”。

| 不要这样写 | 问题 | 改为（主标题 / 副标题） |
|---|---|---|
| “0.961 → 0.828: leakage removed” | 结论，带箭头和数字 | **Data leakage check** / Naive vs minimal preparation: same model, post-diagnosis items excluded |
| “Low HbA1c = controlled, not healthy” | 结论，用 “=” | **Label agreement: self-report vs HbA1c** / Cohen's κ, and self-reported diabetics below the HbA1c threshold |
| “Two structural problems” | 结论，又没说是什么问题 | **Redundancy and skewness** / VIF for weight and BMI; skewness of fasting triglycerides |
| “+0.008 [0.000, 0.016] · inconclusive” | 整个标题是一个结果 | **Minimal vs systematic preparation** / Paired AUC difference and its CI, against a pre-registered equivalence margin |
| “Age confounds: +5.3 → +0.7 pp” | 结论 | **Confounding check: insurance gap** / Diabetes prevalence, insured vs uninsured, crude and age-standardised |
| “519 of 542 flagged are diabetic” | 结论，而且按定义就成立 | **Outlier handling** / HbA1c values beyond the 1.5 × IQR fences, by diabetes status |
| “How did the model cheat?” | 问句预设了答案 | **What the naive model learns** / A depth-3 decision tree, and median imputation of age at diagnosis |
| “Whom does the score serve?” | 看不出比较对象 | **AUC by evaluation population** / Systematic preparation on all adults and on not-yet-diagnosed adults |
| “Three traps, three answers” | “trap” 是内部叫法 | **Robustness and answers** / Internal hold-out check, then answers to the three research questions |
| 副标题 “Naive (M0) · Minimal (M1) · Systematic (S)” | 代号 | “Fourteen evidence-based steps combined into naive, minimal and systematic pipelines” |
| “Most unexpected for” 加成员字母 | 字母代号 | **Most unexpected finding** / `<Name:3>` on AUC change from leakage vs from preparation |

### 5.3 开场、段首页、章节卡与反思页

**第 1 段的开头（01，裁定 4：不设段首页）。**
- 片头卡（0–1.5 s，静默）：片名 “Who gets labelled diabetic?”；副标题行 “Basic models as instruments on NHANES 2021–2023”；第三行 28 px “Presented by `<Name:0>` · Governance & integration · Problem & data”；mono 小字 “CA6003 · Group [no.]”。
- 钩子（约 1.5–11 s）：AUC 轴 0.5–1.0，标 “axis starts at 0.5”，无 coin flip / perfect 标注；墨色指针升到 0.961（M10）。
- 团队页（约 11–29 s）：四张角色卡，三行：姓名 / 职责 / 本人讲的部分（3.2 节）。念到谁，谁的卡保持 100 %、加 2 px 墨色描边，其余暗到 25 %。卡片不收成徽章，结尾用 M12 溶解。

**段首页**（08a、14a、20a）。面板内左对齐，起点面板坐标 x 48，全部内容在 x ≤ 1272、y ≤ 648。

| 行 | 面板坐标 y（基线） | 规格 |
|---|---|---|
| 讲者与职责 | 110 | `Presented by <Name> · <role>`，56 px serif |
| 负责 | 170 | `Owns: …`，28 px sans，墨色 60 % |
| 本段覆盖的部分 | 250–420 | 每个部分一行，28 px sans：部分名 semibold，后接 2–3 个主题 |

| 页 | 主标题 | 副标题 | 卡片第 1 行 | 本段覆盖的部分 |
|---|---|---|---|---|
| 08a | Data quality | Profiling, missing-value codes and outliers | Presented by `<Name:1>` · Data quality & preparation | **Data quality:** missing-value codes · effect on labels · outliers / **EDA & preparation:** redundancy and skewness · preparation design |
| 14a | Labels & bias | Analytical fallacies, label agreement and undiagnosed diabetes | Presented by `<Name:2>` · Exploration, labels & bias | **Labels & bias:** Simpson's paradox scan · label agreement · undiagnosed diabetes / **Experiments:** data leakage check, with `<Name:3>`'s experiments |
| 20a | Experiments, results and reflection | Minimal vs systematic preparation, then results, robustness and reflection | Presented by `<Name:3>` · Modelling & conclusions | **Experiments:** minimal vs systematic · calibration / **Results & robustness:** populations · prior-care ablation · hold-out · answers / **Reflection** |

第 1、2 行在讲者说出姓名时用 M12 淡入；“本段覆盖的部分”在说出职责时淡入。自我介绍句结束（约 5–6 s）后，用 M12 溶解成证据页，标题随之换成证据页标题。

**章节卡**（11、17、22，各 1.2 s，不写 “Part n of 7”）。

| 场景 | 主标题（80 px） | 范围行（34 px） | 讲者行（28 px） |
|---|---|---|---|
| 11 | EDA & preparation | Redundancy, skewness, and the preparation design they inform | Presented by `<Name:1>` · EDA by `<Name:2>` |
| 17 | Experiments | Naive, minimal and systematic preparation: one model, same folds | Presented by `<Name:2>` · experiments by `<Name:3>` |
| 22 | Results & robustness | Performance by population, ablation, hold-out, and answers to the research questions | Presented by `<Name:3>` |

**反思页 “Most unexpected finding”**（07、13、19、25）。主标题相同；副标题以讲者名开头，写主题不写结果；结果写在正文一行里，与旁白同时出现。

| 页 | 副标题 | 正文一行（数据来源） | 交接行 |
|---|---|---|---|
| 07 | `<Name:0>` on the pre-registered hypotheses and their verdicts | Of six pre-registered hypotheses, three were supported and three inconclusive.（`hypotheses.json`：prereg_n 6，supported 3，inconclusive 3） | Next: Data quality · presented by `<Name:1>` |
| 13 | `<Name:1>` on one routine recode line | One routine recode line erased 29 HbA1c-positive results; the either-or label hid it.（`blanket_recode.json`：a1c_lost 29） | Next: Labels & bias · presented by `<Name:2>` |
| 19 | `<Name:2>` on detection at one cut-off, by diagnosis status | At one shared cut-off, 70 of 100 diagnosed but 52 of 100 not-yet-diagnosed diabetics are flagged.（`tpr_100.json`；小字 “specificity 0.80 · rates per 100”） | Next: Experiments, continued · presented by `<Name:3>` |
| 25 | `<Name:3>` on AUC change from leakage vs from preparation | Leakage moved AUC by 0.131; systematic preparation moved it by 0.008.（`leak_gate.json` diff_eall；`prep_band.json` d_auc） | Next: contributions, limits and conclusion |

### 5.4 屏幕术语

**标准术语照用，不在画面上解释：** AUC、HbA1c、Cohen's κ、VIF、skewness、confidence interval（方括号，图注写一次 “CI”，不写 95 %，因为 `prep_band.json` 没有记录置信水平）、data leakage、median imputation、Brier score、calibration、spectrum bias、Simpson's paradox、DAG、pp、L2 logistic regression。

**内部代号 → 屏幕名称。**

| 内部代号 | 屏幕名称（首次） | 之后 | 旁白 | 视觉 |
|---|---|---|---|---|
| M0 | Naive preparation (all columns) | Naive | “naive preparation” | 红色斜纹 |
| M1 | Minimal preparation (post-diagnosis items excluded) | Minimal | “minimal” | 灰色实心 |
| S | Systematic preparation | Systematic | “systematic” | 青色实心 |
| 三者的对照 | 只在 12 的泳道标签下用 24 px 灰字注一次 “notebook: M0 · M1 · S”（裁定 3） | — | — | — |
| E-ALL | All adults | All adults | “all adults” | 灰色实心圆 |
| E-SCREEN / Screening group | Not-yet-diagnosed adults | Not-yet-diagnosed | “adults not yet diagnosed” | 蓝色空心方块 |
| Trap 1 / 2 / 3 | RQ2a · Leakage / RQ1 · Labels / RQ2b · Preparation | 同左 | “the leakage question” 等 | 不用图标 |
| Leak gate | Data leakage check | — | — | — |
| availability rule / P03 | Post-diagnosis items excluded（treatment, diagnosis history, prior glucose testing） | post-diagnosis exclusion | “drop items that exist only after a diagnosis” | 墨色划线 |
| P01–P14、B1–B6、arm | 6 个描述性分组：File and code repair · Post-diagnosis exclusion · Redundancy · Missingness and top-codes · Skewness, splines, scaling · Class and survey weights | — | “fourteen switchable steps” | 青色 |
| P14（WHtR） | 24 px 脚注 “waist-to-height ratio: tested separately” | — | — | — |
| S-B6a | Systematic without class weights | — | “removing only the class weights” | 青色虚线 |
| care traces | Prior-care items (told high blood pressure / high cholesterol) | prior-care items | “items that mark earlier contact with a doctor” | — |
| L_comb | Label: self-report **or** HbA1c ≥ 6.5 % | the label | “the either-or label” | — |
| SESOI | equivalence margin ±0.01 (pre-registered) | margin | “our smallest effect of interest, fixed in advance” | 中性灰带 |
| MDD | minimum detectable difference 0.011（24 px 脚注） | — | — | — |
| prereg / locked (SHA-256) | Pre-registered hypotheses (locked by hash) | — | “locked before …” | — |
| DUA | Data use agreement | — | “data use agreement” | — |
| hold-out | Internal hold-out (scored once) | — | “an internal hold-out” | — |
| post-audit | 不上屏、不进旁白 | — | — | — |
| 成员代号 | 真名（第 3 节） | — | 真名 | 不用字母，不用徽章 |

**代号对照的去处：** YouTube 说明里放一行 “Naive = M0, Minimal = M1, Systematic = S; all adults = E-ALL; not-yet-diagnosed adults = E-SCREEN”，并附章节时间表。

---

## 6 视觉系统

### 6.1 原则

1. **一页一主张**：先写一句 “viewer can point at ___”；无关数据不上屏，细节留给 notebook。
2. **亮一个、暗其余**：焦点 100 %，其余 25 %，不用模糊；由旁白触发。
3. **渐进构建**：3–6 步，每步对应一个旁白短语；末帧自足可读，兼作缩略帧。
4. **数字随口播出现**：不早于念出它的那个词。
5. **画出不确定性**：效应量都带晶须，并画在 ±0.01 margin 带旁。
6. **对照公平**：同轴、同基线，柱从 0 起；AUC 轴从 0.5 起时标 “axis starts at 0.5”。
7. **按比例作图**：几何与数字都由脚本从 JSON 算出，不手摆、不手敲。
8. **文字极少**：主标题 + 副标题 + ≤ 3 个标注（各 ≤ 5 词）；旁白不逐字读屏。
9. **一个视觉动词**：每场景在 reveal、compare、split、shrink 中只选一个。

### 6.2 颜色角色

结构、语义、反馈三类分开，每种颜色只有一个含义。

| 角色 | 令牌 | 色值（白底对比度） | 唯一含义 | 非颜色编码 | 首次出现 |
|---|---|---|---|---|---|
| 结构 | `--structure` 靛蓝 | #3B2F8F（10.6:1） | **当前位置**：只用于进度条当前段的填充线；从不进入图形 | 位置 + 细线 | 02 |
| 语义 | `--leak` 红 | #B42318（6.6:1）；浅底 #FBE7E5 | **受损或泄漏的数据**：Naive、被误删的单元格、泄漏项 | 45° 斜纹 + 警示三角 | 08 |
| 语义 | `--systematic` 青 | #0D7A63（5.3:1）；浅底 #E2F2EE | **只表示 Systematic preparation** 及组成它的步骤 | 实心填充 | 12 |
| 语义 | `--screen` 蓝 | #1D64B0（6.0:1）；浅底 #E3EEF8 | **Not-yet-diagnosed adults**，包括 152 人 | 空心方块 | 16 |
| 语义 | `--reference` 灰 | #5A6672（5.9:1） | **对照基线**：Minimal 与 All adults | 实心圆 | 03 |
| 反馈 | 无色相，用 `--ink` | #15202B（16.5:1） | supported = 实心 ✓；inconclusive = 虚线框 + “?”；refuted = ✗ | 形状本身 | 04 |
| 中性 | `--ink` / `--line` | #15202B / #DCE1E6 | 正文、轴、标题、署名、焦点描边、有意移除的划线、margin 带的虚线边、字幕 | — | — |

- **没有第四种暖色语义色。** 不确定的结论用反馈形状；margin 带是中性浅灰加虚线边。
- **结构色与语义蓝拉开。** 靛蓝色相约 248°，语义蓝约 211°；结构色只在进度条上，两者不会出现在同一角色里。
- **同一张图里，颜色只编码一个变量。** 比较方案时颜色按方案（naive 红 / minimal 灰 / systematic 青），人群用形状（圆 = All adults，方 = Not-yet-diagnosed）；比较人群时，灰圆对蓝方。notebook 原图的 E-ALL 蓝、E-SCREEN 橙不沿用。
- **不属于任何语义的对象用墨色**：保险组（06）、漏斗上层（03）、已确诊者（19、22）、离群值（10）。
- **讲者不用颜色编码**：名签、角色卡一律墨色。
- **面积有主次。** 饱和色只用于线、点、数字、小色块和描边；大面积用同色相极浅底加同色描边。语义色只出现在白色纸面面板上。

**字体**（本地打包或 Google Fonts，离线有备用栈）：标题 Source Serif 4（主标题 64 px，章节卡 80 px，片头 88 px，片尾 120 px）；正文 IBM Plex Sans（副标题与标注 34 px，下限 28 px），字幕 IBM Plex Sans 500（34 px）；数字 IBM Plex Mono tabular-nums（主数字 120–168 px，次级 48–64 px，区间 36 px）。只有底栏的图例行与 notebook 指引、24 px 脚注可用 24 px。

### 6.3 层次与装饰

**纵深靠分层，不靠增加颜色。**

| 层 | 做法 | 数值 |
|---|---|---|
| 1 舞台 | 近白、略偏冷的底色 | #F6F7F9 |
| 2 纸面面板 | 承载图形的白色面板 | #FFFFFF；1 px 边 #E3E7EC；圆角 8 px；阴影 0 2px 16px rgba(21,32,43,0.06) |
| 3 内容 | 图形、数字、标注 | 语义色只出现在这一层 |
| 4 焦点 | 描边或使其余变暗 | 2 px 墨色描边，偏移 4 px；其余降到 25 % |

**唯一的装饰母题：问卷 / 编码表网格。** 极淡的直线网格（1 px 墨色，行高 24 px，不透明度 ≤ 4 %），只出现在画面四边的外边距内，向内渐隐到 0；不压在面板、文字、数字、字幕或小窗下面；完全静止。信息密集的场景（03、11、12、21）去掉网格。片头卡与片尾卡四周用同一母题。没有方格纸纹、成员色、色块转场或深色背景。

### 6.4 动效语汇

只用下面 12 个动作。强调在对象原位完成，不用飞入或弹跳。缓动：入场 `cubic-bezier(.2,0,0,1)`；形变、换值和推近 `cubic-bezier(.4,0,.2,1)`；数据驱动的连续量用线性。

| # | 动作 | 作用 | 时长与细节 | 场景 |
|---|---|---|---|---|
| M1 | 轴绘入 | 交代对象 | 0.6 s；刻度错开 30 ms，刻度标签在轴线画完后 0.3 s 淡入 | 01、03、06、10、17、20、22、23 |
| M2 | 柱从基线生长 | 状态出现 | 0.7 s；柱间错开 120 ms；数值标签随旁白出现 | 03、08、11、17、25 |
| M3 | 聚焦：描边 + 暗其余 | 标示焦点 | 0.4 s；2 px 墨色描边（偏移 4 px），其余降到 25 % | 全片 |
| M4 | 晶须 + margin 带 | 不确定性 | 点 0.3 s → 晶须 0.5 s → 带 0.6 s；越带边的端点脉冲一次。**只在 20 以动画呈现**；其他区间静态出现 | 20 |
| M5 | 漏斗收窄 | 状态转变 | 每级 0.5 s，级间停 0.4 s；掉出部分为墨色幽灵条，淡出到 20 % | 03、09 |
| M6 | 集合分裂或形变 | 状态转变 | 0.9 s；圆面积 ∝ n | 02（路线收缩成进度条）、11、15、26（路线回中） |
| M7 | 划线 | 标示删除 | 0.25 s，标签 0.3 s；**红线 = 被误删的有效值，墨线 = 有意移除的项**；每场景 ≤ 3 次 | 08、13（红）；17（墨） |
| M8 | 原位换值 | 状态转变 | 0.8 s；柱长缓动、数字线性倒数、填充交叉淡变同时完成，位置不动 | 06、17 |
| M9 | 推近 | 标示焦点 | 推 0.9 s，停 ≥ 2 s，拉回 0.6 s；**缩放 ≤ 1.25，全片只用 2 次**；推近后的包围盒不得进入避让区或字幕区 | 08、16 |
| M10 | 计数 | 连续量 | 0.8 s，线性起、末尾减速 | 01、04、15、19 |
| M11 | 标注箭头 | 标示焦点 | 箭头 0.4 s，标签 0.3 s；每次 1 个箭头 | 10、14、18 |
| M12 | 溶解 / 卡片 | 过渡 | 溶解 0.4 s；章节卡与段首页静默 1.2 s | 段首页 08、14、20；章节卡 11、17、22；溶解 01、02、24、26 |

**克制规则。**
- 每个运动都必须对应上表的一个作用，找不到作用就保持静止。
- 同一时刻只动一个物体；两个动作之间停 ≥ 1.5 s，供观众读数。
- 除 08、16 的两次推近外，焦点一律用 M3，不用缩放。
- 禁止：飞入、弹跳、旋转、视差、粒子、闪烁、持续的背景动画、打字机效果、3D 翻转、印章砸下。
- 动效总时长不超过场景时长的 40 %；场景切走前，末帧必须能独立读懂。
- 小窗、名签从不加动画；字幕只做 0.1 s 淡入淡出。

### 6.5 可读性与无障碍

| 项 | 规则 |
|---|---|
| 字号 | 内容文字 ≥ 28 px；主数字 ≥ 96 px；字幕 34 px；只有底栏和脚注可用 24 px |
| 对比度 | 正文 ≥ 4.5:1，大字 ≥ 3:1；ink 16.5、structure 10.6、red 6.6、blue 6.0、grey 5.9、teal 5.3（白纸面板上） |
| 不只靠颜色 | 红 = 斜纹 + 三角；青 = 实心填充 + 文字标签；蓝 = 空心方块；灰 = 实心圆；结构色 = 位置与细线；反馈 = ✓ / 虚线框 + “?” / ✗ |
| 色觉差异 | 红永远带斜纹，青永远不带；结构靛蓝不进图形 |
| 字幕 | 烧录开放字幕 + YouTube `.srt`（第 8 节） |
| 动效敏感 | 不闪烁；每个动画 ≤ 1 s；推近只有 2 次，缩放 ≤ 1.25 |
| 音频 | 人声 −16 LUFS；不加背景音乐，若加则 ≤ −30 LUFS 且在人声时压低 |

### 6.6 整体自检

每个场景渲染出末帧后，以及每段成片看完一遍后回答；有一个答“否”就回到 6.2–6.4 修改。

1. 每种颜色的含义能否用一句话说清？靛蓝 = 当前位置；红 = 受损或泄漏的数据；青 = Systematic；蓝 = Not-yet-diagnosed adults；灰 = 对照基线；反馈只用墨色形状。
2. 饱和色是否少而集中，没有大色块？
3. 去掉网格母题与阴影后，末帧是否依然完整、清楚？
4. 整体看起来像一次数据审计、一份项目汇报，而不是营销海报？
5. 字幕是否从不压到图形、小窗、名签或图例行？

---

## 7 场景总表

### 7.1 时间轴

列说明：**讲者**用名字记号；**mm:ss** 为场景起止（由 `timeline.json` 的时长求和得到）；**部分**为进度条当前段；**关键数字**为上屏的主要数字（口述 ≤ 3）。文件均在 `video/scenes/`，扩展名 `.html`。

| 场景 | 文件 | 讲者 | mm:ss | 部分 | 主标题 | 副标题 | 页面类型 | 关键数字 |
|---|---|---|---|---|---|---|---|---|
| 01 | `s01_hook_team` | `<Name:0>` | 0:00–0:29 | Problem & data | a Who gets labelled diabetic?<br>b How good is AUC 0.961?<br>c Team and roles | a Basic models as instruments on NHANES 2021–2023<br>b One logistic regression on all available columns, all adults<br>c Four members, their roles, and the sections each presents | 片头卡 → 证据页 → 团队页 | 0.961（墨色指针，轴 0.5–1.0） |
| 02 | `s02_agenda` | `<Name:0>` | 0:29–0:55 | Problem & data | Overview and agenda | Question, data, design, research questions and the sections of this talk | 议程页 | 5,730；3×2 设计矩阵；RQ1 / RQ2a / RQ2b |
| 03 | `s03_cohort_funnel` | `<Name:0>` | 0:55–1:14 | Problem & data | Cohort and label definition | NHANES 2021–23 (CDC): from participants to the analysis cohort | 证据页 | 11,933 → 5,730；HbA1c ≥ 6.5 %；14.0 % |
| 04 | `s04_dua_minimisation` | `<Name:0>` | 1:14–1:32 | Problem & data | Data governance | Data use agreement, column minimisation, hash-verified files and locked hypotheses | 证据页 | 78 of 175 columns |
| 05 | `s05_nchs_replication` | `<Name:0>` | 1:32–1:44 | Problem & data | Replication of official estimates | Our weighted prevalence beside NCHS Data Brief 516 | 证据页 | 15.79 % vs 15.8 %；27 estimates；脚注 max gap 0.044 pp |
| 06 | `s06_age_confounding` | `<Name:0>` | 1:44–2:03 | Problem & data | Confounding check: insurance gap | Diabetes prevalence, insured vs uninsured, crude and age-standardised | 证据页；署名 Analysis by `<Name:2>` | +5.3 pp → +0.7 pp；脚注区间 [1.8, 8.8]、[−2.6, 3.9] |
| 07 | `s07_reflection_hypotheses` | `<Name:0>` | 2:03–2:16 | Problem & data | Most unexpected finding | `<Name:0>` on the pre-registered hypotheses and their verdicts | 反思页 | 3 of 6 supported（3 ✓、3 虚线框 ?） |
| 08 | `s08_missing_codes` | `<Name:1>` | 2:16–2:44 | Data quality | a Data quality<br>b Missing-value codes | a Profiling, missing-value codes and outliers<br>b One global recode of NHANES codes, applied to every column | 段首页 → 证据页 | 57 vs 1,496；被划掉的 7.0 |
| 09 | `s09_erased_positives` | `<Name:1>` | 2:44–3:02 | Data quality | Effect on diabetes labels | HbA1c-positive cases hit by the global recode, and label flips | 证据页；“Non-obvious finding” 标签 | 29 of 721；6 flipped |
| 10 | `s10_outliers_kept` | `<Name:1>` | 3:02–3:19 | Data quality | Outlier handling | HbA1c values beyond the 1.5 × IQR fences, by diabetes status | 证据页 | 542 flagged；519 high；upper fence 6.8 % |
| 11 | `s11_redundancy_skew` | `<Name:1>` | 3:19–3:44 | EDA & preparation | Redundancy and skewness | VIF for weight and BMI; skewness of fasting triglycerides | 章节卡 → 证据页；署名 EDA by `<Name:2>` | VIF 95.7 / 97.6（参考线 10）；skewness 6.62 |
| 12 | `s12_preparation_design` | `<Name:1>` | 3:44–4:17 | EDA & preparation | Preparation design | Fourteen evidence-based steps combined into naive, minimal and systematic pipelines | 证据页 | 14 steps，6 个分组；“notebook: M0 · M1 · S” |
| 13 | `s13_reflection_recode` | `<Name:1>` | 4:17–4:30 | EDA & preparation | Most unexpected finding | `<Name:1>` on one routine recode line | 反思页 | 29 erased |
| 14 | `s14_simpson_dag` | `<Name:2>` | 4:30–4:53 | Labels & bias | a Labels & bias<br>b Simpson's paradox scan | a Analytical fallacies, label agreement and undiagnosed diabetes<br>b 224 subgroup comparisons checked for sign reversal; a causal DAG | 段首页 → 证据页 | 6 of 224 |
| 15 | `s15_label_agreement` | `<Name:2>` | 4:53–5:20 | Labels & bias | Label agreement: self-report vs HbA1c | Cohen's κ, and self-reported diabetics below the HbA1c threshold | 证据页 | κ 0.70；250 of 819；165 of 250 |
| 16 | `s16_undiagnosed` | `<Name:2>` | 5:20–5:49 | Labels & bias | Undiagnosed diabetes | High HbA1c without diagnosis: insurance gap, and a second evaluation population | 证据页 | 152；+23.2 pp [6.2, 40.1]；脚注 n = 49 |
| 17 | `s17_leak_gate` | `<Name:2>` | 5:49–6:16 | Experiments | Data leakage check | Naive vs minimal preparation: same model, post-diagnosis items excluded | 章节卡 → 证据页；署名 Experiment by `<Name:3>` | 0.961 → 0.828；−0.131 [−0.148, −0.114] paired |
| 18 | `s18_tree_and_50` | `<Name:2>` | 6:16–6:38 | Experiments | What the naive model learns | A depth-3 decision tree, and median imputation of age at diagnosis | 证据页；署名 Experiment by `<Name:3>` | 86 % never asked；imputed 50 |
| 19 | `s19_reflection_detection` | `<Name:2>` | 6:38–6:51 | Experiments | Most unexpected finding | `<Name:2>` on detection at one cut-off, by diagnosis status | 反思页 | 70 vs 52 per 100；specificity 0.80 |
| 20 | `s20_prep_band` | `<Name:3>` | 6:51–7:19 | Experiments | a Experiments, results and reflection<br>b Minimal vs systematic preparation | a Minimal vs systematic preparation, then results, robustness and reflection<br>b Paired AUC difference and its CI, against a pre-registered equivalence margin | 段首页 → 证据页；署名 Preparation steps by `<Name:1>` | +0.008 [0.000, 0.016]；±0.01；脚注 MDD 0.011 |
| 21 | `s21_brier` | `<Name:3>` | 7:19–7:42 | Experiments | Calibration and Brier score | Systematic vs minimal preparation, with and without class weights | 证据页；署名 Class-weight step by `<Name:1>` | Brier +0.074；41 % vs 17 %；AUC +0.007 |
| 22 | `s22_recognition` | `<Name:3>` | 7:42–7:59 | Results & robustness | AUC by evaluation population | Systematic preparation on all adults and on not-yet-diagnosed adults | 章节卡 → 证据页；署名 Population defined by `<Name:2>` | 0.836 vs 0.781；84 % already diagnosed |
| 23 | `s23_care_flip` | `<Name:3>` | 7:59–8:23 | Results & robustness | Ablation: prior-care items | AUC change after removing two 'told by a doctor' items, per population | 证据页 | −0.016；+0.019 [0.004, 0.034] |
| 24 | `s24_robustness_answers` | `<Name:3>` | 8:23–8:48 | Results & robustness | Robustness and answers | Internal hold-out check, then answers to the three research questions | 证据页 → 议程页（回答版）；署名 Robustness checks led by `<Name:1>` | 1,146 adults；RQ1 / RQ2a ✓ / RQ2b ? |
| 25 | `s25_reflection_leak_vs_prep` | `<Name:3>` | 8:48–8:55 | Reflection | Most unexpected finding | `<Name:3>` on AUC change from leakage vs from preparation | 反思页 | 0.131 vs 0.008 |
| 26 | `s26_close` | `<Name:3>` | 8:55–9:26 | Reflection | a Contributions and reflection<br>b Limits and use of AI<br>c Conclusion<br>d Who gets labelled diabetic? | a Who led which part, and how the parts connect<br>b What this study cannot show, and how generative AI was used<br>c The one message we take from this audit<br>d Basic models as instruments on NHANES 2021–2023 | 收尾页 → 片尾卡 | 152 positives among not-yet-diagnosed adults |

### 7.2 场景要点

| 场景 | 画面要点（数据文件） |
|---|---|
| 01 | 时间段见 5.3 节；AUC 轴与 0.961 指针用墨色（红色留到 17）（`leak_gate.json`） |
| 02 | 见 7.4 节（无数据文件；5,730 来自 `funnel.json`） |
| 03 | 墨色描边顶条 11,933 → 逐级收窄，中间三级只写文字标签 → 末条灰色实心 “All adults” 5,730（灰色图例时刻）→ “Positive = self-report **or** HbA1c ≥ 6.5 %” → 14.0 % weighted（`funnel.json`） |
| 04 | DUA 清单项加实心 ✓；175 个小方块中 97 个暗到 25 %，计数 175 → 78；“hash-verified” / “locked before any results”（`minimisation.json`） |
| 05 | 只留 Total 行 15.79 % vs 15.8 %；“27 estimates”；“max gap 0.044 pp” 为脚注；表宽 ≤ 1272（`db516.json`） |
| 06 | 墨色柱 +5.3 pp → M8 原位换成 +0.7 pp；“interval includes 0”，区间值入 24 px 脚注；小 DAG Age → Insurance / Diabetes；只用墨色（`age_std.json`） |
| 07 | 6 个方块：3 个实心 ✓、3 个虚线框 ?；正文一行与交接行（`hypotheses.json`） |
| 08 | 段首页 → 示例小表（标 “illustrative”）与规则 “Rule: 7, 9, 77, 99 → missing, every column” → 57（墨色实心柱）vs 1,496（红斜纹柱）同刻度同左端 → M7 红线划掉 3 个有效值 → M9 推近 7.0（红色图例时刻）（`blanket_recode.json`） |
| 09 | HbA1c 条带图与 6.5 % 阈值线；721 横条中 29 个掉出（M5），其中 6 个保持红斜纹 “flipped to negative”；墨色标签 “Non-obvious finding”（`blanket_recode.json`） |
| 10 | 直方图与 1.5 × IQR 围栏；标注 “upper fence 6.8 % > 6.5 % threshold”；Flag → Review → Keep 三格在主区中下部、字幕区以上（`iqr_fence.json`、`hist_geometry.json`） |
| 11 | 章节卡 → VIF 柱（参考线 10）与甘油三酯直方图左右排在主区；变换后只写小字 “≈ 0 after”（`vif_skew.json`、`hist_geometry.json`） |
| 12 | 6 个描述性分组 → 三条泳道 → “same L2 logistic regression · same folds”；“no step reads the label”；泳道标签下 24 px “notebook: M0 · M1 · S”；WHtR 脚注（青色图例时刻）（`arms.json`） |
| 13 | “7.0 · diabetic” 红线划掉；正文一行与交接行（`blanket_recode.json`） |
| 14 | 段首页 → 224 格细条，6 格描边 → DAG Race → BMI → Diabetes，标 “mediator”、“exploratory”（`simpson.json`、`hist_geometry.json`） |
| 15 | κ 0.70 → 两个墨色描边圆（面积 ∝ n）→ 250 加描边 → “165 of 250 on insulin or pills” 小号标签；Venn 与图例分三栏放主区（`label_split.json`） |
| 16 | 152 蓝色空心方块并推近（蓝色图例时刻）→ +23.2 pp 与静态晶须 6.2–40.1，“association · exploratory”，脚注 “uninsured n = 49” → 两条人群轨道只写文字（`label_split.json`、`undiagnosed.json`） |
| 17 | 章节卡 → “Naive” 0.961 红斜纹柱 → 三类泄漏项被墨线划掉 → M8 换成 0.828（灰实心 “Minimal”）→ 静态差值区间 “paired” → “✓ correct deterioration”；不显示 −0.072（`leak_gate.json`） |
| 18 | 树放在主区右部（x 560–1272）；根节点是治疗项（红斜纹）；“no” 分支上的 age 节点；86 % 被填成 50 的红斜纹柱；叶子淡到 25 %（`tree.json`） |
| 19 | 左块已确诊 70 / 100（墨色圆点），右块未确诊 52 / 100（蓝色空心方块），差额 18 个位置加描边；“one shared cut-off · specificity 0.80 · rates per 100”（`tpr_100.json`） |
| 20 | 段首页 → 轴 ±0.04 → 中性灰带 ±0.01 → 青色点 +0.008 → 晶须越带边，端点脉冲一次（全片唯一）→ 虚线框 + “?”；脚注 MDD 0.011（`prep_band.json`） |
| 21 | Brier +0.074 横条与 ✗；“mean predicted risk 41 % vs observed 17 %”；无类别权重时 AUC +0.007（小号）；不显示 +0.076（`brier.json`） |
| 22 | 章节卡 → 哑铃图 0.836（灰圆）/ 0.781（蓝方）→ 堆叠条 84 % already diagnosed；图内标注 “spectrum bias”；不显示 +0.055（`recognition.json`） |
| 23 | 同一根差值轴 → 灰圆 −0.016 → 停顿 → 蓝方 +0.019 [0.004, 0.034]（静态）→ “? inconclusive · lower end inside ±0.01”；+0.019 及标签在副区或 x ≤ 1272（`care_flip.json`） |
| 24 | 见 7.4 节（`holdout.json`、`leak_gate.json`、`prep_band.json`、`label_split.json`、`brier.json`） |
| 25 | 同轴两柱：0.131（红斜纹）vs 0.008（青）；正文一行（`leak_gate.json`、`prep_band.json`） |
| 26 | 见 7.4 节（`funnel.json`、`recognition.json`） |

### 7.3 节奏与时长（裁定 5）

**计算方法。** 场景语速 = 旁白词数 ÷（场景时长 − 静默卡时长）。静默卡：01 的片头卡 1.5 s；08、11、14、17、20、22 的段首页或章节卡 1.2 s；26 的片尾卡 1.5 s。停顿算在讲话时间里。目标 125–140 wpm。

**调整规则。**
- 旧时长下语速在 125–140 之间的场景不动。
- 低于 125 的场景缩短时长，到 125–134 之间；不加填充句。最慢的是 21（118 wpm，正在约 118 的下限上），其余 14 个在 120–124 之间，也一并收紧到目标内。
- 场景 25 只有 14 个词，7 s 为 120 wpm，6 s 为 140 wpm 且净语速达 168 wpm。保留 7 s：反思页需要读完正文一行，且 120 仍高于 118 的下限。
- 停顿只放在关键数字或揭示之后，每次 0.8–1.5 s，写在旁白里（`{pause 1.0}`）；除段首页、章节卡和片头片尾卡外，不留超过约 1.5 s 的空白。
- 扣除停顿后的净语速为 130–145 wpm。讲者实际语速不同时，以录像为准重新定时（8.3 节），不改字。

| 场景 | 词数 | 旧时长 | 旧语速 | 新时长 | 新语速 | 停顿（s） | 变化 |
|---|---|---|---|---|---|---|---|
| 01 | 59 | 30 | 124 | 29 | 129 | 1.0 | −1 |
| 02 | 56 | 28 | 120 | 26 | 129 | 0.8 | −2 |
| 03 | 41 | 20 | 123 | 19 | 129 | 1.0 | −1 |
| 04 | 38 | 18 | 127 | 18 | 127 | 0.8 | — |
| 05 | 26 | 13 | 120 | 12 | 130 | 1.0 | −1 |
| 06 | 40 | 20 | 120 | 19 | 126 | 1.2 | −1 |
| 07 | 28 | 13 | 129 | 13 | 129 | 1.0 | — |
| 08 | 56 | 28 | 125 | 28 | 125 | 1.2 | — |
| 09 | 39 | 19 | 123 | 18 | 130 | 1.0 | −1 |
| 10 | 38 | 17 | 134 | 17 | 134 | 0.8 | — |
| 11 | 50 | 25 | 126 | 25 | 126 | 0.8 + 0.8 | — |
| 12 | 70 | 33 | 127 | 33 | 127 | 0.8 + 0.8 | — |
| 13 | 28 | 13 | 129 | 13 | 129 | 1.0 | — |
| 14 | 47 | 24 | 124 | 23 | 129 | 1.0 | −1 |
| 15 | 57 | 28 | 122 | 27 | 127 | 1.0 + 0.8 | −1 |
| 16 | 62 | 30 | 124 | 29 | 128 | 1.0 + 1.0 | −1 |
| 17 | 55 | 28 | 123 | 27 | 128 | 1.5 | −1 |
| 18 | 46 | 23 | 120 | 22 | 125 | 1.0 | −1 |
| 19 | 29 | 14 | 124 | 13 | 134 | 1.0 | −1 |
| 20 | 57 | 29 | 123 | 28 | 128 | 1.2 | −1 |
| 21 | 49 | 25 | 118 | 23 | 128 | 1.0 | −2 |
| 22 | 35 | 18 | 125 | 17 | 133 | 1.2 | −1 |
| 23 | 50 | 24 | 125 | 24 | 125 | 1.0 | — |
| 24 | 54 | 25 | 130 | 25 | 130 | 0.8 × 3 | — |
| 25 | 14 | 7 | 120 | 7 | 120 | 1.0 | — |
| 26 | 65 | 31 | 132 | 31 | 132 | 1.0 | — |
| 合计 | 1,189 | 583 | 123 | **566** | **128** | — | 15 个场景缩短，共 −17 s |

“旧语速”按同一方法重算（改版方案把片头卡和片尾卡算进了讲话时间，所以 01、26 的数字与之不同）。

**各成员时间。**

| 讲者 | 改版方案 | 本方案 | 变化 | 场景 | 词数 | 平均语速 |
|---|---|---|---|---|---|---|
| `<Name:0>` | 2:22 | **2:16**（0:00–2:16） | −6 s | 01–07 | 288 | 128 |
| `<Name:1>` | 2:15 | **2:14**（2:16–4:30） | −1 s | 08–13 | 281 | 128 |
| `<Name:2>` | 2:27 | **2:21**（4:30–6:51） | −6 s | 14–19 | 296 | 128 |
| `<Name:3>` | 2:39 | **2:35**（6:51–9:26，≤ 3:00） | −4 s | 20–26 | 324 | 129 |
| 合计 | 9:43 | **9:26** | −17 s | 26 | 1,189 | 128 |

全片比裁定 5 预估的 9:40–10:10 略短，因为预估按约 122 wpm 计算；按 125–140 wpm 的目标，9:26 就是结果，不为凑时长加内容。

### 7.4 分阶段场景

**02 议程页（26 s）。** 全幅面板，左列栏目名（28 px，墨色 60 %），右列内容（34 px），全部在面板 x 48–1272、y ≤ 648。只用墨色。

| 行 | 面板坐标 y | 栏目 | 内容 |
|---|---|---|---|
| 1 | 24–72 | Question | Who gets labelled diabetic, and what do preparation decisions change? |
| 2 | 92–140 | Data | NHANES 2021–23 (CDC) · 5,730 adults with an HbA1c result |
| 3 | 160–290 | Design | “One L2 logistic regression · same folds”，下方 3×2 小矩阵：行 Naive / Minimal / Systematic，列 All adults / Not-yet-diagnosed adults（墨色细线格，不填色） |
| 4 | 310–460 | Research questions | RQ1 · Labels / RQ2a · Leakage / RQ2b · Preparation 三行（2.3 节）；下面一行小字 “RQ3 (label matrix) and RQ4 (BMI bias): in the notebook” |
| 5 | 490–560 | Sections | 七段路线：22 px 段名 + 细线；每段下方 22 px 讲者名（`<Name:0>` 在第 1 段下，`<Name:1>` 在 2–3，`<Name:2>` 在 4–5，`<Name:3>` 在 5–7） |

构建：
1. 0 s：第 1 行先只出现 “How accurate can a model get?”；念到 “who gets labelled” 时暗到 25 %，0.4 s 后用 M12 溶解成第 1 行的正式内容。
2. 念到 “The design” 时第 2、3 行依次出现；念到 “naive, minimal and systematic” 时矩阵三行依次描边，念到 “all adults … not yet diagnosed” 时两列依次描边。
3. 念到 “Our research questions” 时三行研究问题依次出现，顺序 RQ1 → RQ2a → RQ2b。
4. 约 22.5 s 起，第 5 行路线从左往右画出。
5. 24.8 s 起，路线用 M6（0.9 s）收缩到进度条位置，第 1 段变为当前段；其余四行暗到 25 %，留到场景切走。

**24 留出集与回答（25 s）。** 0–约 8 s：面板顶部一行小号 “Internal hold-out · 1,146 adults · scored once: leakage drop repeats; preparation gain inconclusive”。之后三行研究问题按 02 的字号、顺序回到面板，每行下方用 M12 溶解出答案（2.3 节），每个答案后停 0.8 s。署名 “Robustness checks led by `<Name:1>`”。

**26 收尾（31 s）。**
- 26a 约 0–8 s：四张角色卡，第 3 行写一项成果：`<Name:0>` “Governance · official-estimate replication”；`<Name:1>` “Missing-code audit · 14 preparation steps”；`<Name:2>` “Label agreement · undiagnosed adults · fairness”；`<Name:3>` “Leakage check · experiments and verdicts”。贡献链 “`<Name:2>` finds → `<Name:1>` implements → `<Name:3>` evaluates → `<Name:2>` interprets”；`<Name:0>` 的外框标 “integrates and checks every number”。念到谁，谁的卡加描边。
- 26b 约 8–19 s：局限标签 “One survey cycle”、“Low response”、“152 positives among not-yet-diagnosed adults”、“A data audit, not a screening tool”；GenAI 卡 “GenAI drafted code & text · reviewed by us · no LLM in the pipeline · every number recomputed”。
- 26c 约 19–29.5 s：收束句 “The score is not the finding; what it reveals about the data is.”，56 px serif，面板 x 48–1272、y 240–400，念到 “The score” 时用 M12 淡入一次。
- 26d 最后 1.5 s：片尾卡，片名 120 px 居中于 y 420–560，七段路线在 y 640–680，组号行 “Group [no.] · Thank you”，底部 24 px “Data: NHANES 2021–2023, CDC/NCHS public files”；全部在 x < 1392 或 y < 632；没有字幕。

### 7.5 旁白全文

规则：
- `<Name>` 是本场景讲者，`<Name:i>` 是成员 i（第 3 节）；录制时念真名，字幕显示真名或 “[Name]”。
- `{pause s}` 是读数停顿，只出现在旁白稿和 `timeline.json` 里，不进字幕。
- 每行标注：场景 · 讲者 · 起止 · 时长 · 词数 · 语速。

**01** · `<Name:0>` · 0:00–0:29 · 29 s（片头卡 1.5 s）· 59 词 · 129 wpm

> A basic logistic regression separates adults with and without diabetes at an AUC of 0.961. {pause 1.0} From survey data alone, that is suspiciously high. I'm `<Name>`; I led governance and integration. `<Name:1>` led data quality and preparation, `<Name:2>` exploration, labels and bias, and `<Name:3>` modelling and conclusions. We present in that order, and the 0.961 runs through the whole talk.

**02** · `<Name:0>` · 0:29–0:55 · 26 s · 56 词 · 129 wpm

> Our question: who gets labelled diabetic, and what do preparation decisions change? The design: one L2 logistic regression on three preparations of the same data, naive, minimal and systematic, scored on all adults and on adults not yet diagnosed. {pause 0.8} Our research questions: what does the label measure? Is the high AUC leakage? Does systematic preparation pay?

**03** · `<Name:0>` · 0:55–1:14 · 19 s · 41 词 · 129 wpm

> The data: NHANES 2021 to 2023, the CDC's national health survey. Our cohort is 5,730 non-pregnant adults with an HbA1c result. The label is positive for a self-reported diagnosis, or HbA1c of 6.5 percent or more. Survey-weighted, 14.0 percent are positive. {pause 1.0}

**04** · `<Name:0>` · 1:14–1:32 · 18 s · 38 词 · 127 wpm

> Governance came first. The NCHS data use agreement forbids re-identification and linkage, so we did neither. We kept 78 of 175 columns, verified every raw file by hash, and locked our hypotheses by hash before running any model. {pause 0.8}

**05** · `<Name:0>` · 1:32–1:44 · 12 s · 26 词 · 130 wpm

> To check our survey-weighting code, we re-ran NCHS Data Brief 516: total prevalence 15.79 percent against the published 15.8, and all 27 published estimates match closely. {pause 1.0}

**06** · `<Name:0>` · 1:44–2:03 · 19 s · 40 词 · 126 wpm

> Correct numbers can still mislead. In `<Name:2>`'s analysis, insured adults show 5.3 points more diabetes than the uninsured. That is confounding by age: the insured are much older. Age-standardised, the gap falls to 0.7 points, and its interval includes zero. {pause 1.2}

**07** · `<Name:0>` · 2:03–2:16 · 13 s · 28 词 · 129 wpm

> Most unexpected for me: of six hypotheses locked before we saw any related data, only three were supported. {pause 1.0} Now `<Name:1>` asks whether the data deserve the same trust.

**08** · `<Name:1>` · 2:16–2:44 · 28 s（段首页 1.2 s）· 56 词 · 125 wpm

> I'm `<Name>`; I led data quality and preparation. I profiled before cleaning. NHANES stores 'refused' and 'don't know' as numeric codes such as 7, 9, 77 and 99. The common shortcut sets those values to missing in every column. That catches 57 genuine codes, and destroys 1,496 valid measurements, including HbA1c values of exactly 7.0 percent. {pause 1.2}

**09** · `<Name:1>` · 2:44–3:02 · 18 s · 39 词 · 130 wpm

> Each 7.0 is above the 6.5 threshold: a diabetes case. The shortcut erased 29 of 721 HbA1c-based positives. {pause 1.0} Only six changed label; the rest had also self-reported, so the either-or label hid the damage. No summary statistic shows this.

**10** · `<Name:1>` · 3:02–3:19 · 17 s · 38 词 · 134 wpm

> Second, outliers. The 1.5 times IQR rule flags 542 HbA1c values. {pause 0.8} Its upper fence lies above the diagnostic threshold, so the 519 high values are diabetes by definition: the disease, not errors. We reviewed and kept them all.

**11** · `<Name:1>` · 3:19–3:44 · 25 s（章节卡 1.2 s）· 50 词 · 126 wpm

> `<Name:2>`'s exploration found redundancy and skew. Weight and BMI show severe multicollinearity: variance inflation factors of 95.7 and 97.6. {pause 0.8} Fasting triglycerides are strongly right-skewed: skewness 6.62. {pause 0.8} Both matter for a linear model, so the systematic preparation drops weight and applies a Yeo-Johnson transform, which brings the skewness close to zero.

**12** · `<Name:1>` · 3:44–4:17 · 33 s · 70 词 · 127 wpm

> Each finding became a switchable step, fourteen in all, each tied to its evidence, and none reads the label. {pause 0.8} From them we built three versions of the data. Naive keeps every column. Minimal adds one rule: drop items that exist only after a diagnosis, such as treatment. Systematic adds my other steps, from per-variable recoding to transforms and class weights. All three feed the same model on the same folds. {pause 0.8}

**13** · `<Name:1>` · 4:17–4:30 · 13 s · 28 词 · 129 wpm

> Most unexpected for me: one routine cleaning line erased 29 diabetic HbA1c results, and the label hid it. {pause 1.0} But cleaning cannot fix the label itself. `<Name:2>` shows why.

**14** · `<Name:2>` · 4:30–4:53 · 23 s（段首页 1.2 s）· 47 词 · 129 wpm

> I'm `<Name>`; I led exploration, labels and bias. First, a fallacy check: we scanned 224 subgroup comparisons for Simpson's paradox, and six reversed sign. {pause 1.0} A causal diagram suggests why: BMI lies between race and diabetes, so adjusting for it distorts the comparison. We report this as exploratory.

**15** · `<Name:2>` · 4:53–5:20 · 27 s · 57 词 · 127 wpm

> Research question one: the label. Our label combines two sources, and they agree substantially but far from perfectly: Cohen's kappa is 0.70. {pause 1.0} Of 819 self-reported diabetics, 250 test below 6.5 percent, and two thirds of those take insulin or pills. {pause 0.8} Treatment lowers the very marker we label by, so a blood-test-only label would call treated patients healthy.

**16** · `<Name:2>` · 5:20–5:49 · 29 s · 62 词 · 128 wpm

> The other direction: 152 adults have HbA1c of 6.5 or more but no diagnosis. {pause 1.0} Among adults with high HbA1c, the uninsured are 23.2 percentage points more often undiagnosed, interval 6.2 to 40.1, an association from a small subgroup. {pause 1.0} So the label also records access to care. That is why we also evaluate on adults not yet diagnosed: the people screening is for.

**17** · `<Name:2>` · 5:49–6:16 · 27 s（章节卡 1.2 s）· 55 词 · 128 wpm

> The leakage question, from `<Name:3>`'s experiments. Naive preparation scores an AUC of 0.961. Minimal preparation removes only the post-diagnosis items: treatment, diagnosis history and prior glucose testing. Same model, same folds: the AUC falls to 0.828, a paired drop of 0.131. {pause 1.5} A deterioration we wanted: the 0.961 was the label leaking back in, not skill.

**18** · `<Name:2>` · 6:16–6:38 · 22 s · 46 词 · 125 wpm

> `<Name:3>`'s shallow decision tree shows the mechanism. Its root is a treatment item; one branch then splits on age at diagnosis. But 86 percent were never asked that question, and median imputation filled every blank with 50. {pause 1.0} So 'age 50' became a code for 'never diagnosed'.

**19** · `<Name:2>` · 6:38–6:51 · 13 s · 29 词 · 134 wpm

> Most unexpected for me: at one shared threshold, the model flags 70 of every 100 diagnosed diabetics, but only 52 of 100 undiagnosed ones. {pause 1.0} `<Name:3>` takes the last question.

**20** · `<Name:3>` · 6:51–7:19 · 28 s（段首页 1.2 s）· 57 词 · 128 wpm

> I'm `<Name>`; I led modelling and conclusions. Last question: does systematic preparation pay? Same model, minimal against systematic: AUC rises by 0.008, interval 0.000 to 0.016. {pause 1.2} Our smallest effect of interest, fixed in advance, was 0.01. The interval covers both no gain and a worthwhile one, so the result is inconclusive: underpowered, not evidence of no effect.

**21** · `<Name:3>` · 7:19–7:42 · 23 s · 49 词 · 128 wpm

> One step did harm. From minimal to systematic, the Brier score worsens by 0.074. {pause 1.0} The cause is `<Name:1>`'s class weights: the systematic model predicts an average risk of 41 percent where the observed rate is 17. Removing only the class weights restores calibration and leaves AUC 0.007 above minimal.

**22** · `<Name:3>` · 7:42–7:59 · 17 s（章节卡 1.2 s）· 35 词 · 133 wpm

> Who does the score serve? On all adults, the systematic model scores 0.836; on adults not yet diagnosed, 0.781. {pause 1.2} 84 percent of positives were already diagnosed, so the all-adults AUC mostly measures recognition: spectrum bias.

**23** · `<Name:3>` · 7:59–8:23 · 24 s · 50 词 · 125 wpm

> Next, drop two items that mark earlier contact with a doctor. On all adults, AUC falls by 0.016. On adults not yet diagnosed, it rises by 0.019, interval 0.004 to 0.034: consistent with recognition and screening pulling apart. {pause 1.0} But the lower end lies inside our margin, so it is inconclusive.

**24** · `<Name:3>` · 8:23–8:48 · 25 s · 54 词 · 130 wpm

> An internal hold-out of 1,146 adults, scored once, repeats the leakage drop and the inconclusive preparation result. So, three answers. The label records care as well as disease. {pause 0.8} The 0.961 was leakage, not skill. {pause 0.8} Systematic preparation barely moved AUC; its value was valid data kept and an honest test on adults not yet diagnosed. {pause 0.8}

**25** · `<Name:3>` · 8:48–8:55 · 7 s · 14 词 · 120 wpm

> Most unexpected for me: leakage moved the score far more than careful preparation did. {pause 1.0}

**26** · `<Name:3>` · 8:55–9:26 · 31 s（片尾卡 1.5 s）· 65 词 · 132 wpm

> Four roles, one audit: `<Name:0>`'s governance, `<Name:1>`'s preparation, `<Name:2>`'s labels and bias, my models. Limits: one survey cycle, low response, and only 152 undiagnosed positives; this is a data audit, not a screening tool. Generative AI drafted much of our code and text; we reviewed it and recomputed every number. {pause 1.0} The score is not the finding; what it reveals about the data is. Thank you.

---

## 8 字幕（裁定 7）

### 8.1 样式与字幕区

| 项 | 规格 |
|---|---|
| 形式 | 烧录进画面的开放字幕；同一份文字另出 `.srt` 供 YouTube |
| 字幕区 | 舞台 x 96–1368，y 872–988（面板坐标 x 0–1272，y 648–764）：图区面板左下的一条，位于避让区左侧 |
| 对齐 | 在字幕区内水平居中、底端对齐；单行时贴底 |
| 字体 | IBM Plex Sans 500，34 px，行高约 42 px（ASS 文件写 Fontsize 44，因为 libass 按上伸加下伸、即 1.3 em 计字号）；墨色 #15202B，2 px 白色描边（白纸上看不出）；无阴影、无底板（对比度 16.5:1）；末行基线约在 y 974 |
| 行数与长度 | 最多 2 行，每行最多 42 个字符 |
| 显示时长 | 每条 1.0–6.0 s；相邻两条间隔不足 0.3 s 时前一条延到后一条开始，避免闪烁 |
| 阅读速度 | 目标 ≤ 17 字符/秒，只作警告：按比例估时，在 130–140 wpm 下信息密集的分句会到 18–22 字符/秒。`build_subs.mjs` 打印最差的几条，录像后用 `overrides.json` 修正 |
| 出入 | 0.1 s 淡入淡出；不做其他动画 |
| 不出字幕 | 片头卡、片尾卡、段首页与章节卡的静默 1.2 s、停顿期间（停顿不进字幕） |
| 不冲突 | 字幕区不放任何图形内容；小窗、名签、图例行、notebook 指引都在字幕区之外。kit 审计在任何内容进入字幕区时报错 |

### 8.2 断句规则

- 文字就是该场景的旁白，名字记号换成真名（未填时为 “[Name]”），去掉 `{pause}`。
- 优先在句末断条，其次在逗号、冒号、分号处；同一条的两行尽量等长，下行可略长。
- 不拆开：数字与单位（“6.5 percent”）、区间（“interval 0.000 to 0.016”）、人名、“HbA1c”、“Cohen's kappa”。
- 行首不放标点；不在冠词或介词后断行。
- 拼写与旁白稿完全一致；数字用阿拉伯数字，与屏幕一致。

### 8.3 生成与重新定时

1. **生成：** `node video/subtitles/build_subs.mjs` 读 `video/timeline/timeline.json` 与 `notebooks/final/team.json`，写出 `video/subtitles/full.srt`（YouTube）、`full.ass`、每段的 `block_<n>.srt` / `block_<n>.ass`，以及 `words.json`（逐词时钟，场景的构建 cue 也从这里取）。
2. **录像前（估计）：** 每个场景的讲话窗口是 `[silentLead + 0.3, (speechEnd 或 duration) − 0.5]`（`timeline.json` 的 `subtitles.leadIn` / `leadOut`）。窗口内按估计音节数把时间分给各词，标点处加短停顿，`{pause}` 处加读数停顿；断条在句末优先，其次在冒号、分号、逗号处。名字记号按 2 个音节计，所以填入真名不会移动 cue。
3. **录像后（重新定时）：** 听每段录像，在 `video/subtitles/overrides.json` 里按场景写入整体平移（`shift`）、讲话结束时刻（`speechEnd`）、额外停顿或逐条字幕的起止（`chunks`），重新运行 `build_subs.mjs`，再重渲染受影响的场景并重新合成该段。动画 cue 读同一个 `words.json`，所以字幕与动画一起移动。若某个场景实测时长变化，先改 `timeline.json` 的 `duration`，进度条与起止时间会跟着变。
4. **检查：** 抽查每段 3 处，字幕出现与开口相差 ≤ 0.3 s；没有一条超过 2 行 × 42 字符；`build_subs.mjs` 报出的超速字幕已修正；字幕区无冲突（审计全绿）。

### 8.4 烧录与 YouTube

- `compose_block.mjs` 用 libass 把 `block_<n>.ass` 烧进该段成片（样式即 8.1 节）。
- 上传时把 `video/subtitles/full.srt` 作为 English 字幕上传，避免 YouTube 自动字幕；画面已有开放字幕，YouTube 的 CC 默认保持关闭。
- 名字填好后必须重新生成字幕、重新合成，否则画面里会留下 “[Name]”。

---

## 9 制作管线

### 9.1 工具

HTML/SVG 场景 → Playwright 逐帧截图 → ffmpeg。场景复用项目的令牌和字体，画面是时间 t 的纯函数（逐帧确定、可重复），数字从 `video/data/*.json` 读取。渲染用 `playwright-core`（只装在 `video/render/`），驱动本机 Chrome，不下载浏览器；需要 PATH 上的 ffmpeg（带 libass）。OBS 只在回退方案里使用；matplotlib 静帧只作应急。

### 9.2 规格

| 项 | 值 |
|---|---|
| 画面 | 1920×1080，30 fps，SDR，BT.709 |
| 场景中间文件 | 无声 MP4，H.264 yuv420p，CRF 18，BT.709 标签 |
| 讲者录像 | 每段一条连续录像，1080p30，MP4；音频 48 kHz；放在 `video/takes/block_<n>.mp4` |
| 小窗 | 缩放并居中裁成 384×216，叠在 x 1416，y 748 |
| 成片 | H.264 High 约 12 Mbps；AAC 192 kbps；−16 LUFS，真峰值 ≤ −1 dBTP |
| 字幕 | 烧录（libass）+ `video/subtitles/full.srt` |

### 9.3 文件

| 路径 | 内容 |
|---|---|
| `video/kit/tokens.css`、`video/kit/kit.js` | kit v2：单一版式、进度条、标题与副标题、署名、名签、小窗细边、底栏、字幕区、审计（9.4 节） |
| `video/timeline/timeline.json` | 唯一的顺序、时长、讲者与旁白来源（9.5 节） |
| `video/scenes/sNN_*.html` | 26 个场景，文件名见 7.1 节；`_template.html` 是模板 |
| `video/data/*.json`、`video/data/SOURCES.md` | 场景数据与逐值出处，由 `build_data.py` 与 `build_geometry_s10_11_15.py` 生成 |
| `video/subtitles/` | `build_subs.mjs`、`overrides.json`、生成的 `.srt` / `.ass` / `words.json` |
| `video/render/` | `render.mjs`、`render_all.mjs`、`snap.mjs`、`serve.mjs`、`compose_block.mjs`、`compose_film.mjs` |
| `video/takes/` | 四段讲者录像（不进 git） |
| `video/out/` | 渲染与合成结果；git 只保留每个场景的 `_last.png` |
| `video/README.md` | 写场景的规则与 kit API |

### 9.4 kit v2

- **网格：** 只有一种版式（4.1 节）：`panel {96, 224, 1728, 764}`、`camera {1416, 748, 384, 216}`、`nametag {1416, 656, 384, 84}`、`keepOut {1392, 632, 432, 356}`、字幕区 `{96, 872, 1272, 116}`。删除右栏、徽章、陷阱条、lower-third、F / S / X / R 版式和 alpha 模式。
- **界面：** `buildChrome` 依次画进度条、主标题、副标题、署名、面板、小窗细边、名签、底栏；页面类型 `evidence | blockstart | reflection | agenda | closing | card`。
- **名字：** 从 `team.json` 读；占位渲染为 “[Name]”。
- **进度条：** 段起止由 `timeline.json` 求和得到，填充是全局时间的纯函数。
- **审计（每帧抽查，渲染后打印）：**
  - 文字小于 28 px（底栏与脚注除外）、文字重叠、超出面板；
  - 任何内容进入避让区或字幕区（推近按 1.25 倍包围盒计算）；
  - 主标题超过 1728 px、副标题与署名重叠；
  - 渲染文字含 “§”，或匹配内部代号 `M0|M1|E-ALL|E-SCREEN|P\d{2}|B[1-6]|Trap|S7_|S10_`（白名单只有 12 的 “notebook: M0 · M1 · S”）；
  - 渲染文字里出现单独的 A–D 人名；
  - 一帧里结构靛蓝出现超过一处。

### 9.5 `timeline.json`

`video/timeline/timeline.json` 是顺序、时长、讲者与旁白的唯一来源；本方案 7.1、7.3、7.5 节是它的内容来源。主副标题不在其中，写在场景文件里。

| 字段 | 内容 |
|---|---|
| `version`、`fps` | 版本号；30 |
| `sections[]` | `{n 1–7, label, scope}`（5.1 节） |
| `members[]` | `{index 0–3, roleKey governance / quality / labels / modelling, role, owns, presents}`（3.2 节；`presents` 是团队页卡片第 3 行）；名字不在这里，在 `team.json` |
| `blocks[]` | `{n 1–4, speaker, scenes[]}` |
| `scenes[]` | `{n, file, block, speaker（成员序号，从不用字母）, section, duration, silentLead, speechEnd?, narration}`；`narration` 用 `<Name>` / `<Name:i>` 记号和 `{pause s}`（放在最后一个词之后时，在场景末尾留出静默） |
| `subtitles` | `{leadIn, leadOut}` |

起止时间不存，由时长求和。录像后按实测回填 `duration`。署名行（例如 24 的 “Robustness checks led by `<Name:1>`”）不在 `timeline.json`，写在场景配置的 `credit` 字段。

### 9.6 步骤

1. **kit v2 与 `timeline.json`。** 网格、进度条、名签、字幕区、审计；时间轴按 7.3 节。
2. **场景。** 按 7.1、7.2 节逐个改写或新做，`?t=` 预览、`snap.mjs` 检查每个构建步骤，审计全绿。
   ```bash
   node video/render/serve.mjs                                   # 预览 http://127.0.0.1:8130/scenes/s17_leak_gate.html
   node video/render/render.mjs video/scenes/s17_leak_gate.html  # → video/out/s17_leak_gate.mp4 + _last.png
   node video/render/render_all.mjs --block 1 --jobs 3           # 一段或全部场景
   ```
3. **字幕。** `node video/subtitles/build_subs.mjs`（8.3 节）。
4. **按段合成。** 拼接本段场景（`timeline.json` 顺序）→ 整段叠一次讲者录像（384×216，x 1416，y 748）→ 烧录本段字幕。没有录像时用灰色占位块。
   ```bash
   node video/render/compose_block.mjs 1                                          # 占位小窗
   node video/render/compose_block.mjs 2 --take video/takes/block_2.mp4 --take-offset 3.4
   ```
   `--take-offset` 是录像里本段第 1 帧对应的秒数；也可写进 `video/subtitles/overrides.json` 的 `"takes": {"1": {"offset": 2.4}}`。录像放在 `video/takes/block_<n>.mp4`（git 忽略）。
5. **成片。** `compose_film.mjs` 把 `video/out/block_1.mp4`–`block_4.mp4` 拼接并做响度归一（loudnorm，−16 LUFS）；YouTube 字幕用 `video/subtitles/full.srt`。
   ```bash
   node video/render/compose_film.mjs    # → video/out/film.mp4
   ```
6. **录像后。** 标 cue 与字幕时刻（8.3 节）→ 回填时长 → 重渲染受影响的场景 → 重新合成该段 → 成片。

场景代码一律写成“步骤状态机”，同一份代码既支持逐帧渲染，也支持按 N / P 手动步进（回退方案用）。

### 9.7 场景改动分级

| 级 | 场景 | 工作内容 |
|---|---|---|
| 高 | 01、02、24、26 | 片头卡与团队页；议程页与路线收缩成进度条；回答页复用 02 的研究问题行；收尾四阶段与片尾路线回中 |
| 中 | 07、08、13、14、19、20、25 | 三个段首页与四个反思页 |
| 中 | 12、16、17、21、22 | 合并的准备设计；人群轨道改文字；删次级数字；41 % vs 17 %；章节卡 |
| 低 | 03、04、05、06、09、10、11、15、18、23 | 改标题与标签、收进主区、加脚注 |

所有场景都要让出字幕区（主区高度从 764 降到 648）。快速迁移：原图形缩放后左对齐放进主区，再逐个拉宽。

### 9.8 数据改动

- **屏幕名称：** `build_data.py` 的 `_meta.naming` 与 `label` 改为 5.4 节的名称（例如 “Naive (M0)” → “Naive”；“Screening group” → “Not-yet-diagnosed adults”；“Systematic (S) − Minimal (M1)” → “Systematic − Minimal”），场景代码不手改。
- **显示项（格式，不是新数字）：** `brier.json` 的 “41 %”“17 %”；`label_split.json` 的 “165 of 250”（旁白念 “two thirds”，66 %）；`iqr_fence.json` 注明高端 519、低端 23（取自 `hist_geometry.json`）。
- **不需要新算的数字。** 所有上屏数字都已在 `video/data/*.json` 中。

### 9.9 首个交付（裁定 9）

改完后先渲染第 1 段（场景 01–07，2:16）：全部场景拼接，灰色占位小窗，名签与字幕里的名字为 “[Name]”，字幕烧录。输出 `video/out/block_1.mp4` 交用户审阅。第 2–4 段在用户反馈后再做。

### 9.10 日程（截止 10/18）

| 日期 | 任务 |
|---|---|
| 10/14 | 本方案定稿；kit v2 与 `timeline.json`；第 1 段场景；`block_1.mp4` 交审 |
| 10/15 | 按反馈改；第 2–4 段场景；各人计时朗读；给讲师的邮件 |
| 10/16 | 录制四段连续录像；标 cue 与字幕时刻；合成粗剪 |
| 10/17 | 对照粗剪排练与修正；填真名与组号；定稿、上传、无痕窗口核验 |
| 10/18 | 缓冲，提交 |

### 9.11 制作风险

| 风险 | 对策 |
|---|---|
| 时间不够 | 先保高级场景与审计全绿；低级场景必要时只做快速迁移加改标签 |
| 录像后场景时长变化 | 进度条、起止、字幕都从 `timeline.json` 与 `overrides.json` 读，不写死 |
| 名字迟迟未定 | 一律渲染 “[Name]”；名字填好后重新生成字幕并重新合成（只需重跑脚本） |
| 小窗里人脸较小 | 胸像构图、浅色背景、同侧主光（10.5 节） |
| 字幕区挤压图形 | 主区仍有 1272×648；密集场景（12、17、21）优先检查 |
| 本机 ffmpeg 无 libass | 先用 `ffmpeg -filters` 确认 `subtitles` / `ass` 滤镜可用 |

---

## 10 讲解与录制

### 10.1 表达

- **语速：** 场景平均约 128 wpm（含停顿），净语速 130–145 wpm。超时就删句，不加快语速。
- **停顿：** 只在旁白稿标出的 `{pause}` 处停 0.8–1.5 s；其他地方不留长于约 1.5 s 的空白。
- **画幅与视线：** 胸像，头顶留一拳空间，眼睛在上三分线；看镜头，脚本放在镜头正下方。
- **状态：** 能量比日常说话高一档；重点词前停顿；句尾下沉。不做手势指向（画面是后期合成的）。
- **脚本用法：** 每人把自己的段落压成“一拍一句”的卡片按拍练习。数字、术语、署名句和措辞边界必须一字不差。
- **非母语表达：** 每句 ≤ 20 词；重读数字和否定词（not、no、barely、only）；说错时停 1 秒，从那一句开头重说，剪辑时只去掉错误部分（若讲师要求不剪辑，则整段重录）。
- **对齐：** 新元素出现后 0.5 s 再开口；数字的出现与念出相差 ≤ 0.5 s。

### 10.2 数字念法

念出的数字与屏幕完全一致（精度相同）；区间读 “interval … to …”；下降用动词（“falls by”）；百分点读 “percentage points”。

| 屏幕 | 念法 |
|---|---|
| 0.961 → 0.828 | “zero point nine six one … falls to zero point eight two eight” |
| −0.131 | “a paired drop of zero point one three one” |
| +0.008 [0.000, 0.016] | “rises by zero point zero zero eight, interval zero to zero point zero one six” + “inconclusive” |
| κ = 0.70 | “Cohen's kappa is zero point seven zero”；不说 “70 percent agree” |
| 1,496 | “one thousand four hundred and ninety-six” |
| +23.2 pp [6.2, 40.1] | “twenty-three point two percentage points … interval six point two to forty point one” + “an association” |
| 14.0 % | “fourteen point zero percent” |
| 15.79 vs 15.8 | “fifteen point seven nine … fifteen point eight” |
| 70 / 52 of 100 | “70 of every 100 … only 52 of 100” |

**发音表（四人统一）。** HbA1c “H-B-A-one-C”；NHANES “EN-haynz”；AUC “A-U-C”；κ “kappa”；Brier “BRY-er”；DAG “dag”；Yeo-Johnson “YO-johnson”；SHA-256 只在画面上出现，旁白说 “hash”。

### 10.3 措辞边界

证据等级取自 `governance/claims.csv`：E1 “confirms”，E2 “shows”，E3 “is consistent with”，E4 “suggests”。不用因果动词。

| 主张 | 可以说 | 不要说 |
|---|---|---|
| 泄漏检查（C01，E2） | “The AUC falls to 0.828, a paired drop of 0.131. The 0.961 was not skill.” | “The model is 96 % accurate.” “Leakage is gone for good.” |
| 统一重编码（C03–C04） | “Erased 29 of 721 HbA1c-based positives; only six changed label.” 只说 “values of exactly 7.0”（29 个中 28 个是 7.0、1 个是 9.0） | “Deleted 29 diabetic labels.” “All 29 were 7.0.” |
| 离群值 | “The upper fence lies above the threshold, so the 519 high values are diabetes by definition.” | 把 519 说成一个发现 |
| minimal vs systematic（C05，E3） | “Plus 0.008, interval 0.000 to 0.016: inconclusive, underpowered.” | “Preparation improves AUC.” “No difference.” “Equivalent.” |
| 类别权重（C06，E2） | “From minimal to systematic, the Brier score worsens by 0.074.” 0.074 只配 “from minimal to systematic” | 念 0.076；把 41 % 说成对美国成人的风险估计；把训练部分未加权的 17 % 与加权的 14.0 % 混用 |
| 识别 vs 筛查（C07，E2） | “The all-adults AUC mostly measures recognition.” | “Our model screens diabetes at AUC 0.781.” |
| prior-care 消融（C08，E3） | “Consistent with recognition and screening pulling apart … the lower end lies inside our margin, so it is inconclusive.” | “Care items hurt screening.” “The best screening model.” |
| 年龄混杂（C11，E2） | “Confounding by age … its interval includes zero.” | “Insurance has no effect.” “Insurance causes diabetes.” |
| Simpson / DAG（C13，E3） | “Suggests why … We report this as exploratory.” | “We explained Simpson's paradox.” |
| 治疗掩盖（C14，E1） | “250 test below 6.5 percent, and two thirds of those take insulin or pills.” | “All 250 are controlled by treatment.” “HbA1c is the truth.” |
| 未确诊不平等（C15，E3） | “An association from a small subgroup, interval 6.2 to 40.1.” | “Lacking insurance causes missed diagnoses.” |
| κ | “Cohen's kappa is 0.70.” | “70 percent agree.” |
| 复现（C23，E2） | “All 27 published estimates match closely.” | “Reproduced all 27.”（24 of 27 落在发布区间内）；“Our 14.0 percent matches NCHS.” |
| 留出集（C25，E3） | “An internal hold-out of 1,146 adults, scored once, repeats the leakage drop and the inconclusive preparation result.” | “Independent validation.” “Changed no locked verdict.” 提外部评审六项 |
| 预注册 | “Of six hypotheses locked before we saw any related data, only three were supported.” | “10 of 17 hypotheses confirmed.” |
| 公平性 | “At one shared threshold, 70 of every 100 diagnosed … only 52 of 100 undiagnosed.” | 把每 100 人的点阵说成实际人数 |
| 树 | “One branch then splits on age at diagnosis.” | 暗示分裂的先后或因果 |
| 署名 | “`<Name:2>`'s exploration found…”，“`<Name:3>`'s experiments” | 讲他人的工作却用 “I found…” |
| GenAI | “Generative AI drafted much of our code and text; we reviewed it and recomputed every number.” | “No AI was used.” “The AI found the results.” |

### 10.4 设备与文件

- **声音：** 耳机麦克风，嘴距约一拳，不用笔记本自带麦克风；峰值 −12 至 −6 dB；开录前录 10 s 房间静音供降噪；关窗、关空调和风扇。
- **画面：** 1080p30，摄像头与眼睛同高；窗户在前方，不背光；浅色中性背景，无个人信息，不用虚拟背景；笔记本接电源。
- **构图：** 四人同一构图：胸像，双眼在上三分线，同一侧主光。小窗只有 384×216，脸要占画面高度的约 45 %。
- **文件：** 本地录 MKV，录完转 MP4，命名 `block_<n>_take<k>.mp4`；选定的一条复制为 `video/takes/block_<n>.mp4`。每人至少两条完整可用的 take；原始素材保留到成绩公布。
- **分工：** `<Name:0>` 录第 1 段（01–07，2:16）；`<Name:1>` 录第 2 段（08–13，2:14）；`<Name:2>` 录第 3 段（14–19，2:21）；`<Name:3>` 录第 4 段（20–26，2:35）。

### 10.5 录制方式

**主方案：每人一次连续录完自己的段落，后期合成。** 对着提词器一口气录完，可以录多条完整 take，选最好的一条整体使用；动画与字幕按这条录像定时。成片只有 3 个切点，都在段落交接处。

**未决：“single continuous video” 的含义。** 可以理解为“提交一个完整的视频文件”，也可以理解为“一次不间断录制、不能剪辑”。发邮件问讲师（第 15 节第 1 项）。一人一段的结构让两种理解都容易满足。

**回退方案：一次连续录制。** 如果讲师要求不剪辑，或到 10/15 仍未回复：
- 用 OBS 做一次连续录制。四人依次讲自己的段落：正在讲的成员开摄像头和麦克风，其余关闭，画面里始终只有一个人。OBS 把摄像头放在 x 1416，y 748，384×216，与主方案一致。
- 场景用浏览器按 N / P 步进，由讲者本人或一名不出镜的成员推进。
- 字幕不能现场烧录：录完后在成片上叠加 `full.ass`（不剪辑画面），或只上传 `.srt`，需在邮件里一并确认。
- 每人在本地同时录一份备份轨。

---

## 11 排练与时间控制

### 11.1 排练轮次

| 轮次 | 内容 | 目标 |
|---|---|---|
| 1 | 各人单独朗读自己的段落并计时 | 每段与 7.3 节相差 ≤ 5 %；**第 4 段 ≤ 2:50**；实测值回填 `timeline.json` |
| 2 | 四人在线顺读一遍，只听不看 | 检查交接句、署名句、发音表、措辞边界；名字念法 |
| 3 | 对照第 1 段成片与其余粗剪完整播放 | 数字出现与念出相差 ≤ 0.5 s；字幕与开口相差 ≤ 0.3 s |
| 4 | 各人按正式方式连续录一遍 | 总长 ≤ 10:30，记录卡顿点 |
| 5（可选） | 针对卡顿点补练 | — |

### 11.2 时间检查点

| 检查点 | 场景 | 目标时刻 | 段长目标 | 容差 |
|---|---|---|---|---|
| 议程结束 | 02 | 0:55 | — | ±5 s |
| 第 1 段结束 | 07 | 2:16 | 2:16 | ±10 s |
| 第 2 段结束 | 13 | 4:30 | 2:14 | ±10 s |
| 泄漏检查结束 | 17 | 6:16 | — | ±10 s |
| 第 3 段结束 | 19 | 6:51 | 2:21 | ±10 s |
| 第 4 段结束 | 26 | 9:26 | **2:35，硬上限 3:00** | 超过 2:50 即触发砍减 |
| 全片 | — | 9:26 | — | 上限 10:30 |

### 11.3 同伴反馈（每轮，1–5 分加一句话）

1. 我能用一句话复述这一段的结论吗？
2. 我看到的、听到的和字幕一致吗？有没有在读屏幕？
3. 讲他人工作时，我听得出是谁做的吗？
4. 最让我困惑的数字是哪个？哪一句最像在背稿？
5. 语速和停顿合适吗？有没有空等的地方？

另请两位非组员看第 1 段成片与粗剪：两人都能说出三个研究问题及其回答，才算主线通过。

### 11.4 超时砍减顺序

**第一优先：保护第 4 段 ≤ 3:00。** 第 4 段实测超过 2:50 时按顺序砍，直到回到 2:50 以内：

| 顺序 | 场景 | 砍什么 | 节省 |
|---|---|---|---|
| 1 | 22 | 删 “: spectrum bias”（图内标注保留） | 约 1 s |
| 2 | 20 | 删 “The interval covers both no gain and a worthwhile one, so”，直接说 “The result is inconclusive …” | 约 3 s |
| 3 | 24 | 留出集一句改为 “An internal hold-out, scored once, repeats both results.”（1,146 只在画面上） | 约 3 s |
| 4 | 26 | 回顾句改为 “Four roles, one audit.”（卡片仍写四人分工） | 约 4 s |
| 5 | 21 | 删 “and leaves AUC 0.007 above minimal”（画面保留小号数字） | 约 2 s |

合计约 13 s。**第 4 段不砍：** 自我介绍、Brier 恶化、prior-care 消融、三个回答、意外发现、局限、GenAI、结论。

**第二优先：全片超过 10:30。**

| 顺序 | 场景 | 砍什么 | 节省 |
|---|---|---|---|
| 1 | 全片 | 停顿统一缩到 0.8 s | 约 8 s |
| 2 | 01 | 删 “We present in that order, and” | 约 2 s |
| 3 | 12 | 删 “from per-variable recoding to transforms and class weights” | 约 3 s |
| 4 | 05 | 删 “To check our survey-weighting code,” | 约 2 s |
| 5 | 14 | 删 DAG 一句，保留 Simpson 与 “exploratory” | 约 7 s |

**全片不砍：** 每段的自我介绍、署名句、意外发现与交接句；08–09（非显然发现）；15–17（RQ1 与 RQ2a 的证据）；20–21（RQ2b 与恶化）。

---

## 12 上传前检查清单

**内容。**
- [ ] 两名非组员看完都能说出三个研究问题及其回答
- [ ] 每页一个主张；主标题写主题、副标题写展示什么，没有一个标题是结论
- [ ] 数字出现与念出相差 ≤ 0.5 s（抽查 03、08、17、20、22）
- [ ] 每个 AUC 后面都有一句“这说明什么”；全片没有代码画面
- [ ] 改进和恶化都讲到：17（正确的恶化）、21（Brier）、23（消融）、24b 账本
- [ ] 每个带区间的数字都说了区间和结论强度
- [ ] 措辞符合 10.3 节；全片不念 0.076
- [ ] 每位成员只出现在自己的一段里，顺序固定；全片没有同框镜头
- [ ] 第 2–4 段以段首页和自我介绍开头；第 1 段由片头卡与团队页介绍；每段末尾有意外发现与交接句
- [ ] 讲他人工作的场景（06、11、17、18、20、21、22、24）都有口头点名或署名行；24 署 “Robustness checks led by” 加真名
- [ ] **屏幕、字幕和语音里没有任何字母代号 A–D**；所有名字都是真名，没有残留 “[Name]” 或 “[no.]”
- [ ] 颜色角色：靛蓝只在进度条当前段；红只表示受损或泄漏的数据；青只表示 Systematic；蓝空心方块只表示未确诊成人；灰实心圆只表示对照基线；反馈只用墨色形状
- [ ] 四种语义色首次出现时都有图例条（03、08、12、16）
- [ ] 推近只有 2 次（08、16）；晶须脉冲只有 1 次（20）；M8 只做原位换值
- [ ] 屏幕名称符合 5.4 节；内部代号只在 12 出现一次
- [ ] **第 4 段 ≤ 3:00**（目标 2:35）
- [ ] 所有上屏和口述的数字都在 `numbers_on_slides.csv` 中（含 13.2 节的补登行），§10.11 断言通过
- [ ] 全部旁白由四位成员亲口录制，没有合成语音

**字幕。**
- [ ] 每条 ≤ 2 行 × 42 字符；字幕区与图形、小窗、名签、图例行无冲突（审计全绿）
- [ ] 字幕与开口相差 ≤ 0.3 s；停顿和静默卡期间没有字幕
- [ ] `full.srt` 与烧录字幕文字一致；HbA1c、NHANES、kappa 拼写正确

**技术与合规。**
- [ ] 总长 ≤ 12:00（目标 9:26）；上传后以 YouTube 显示的时长再核对
- [ ] 响度约 −16 LUFS；没有爆音；四段音量一致
- [ ] 画面里没有个人数据：姓名以外的学号、邮箱、文件路径中的用户名、浏览器书签或通知
- [ ] `full.srt` 已作为 English 字幕上传
- [ ] 可见性为 Public；标题含组号；片尾卡写组号
- [ ] 用无痕窗口打开链接，确认未登录也能播放
- [ ] 缩略图：一个主数字（0.961）加片名，没有小字
- [ ] 说明里有代号对照一行和章节时间表（5.4 节）
- [ ] 链接写入 `notebooks/final/team.json` 的 `video_url`，运行 `.venv/Scripts/python tools/build_final.py --fill-team notebooks/final/CA6003_NHANES_Diabetes.ipynb`，再运行 `--validate-only` 确认没有残留的 [TEAM TO FILL]
- [ ] 提交前由一位非负责人再检查一遍

---

## 13 数字核对与待补登

### 13.1 核对方法

每个上屏或口述的数字都来自 `video/data/*.json`。这些文件由 `video/data/build_data.py` 只读已保存的结果生成，并与 `results/S10/numbers_on_slides.csv` 断言一致；逐值出处见 `video/data/SOURCES.md`。场景里不手敲数字。本方案的数字已与 `video/data/*.json` 和改版方案逐个核对，没有新增或改动数值。

若结果文件或 CSV 有变动：先运行 `.venv/Scripts/python video/data/build_data.py`（及 `build_geometry_s10_11_15.py`），再重渲染受影响的场景。

### 13.2 需补登到 `numbers_on_slides.csv` 的数字

补登方式：在 `notebooks/sections/09_synthesis.py` 的 `NUM` 列表中加行（slide、label、source key、format），重跑 §10，让 §10.11 的断言覆盖这些值。CSV 由脚本生成，不能手改。标 * 的行目前还没有标量键，需要先把对应标量存入 metrics。

| # | 值 | label（英文，入 CSV） | source key | slide_id | 场景 |
|---|---|---|---|---|---|
| 1 | 175 | raw columns before minimisation | `S1:minimisation.raw_columns` | V1 | 04 |
| 2 | 78 | columns kept after minimisation | `S1:minimisation.kept` | V1 | 04 |
| 3 | 27 | DB516 estimates compared | `S4:db516.n_estimates` | V7 | 05 |
| 4 | 0.044 | DB516 max absolute difference (pp) | `S4:db516.max_abs_diff_pp` | V7 | 05 |
| 5* | 15.8 | DB516 published total prevalence (%) | `results/S4/db516_replication.csv`（total, All, crude, nchs）→ 建议存为 `S4:db516.nchs_total` | V7 | 05 |
| 6* | +1.8 / +8.8 | insurance gap crude CI low / high (pp) | `S4:standardisation.insured_uninsured.crude_ci`（列表下标；不支持则另存 lo / hi） | V5 | 06 |
| 7* | −2.6 / +3.9 | insurance gap standardised CI low / high (pp) | `S4:standardisation.insured_uninsured.std_ci`（同上） | V5 | 06 |
| 8 | 6 | pre-registered (prior exposure none) hypotheses | 由 `S10:scoreboard` 计数 → 建议存为 `S10:prereg_none_n` | V8 | 07 |
| 9 | 3 | pre-registered hypotheses supported | `S10:verdict_counts_prereg_none.supported` | V8 | 07 |
| 10 | 3 | pre-registered hypotheses inconclusive | `S10:verdict_counts_prereg_none.inconclusive` | V8 | 07 |
| 11 | 57 | genuine codes caught by blanket recode | `S3:blanket_recode.questionnaire_only_cells` | V2 | 08 |
| 12 | 6.8 | HbA1c IQR fence, upper (%) | `S3:outliers.a1c_iqr_fence_upper` | V2 | 10 |
| 13* | 14 | preparation steps | `results/S6/step_catalogue.csv`（14 行）→ 建议存为 `S6:n_steps` | V2 | 12 |
| 14 | 0.70 | kappa self-report vs HbA1c (unweighted) | `S5:labels.agreement_unweighted.kappa` | V6 | 15 |
| 15 | 165 | self-reported below 6.5 on medication | `S5:masking.below_6_5_on_med` | V6 | 15 |
| 16 | 49 | uninsured adults with HbA1c >= 6.5 (n) | `S5:undiagnosed_inequality.proportions.uninsured.n` | V6 | 16 |
| 17 | 0.80 | specificity of the shared threshold | `S8:spec` | V6 | 19 |
| 18* | 40.9 % / 17.0 % | systematic mean predicted risk / observed prevalence (training part) | `results/S7/calibration.csv`（arm=S，pop=E-ALL：mean_p、prevalence）→ 建议存为 `S7:calibration.S.mean_p` / `.prevalence` | V7 | 21 |
| 19 | +0.004 / +0.034 | prior-care removal, not-yet-diagnosed adults, CI low / high | `S7:headline.minus_care_escreen.lo` / `.hi` | V7 | 23 |

### 13.3 定义常量与外部参考值（不入 CSV，脚本中以常量注明出处）

| 值 | 含义 | 出处 | 场景 |
|---|---|---|---|
| 0.5 | AUC 轴起点（随机基线） | 定义 | 01、17、22 |
| 6.5 % | HbA1c 诊断阈值（标签定义） | §5.1；`src/labels.py` | 03、09、15 |
| 1.5 × IQR | 教科书的离群值规则 | §3 | 10 |
| ±0.01 | 事先固定的 margin | `governance/hypotheses.md` H2b | 20、23 |
| 10 | VIF 参考线 | §4 | 11 |
| 7.0 %、9.0 %；示例值 7、9、77、99 | 与哨兵代码重合的真实值；示意值 | notebook §3.4 | 08、13 |
| “of 100” | 把 TPR 0.70 / 0.52 换算成每 100 人 | 由 `tpr_100.json` 换算 | 19 |

### 13.4 不使用的数字

- **已核实但不上屏：** −0.072（17）、+0.055（22）、+0.076（21）、+0.060（留出集差值）、0.844 / 0.772、0.60（对数偏度）、85、30.5 %、51.1 % / 7.2 %、0.633 / 0.701、88 / 46 / 42（设计列数）、7,809 / 6,064 / 5,767（漏斗中间级，改为文字）、Diagnosed / Undiagnosed 两行（05）、外部评审六项、133 条登记、17 条局限、26 条主张、响应率。
- **无法写成可断言的键：** 23（29 − 6）、569（819 − 250），改为图形或删除。
- **没有存储数字支持：** “almost all older adults have Medicare”，改为 “the insured are much older”（`age_std.json`：60 岁以上者占参保者 34 %、未参保者 10 %）。

---

## 14 评分覆盖与风险

### 14.1 rubric 覆盖

| 要求 | 场景 |
|---|---|
| 全员出镜，贡献可区分 | 小窗与名签全程；01 团队页；段首页 08a、14a、20a；26a 回顾；署名 06、11、17、18、20b、21、22、24 |
| 治理 | 04、05、07、26b（GenAI） |
| 剖析与数据质量，含非显然发现 | 08、09（“Non-obvious finding” 标签）、10 |
| EDA：冗余、多重共线、偏度 | 11（三个词都念出来） |
| 谬误 | 06（混杂）、14（Simpson、中介）、22（spectrum bias） |
| 重要准备决定的理由 | 10、11、12 |
| minimal vs systematic，同一模型 | 02、12、20（“same model, same folds” 念三次） |
| 改进与恶化 | 恶化：21 Brier +0.074（有害）、17 −0.131（预期内）、23 −0.016；改进：08 保住 1,496 个值、20 +0.008 与 23 +0.019（都 inconclusive）；24b 账本归在一起 |
| 偏差与标签 | 15、16、19 |
| 贡献与反思 | 07、13、19、25、26 |
| ML 是证据，不是目标 | 01、17、24、25、26 |
| ≤ 12:00，第 4 段 ≤ 3:00 | 9:26；第 4 段 2:35 |

| 准则 | 场景 | 观众看到的证据 |
|---|---|---|
| Appropriateness | 03、04、08、10、11、15–17、19、20、22 | 漏斗、得失对比柱、IQR 围栏、VIF 与偏度、Venn 与风险差、泄漏检查与哑铃图、点阵 |
| Correctness & Clarity | 01、05、07、08、11、13、14、17、19、20、24–26 | 团队页；一人一段；名签；段首页；署名；意外发现；收尾回顾；notebook 指引；DB516 复现 |
| Data Interpretation | 06、11、14–16、20–23 | VIF 95.7 / 97.6、偏度 6.62、混杂、Simpson、中介、κ、区间与 margin、spectrum bias |
| Novelty & depth | 01、08–09、17–18、22–24 | 被删的 7.0；插补出的 50；全体成人 AUC 度量的是识别；模型作为泄漏探测器 |

### 14.2 内容风险

| 风险 | 对策 |
|---|---|
| +0.008 被看成失败 | 02 先把“准备是否有用”立为研究问题；20 画出区间与 margin；21–24 说明价值在别处 |
| 讲他人的工作，贡献变模糊 | 口头点名 + 署名行；段首页的 “Owns” 行；收尾回顾；`team.json` 记录各人负责的章节 |
| 第 4 段超时 | 目标 2:35；第 1 轮排练即检查；11.4 节先砍第 4 段 |
| 数字太密 | 每场景口述 ≤ 3 个；补登表之外不加数字 |
| 不允许剪辑 | 10.5 节回退方案 |
| 夸大主张 | 10.3 节措辞边界；第 2 轮排练专查 |
| 名字没填就上传 | 检查清单第一组；审计拦截 “[Name]” 以外的字母人名，上传前人工核对没有 “[Name]” |
| 补登触碰冻结规则 | 只做 `fix` 提交，跑 FAST clean-room |

---

## 15 待确认

1. **给讲师的邮件。** 草稿：
   > “Dear [lecturer], our group plans to submit one YouTube video under 12 minutes. Each member presents one continuous part, in turn, in a small camera window beside animated charts; no shot shows more than one member. Each part is recorded in one continuous take, and captions are added afterwards. May the four takes be joined into one video, or must the whole video be recorded in a single session? Thank you, Group [no.]”
   - 回复“可以拼接” → 10.5 节主方案；
   - 回复“必须一次录制”，或 10/15 仍未回复 → 10.5 节回退方案。
2. **真名与组号。** 填进 `notebooks/final/team.json` 的 `members[].name` 与 `group_number`；之后重新生成字幕并重新合成。
3. **同步仓库文档。** `team.json` 的 `video_segment`、`docs/team_roles.md` §5、notebook 团队表的 “Video” 列仍是旧值（例如 “0:30–2:40, plus opening and closing”）。按实测时长改成四个区间，当前值为：

   | 成员 | video_segment |
   |---|---|
   | `members[0]` | 0:00–2:16 |
   | `members[1]` | 2:16–4:30 |
   | `members[2]` | 4:30–6:51 |
   | `members[3]` | 6:51–9:26 |

   `docs/team_roles.md` §5 的内容列也要更新：第 1 段讲年龄混杂（`<Name:2>` 的分析）；第 2 段讲冗余与偏度（`<Name:2>` 的发现）；第 3 段讲泄漏检查与决策树（`<Name:3>` 的实验）；稳健性核查署 `<Name:1>`，由第 4 段讲。更新后运行 `tools/build_final.py --fill-team` 和 `--validate-only`（交 main 处理）。
4. **CSV 补登。** 13.2 节的 19 行通过修改 `09_synthesis.py` 的 `NUM` 列表加入；标 * 的需先存标量。
5. **成员确认跨作者讲解。** 06、11 用 `<Name:2>` 的分析；17、18 用 `<Name:3>` 的实验；21 用 `<Name:1>` 的类别权重步骤；24 署 `<Name:1>`。原作者在第 2 轮排练时核对措辞。
6. **树的 “no” 分支。** 标签与 `tree.json` 一致。训练部分 4,584 行中有 4,044 行走 “no” 分支，其中 3,766 行是非糖尿病者；从未被问到服药问题的人在 naive 准备中也落在这一侧。是否把标签改为 “no / not asked”，由 `<Name:2>`、`<Name:3>` 在 notebook 中核实后决定；不改也不算错。
7. **GenAI 声明。** 26 的措辞须与 `governance/genai_log.csv` 和 `docs/team_roles.md` §6 一致，由 `<Name:0>` 在排练时核对。
8. **字幕校对人。** 指定一人校对 `full.srt` 与烧录字幕（建议 `<Name:0>`）。
