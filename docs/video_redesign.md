# CA6003 讲解视频改版方案

本文合并三份调研（`01_layout.md` 版面、`02_titles.md` 标题与导航、`03_audience.md` 面向专家讲师的内容），并按用户与协调者的裁定统一冲突。它取代 `docs/video_plan.md` 中与版面、导航、标题、场景划分和旁白有关的部分（见 6.6 节）；颜色角色、动效语汇和数字出处规则不变。

屏幕文字、标题、副标题和旁白用英文，其余用中文。`<A>`–`<D>` 和 `<Name>` 在录制前换成真名。

---

## 0 摘要

**改什么，为什么。**
- **用户反馈（2026-10-14）：**
  - 整体视觉风格保留；
  - 右栏（摄像头位、署名标签、A–D 徽章）占画面 18.3 %，其中 9.2 % 是空白，删掉；
  - 画面上不出现 “§7.5 · S7_leak_gate” 这类代码，也不用只有图标的阶段标签；
  - 每页都要有主标题（写主题，不写结论）和副标题（写本页展示什么）。
- **受众与形式：** 观众是课程讲师，本领域专家，但没有看过本项目；形式是项目汇报。标准术语照用，项目内部的代号一律替换或在首次出现时交代。
- **讲者小窗：** 讲者全片只出现在右下角一个固定的直角小窗里（x 1416–1800，y 748–964，384×216），上方有名签。没有全屏，没有分屏。每人仍是一段连续录像，顺序 A → B → C → D。

**结果。**
- 26 个场景（旧 12 + 13 合并；旧 25 并入旧 26）；
- 总长 **9:43**：A 2:22、B 2:15、C 2:27、D 2:39（≤ 3:00）；
- 旁白 1,189 词，平均 122 wpm，单场 118–134 wpm；
- 图区占画面从 **46.7 % 增加到 63.7 %**（扣除小窗避让区后为 56.3 %）；
- 26 个场景中，12 个只需 re-flow，12 个 rebuild，2 个 new。

**关键决定。**
1. **唯一版式。** 顶部进度条，64 px 主标题加 34 px 副标题，图区 1728×764，右下固定小窗和名签；删去右栏、徽章、陷阱条、lower-third 和 F / S / X 版式。
2. **七部分进度条。** 段名沿用 `02_titles.md`：Problem & data · Data quality · EDA & preparation · Labels & bias · Experiments · Results & robustness · Reflection。全片不出现 “Part n of 4/7” 一类编号。靛蓝只用于当前段的填充线。
3. **标题写主题。** 主标题写本页主题，副标题写本页展示什么；结论放进旁白和图内 ≤ 5 词的标注。
4. **先讲设计。** 场景 02 改为议程页：研究问题、同一模型 × 三种数据准备 × 两个评估人群，以及三个研究问题。
5. **研究问题沿用 notebook 编号。** RQ1 Labels → RQ2a Leakage → RQ2b Preparation，在 02 提出，在 24 回答，与揭示顺序一致。
6. **身份标注都用普通文字。** 名签 “Presented by <Name>” 加职责；段首页 “Presented by <Name> · <role>” 加本段覆盖的部分；他人工作用 “Analysis by <C>” 一类署名。
7. **底栏一行指引。** “Notebook section N.M”，全部按最终 notebook 标题核对过，改正 5 处。
8. **合成。** 每位成员的连续录像整段叠一次，坐标全片不变。

---

## 1 设计依据

### 1.1 用户反馈

| # | 反馈 | 本方案的处理 |
|---|---|---|
| 1 | 风格好，但右栏（480×270 空摄像头位、“experiment: D · §7” 署名、A–D 徽章与节号）浪费约四分之一画面 | 删除右栏；图区拉宽到 1728 px；讲者移到右下固定小窗（第 2 节） |
| 2 | 阶段显示不要怪符号：“§7.5 · S7_leak_gate”、“§0–2 / §3·6·9”、桶 / 尺 / 天平图标 | 进度条只写部分名；底栏只写 “Notebook section N.M”；不用任何图标标识阶段；kit 审计拦截 “§” 和内部代号（6.1 节） |
| 3 | 每页一个主标题、一个副标题；标题不是结论 | 规则与示例见 3.2 节；26 个场景的标题见第 5 节 |
| 4 | 观众不了解项目 | 按协调者修正，观众是没看过项目的专家讲师，形式为项目汇报；术语照用，内部代号替换（3.5 节） |

### 1.2 受众与形式

- **观众：** 课程讲师，熟悉数据治理、数据准备与分析，熟悉 AUC、HbA1c、κ、VIF、偏度、混杂、置信区间、等效界、泄漏、插补、调查权重。没有跟过本项目的设计与实验。
- **形式：** 项目汇报。顺序为：问题与数据 → 方法与设计 → 关键发现与证据 → minimal vs systematic → 改进与恶化 → 贡献与反思。
- **对内容的要求：**
  - 不给标准概念配比喻；
  - 去掉或交代内部代号；
  - 补上逻辑跳跃，例如研究设计原来到 4:32 才讲；
  - 每场景按“问题 → 方法 → 证据 → 含义”组织，口述数字 ≤ 3 个，关键效应带区间。

### 1.3 已定决定（全部有约束力）

1. 整体视觉风格不变：近白舞台、白纸面板、克制的动效（M1–M12）、原位强调；颜色角色不变。
2. 删去右栏（摄像头位、署名标签、A–D 徽章）。
3. 不用晦涩符号：没有 “§” 代码，没有内部键名，没有只靠图标的阶段标签。阶段名简单直接。
4. 每页有主标题（主题）和副标题（展示什么）。
5. 观众是专家讲师，形式是项目汇报。标准术语保留，内部代号替换或交代。
6. 讲者全片只在一个固定直角小窗里：x 1416–1800，y 748–964（384×216），外侧 1 px 细边；小窗上方是名签 “Presented by <Name>” 加职责。不用全屏，不用分屏。
7. 每人一段连续录像，A → B → C → D；D ≤ 3:00；没有合影。

### 1.4 仍然有效的评分约束

- 视频 ≤ 12:00；四人都要出镜并讲解；每人的贡献清楚可分（rubric “Correctness & Clarity”）。
- 必须覆盖：
  - 治理；
  - 剖析与数据质量，至少一个非显然发现；
  - EDA：冗余、多重共线、偏度、谬误；
  - 用同一个基础模型比较 minimal 与 systematic 准备；
  - 改进与恶化；
  - 结尾讲贡献，并反思新颖或意外之处。
- 讲推理、证据和解释，不讲代码和准确率。
- 每个数字都来自已保存的结果（`video/data/*.json`，由 `build_data.py` 生成并断言）。

覆盖情况见 4.2 节和 `03_audience.md` 5.1 节（场景号按新编号）。

---

## 2 版式

### 2.1 唯一版式与网格

全片只有一种版式。画布 1920×1080，外边距左右 96 px、上 40 px、下 52 px。

```
x  96                                                                                 1824
y  40 ┌ Problem & data   Data quality   EDA & preparation   Labels & bias   Experiments ... ┐  74  进度条
y  96 │ Main title (64 px serif)                                                            │ 160
y 172 │ Subtitle (34 px sans)                                         | Analysis by <C>     │ 206
y 224 ┌──────────────────────────── 图区纸面面板 1728×764 ───────────────────────────────────┐
      │                                                                                     │
      │   主区：面板坐标 x 0–1296，全高（内容右端 ≤ 1272）          副区：x ≥ 1296 且 y < 408 │
      │                                                                                     │
      │                                                   ┌ Presented by <Name> ───────┐    │ 656
      │                                                   └ Data quality & preparation ┘    │ 740
      │                                                   ┌────────────────────────────┐    │ 748
      │                                                   │   PiP 384×216（固定）       │    │
      │                                                   └────────────────────────────┘    │ 964
y 988 └─────────────────────────────────────────────────────────────────────────────────────┘
y1000   ● reference baseline  ▨ harmed or leaked data  ■ Systematic preparation  □ Not-yet-...   Notebook section 7.5  1028
```

| 区域 | x | y | 尺寸 | 规格 |
|---|---|---|---|---|
| 进度条 | 96–1824 | 40–74 | 1728×34 | 七段；段名 24 px IBM Plex Sans，基线 y 60；4 px 细线在 y 70–74（3.1 节） |
| 主标题 | 96–1824 | 96–160 | 1728×64 | Source Serif 4，64 px（原 72），单行 |
| 副标题 | 96–1824 | 172–206 | 1728×34 | IBM Plex Sans 34 px，墨色，单行；有署名时在署名左侧 48 px 处结束 |
| 署名 | 副标题行右端 | 172–206 | 自适应 | 28 px sans，左侧 2×28 px 墨色竖线，无框，无 “§” |
| 图区纸面面板 | 96–1824 | 224–988 | **1728×764** | 白纸，8 px 圆角，1 px #E3E7EC 边，柔和阴影；面板坐标原点 (96, 224) |
| 名签 | 1416–1800 | 656–740 | 384×84 | 两行 28 px：`Presented by <Name>`（semibold）/ `<role>`；纸色底，1 px 细边，直角；下边距小窗 8 px |
| 小窗 | 1416–1800 | 748–964 | 384×216 | 直角；1 px #E3E7EC 细边画在外侧（1415–1801 × 747–965），由 kit 渲染；无阴影、无动画 |
| 避让区 | 1392–1824 | 632–988 | 432×356 | 小窗与名签外扩 24 px。图中任何内容不得进入。面板坐标为 **x 1296–1728，y 408–764** |
| 底栏 | 96–1824 | 1000–1028 | 1728×28 | 左侧图例行（24 px）；右端 notebook 指引（24 px，墨色 60 %，右对齐到 x 1824） |

**面积。**

| | 旧版（R 版式） | 新版 |
|---|---|---|
| 图区尺寸 | 1224×792 | 1728×764（宽 +41 %，高 −3.5 %） |
| 图区占画面 | 46.7 % | **63.7 %** |
| 扣除避让区后 | 46.7 % | **56.3 %** |
| 讲者窗口 | 6.3 %（480×270） | 4.0 %（384×216） |
| 身份与导航界面 | 20.1 %（右栏 + 陷阱条） | 4.4 %（进度条 2.8 % + 名签 1.6 %） |
| 空白右栏 | 9.2 % | 0 |

图区可用部分是一块 1296×764 的全高主区，加上右侧一块 432×408 的上部副区。现有图形多数横向顶到旧面板两侧，所以宽度是瓶颈；新增的 504 px 正好补在这个方向上。

### 2.2 小窗、名签与避让区

- **小窗：** 384×216（16:9，画面宽度的 1/5），全片同一坐标。胸像构图下脸高约 97 px，口型和表情清楚。面积比旧摄像头位小 36 %。
- **名签：** 全程常驻，写 “Presented by <Name>” 和职责。四人的职责：

  | 成员 | 名签第 2 行（role） | 段首页 “Owns” 行 |
  |---|---|---|
  | A | Governance & integration | governance, data access, reproducibility |
  | B | Data quality & preparation | quality audit, preparation design, robustness checks |
  | C | Exploration, labels & bias | exploratory analysis, label analysis, fairness audit |
  | D | Modelling & conclusions | experiments, synthesis of conclusions |

- **避让区：** 面板坐标 x ≥ 1296 且 y ≥ 408 的区域不放任何内容，包括章节卡、片尾卡和推近（M9，缩放 ≤ 1.25）后的图形。kit 审计会拦截（6.1 节）。
- **切换：** 换讲者只发生在 A→B（2:22）、B→C（4:37）、C→D（7:04）三处，都在段首页的第 1 帧。新讲者从第 1 帧起就在小窗里，名签同时换字。

### 2.3 页面类型

网格和小窗不变，面板里放什么分成五种页面，外加两种过渡元素。

| 类型 | 用途 | 面板内容 | 规则 | 场景 |
|---|---|---|---|---|
| **证据页** | 数据讲解 | 一张证据图 | 一页一个主张；口述数字 ≤ 3；内容不进避让区 | 03–06、08b–12、14b–18、20b–24a |
| **段首页** | 每位成员的开头；取代旧的全屏自我介绍 | 第 1 行 56 px serif：`Presented by <Name> · <role>`；第 2 行 28 px 墨色 60 %：`Owns: …`；下面每个部分一行（部分名 semibold，后接 2–3 个主题） | 前 1.2 s 静默（进度条在此时切换）；讲者说完自我介绍句后，用 M12 溶解成第一张证据页 | 01c（A，与团队页合一）、08a、14a、20a |
| **反思页** | 每段末尾的 “Most unexpected finding”；取代旧的分屏 | 正文一行 40 px serif（讲者的反思句）；原小图缩到 ≤ 400 px 高放在下方；左下 28 px 墨色 60 % 的交接行 | ≤ 14 s；主标题固定，副标题以讲者名开头 | 07、13、19、25 |
| **议程页** | 开场路线图；24 的回答版与之呼应 | 栏目名 28 px（墨色 60 %）+ 内容 34 px，左对齐 | 研究问题行的字号、顺序在 02 和 24 完全相同 | 02、24b |
| **收尾页** | 贡献、局限与 AI、结论 | 角色卡与贡献链；局限标签与 GenAI 卡；一句 56 px 收束语 | 收束语是全片唯一以大字出现的结论 | 26a–c |
| 过渡：**章节卡** | 不换讲者的部分开头 | 舞台色满幅（小窗、名签照常露出）：80 px 部分名（主标题）、34 px 范围行（副标题）、28 px 讲者行 | 1.2 s 静止，计入所在场景时长，旁白在其后开口 | 11、17、22 |
| 过渡：**片头卡 / 片尾卡** | 开场 2 s、结尾 2 s | 片名 88 / 120 px，副标题行 “Basic models as instruments on NHANES 2021–2023” | 片尾卡：七段路线回到画面中央并全部为“已讲完”；底部一行数据来源 | 01a、26d |

**靛蓝只出现一处。** 一帧里，结构靛蓝只用于进度条当前段的填充线。旧章卡左侧的 4×120 px 靛蓝竖线、角色卡的靛蓝左侧细线都取消；当前卡片改用 M3 的 2 px 墨色描边加“暗其余”。

### 2.4 底栏：图例行与 notebook 指引

**图例行**（左侧，24 px，常驻，只显示已出现过的颜色）：
- `● reference baseline`
- `▨ harmed or leaked data`
- `■ Systematic preparation`
- `□ Not-yet-diagnosed adults`

**图例时刻**（颜色第一次出现时，面板一角出现 2–3 s，随后收进底栏）：

| 颜色 | 首次出现（新场景） | 图例条文字 |
|---|---|---|
| 灰 | 03（All adults 末条） | “● grey = reference: all adults” |
| 红 | 08（被误删的单元格、1,496 柱） | “▨ red = harmed or leaked data” |
| 青 | 12（systematic 泳道） | “■ teal = systematic preparation” |
| 蓝 | 16（152 人） | “□ blue = not-yet-diagnosed adults” |

议程页（02）里的设计矩阵只用墨色，不提前用语义色。

**Notebook 指引**（右端，纯文字一行）。格式为 `Notebook section 7.5`，多节时写 `Notebook sections 4.7–4.8`。不写 “§”，不写结果键名，也不写 notebook 原标题（原标题里有 “M0 → M1”、“E-SCREEN” 等代号）。段首页、章节卡、片头卡和片尾卡不显示指引。

以下章节号已用 `.venv/Scripts/python` + nbformat 逐条对照 `notebooks/final/CA6003_NHANES_Diabetes.ipynb` 的标题。★ 表示改正了旧场景里的错误指引。

| 新 | 指引 | 依据（notebook 标题） | 新 | 指引 | 依据（notebook 标题） |
|---|---|---|---|---|---|
| 01 | section 7.5 | 7.5 Leak gate（0.961 出处） | 14 | ★ sections 4.7–4.8 | 4.7 Simpson scan；4.8 Causal structure（旧 §4.6 是保险一节） |
| 02 | sections 1.3–1.5 | 1.3 Feature-availability rule；1.4 Evaluation populations；1.5 Research questions | 15 | ★ sections 5.1–5.2 | 5.1 Three labels and their agreement；5.2 Treatment masking（旧 §5.3） |
| 03 | ★ sections 1.1, 3.2 | 1.1 Analysis cohort；3.2 … the sample funnel（旧 §2 是数据来源与规格） | 16 | sections 5.3–5.4 | 5.3 What "undiagnosed" means；5.4 Who is undiagnosed |
| 04 | sections 1.8–1.9 | 1.8 Data user agreement；1.9 Data minimisation | 17 | section 7.5 | 7.5 Leak gate |
| 05 | section 4.3 | 4.3 External anchor: NCHS Data Brief 516 | 18 | section 7.5 | 7.5 的 “So what” 讨论了树与插补的 50 |
| 06 | sections 4.5–4.6 | 4.5 Age standardisation；4.6 Insurance | 19 | sections 8.2–8.3 | 8.2 Group metrics at the fixed threshold；8.3 Gaps |
| 07 | section 10.2 | 10.2 Hypothesis scoreboard | 20 | sections 7.12, 10.2 | 7.12 Verdicts（H2b +0.008）；10.2.1 H2b in detail |
| 08 | section 3.4 | 3.4 Cost of a blanket recode | 21 | section 7.10 | 7.10 Precision–recall and calibration（类别权重） |
| 09 | section 3.4 | 同上 | 22 | section 7.9 | 7.9 E-ALL vs E-SCREEN（84 %，spectrum bias） |
| 10 | ★ section 3.8 | 3.8 Outliers: a three-layer rule（旧 §3.5 是一致性检查） | 23 | section 7.8 | 7.8 Leave-one-block-out（care items） |
| 11 | sections 4.9–4.10 | 4.9 Redundancy and collinearity；4.10 Skewness | 24 | sections 9.11, 10.6 | 9.11 Internal hold-out check；10.6 Headline findings |
| 12 | ★ sections 6.2, 6.9 | 6.2 Step catalogue；6.9 Arms（旧 13 的 §6.4 是 availability rule 一节） | 25 | sections 7.5, 10.2 | 7.5 与 10.2 |
| 13 | section 3.4 | 3.4 | 26 | Notebook: Team and contributions; section 10.9 | 无编号的 “Team and contributions” 与 10.9 Limitations register |

旧标签里另有一些只写到章（“§7”“§8”“§10”），上表都改成了具体的小节。

---

## 3 导航与标题

### 3.1 七部分进度条

**段与场景。** 场景顺序由“每人一段”锁定，所以进度条只往前走。探索性分析分散在 06、11、14 三处，处理沿用 `02_titles.md`：06 留在第 1 部分；11 与准备设计合为第 3 部分；14（Simpson 与 DAG）归入 “Labels & bias”。

| 段名（进度条与章节卡一字不差） | 新场景 | 起止 | 时长 | 讲者 | 开头标识 | rubric 要点 |
|---|---|---|---|---|---|---|
| Problem & data | 01–07 | 0:00–2:22 | 142 s | A | 片头卡 + 团队页（01） | 问题、设计、队列、治理、外部复现、混杂 |
| Data quality | 08–10 | 2:22–3:26 | 64 s | B | B 的段首页（08a） | 剖析、非显然发现、离群值 |
| EDA & preparation | 11–13 | 3:26–4:37 | 71 s | B | 章节卡（11） | 冗余、多重共线、偏度；准备设计；三条流水线 |
| Labels & bias | 14–16 | 4:37–5:59 | 82 s | C | C 的段首页（14a） | 谬误；标签一致性；未确诊者与第二个评估人群 |
| Experiments | 17–21 | 5:59–7:58 | 119 s | C → D | 章节卡（17）；D 的段首页（20a）不切换段 | 泄漏检查；minimal vs systematic；恶化 |
| Results & robustness | 22–24 | 7:58–9:05 | 67 s | D | 章节卡（22） | 分人群表现；消融；留出集；回答研究问题 |
| Reflection | 25–26 | 9:05–9:43 | 38 s | D | 无章节卡（25 只有 7 s） | 意外发现；贡献；局限；GenAI；结论 |

合计 583 s。

**进度条规格。**

| 项 | 规格 |
|---|---|
| 位置 | x 96–1824，y 40–74 |
| 段名 | 只写部分名，不加序号，不用图标，不用 “§” |
| 段宽 | 段名宽 + 32 px，段间隙 16 px，从 x 96 左对齐；估算总宽约 1,450 px |
| 细线 | y 70–74，每段一条，与该段同宽 |
| 已讲完 | 段名墨色 60 %，细线墨色 |
| 当前段 | 段名墨色 100 % semibold；细线为结构靛蓝，按本段已用时间从左往右填充（全局时间 t 的纯函数），未填部分为 `--line` |
| 未讲到 | 段名墨色 60 %，细线 `--line` |
| 切换 | 在段首页或章节卡的前 1.2 s 内完成：上一段转为“已讲完”，新段变为 semibold，靛蓝线从新段左端开始填充（0.4 s，M12） |
| 出现 | 场景 02 末尾，议程里的七段路线用 M6（0.9 s）收缩到页顶，之后常驻到 26c；01 与 02 的前 27 s 没有进度条 |
| 片尾 | 26d 片尾卡上，路线回到画面中央，七段全部为“已讲完” |

示例（场景 17 开头，第 5 段刚开始）：

```
y 60  Problem & data   Data quality   EDA & preparation   Labels & bias   Experiments   Results & robustness   Reflection
y 72  ━━━━━━━━━━━━━━   ━━━━━━━━━━━━   ━━━━━━━━━━━━━━━━━   ━━━━━━━━━━━━━   ▬───────────   ────────────────────   ──────────
      墨色 60 %，墨线   墨色 60 %，墨线 墨色 60 %，墨线      墨色 60 %，墨线  100 % semibold 墨色 60 %，浅线          墨色 60 %，浅线
                                                                          靛蓝填充 ≈ 0 %
```

### 3.2 主标题与副标题

**主标题。**
- 64 px Source Serif 4，单行，≤ 1728 px，最多约 5 个词。
- 写本页的主题，可用标准术语，例如 “Data leakage check”、“Label agreement: self-report vs HbA1c”。
- 可以用问句，但只能说明本页检验什么，不能预设答案。
  - 可以：“How good is AUC 0.961?”
  - 不可以：“How did the model cheat?”
- 不写结论。不用 →、=、≫，不用 “worse”、“removed”、“inconclusive” 这类判定词，不放区间。
- 数字只在它本身就是主题时出现，全片只有 01b 一处。
- 不用内部代号（M0 / M1 / S、E-ALL / E-SCREEN、trap、P 编号、§）。
- 一个场景一个标题，从头到尾不变，不再溶解成结论。分阶段的场景每个阶段换一次：01（片头、钩子、团队）、08 / 14 / 20（段首页、正文）、24（留出集、回答）、26（贡献、局限、结论、片尾）。

**副标题。**
- 34 px IBM Plex Sans，单行，最多约 12 个词；比主标题晚 0.3 s 淡入，之后常驻。
- 说明这一页给观众看什么：数据、方法或比较。
- 不写结论，最多一个数字。

**结论的去处：** 旁白，或图内 ≤ 5 词的小标注，例如 17 的 “✓ correct deterioration”、23 的 “? inconclusive”。

**好坏对照。**

| 旧（坏） | 问题 | 新主标题 / 副标题 |
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
| “Most unexpected for D” | 字母代号放进标题 | **Most unexpected finding** / <D> on AUC change from leakage vs from preparation |

### 3.3 段首页、章节卡与反思页

**段首页**（08a、14a、20a；A 的段首由 01 的片头卡与团队页承担）。面板内左对齐，起点面板坐标 x 48，全部内容在 x ≤ 1272。

| 行 | 面板坐标 y（基线） | 规格 |
|---|---|---|
| 讲者与职责 | 110 | `Presented by <Name> · <role>`，56 px serif |
| 负责 | 170 | `Owns: …`，28 px sans，墨色 60 % |
| 本段覆盖的部分 | 250–420 | 每个部分一行，28 px sans：部分名 semibold，后接 2–3 个主题 |

| 页 | 主标题 | 副标题 | 卡片第 1 行 | 本段覆盖的部分 |
|---|---|---|---|---|
| 08a | Data quality | Profiling, missing-value codes and outliers | Presented by <B> · Data quality & preparation | **Data quality:** missing-value codes · effect on labels · outliers / **EDA & preparation:** redundancy and skewness · preparation design |
| 14a | Labels & bias | Analytical fallacies, label agreement and undiagnosed diabetes | Presented by <C> · Exploration, labels & bias | **Labels & bias:** Simpson's paradox scan · label agreement · undiagnosed diabetes / **Experiments:** data leakage check, with <D>'s experiments |
| 20a | Experiments, results and reflection | Minimal vs systematic preparation, then results, robustness and reflection | Presented by <D> · Modelling & conclusions | **Experiments:** minimal vs systematic · calibration / **Results & robustness:** populations · prior-care ablation · hold-out · answers / **Reflection** |

- 第 1、2 行在讲者说出姓名时用 M12 淡入；“本段覆盖的部分”在说出职责时淡入。
- 自我介绍句结束（约 5–6 s）后，用 M12 溶解成该场景的证据页，标题随之换成证据页标题。

**A 的开头（01）。**
- 片头卡（0–2 s）：片名 “Who gets labelled diabetic?”；副标题行 “Basic models as instruments on NHANES 2021–2023”；第三行 28 px “Presented by <A> · Governance & integration · Problem & data”；mono 小字 “CA6003 · Group [no.]”。
- 团队页（约 12–30 s）：四张角色卡，三行：姓名 / 职责 / 本人讲的部分。

  | 卡 | 第 1 行 | 第 2 行 | 第 3 行 |
  |---|---|---|---|
  | A | <Name A> | Governance & integration | Problem & data |
  | B | <Name B> | Data quality & preparation | Data quality · EDA & preparation |
  | C | <Name C> | Exploration, labels & bias | Labels & bias · Experiments (leakage check) |
  | D | <Name D> | Modelling & conclusions | Experiments · Results & robustness · Reflection |

  念到谁，谁的卡保持 100 %、加 2 px 墨色描边，其余暗到 25 %。卡片不再收成徽章，结尾用 M12 溶解。

**章节卡**（11、17、22，各 1.2 s）。不写 “Part n of 7”。

| 场景 | 主标题（80 px） | 范围行（34 px） | 讲者行（28 px） |
|---|---|---|---|
| 11 | EDA & preparation | Redundancy, skewness, and the preparation design they inform | Presented by <B> · EDA by <C> |
| 17 | Experiments | Naive, minimal and systematic preparation: one model, same folds | Presented by <C> · experiments by <D> |
| 22 | Results & robustness | Performance by population, ablation, hold-out, and answers to the research questions | Presented by <D> |

**反思页 “Most unexpected finding”**（07、13、19、25）。主标题相同；副标题以讲者名开头，写主题不写结果；结果写在正文一行里（这是讲者的反思句，与旁白同时出现）。

| 页 | 副标题 | 正文一行（数据来源） | 交接行 |
|---|---|---|---|
| 07 | <A> on the pre-registered hypotheses and their verdicts | Of six pre-registered hypotheses, three were supported and three inconclusive.（`hypotheses.json`：prereg_n 6，supported 3，inconclusive 3） | Next: Data quality · presented by <B> |
| 13 | <B> on one routine recode line | One routine recode line erased 29 HbA1c-positive results; the either-or label hid it.（`blanket_recode.json`：a1c_lost 29） | Next: Labels & bias · presented by <C> |
| 19 | <C> on detection at one cut-off, by diagnosis status | At one shared cut-off, 70 of 100 diagnosed but 52 of 100 not-yet-diagnosed diabetics are flagged.（`tpr_100.json`；小字 “specificity 0.80 · rates per 100”） | Next: Experiments, continued · presented by <D> |
| 25 | <D> on AUC change from leakage vs from preparation | Leakage moved AUC by 0.131; systematic preparation moved it by 0.008.（`leak_gate.json` diff_eall；`prep_band.json` d_auc） | Next: contributions, limits and conclusion |

### 3.4 研究问题的呈现

沿用 notebook 1.5 节的编号。notebook 的 RQ2 “Rules and preparation” 同时包括 availability rule（泄漏）和系统准备，对应假设 H2a 与 H2b，所以视频拆成 RQ2a 与 RQ2b。RQ3、RQ4 不讲。

| 屏幕文字（议程页 02 与回答页 24b，字号、顺序相同） | 揭示 | 旁白中的叫法 |
|---|---|---|
| **RQ1 · Labels:** What do self-report and HbA1c each measure? | 15（C） | “Research question one: the label.” |
| **RQ2a · Leakage:** Does AUC 0.961 survive excluding post-diagnosis items? | 17（C） | “The leakage question” |
| **RQ2b · Preparation:** Does systematic beat minimal preparation, same model? | 20（D） | “Last question: does systematic preparation pay?” |

- 议程页研究问题区下方加一行 28 px、墨色 60 % 的小字：“RQ3 (label matrix) and RQ4 (BMI bias): in the notebook”。
- 屏幕顺序、旁白顺序、揭示顺序一致：RQ1 → RQ2a → RQ2b。旧稿的 “Trap two … Trap one … Trap three” 顺序错乱，已取消。
- 不用任何图标；不常驻在画面上，导航由进度条承担。
- 24b 的答案行（写在每个研究问题下方，28–34 px；结论只写在这里，不进标题）：
  - **RQ1 · Labels：** “Self-report records contact with care as well as disease (κ = 0.70)”。不加 ✓：这一问是描述性的，加 ✓ 会被读成“标签可靠”。
  - **RQ2a · Leakage：** “No: AUC 0.961 → 0.828 once post-diagnosis items are excluded”，墨色实心 ✓。
  - **RQ2b · Preparation：** “AUC +0.008 [0.000, 0.016]: inconclusive”，墨色虚线框加 “?”。下面两行账本：“better: 1,496 valid values kept · an honest test on not-yet-diagnosed adults” / “worse: calibration (Brier +0.074)”。

### 3.5 屏幕术语

**标准术语照用，不在画面上解释：** AUC、HbA1c、Cohen's κ、VIF、skewness、confidence interval（方括号，图注写一次 “CI”，不写 95 %，因为 `prep_band.json` 没有记录置信水平）、data leakage、median imputation、Brier score、calibration、spectrum bias、Simpson's paradox、DAG、pp、L2 logistic regression。

**内部代号 → 屏幕名称。**

| 内部代号 | 屏幕名称（首次） | 之后 | 旁白 | 视觉（不变） |
|---|---|---|---|---|
| M0 | Naive preparation (all columns) | Naive | “naive preparation” | 红色斜纹 |
| M1 | Minimal preparation (post-diagnosis items excluded) | Minimal | “minimal” | 灰色实心 |
| S | Systematic preparation | Systematic | “systematic” | 青色实心 |
| 三者的对照 | 只在 12 的泳道标签下用 24 px 灰字注一次 “notebook: M0 · M1 · S” | — | — | — |
| E-ALL | All adults | All adults | “all adults” | 灰色实心圆 |
| E-SCREEN / Screening group | Not-yet-diagnosed adults | Not-yet-diagnosed | “adults not yet diagnosed” | 蓝色空心方块 |
| Trap 1 / 2 / 3；Leak / Label / Little gain | RQ2a · Leakage / RQ1 · Labels / RQ2b · Preparation | 同左 | “the leakage question” 等 | 不用图标 |
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
| 成员 A–D | 真名；名签 “Presented by <Name>” | — | 真名 | 不再用字母徽章 |
| 署名标签 “work: C · §4” | “Analysis by <C>”（副标题行右端） | — | “C's analysis” | 28 px 墨色 |

**署名一览：** 06 Analysis by <C>；11 EDA by <C>；17、18 Experiment by <D>；20b Preparation steps by <B>；21 Class-weight step by <B>；22 Population defined by <C>；24 Robustness checks led by <B>。

**代号对照的去处：** YouTube 说明里放一行 “Naive = M0, Minimal = M1, Systematic = S; all adults = E-ALL; not-yet-diagnosed adults = E-SCREEN”，并附章节时间表。

---

## 4 内容

### 4.1 汇报结构

| 阶段 | 新场景 | 内容 |
|---|---|---|
| 开场 | 01–02 | 可疑的 0.961；团队与分工；问题、设计、三个研究问题 |
| 数据与治理 | 03–07 | 队列与标签；治理；外部复现；混杂；A 的意外 |
| 数据质量与准备 | 08–13 | 先剖析后清洗（非显然发现）；离群值；冗余与偏度；准备设计与三条流水线；B 的意外 |
| 标签与偏差 | 14–16 | Simpson 与 DAG；RQ1 标签一致性；未确诊者与第二个评估人群 |
| 实验 | 17–21 | RQ2a 泄漏检查与机制；C 的意外；RQ2b minimal vs systematic；一个恶化（校准） |
| 结果与稳健性 | 22–24 | 分人群 AUC；prior-care 消融；内部留出集；三个回答 |
| 反思 | 25–26 | D 的意外；贡献；局限；GenAI；结论 |

全片论点：**“The score is not the finding; what it reveals about the data is.”**

### 4.2 四条核心信息

| # | 核心信息 | 主证据 | 新场景 |
|---|---|---|---|
| 1 | The headline AUC was leakage. Excluding post-diagnosis items is a correct deterioration; median imputation of a skipped question created a label proxy. | 0.961 → 0.828，配对下降 0.131 [−0.148, −0.114]；86 % 未被问及，插补为 50 | 17、18 |
| 2 | The label is a measurement shaped by care. Treatment masks HbA1c, and access to care decides who is diagnosed, so the all-adults AUC mostly measures recognition. | κ 0.70；250 of 819；152 未确诊，+23.2 pp [6.2, 40.1]；0.836 vs 0.781 | 15、16、22 |
| 3 | With the same model, systematic preparation barely moves AUC. Its value is data integrity, and one step had a measurable cost. | +0.008 [0.000, 0.016] vs margin 0.01，inconclusive；1,496 个有效值被保住；Brier +0.074 | 08–12、20–21 |
| 4 | Governance made these claims checkable. | 数据使用协议与最小化；NCHS 复现；事先锁定的假设；内部留出集 | 04、05、07、24 |

**rubric 覆盖（新编号）。**

| 要求 | 场景 |
|---|---|
| 全员出镜，贡献可区分 | 小窗与名签全程；段首页 08a、14a、20a；01 团队页；26a 回顾；跨人署名 06、11、17、18、20b、21、22、24 |
| 治理 | 04、05、07、26b（GenAI） |
| 剖析与数据质量，含非显然发现 | 08、09（“Non-obvious finding” 标签）、10 |
| EDA：冗余、多重共线、偏度 | 11（三个词都念出来） |
| 谬误 | 06（混杂）、14（Simpson、中介）、22（spectrum bias） |
| minimal vs systematic，同一模型 | 02、12、20（“same model, same folds” 念三次） |
| 改进与恶化 | 恶化：21 Brier +0.074（有害）、17 −0.131（预期内）、23 −0.016；改进：08 保住 1,496 个值、20 +0.008 与 23 +0.019（都 inconclusive）；24b 账本归在一起 |
| 偏差与公平 | 15、16、19 |
| 贡献与反思 | 07、13、19、25、26 |
| ≤ 12:00，D ≤ 3:00 | 9:43；D 2:39 |

### 4.3 议程场景（新 02）

**主标题** “Overview and agenda”；**副标题** “Question, data, design, research questions and the sections of this talk”。全幅面板，左列栏目名（28 px，墨色 60 %，sentence case），右列内容（34 px），全部在面板坐标 x 48–1272 以内。只用墨色。

| 行 | 面板坐标 y | 栏目 | 内容 |
|---|---|---|---|
| 1 | 40–88 | Question | Who gets labelled diabetic, and what do preparation decisions change? |
| 2 | 112–160 | Data | NHANES 2021–23 (CDC) · 5,730 adults with an HbA1c result |
| 3 | 184–330 | Design | 一行 “One L2 logistic regression · same folds”，下方一个 3×2 小矩阵：行 Naive / Minimal / Systematic，列 All adults / Not-yet-diagnosed adults（墨色细线格，不填色） |
| 4 | 354–520 | Research questions | RQ1 · Labels / RQ2a · Leakage / RQ2b · Preparation 三行（3.4 节）；下面一行小字 “RQ3 (label matrix) and RQ4 (BMI bias): in the notebook” |
| 5 | 560–620 | Sections | 七段路线：22 px 段名 + 细线，宽度限于 x 48–1272；每段下方 22 px 讲者名（A 在第 1 段下，B 在 2–3，C 在 4–5，D 在 5–7） |

**构建**（28 s）：
1. 0 s：第 1 行先只出现 “How accurate can a model get?”；念到 “who gets labelled” 时暗到 25 %，0.4 s 后用 M12 溶解成第 1 行的正式内容。
2. 念到 “The design” 时第 2、3 行依次出现；念到 “naive, minimal and systematic” 时矩阵三行依次描边，念到 “all adults … not yet diagnosed” 时两列依次描边。
3. 念到 “Our research questions” 时三行研究问题依次出现，顺序 RQ1 → RQ2a → RQ2b，与旁白一致。
4. 约 25 s 起，第 5 行路线从左往右画出（M1 节奏）。
5. 26.8 s 起，路线用 M6（0.9 s）收缩到 y 40–74 的进度条位置，第 1 段变为当前段；其余四行暗到 25 %，留到场景切走。

**旁白**（按裁定改写为 RQ1 → RQ2a → RQ2b；56 词 / 28 s = 120 wpm）：

> **A**: Our question: who gets labelled diabetic, and what do preparation decisions change? The design: one L2 logistic regression on three preparations of the same data, naive, minimal and systematic, scored on all adults and on adults not yet diagnosed. Our research questions: what does the label measure? Is the high AUC leakage? Does systematic preparation pay?

### 4.4 28 → 26 场景对照

| 新 | 旧 | 变化 |
|---|---|---|
| 01 | 01 | 删 AUC 定义与 coin flip / perfect 标注；交代 0.961 的来历；S 半屏取消 |
| 02 | 02 | 陷阱卡改为议程页（研究设计 + RQ） |
| 03–07 | 03–07 | 编号不变；内容简化 |
| 08–11 | 08–11 | 编号不变 |
| **12** | **12 + 13** | 十四个步骤与三个数据版本合并为 “Preparation design” |
| 13 | 14 | B 的意外 |
| 14 | 15 | Simpson 与 DAG（含 C 的段首页） |
| 15 | 16 | RQ1 标签一致性 |
| 16 | 17 | 未确诊者与第二个评估人群 |
| 17 | 18 | RQ2a 泄漏检查 |
| 18 | 19 | 泄漏机制：树与插补的 50 |
| 19 | 20 | C 的意外 |
| 20 | 21 | RQ2b minimal vs systematic（含 D 的段首页） |
| 21 | 22 | 校准与 Brier |
| 22 | 23 | 分人群 AUC |
| 23 | 24 | prior-care 消融 |
| **24** | **25 + 26** | 留出集压成开头一句，接三个回答 |
| 25 | 27 | D 的意外 |
| 26 | 28 | 贡献、局限、GenAI、结论、片尾 |

### 4.5 各成员时间

| 成员 | 旧段落 | 新段落 | 新时长 | 场景 | 旁白词数 | 平均语速 | 节省 |
|---|---|---|---|---|---|---|---|
| A | 0:00–2:30 | 0:00–2:22 | 2:22（142 s） | 01–07 | 288 | 122 wpm | 8 s |
| B | 2:30–5:03 | 2:22–4:37 | 2:15（135 s） | 08–13 | 281 | 125 wpm | 18 s |
| C | 5:03–7:47 | 4:37–7:04 | 2:27（147 s） | 14–19 | 296 | 121 wpm | 17 s |
| D | 7:47–10:41 | 7:04–9:43 | 2:39（159 s，≤ 3:00） | 20–26 | 324 | 122 wpm | 15 s |
| 合计 | 10:41（641 s） | 0:00–9:43 | **9:43（583 s）** | 26 | 1,189 | 122 wpm | **58 s** |

- 语速目标约 125 wpm，比旧稿（135）慢，给专家读证据留时间。有静默卡（段首页、章节卡）的场景扣除 1.2 s 再算。
- 节省的 58 s 不填回旁白：一部分用于“数字出现后停 ≥ 1.5 s”，其余作排练余量。
- 新时间检查点：A 结束 2:22，B 结束 4:37，C 结束 7:04，D 结束 9:43（D 段实测超过 2:55 即按 `video_plan.md` 10.4 节的思路砍 D，场景号需换成新编号）。

### 4.6 内容更正

| # | 场景（新） | 问题 | 更正 | 依据 |
|---|---|---|---|---|
| 1 | 10 | 旧旁白 “519 of them have diabetes” 像是一个发现；其实按定义就成立 | 旁白明说：上围栏（6.8 %）在 6.5 % 诊断阈值之上，所以 519 个高端值按定义就是糖尿病值；另 23 个是低端值。标题改为 “Outlier handling” | `iqr_fence.json`：fence 6.8，flagged_pos 定义为 HbA1c ≥ 6.5；`hist_geometry.json`：a1c_flagged_high 519，a1c_flagged_low 23 |
| 2 | 18 | 需核对树的分支标签 | **一致，保留。** `tree.json` 中根节点 DIQ070_2.0 > 0.5 的分支注为 answer “no”，其下第二层是 DID040（age at diabetes diagnosis）；图上 age 节点画在 “no” 分支上，与数据一致。旁白改为 “one branch then splits on age at diagnosis”，不暗示先后 | `tree.json` groups.nodes.tree[1]；`s19_tree_and_50.html` 第 52–69 行 |
| 3 | 23 | 未确诊人群上的 +0.019 容易被读成确定的改进 | 旁白与图注都写 inconclusive：下限 0.004 落在 ±0.01 带内。图注 “? inconclusive · lower end inside ±0.01”；旁白 “But the lower end lies inside our margin, so it is inconclusive.” | `care_flip.json`：verdict_escreen inconclusive；note “lower bound 0.004 lies inside the band” |
| 4 | 24 | 旧 25 说 “changed no locked verdict” | 删去。只说 notebook 9.11 节直接支持的内容：“repeats the leakage drop and the inconclusive preparation result”。外部评审的六项问题不上屏、不进旁白 | `holdout.json` note：B3-b、H2b(c) 两个子主张审后撤回；notebook 9.11：M1 − M0 −0.117（supported），S − M1 +0.004 [−0.007, +0.014]（inconclusive） |
| 5 | 02、15、17、20、24 | 旧稿陷阱顺序 2 → 1 → 3，与 notebook 编号对不上 | 统一为 RQ1 Labels → RQ2a Leakage → RQ2b Preparation | notebook 1.5 节 |
| 6 | 01 | 0.961 没说是哪个模型、哪种准备 | 副标题 “One logistic regression on all available columns, all adults”；旁白 “A basic logistic regression …” | `leak_gate.json` auc_m0_eall（naive，Tier 1） |
| 7 | 21 | 41 % 与 17 % 的口径 | 17.0 % 是训练部分未加权的患病率，不能与加权的 14.0 % 混用；41 % 不是对美国成人的风险估计。0.074 只配 “from minimal to systematic”；0.076 不再上屏 | `brier.json`：meanp_s 40.9 %，prevalence 17.0 %，nocw_auc +0.007 |
| 8 | 09、13 | “all 29 were 7.0” 的风险 | 只说 “values of exactly 7.0”：29 个中 28 个是 7.0、1 个是 9.0；被删 ≠ 翻转，只有 6 人翻转 | `blanket_recode.json`：a1c_lost_7_0 28，a1c_lost_9_0 1，flips 6 |
| 9 | 07 | “3 of 6” 的分量 | 旁白说明 6 个是“看到相关数据之前锁定”的假设（17 个中的 6 个）；不能说 “10 of 17 confirmed” | `hypotheses.json`：n_total 17，prior_none 6，prereg_supported 3 |
| 10 | 15 | κ 的念法 | 说 “Cohen's kappa is 0.70”，不说 “70 percent agree” | `label_split.json` kappa_unw 0.70 |
| 11 | 全片 | 底栏章节号 | 5 处改正（旧 03、10、13、15、16），其余从“章”细化到“节” | 2.4 节 |
| 12 | 24 | 留出集的署名 | 署名写 “Robustness checks led by <B>”（B 主持 notebook §9）；旁白不再说 “B's final check”，以免与 notebook 团队表 “D: owner of the hold-out” 冲突（见第 8 节） | notebook “Team and contributions”；`docs/team_roles.md` |

---

## 5 逐场景修改总表

列说明：
- **mm:ss** 为场景起止；
- **部分** 为进度条上的当前段；
- **需重排？** 指拉宽到 1728 px 后是否有元素落进避让区（面板 x ≥ 1296 且 y ≥ 408），或面板内容需要新做；
- **状态**：re-flow = 原图形保留，换网格与界面、改标签、避开避让区；rebuild = 原场景的一部分要重新设计；new = 面板内容全新。

| 新 | 旧 | 讲者 | mm:ss | 部分 | 主标题 | 副标题 | 页面类型 | 关键内容与数字（≤ 3） | 需重排？ | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 | 01 | A | 0:00–0:30 | Problem & data | a Who gets labelled diabetic?<br>b How good is AUC 0.961?<br>c Team and roles | a Basic models as instruments on NHANES 2021–2023<br>b One logistic regression on all available columns, all adults<br>c Four members, their roles, and the sections each presents | 片头卡 → 证据页 → 段首页（团队） | AUC 轴 0.5–1.0，无 coin flip / perfect 标注；0.961 指针（墨色）；四张角色卡 | 是：原 S 半屏刻度移入主区；角色卡不收成徽章 | rebuild |
| 02 | 02 | A | 0:30–0:58 | Problem & data | Overview and agenda | Question, data, design, research questions and the sections of this talk | 议程页 | 3×2 设计矩阵（墨色）；RQ1 / RQ2a / RQ2b；七段路线收缩为进度条 | 是：全新面板 | new |
| 03 | 03 | A | 0:58–1:18 | Problem & data | Cohort and label definition | NHANES 2021–23 (CDC): from participants to the analysis cohort | 证据页 | 11,933 → 5,730（中间三级改为文字标签）；“Positive = self-report **or** HbA1c ≥ 6.5 %”；14.0 % | 是：14.0 % 及数字列收到 x ≤ 1272 | re-flow |
| 04 | 04 | A | 1:18–1:36 | Problem & data | Data governance | Data use agreement, column minimisation, hash-verified files and locked hypotheses | 证据页 | DUA ✓；78 of 175 columns；“hash-verified” / “locked before any results” | 否 | re-flow |
| 05 | 05 | A | 1:36–1:49 | Problem & data | Replication of official estimates | Our weighted prevalence beside NCHS Data Brief 516 | 证据页 | 只留 Total 行：15.79 % vs 15.8 %；“27 estimates”；“max gap 0.044 pp” 改脚注 | 是：表宽 ≤ 1272 | re-flow |
| 06 | 06 | A | 1:49–2:09 | Problem & data | Confounding check: insurance gap | Diabetes prevalence, insured vs uninsured, crude and age-standardised | 证据页；署名 Analysis by <C> | +5.3 pp → +0.7 pp（原位换值）；“interval includes 0”，区间值入 24 px 脚注；DAG Age → Insurance / Diabetes | 否 | re-flow |
| 07 | 07 | A | 2:09–2:22 | Problem & data | Most unexpected finding | <A> on the pre-registered hypotheses and their verdicts | 反思页 | 3 of 6 supported（6 个方块：3 ✓、3 虚线框 ?）；交接行 | 是：原 S 卡片移入主区并放大 | rebuild |
| 08 | 08 | B | 2:22–2:50 | Data quality | a Data quality<br>b Missing-value codes | a Profiling, missing-value codes and outliers<br>b One global recode of NHANES codes, applied to every column | 段首页 → 证据页 | 57 vs 1,496（按比例两柱）；被划掉的 7.0（推近 ≤ 1.25，不进避让区） | 是：段首页新做；证据图无冲突 | rebuild |
| 09 | 09 | B | 2:50–3:09 | Data quality | Effect on diabetes labels | HbA1c-positive cases hit by the global recode, and label flips | 证据页 | 29 of 721；6 flipped；“Non-obvious finding” 标签 | 是：底部横条与 “flipped to negative” ≤ 1272 | re-flow |
| 10 | 10 | B | 3:09–3:26 | Data quality | Outlier handling | HbA1c values beyond the 1.5 × IQR fences, by diabetes status | 证据页 | 542 flagged；519 高端值（标注 “upper fence 6.8 % > 6.5 % threshold”）；Flag → Review → Keep | 是：三格移到中下，直方图 ≤ 1272 | re-flow |
| 11 | 11 | B | 3:26–3:51 | EDA & preparation | Redundancy and skewness | VIF for weight and BMI; skewness of fasting triglycerides | 章节卡 → 证据页；署名 EDA by <C> | VIF 95.7 / 97.6（参考线 10）；skewness 6.62；变换后只写小字 “≈ 0 after” | 是：两块左右排在主区 | re-flow |
| 12 | 12 + 13 | B | 3:51–4:24 | EDA & preparation | Preparation design | Fourteen evidence-based steps combined into naive, minimal and systematic pipelines | 证据页 | 14 steps，6 个描述性分组；三条泳道 → “same L2 logistic regression · same folds”；“no step reads the label” | 是：合并后重排；一次性 “notebook: M0 · M1 · S” | rebuild |
| 13 | 14 | B | 4:24–4:37 | EDA & preparation | Most unexpected finding | <B> on one routine recode line | 反思页 | 29 erased；“7.0 · diabetic” 红线划掉；交接行 | 是：原 S 卡片移入主区 | rebuild |
| 14 | 15 | C | 4:37–5:01 | Labels & bias | a Labels & bias<br>b Simpson's paradox scan | a Analytical fallacies, label agreement and undiagnosed diabetes<br>b 224 subgroup comparisons checked for sign reversal; a causal DAG | 段首页 → 证据页 | 6 of 224（224 格矩阵改为细条，6 格描边）；DAG Race → BMI → Diabetes，“mediator”；“exploratory” | 是：段首页新做；DAG ≤ 1272 | rebuild |
| 15 | 16 | C | 5:01–5:29 | Labels & bias | Label agreement: self-report vs HbA1c | Cohen's κ, and self-reported diabetics below the HbA1c threshold | 证据页 | κ 0.70；250 of 819；“165 of 250 on insulin or pills” 小号标签 | 是：Venn 与图例分三栏放主区；删 721 | re-flow |
| 16 | 17 | C | 5:29–5:59 | Labels & bias | Undiagnosed diabetes | High HbA1c without diagnosis: insurance gap, and a second evaluation population | 证据页 | 152；+23.2 pp [6.2, 40.1]（“uninsured n = 49” 脚注）；两条人群轨道只写文字 | 是：柱长按同一刻度缩到 ≤ 1272 | rebuild |
| 17 | 18 | C | 5:59–6:27 | Experiments | Data leakage check | Naive vs minimal preparation: same model, post-diagnosis items excluded | 章节卡 → 证据页；署名 Experiment by <D> | 0.961 → 0.828（原位换值）；−0.131 [−0.148, −0.114] “paired”；“✓ correct deterioration” | 是（重）：删 −0.072，三栏收进主区 | re-flow |
| 18 | 19 | C | 6:27–6:50 | Experiments | What the naive model learns | A depth-3 decision tree, and median imputation of age at diagnosis | 证据页；署名 Experiment by <D> | 86 % never asked；imputed 50；叶子淡到 25 %，“no” 分支标签保留 | 是：树放在 x 560–1272 | re-flow |
| 19 | 20 | C | 6:50–7:04 | Experiments | Most unexpected finding | <C> on detection at one cut-off, by diagnosis status | 反思页 | 70 vs 52 per 100（两组点阵）；“specificity 0.80 · rates per 100”；交接行 | 是：原 S 卡片移入主区 | rebuild |
| 20 | 21 | D | 7:04–7:33 | Experiments | a Experiments, results and reflection<br>b Minimal vs systematic preparation | a Minimal vs systematic preparation, then results, robustness and reflection<br>b Paired AUC difference and its CI, against a pre-registered equivalence margin | 段首页 → 证据页；署名 Preparation steps by <B> | +0.008 [0.000, 0.016]；±0.01 margin（越界端点脉冲一次）；“minimum detectable difference 0.011” 脚注 | 是：段首页新做；轴宽 ≤ 1272 | rebuild |
| 21 | 22 | D | 7:33–7:58 | Experiments | Calibration and Brier score | Systematic vs minimal preparation, with and without class weights | 证据页；署名 Class-weight step by <B> | Brier +0.074 ✗；mean predicted risk 41 % vs observed 17 %；无类别权重时 AUC +0.007（小号）；删 +0.076 行 | 是：横条与 ✗ ≤ 1272 | rebuild |
| 22 | 23 | D | 7:58–8:16 | Results & robustness | AUC by evaluation population | Systematic preparation on all adults and on not-yet-diagnosed adults | 章节卡 → 证据页；署名 Population defined by <C> | 0.836 vs 0.781；84 % already diagnosed；图内标注 “spectrum bias”；删 +0.055 | 是：堆叠条 ≤ 1272 | re-flow |
| 23 | 24 | D | 8:16–8:40 | Results & robustness | Ablation: prior-care items | AUC change after removing two 'told by a doctor' items, per population | 证据页 | −0.016（all adults）；+0.019 [0.004, 0.034]（not yet diagnosed）；“? inconclusive · lower end inside ±0.01” | 是：+0.019 及其标签移到 y < 408 或 x ≤ 1272 | re-flow |
| 24 | 25 + 26 | D | 8:40–9:05 | Results & robustness | a Robustness and answers<br>b（同一标题，面板换成回答） | Internal hold-out check, then answers to the three research questions | 证据页 → 议程页（回答版）；署名 Robustness checks led by <B> | 小号 “internal hold-out · 1,146 adults · scored once”；RQ1 / RQ2a ✓ / RQ2b ? 三行答案；better / worse 两行账本 | 是：全新面板 | new |
| 25 | 27 | D | 9:05–9:12 | Reflection | Most unexpected finding | <D> on AUC change from leakage vs from preparation | 反思页 | 0.131（红斜纹）vs 0.008（青）同轴两柱 | 是：原 S 卡片移入主区 | rebuild |
| 26 | 28 | D | 9:12–9:43 | Reflection | a Contributions and reflection<br>b Limits and use of AI<br>c Conclusion<br>d Who gets labelled diabetic? | a Who led which part, and how the parts connect<br>b What this study cannot show, and how generative AI was used<br>c The one message we take from this audit<br>d Basic models as instruments on NHANES 2021–2023 | 收尾页（贡献 → 局限与 AI → 结论 → 片尾卡） | 四张角色卡加成果与贡献链；“152 positives among not-yet-diagnosed adults”；收束句 56 px | 是：四卡总宽 ≤ 1272；结论页新做 | rebuild |

统计：re-flow 12 个（03、04、05、06、09、10、11、15、17、18、22、23）；rebuild 12 个（01、07、08、12、13、14、16、19、20、21、25、26）；new 2 个（02、24）。需要重排的 24 个，不需要的 2 个（04、06）。

**补充说明。**
- **26 的四个阶段**（31 s）：
  - 26a 约 0–8 s：角色卡第 3 行写一项成果。A “Governance · official-estimate replication”；B “Missing-code audit · 14 preparation steps”；C “Label agreement · undiagnosed adults · fairness”；D “Leakage check · experiments and verdicts”。贡献链 “C finds → B implements → D evaluates → C interprets”，A 的外框标 “integrates and checks every number”。
  - 26b 约 8–21 s：局限标签 “One survey cycle”、“Low response”、“152 positives among not-yet-diagnosed adults”、“A data audit, not a screening tool”；GenAI 卡 “GenAI drafted code & text · reviewed by us · no LLM in the pipeline · every number recomputed”。
  - 26c 约 21–29 s：收束句 “The score is not the finding; what it reveals about the data is.”，56 px serif，面板坐标 x 48–1272、y 240–400，念到 “The score” 时用 M12 淡入一次。
  - 26d 最后 2 s：片尾卡，片名 120 px 居中于 y 420–560，七段路线在 y 640–680，组号行 “Group [no.] · Thank you”，底部 24 px “Data: NHANES 2021–2023, CDC/NCHS public files”；全部在 x < 1392 或 y < 632。
- **24 的两个阶段：** 0–约 9 s 面板顶部一行小号 “Internal hold-out · 1,146 adults · scored once: leakage drop repeats; preparation gain inconclusive”；之后三行研究问题按 02 的字号、顺序回到面板，每行下方用 M12 溶解出答案（3.4 节）。

### 5.1 旁白全文

相对 `03_audience.md` 的改动：
- **02：** 研究问题改为 label → leakage → preparation 的顺序；
- **07：** 压到 28 词；
- **10：** 明说 519 按定义成立；
- **15：** 以 “Research question one” 开头；
- **23：** 写明 inconclusive；
- **24：** 删 “B's final check” 与 “same pattern”，改为 9.11 节直接支持的说法，答案顺序改为 RQ1 → RQ2a → RQ2b。

其余场景沿用 `03_audience.md` 的文字。`I'm A` 与 “B”“C's” 等在录制前换成真名。

**01** · A · 0:00–0:30 · 30 s · 59 词 · 118 wpm

> **A**: A basic logistic regression separates adults with and without diabetes at an AUC of 0.961. From survey data alone, that is suspiciously high. I'm A; I led governance and integration. B led data quality and preparation, C exploration, labels and bias, and D modelling and conclusions. We present in that order, and the 0.961 runs through the whole talk.

**02** · A · 0:30–0:58 · 28 s · 56 词 · 120 wpm

> **A**: Our question: who gets labelled diabetic, and what do preparation decisions change? The design: one L2 logistic regression on three preparations of the same data, naive, minimal and systematic, scored on all adults and on adults not yet diagnosed. Our research questions: what does the label measure? Is the high AUC leakage? Does systematic preparation pay?

**03** · A · 0:58–1:18 · 20 s · 41 词 · 123 wpm

> **A**: The data: NHANES 2021 to 2023, the CDC's national health survey. Our cohort is 5,730 non-pregnant adults with an HbA1c result. The label is positive for a self-reported diagnosis, or HbA1c of 6.5 percent or more. Survey-weighted, 14.0 percent are positive.

**04** · A · 1:18–1:36 · 18 s · 38 词 · 127 wpm

> **A**: Governance came first. The NCHS data use agreement forbids re-identification and linkage, so we did neither. We kept 78 of 175 columns, verified every raw file by hash, and locked our hypotheses by hash before running any model.

**05** · A · 1:36–1:49 · 13 s · 26 词 · 120 wpm

> **A**: To check our survey-weighting code, we re-ran NCHS Data Brief 516: total prevalence 15.79 percent against the published 15.8, and all 27 published estimates match closely.

**06** · A · 1:49–2:09 · 20 s · 40 词 · 120 wpm

> **A**: Correct numbers can still mislead. In C's analysis, insured adults show 5.3 points more diabetes than the uninsured. That is confounding by age: the insured are much older. Age-standardised, the gap falls to 0.7 points, and its interval includes zero.

**07** · A · 2:09–2:22 · 13 s · 28 词 · 129 wpm

> **A**: Most unexpected for me: of six hypotheses locked before we saw any related data, only three were supported. Now B asks whether the data deserve the same trust.

**08** · B · 2:22–2:50 · 28 s · 56 词 · 125 wpm（扣除 1.2 s 静默卡，按 26.8 s 计）

> **B**: I'm B; I led data quality and preparation. I profiled before cleaning. NHANES stores 'refused' and 'don't know' as numeric codes such as 7, 9, 77 and 99. The common shortcut sets those values to missing in every column. That catches 57 genuine codes, and destroys 1,496 valid measurements, including HbA1c values of exactly 7.0 percent.

**09** · B · 2:50–3:09 · 19 s · 39 词 · 123 wpm

> **B**: Each 7.0 is above the 6.5 threshold: a diabetes case. The shortcut erased 29 of 721 HbA1c-based positives. Only six changed label; the rest had also self-reported, so the either-or label hid the damage. No summary statistic shows this.

**10** · B · 3:09–3:26 · 17 s · 38 词 · 134 wpm

> **B**: Second, outliers. The 1.5 times IQR rule flags 542 HbA1c values. Its upper fence lies above the diagnostic threshold, so the 519 high values are diabetes by definition: the disease, not errors. We reviewed and kept them all.

**11** · B · 3:26–3:51 · 25 s · 50 词 · 126 wpm（扣除 1.2 s 静默卡，按 23.8 s 计）

> **B**: C's exploration found redundancy and skew. Weight and BMI show severe multicollinearity: variance inflation factors of 95.7 and 97.6. Fasting triglycerides are strongly right-skewed: skewness 6.62. Both matter for a linear model, so the systematic preparation drops weight and applies a Yeo-Johnson transform, which brings the skewness close to zero.

**12** · B · 3:51–4:24 · 33 s · 70 词 · 127 wpm

> **B**: Each finding became a switchable step, fourteen in all, each tied to its evidence, and none reads the label. From them we built three versions of the data. Naive keeps every column. Minimal adds one rule: drop items that exist only after a diagnosis, such as treatment. Systematic adds my other steps, from per-variable recoding to transforms and class weights. All three feed the same model on the same folds.

**13** · B · 4:24–4:37 · 13 s · 28 词 · 129 wpm

> **B**: Most unexpected for me: one routine cleaning line erased 29 diabetic HbA1c results, and the label hid it. But cleaning cannot fix the label itself. C shows why.

**14** · C · 4:37–5:01 · 24 s · 47 词 · 124 wpm（扣除 1.2 s 静默卡，按 22.8 s 计）

> **C**: I'm C; I led exploration, labels and bias. First, a fallacy check: we scanned 224 subgroup comparisons for Simpson's paradox, and six reversed sign. A causal diagram suggests why: BMI lies between race and diabetes, so adjusting for it distorts the comparison. We report this as exploratory.

**15** · C · 5:01–5:29 · 28 s · 57 词 · 122 wpm

> **C**: Research question one: the label. Our label combines two sources, and they agree substantially but far from perfectly: Cohen's kappa is 0.70. Of 819 self-reported diabetics, 250 test below 6.5 percent, and two thirds of those take insulin or pills. Treatment lowers the very marker we label by, so a blood-test-only label would call treated patients healthy.

**16** · C · 5:29–5:59 · 30 s · 62 词 · 124 wpm

> **C**: The other direction: 152 adults have HbA1c of 6.5 or more but no diagnosis. Among adults with high HbA1c, the uninsured are 23.2 percentage points more often undiagnosed, interval 6.2 to 40.1, an association from a small subgroup. So the label also records access to care. That is why we also evaluate on adults not yet diagnosed: the people screening is for.

**17** · C · 5:59–6:27 · 28 s · 55 词 · 123 wpm（扣除 1.2 s 静默卡，按 26.8 s 计）

> **C**: The leakage question, from D's experiments. Naive preparation scores an AUC of 0.961. Minimal preparation removes only the post-diagnosis items: treatment, diagnosis history and prior glucose testing. Same model, same folds: the AUC falls to 0.828, a paired drop of 0.131. A deterioration we wanted: the 0.961 was the label leaking back in, not skill.

**18** · C · 6:27–6:50 · 23 s · 46 词 · 120 wpm

> **C**: D's shallow decision tree shows the mechanism. Its root is a treatment item; one branch then splits on age at diagnosis. But 86 percent were never asked that question, and median imputation filled every blank with 50. So 'age 50' became a code for 'never diagnosed'.

**19** · C · 6:50–7:04 · 14 s · 29 词 · 124 wpm

> **C**: Most unexpected for me: at one shared threshold, the model flags 70 of every 100 diagnosed diabetics, but only 52 of 100 undiagnosed ones. D takes the last question.

**20** · D · 7:04–7:33 · 29 s · 57 词 · 123 wpm（扣除 1.2 s 静默卡，按 27.8 s 计）

> **D**: I'm D; I led modelling and conclusions. Last question: does systematic preparation pay? Same model, minimal against systematic: AUC rises by 0.008, interval 0.000 to 0.016. Our smallest effect of interest, fixed in advance, was 0.01. The interval covers both no gain and a worthwhile one, so the result is inconclusive: underpowered, not evidence of no effect.

**21** · D · 7:33–7:58 · 25 s · 49 词 · 118 wpm

> **D**: One step did harm. From minimal to systematic, the Brier score worsens by 0.074. The cause is B's class weights: the systematic model predicts an average risk of 41 percent where the observed rate is 17. Removing only the class weights restores calibration and leaves AUC 0.007 above minimal.

**22** · D · 7:58–8:16 · 18 s · 35 词 · 125 wpm（扣除 1.2 s 静默卡，按 16.8 s 计）

> **D**: Who does the score serve? On all adults, the systematic model scores 0.836; on adults not yet diagnosed, 0.781. 84 percent of positives were already diagnosed, so the all-adults AUC mostly measures recognition: spectrum bias.

**23** · D · 8:16–8:40 · 24 s · 50 词 · 125 wpm

> **D**: Next, drop two items that mark earlier contact with a doctor. On all adults, AUC falls by 0.016. On adults not yet diagnosed, it rises by 0.019, interval 0.004 to 0.034: consistent with recognition and screening pulling apart. But the lower end lies inside our margin, so it is inconclusive.

**24** · D · 8:40–9:05 · 25 s · 54 词 · 130 wpm

> **D**: An internal hold-out of 1,146 adults, scored once, repeats the leakage drop and the inconclusive preparation result. So, three answers. The label records care as well as disease. The 0.961 was leakage, not skill. Systematic preparation barely moved AUC; its value was valid data kept and an honest test on adults not yet diagnosed.

**25** · D · 9:05–9:12 · 7 s · 14 词 · 120 wpm

> **D**: Most unexpected for me: leakage moved the score far more than careful preparation did.

**26** · D · 9:12–9:43 · 31 s · 65 词 · 126 wpm

> **D**: Four roles, one audit: A's governance, B's preparation, C's labels and bias, my models. Limits: one survey cycle, low response, and only 152 undiagnosed positives; this is a data audit, not a screening tool. Generative AI drafted much of our code and text; we reviewed it and recomputed every number. The score is not the finding; what it reveals about the data is. Thank you.

---

## 6 实施方案

### 6.1 kit 改动

**`video/kit/tokens.css`**
- **删除：** `.kit-rightcol`、`.kit-badges`、`.kit-badge-cell`、`.kit-badge-sec`、`.kit-trapbar`、`.kit-trapcell`、`.kit-trap-rule`、`.kit-lowerthird` 与 `.kit-lt-*`、alpha 模式规则（`.kit-alpha …`）、章卡左侧靛蓝竖线。
- **修改：**
  - `--fs-title: 64px`；新增 `--fs-subtitle: 34px`；
  - `.kit-title-band`：top 96，height 64；
  - `.kit-bottombar`：top 1000，height 28；
  - `.kit-camera`：去掉内边框，改为外侧 1 px 细线（`outline: 1px solid var(--paper-edge)`），固定在 1416, 748；
  - `.kit-chapter`：三行（80 px 部分名、34 px 范围行、28 px 讲者行），不遮小窗与名签。
- **改名：** `.kit-attrib` → `.kit-credit`；`.kit-source` → `.kit-pointer`。
- **新增：** `.kit-progress`、`.kit-progress-seg`、`.kit-progress-fill`、`.kit-subtitle`、`.kit-nametag`、`.kit-blockstart`、`.kit-reflection`。

**`video/kit/kit.js`**
- **`GRID`：** 只保留一种版式：
  - `panel {x:96, y:224, w:1728, h:764}`；
  - `camera {x:1416, y:748, w:384, h:216}`；
  - `nametag {x:1416, y:656, w:384, h:84}`；
  - `keepOut {x:1392, y:632, w:432, h:356}`；
  - `progress`、`title`、`subtitle`、`bottom` 的常量见 2.1 节。
  - 删除 `rightCol` 和按版式分开的 `camera`、`panel`、`titleBand` 表。迁移期 `cfg.layout` 的任何值都按新版式处理。
- **常量：**
  - `SPEAKERS`：`{name, role, owns}`（2.2 节）；
  - `SECTIONS`：七段，`{label, scope, firstScene, lastScene}`（3.1 节）；
  - `TIMELINE`：26 个场景的时长，从一个文件读入（6.4 节），由它算出 `SCENE_START` 与各段起止，进度条填充 = 全局时间的纯函数；
  - 删除 `TRAPS`。
- **`buildChrome(cfg)`：** 参数 `{scene, speaker, title, subtitle, credit, pointer, page}`，`page` 取 `evidence | blockstart | reflection | agenda | closing | card`。依次画进度条、标题、副标题、署名、面板、小窗细边、名签、底栏。删除陷阱条、徽章列、lower-third，以及 alpha 模式的舞台挖洞。
- **`updateChrome(t)`：** 进度条填充与切换；分阶段场景的标题、副标题溶解。
- **`audit()`：**
  - 任何内容进入 `keepOut` 报错（推近按 1.25 倍包围盒计算）；
  - 主标题超过 1728 px、副标题与署名重叠报错；
  - **新增代号检查：** 渲染出的文字含 “§”，或匹配 `\b(M0|M1|E-ALL|E-SCREEN|P\d{2}|B[1-6]|Trap|S7_|S10_)\b` 时报错；白名单只有 12 的 “notebook: M0 · M1 · S”；
  - 一帧里结构靛蓝出现超过一处报错；
  - 删除“标题撞到陷阱条”一项。
- **删除：** `_phases.js` 与 `_d_common.js` 的 `cameraPhase`，场景内不再换版式；`render.mjs --alpha` 保留但不再使用。

**快速迁移：** 原图形包进 `<g transform="scale(0.965)">`，左对齐放进新面板，右端约在面板 x 1181（< 1296），所有场景当天就不进避让区；之后再按第 5 节逐个拉宽。

### 6.2 场景改动分级

| 级 | 场景 | 工作内容 | 风险 | 估时 |
|---|---|---|---|---|
| A 高 | 01、02、24、26 | 01 去掉 S 阶段、片头卡、团队页；02 议程页与路线收缩成进度条（依赖新的进度条 DOM）；24 回答页复用 02 的研究问题行；26 四阶段与片尾路线回中 | 动画依赖新界面 DOM | 各 2–3 h |
| B 中 | 07、08、13、14、19、20、25 | 三个段首页（08a、14a、20a）与四个反思页 | 都是文字卡和已有小图放大，不涉及合成 | 各 45 min |
| C 中 | 12、16、17、21、22 | 12 合并两场；16 两条人群轨道改文字；17 删次级数字并收进主区；21 删 +0.076 行、加 41 % vs 17 %；22 加章节卡、删 +0.055 | 信息密集，容易重叠；审计能抓到 | 各 1–1.5 h |
| D 低 | 03、04、05、06、09、10、11、15、18、23 | 改标签与标题、收到 x ≤ 1272、加脚注；11、18 的小幅删减 | 低 | 各 20–45 min |

**文件编号。** 场景文件按新编号重命名（例如 `s12_preparation_design.html` 合并旧 s12、s13；`s24_robustness_answers.html` 合并旧 s25、s26；旧 s14–s28 依次减一或减二）。用 `git mv` 在一次提交里完成，`video/out/*_last.png` 重新渲染。

### 6.3 合成：每段一次叠加

小窗坐标全片不变，每人又是一条连续录像，所以按段合成：先把本段场景拼接成无声视频，再把这条 take 整段叠上去。不再需要遮罩、`--alpha`、逐场景的 `-ss` 偏移，以及 F / S 坐标表。小窗细边由场景渲染在外侧 1 px，ffmpeg 不需要 `drawbox`。

| 段 | 场景 | 全片起点 | 时长 `$DUR` |
|---|---|---|---|
| A | 01–07 | 0:00 | 142 s |
| B | 08–13 | 2:22 | 135 s |
| C | 14–19 | 4:37 | 147 s |
| D | 20–26 | 7:04 | 159 s |

```bash
# 1) 拼接 B 段场景（s08–s13），无音频
ffmpeg -f concat -safe 0 -i video/out/list_B.txt -c copy video/out/scenes_B.mp4
# 2) 叠上 B 的连续 take：缩放到 384×216，固定在 1416,748
ffmpeg -i video/out/scenes_B.mp4 -ss $OFF_B -t 135 -i B_block_take2.mp4 -filter_complex "\
  [1:v]fps=30,scale=384:216:force_original_aspect_ratio=increase,crop=384:216,setsar=1[cam];\
  [0:v][cam]overlay=x=1416:y=748:eof_action=pass,format=yuv420p[v]" \
  -map "[v]" -map 1:a -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -shortest video/out/block_B.mp4
```

- `$OFF_B` 是 take 中本段开口前的起点。
- 四段再用 concat 合并，最后做响度归一（−16 LUFS）。
- 只重渲染一个场景时，仍可按场景合成（`-ss <场景在 take 中的起点>`），坐标相同。
- `video/render/compose_example.md` 改写为这一种方法。

### 6.4 数据改动

- **`build_data.py` 的命名：** 所有 `_meta.naming` 与 `label` 改为 3.5 节的屏幕名称，场景代码不手改。例如：
  - “Naive (M0)” → “Naive”；
  - “Screening group” → “Not-yet-diagnosed adults”；
  - `prep_band.json` d_auc 标签 “Systematic (S) − Minimal (M1)” → “Systematic − Minimal”；
  - `holdout.json` timeline 改为 “internal hold-out · scored once”。
- **新增显示项（只是格式，不是新数字）：**
  - `brier.json`：meanp_s 与 prevalence 的整数显示 “41 %”“17 %”，与旁白念法一致；
  - `label_split.json`：masked_med / masked 的派生项 “165 of 250”（旁白念 “two thirds”，66 %）；
  - `iqr_fence.json`：注明 a1c_flagged_high 519、a1c_flagged_low 23（取自 `hist_geometry.json`）。
- **新文件 `video/data/timeline.json`：** 26 个场景的编号、文件名、讲者、时长、所属段，供 kit 计算进度条与 `SCENE_START`；录像后按实测时长回填。
- **仓库外文档：** `notebooks/final/team.json` 的 `video_segment` 与 `docs/team_roles.md` §5 改为 A 0:00–2:22、B 2:22–4:37、C 4:37–7:04、D 7:04–9:43。notebook 团队表目前写的是 “0:30–2:40, plus opening and closing” 一类旧值（交 main 处理）。
- **不需要新算的数字。** 所有上屏数字都已在 `video/data/*.json` 中。

### 6.5 顺序、工作量与风险

| 步 | 内容 | 估时 | 风险 |
|---|---|---|---|
| 1 | kit：网格、进度条、名签、署名、指引、审计；快速迁移（scale 0.965）；`timeline.json` | 5 h | 低：集中在一处；所有 `layout` 按新版式兜底 |
| 2 | 数据命名与显示项；场景文件重命名与合并 | 1.5 h | 低 |
| 3 | A 级：01、02、24、26 | 10 h | **高**：依赖新界面 DOM，进度条收缩与回中的动画最易出错 |
| 4 | B 级：段首页与反思页 | 5 h | 中 |
| 5 | C 级：12、16、17、21、22 | 6 h | 中：密集场景的重叠 |
| 6 | D 级：其余 10 个场景 | 5 h | 低 |
| 7 | 合成说明改写；按段合成试跑 | 1 h | 很低 |
| 8 | 录像后对 cue、回填 `timeline.json`、全量渲染 | 3 h | 中：取决于录像时间 |

合计约 36 h，约 4.5 人日。截止 10/18，今天 10/14，所以 3–6 步需要并行（vscene-1/2/3 各领一组）。

**主要风险。**
- 时间不够：先保 A 级与审计全绿；D 级场景必要时只做快速迁移加改标签。
- 进度条依赖全局时间：录像后场景时长会变，必须从 `timeline.json` 读，不能写死。
- 名签与段首页的真名：未提供前一律用 `Member A–D`，录制前统一替换。
- 小窗里人脸较小：录制时胸像构图、浅色背景、同侧主光（`video_plan.md` 6.3 第 5 条）。

### 6.6 `docs/video_plan.md` 中作废的部分

本文不改 `video_plan.md`，只列出被取代的部分。

| 节 | 作废内容 | 取代于 |
|---|---|---|
| §0 一页摘要 | 时长、段落时间、布局描述 | 本文第 0 节 |
| §1 目标与约束 | 段落时间 A 0:00–2:30 等 | 4.5 节 |
| §2.2 三个陷阱 | 陷阱名称、编号与图标 | 3.4 节（RQ1 / RQ2a / RQ2b） |
| §2.6 衔接 | 章卡与切点 | 3.1、3.3 节 |
| §3 时间轴总表 | 全部 | 第 5 节总表与 4.5 节 |
| §4 逐场景分镜与台词 | “版式”“屏幕文字”“旁白”“衔接”字段，以及章卡和署名标签 | 第 5 节；re-flow 场景的“构建”步骤与数字出处仍有效 |
| §6.2 视觉识别 | “网格与固定元素”（右栏、陷阱条、署名标签、底栏来源标签、lower-third）、图例条文字、讲者徽章规则 | 第 2 节；颜色角色表仍有效 |
| §6.3 讲者版式 | F / R / X / S 全部与切换规则 1–4 | 2.1–2.3 节；第 5 条（人像构图）仍有效 |
| §6.4 动效语汇 | “场景”列的编号；M12 的章卡场景；M9 推近依赖的 X 版式 | 按新编号；推近在面板内完成，不进避让区 |
| §6.5 层次与装饰 | 章卡描述（编号与讲者徽章） | 3.3 节 |
| §6.6 命名表 | 全部 | 3.5 节 |
| §7 签名视觉清单 | 视觉 1 “Three traps”；视觉 12 收成徽章的部分；全部场景号 | 4.3 节、3.4 节；第 5 节 |
| §8.3 步骤 7 | 右栏留空、按 EDL 逐场景贴入 | 6.3 节 |
| §8.5 已制作的动画场景 | 场景清单、`--alpha` 渲染、“从录像到成片”第 3 步、已知待办中的 S 版式图例与换版式工具 | 6.1–6.3 节 |
| §9.3 自我介绍、署名与交接 | 旧旁白里的句子 | 5.1 节 |
| §9.4 措辞边界 | 留出集一行的 “kept the pattern”，以及旧 25 的 “changed no locked verdict” | 4.6 节第 4 条 |
| §10.2 时间检查点；§10.4 超时砍减顺序 | 时刻与场景号 | 4.5 节（砍减表需按新编号重排） |
| §12.6 删除而不使用的数字 | 需补上：−0.072、+0.055、+0.076、0.044 pp、88 / 46 / 42、7,809 / 6,064 / 5,767（改为文字）、Diagnosed / Undiagnosed 两行、六项外部评审 | 第 5 节 |
| §13.1 评分覆盖 | 场景号 | 4.2 节 |
| §14 第 2、4 项 | 旧段落时间；“D 讲 B 的稳健性核查（25）” | 4.5 节；第 8 节第 2 项 |

---

## 7 合并决定

| # | 冲突 | 来源 | 决定 | 理由 |
|---|---|---|---|---|
| 1 | 进度条按讲者分 4 段，还是按汇报分 7 段 | 01 §3.1 四段；02 §2.2 七段 | **七段**，段名照 02 | 协调者裁定；七段对应报告结构，讲者身份由名签与段首页承担 |
| 2 | “Part n of 4 / of 7” 编号 | 01 §3.2 章卡；02 §2.5 章卡与段首页 | **全部取消**，进度条段名也不加序号 | 协调者裁定；两套编号会混淆，段名已足够 |
| 3 | 段首卡写什么 | 01 “Part 2 of 4 · <role> · Presented by”；02 段首页 | “Presented by <Name> · <role>” 加本段覆盖的部分名 | 协调者裁定 |
| 4 | 场景数与时长 | 01、02 按 28 场；03 合并为 26 场 | **26 场**，时长照 03（A 2:22、B 2:15、C 2:27、D 2:39，共 9:43） | 协调者裁定；合并场景用 02 §3.2 的标题 |
| 5 | 研究问题顺序 | 02 RQ1 → RQ2a → RQ2b；03 新 02 旁白 leakage → label → preparation，不编号 | **RQ1 Labels → RQ2a Leakage → RQ2b Preparation**；03 的议程旁白重写为此顺序（56 词 / 28 s） | 协调者裁定；与 notebook 编号和揭示顺序（C：标签 → 泄漏；D：准备）一致 |
| 6 | 版式时间轴 | 01 假设时长不变 | 版式规则用于全部 26 场；时长照 03 | 协调者裁定 |
| 7 | 底栏指引 | 02 每场一行 “Notebook section N.M”；03 “Notebook: Section 7, leakage test”，只放证据场景，左侧 | **右端一行 “Notebook section N.M”**；证据页与反思页显示，段首页、章节卡、片头片尾不显示 | 协调者裁定格式；不带标题文字，避免带出代号 |
| 8 | 章节号错误 | 02 发现 4 处（旧 10、13、15、16） | 全部按最终 notebook 标题核对；确认这 4 处，另改旧 03 的 “§2”，共 5 处；“§7”“§10” 等细化到节 | 2.4 节 |
| 9 | 避让区坐标 | 01 x 1392–1824、y 632–988；02 x 1456–1824、y 716–988（较早的小窗尺寸） | 照 01 | 01 是按已定小窗（384×216 + 名签）计算的 |
| 10 | 段首页时长 | 02 沿用旧 F 段 13.2 s；03 的自我介绍只有一句 | 1.2 s 静默 + 自我介绍句（约 5–6 s），之后溶解成证据页 | 新旁白没有 12 s 的自我介绍 |
| 11 | 章卡位置 | 旧稿 02、08、15、16、18、21；03 的时长按 02、08、14、15、17、20 有卡计算；02 改为 11、18、23 + 段首页 | 章节卡在 11、17、22；段首页（含 1.2 s 静默）在 08、14、20；02、15 无卡 | 进度条每段一个开头标识；02、15 去卡后时长不变，语速降到 120、122 wpm |
| 12 | 第 7 段的开头 | 02：25（旧 27）只有 7 s，不设章卡 | 不设章卡，进度条在 25 开头直接切换 | 7 s 里加 1.2 s 卡会把语速推到 145 wpm |
| 13 | 靛蓝的使用 | 02 段首页有 4×120 px 靛蓝竖线；旧角色卡用靛蓝细线 | 只留进度条填充线；卡片焦点改用 2 px 墨色描边 | 视觉系统规则“一帧靛蓝只出现一处” |
| 14 | 未确诊人群的名称 | 02 “Not-yet-diagnosed adults”；03 “Not yet diagnosed” | 屏幕 “Not-yet-diagnosed adults”，旁白 “adults not yet diagnosed” | 屏幕上是名词短语，旁白自然 |
| 15 | 步骤卡 | 02 保留 14 张卡，只写描述；03 改为 6 个描述性分组 | 6 个分组（与 notebook 6.3–6.8 的 B1–B6 对应），不带编号 | 合并场景只有 33 s；分组名都是描述性的 |
| 16 | 代号对照 | 02 首次出现处注 “notebook: M0”；03 只在新 12 注一次 | 只在 12 注一次 “notebook: M0 · M1 · S”，其余放 YouTube 说明 | 审计白名单只需一处 |
| 17 | 01 的 AUC 刻度 | 02 保留 “coin flip / perfect”；03 删除 | 删除；轴仍从 0.5 起并标 “axis starts at 0.5” | 专家已知 AUC；03 的取舍 |
| 18 | 场景 10 旁白 | 03 “519 … lie above the diabetes threshold itself” | 改为明说“按定义”：上围栏 6.8 % 高于 6.5 % 阈值 | 协调者指出；`hist_geometry.json` 证实 519 = 高端被标记数 |
| 19 | 场景 23 结论 | 03 “Consistent …; not settled” | 旁白与图注都写 “inconclusive”，说明下限落在 margin 内 | 协调者指出；`care_flip.json` verdict_escreen |
| 20 | 场景 24 留出集一句 | 03 “B's final check agrees … showed the same pattern” | “An internal hold-out of 1,146 adults, scored once, repeats the leakage drop and the inconclusive preparation result.” | 协调者：不得暗示“没有锁定结论改变”；notebook 9.11 节只支持这两点；ADA-lite 的差值在留出集上没有复现 |
| 21 | 场景 24 署名 | 旧稿 “checks: B · §9”；03 旁白 “B's final check” | 署名 “Robustness checks led by <B>”，旁白不点名 | B 主持 §9，但 notebook 团队表写 D 是留出集负责人；待确认（第 8 节） |
| 22 | 场景 18 的分支标签 | 03 怀疑 “no” 分支有误 | 核对后一致，保留 | `tree.json` |
| 23 | 片尾数据来源 | 01 §3.3 与 02 §4.3 都要求片尾交代一次 | 03 副标题一次，05 副标题写 NCHS Data Brief 516，片尾卡一行 | 两份一致 |
| 24 | 合成方法 | 旧稿逐场景 `-ss` + `--alpha` | 每段一次 overlay | 01 §7.3；小窗坐标全片不变 |

---

## 8 待确认

1. **真名与组号。** 名签、段首页、角色卡、片头片尾卡和旁白里的 `<A>`–`<D>`、`[no.]`。在提供之前，渲染用 `Member A–D`。
2. **留出集的归属。** notebook “Team and contributions” 表写 D 是 “owner of the hold-out”；`docs/team_roles.md` 写 B 负责 §9 并“与 D 配合实现留出集”；旧稿写 “B's checks”。本文暂用署名 “Robustness checks led by <B>”，旁白不点名。请 B、D 确认措辞。
3. **底栏指引是否保留。** 本文保留 “Notebook section N.M”。如果希望画面更干净，可以整行删除，把 2.4 节的表放进 YouTube 说明；版面不受影响。
4. **树的 “no” 分支。** 标签与 `tree.json` 一致，保留。另一个事实可供参考：训练部分 4,584 行中有 4,044 行走 “no” 分支，其中 3,766 行是非糖尿病者；按叶子计数推断，从未被问到服药问题的人在 naive 准备中也落在这一侧。是否把标签改为 “no / not asked”，请 C、D 先在 notebook 中核实再决定；不改也不算错。
5. **节省的 58 s。** 本文建议用于读数停顿和排练余量，不填回旁白。是否同意？
6. **场景文件重命名。** 本文建议用 `git mv` 一次改为新编号，好处是文件号与本文一致，代价是一次大的重命名提交。也可以保留旧文件名，只在 `timeline.json` 里映射。
7. **代号对照上屏。** 12 的 24 px “notebook: M0 · M1 · S” 是全片唯一上屏的内部代号，用来帮讲师对照 notebook。是否保留？
8. **A 的段首。** A 没有单独的段首页，由片头卡第三行和团队页承担。若希望四人一致，可在 01 团队页后加约 5 s 的段首页，A 段会变成 2:27，全片 9:48。
9. **同步仓库文档。** `team.json` 的 `video_segment`、`docs/team_roles.md` §5、notebook 团队表的 “Video” 列都要改为新时间。这一步交 main 处理。
10. **`video_plan.md` 的处理。** 本文只列出作废部分（6.6 节）。是在 `video_plan.md` 顶部加一行指向本文，还是改写相应各节，需要决定。
