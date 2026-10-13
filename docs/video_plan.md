# CA6003 讲解视频方案

本文是视频唯一有效的方案（2026-10-14，第三版）。它合并了四份 v3 设计稿（故事与旁白、标题与屏幕文字、视觉系统、内容与画面配对）和用户第二轮反馈，并保留旧方案中仍然有效的录制、字幕、排练与检查部分。旧版本在 git 历史中可查。

**语言。** 旁白、屏幕文字、主副标题和字幕用英文，其余用中文。

**人名记号。** 旁白与屏幕文字一律用人名记号（规则见第 7 节）：

| 记号 | 含义 | `notebooks/final/team.json` |
|---|---|---|
| `<Name>` | 本场景的讲者 | 本段讲者的 `members[i].name` |
| `<Name:0>` | 治理与集成成员 | `members[0].name` |
| `<Name:1>` | 数据质量与准备成员 | `members[1].name` |
| `<Name:2>` | 探索、标签与偏差成员 | `members[2].name` |
| `<Name:3>` | 建模与结论成员 | `members[3].name` |

---

## 0 摘要

**视频是什么。** 一段 10:15 的项目汇报视频，观众是没看过本项目的课程讲师。四位成员按顺序各讲一段连续录像，讲者只出现在右下角固定小窗里；画面是动画证据图。核心信息（片尾原句）：“The score is not the finding; what it reveals about the data is.”

**结构。** 先像论文摘要一样用 78 s 讲清问题、做法、数据与方法、四条发现（场景 01–03），再用议程页（04）交代分工，然后按报告顺序逐层展开。四条发现是贯穿全片的主线：每条在细讲时口头点名一次，收尾（27）原位回到画面并逐条作答。

```text
第 1 段 <Name:0>  0:00–2:31  01–07  问题 · 项目与方法 · 四条发现 · 团队 · 调查设计与权重 · 治理约束 · 意外发现
第 2 段 <Name:1>  2:31–5:01  08–14  缺失值代码（非显然发现）· 对标签的影响 · 离群值 · 冗余与偏度 · Simpson 与 DAG · 准备设计 · 意外发现
第 3 段 <Name:2>  5:01–7:30  15–20  混杂 · 标签一致性 · 未确诊者 · 泄漏检查 · 决策树 · 意外发现
第 4 段 <Name:3>  7:30–10:15 21–27  minimal vs systematic · 校准 · 分人群 AUC · prior-care 项 · 留出集 · 意外发现 · 收尾
```

**时间。** 全片 **10:15**（615 s），上限 12:00；27 个场景；旁白 1,339 词；扣除静默卡后平均 132 wpm，单场 128–136 wpm。

| 讲者 | 段落 | 时长 | 场景 | 词数 | 平均语速 |
|---|---|---|---|---|---|
| `<Name:0>` 治理与集成 | 0:00–2:31 | **2:31**（151 s） | 01–07 | 332 | 133 wpm |
| `<Name:1>` 数据质量与准备 | 2:31–5:01 | **2:30**（150 s） | 08–14 | 327 | 132 wpm |
| `<Name:2>` 探索、标签与偏差 | 5:01–7:30 | **2:29**（149 s） | 15–20 | 324 | 132 wpm |
| `<Name:3>` 建模与结论 | 7:30–10:15 | **2:45**（165 s，≤ 3:00） | 21–27 | 356 | 132 wpm |
| 合计 | 0:00–10:15 | **10:15**（615 s） | 27 | 1,339 | 132 wpm |

前三段相差 2 s；第 4 段多 14–16 s，因为它包含全片收尾。

**关键设计决定（详见第 13 节）。**
- **摘要式开场。** 0:51 前讲完问题、项目、数据与方法；1:18 前讲完四条发现。没有悬念钩子页。
- **七段进度条从第 1 秒起常驻：** Overview · Data & governance · Data quality · EDA & preparation · Labels & bias · Experiments · Results & conclusions。
- **标题只写主题。** 主标题是 ≤ 5 词的名词短语，不放数字、问句、冒号、结论或代号；副标题写本页展示什么。屏幕上不给研究问题编号。
- **多张纸的版式。** 左边 1272 宽的主纸面；右栏是与小窗同宽的侧卡，下面接名签和小窗；字幕在舞台上，底边与小窗对齐。六种构图模板（T1–T6）和防空白规则保证右侧永远有内容。
- **语义色真正用起来。** 红斜纹 = 受损或泄漏的数据，青 = systematic preparation，蓝空心方块 = 尚未确诊者，灰实心圆 = 对照基线，靛蓝 = 当前位置。四种语义色在第一分钟内全部出现并配图例。问卷 / 编码表网格母题、双层阴影和面板标题恢复。
- **只讲项目的设计与结果。** 治理只讲与分析和结论有关的部分：调查设计与权重、数据使用协议的约束、标签定义、事先固定的假设。工程与流程琐事一律不上屏、不进旁白。
- **简单转场。** 段内场景之间 0.4 s 溶解；交接时 0.6 s 溶解进段首卡。所有卡片的静默都 ≤ 1.0 s，讲者的第一句就在卡上说，任何位置的无声都不超过约 1.5 s。

---

## 1 目标、受众与约束

**目标。** 一段设计过的项目汇报，不是随意谈话。讲师在第一分钟内知道项目是什么、怎么做、发现了什么，然后跟着四条发现逐层看到证据。每个旁白节拍都有一张恰好表达这一点的图；没有不配旁白的画面，也没有配着无关或静止画面的旁白。

**受众。** 课程讲师：本领域专家，没看过本项目。标准术语（AUC、HbA1c、VIF、calibration、spectrum bias……）可以直接用；项目内部代号不用，改用描述性名称（第 6.7 节）。

**作业硬性规则（课程 brief）。**

| 规则 | 落实 |
|---|---|
| “12-minute (maximum)”，超出部分不计 | 10:15；排练上限 11:00 |
| “all group members must appear and present” | 四人各一段连续录像，各 2:29–2:45；小窗与名签全程可见 |
| “single continuous video” | 提交一个视频文件；每段一次连续录制；含义待讲师确认（第 13.2 节） |
| 治理、剖析、EDA、准备、对 ML 的影响、非显然发现、minimal vs systematic、改进与恶化、偏差、贡献与反思 | 逐项对应见第 12.1 节 |
| “reasoning, evidence, and interpretation rather than code or model accuracy” | 无代码画面；每个 AUC 后接“这说明什么” |
| YouTube 公开链接 + 组号 | 第 10 节 |

**评分（各 25 %）。**

| 准则 | 核心要求 | 主要抓手 |
|---|---|---|
| Appropriateness | 各阶段的技术与可视化恰当 | 每个场景一张证据图（第 4 节） |
| Correctness & Clarity | 技术正确、解释清楚，各成员贡献可分 | 摘要式开场；一人一段；名签；团队页；段首卡；署名行 |
| Data Interpretation | 统计量、分布、关系；冗余、多重共线、偏度、谬误 | 11、12、15、16、17、21、23、24 |
| Novelty & depth | 原创的问题、准备策略和偏差分析；用 basic ML 为数据决定提供证据 | 被删的 7.0；插补出的 50；识别与筛查之分；模型当量具 |

**用户第二轮反馈（全部有约束力）。**

| # | 反馈 | 落实 |
|---|---|---|
| 1 | 标题不写结论或悬念；不放未解释的数字、代号、问句 | 第 6.1 节规则与自检；27 个场景逐条通过 |
| 2 | 议程页不放“设计矩阵”；不放空框或无内容的图 | 04 改为团队页（角色卡 + 段路线）；防空白规则 R8 |
| 3 | 空间平衡，右侧不能大片留空 | 多张纸版式；侧卡永远有内容；R1–R7 |
| 4 | 恢复丢失的设计元素：母题、纸面纵深、语义色、图例时刻 | 第 5 节 |
| 5 | 只讲项目的设计与结果，不讲工程琐事 | 第 2.6 节取舍；第 4 节无此类内容 |
| 6 | 论文摘要式开场 | 01–03 |
| 7 | 内容与画面配合 | 第 4 节每一步构建都绑定一个旁白短语 |
| 8 | 成员时长接近：各约 2:15–2:35，第 4 段 ≤ 3:00；每人一段连续，顺序固定 | 2:31 / 2:30 / 2:29 / 2:45 |
| 9 | 简单统一的转场 | 第 5.10 节 |

**其他约束。**
- 每位成员只出现在自己的一段里；任何一帧只出现一位成员；没有全屏、分屏或合影。
- 内容可以不与作者一致，用来平衡段长并保持故事顺序；讲他人的工作时，旁白点名，副标题行右端显示署名行。
- 语速 125–140 wpm；只在关键揭示后停 0.8–1.5 s；不留超过约 1.5 s 的空白。
- 每个数字都来自 `video/data/*.json` 或已存的结果（第 11 节）。
- 画面是 HTML/SVG 动画场景加讲者小窗，不是幻灯片。只用 basic models，不用 LLM。截止 10/18。

---

## 2 叙事结构

### 2.1 一句话与主线

**一句话。** 谁被标为糖尿病，决定了模型学到什么、漏掉谁；我们把同一个基础模型当作量具，只改数据准备和评估人群，读出每个决定改变了什么。

```text
问题（01）  全国 15.8 % 的成人有糖尿病，4.5 % 未确诊；模型从标签学习，谁算糖尿病由人决定
做法（02）  NHANES 2021–2023，5,730 名成人；基础可解释模型当量具：模型固定，只改准备
发现（03）  ① 常见的缺失值代码捷径删掉有效值（HbA1c 7.0）
            ② 标签记录了就医机会 → 全样本 AUC 主要度量“认出已确诊者”
            ③ naive 模型的 AUC 0.961 是泄漏
            ④ 系统准备只让 AUC 动了 0.008（inconclusive），类别权重损害校准
议程（04）  四人分工与七段路线
展开        Data & governance（05–07）→ Data quality（08–10）→ EDA & preparation（11–14）
            → Labels & bias（15–17）→ Experiments（18–22）→ Results & conclusions（23–27）
回答（27）  四条发现原位回到画面，各配一行答案；局限；GenAI；核心信息
```

### 2.2 摘要式开场（01–04，0:00–1:31）

| 场景 | 时刻 | 摘要要素 | 画面 |
|---|---|---|---|
| 01 | 0:00–0:26 | 问题情境：未确诊糖尿病；谁被标为糖尿病决定模型学什么、漏掉谁 | 片头卡 → 全国患病率分成已确诊与未确诊（蓝）→ 三种标签来源 |
| 02 | 0:26–0:51 | 本项目做什么；数据与方法一眼看清 | 五节点流程：Survey data → Label → Preparation（变）→ Basic model（固定）→ Score change |
| 03 | 0:51–1:18 | 四条主要发现，各至多一个数字 | 四张发现卡依次出现；侧卡逐行建立颜色图例 |
| 04 | 1:18–1:31 | 按报告顺序展开、谁讲哪一段 | 四张角色卡；侧卡是七段路线 |

讲师在 0:51 知道问题、项目、数据与方法，在 1:18 知道全部结论。之后每一页都在展开某一条发现的证据。

### 2.3 展开

六个正文部分按报告顺序走，进度条只往前：

| 部分 | 场景 | 讲到什么 |
|---|---|---|
| Data & governance | 05–07 | 调查设计与权重、官方复现、标签更窄；数据使用协议与“筛查时刻可得”规则；事先固定的假设 |
| Data quality | 08–10 | 先剖析后清洗：缺失值代码捷径删掉有效值（发现 ①）；离群值是病人 |
| EDA & preparation | 11–14 | 冗余、多重共线、偏度；Simpson 与 DAG；三种准备的设计 |
| Labels & bias | 15–17 | 年龄混杂；标签一致性与治疗掩盖；未确诊与就医机会（发现 ②） |
| Experiments | 18–22 | 泄漏检查（发现 ③）与机制；minimal vs systematic（发现 ④）；类别权重损害校准 |
| Results & conclusions | 23–27 | 分人群 AUC（spectrum bias，回扣 ②）；prior-care 项；留出集；收尾 |

### 2.4 四条发现作主线

| 发现 | 摘要（03）中的说法 | 细讲场景 | 口头回扣原句 | 收尾（27）的回答 |
|---|---|---|---|---|
| ① 清洗捷径删掉有效值 | “destroys valid data, including HbA1c results of 7.0 percent” | 08–09（14 反思） | 09：“That is our first finding.” | “A common cleaning shortcut destroys valid diabetes results.” |
| ② 标签记录就医；AUC 度量识别 | “the label partly records access to care, so whole-sample AUC mostly measures recognition” | 16–17（标签）、23–24（AUC） | 17：“our second finding”；23：“as our second finding said” | “The label records care as well as disease, so whole-sample AUC rewards recognition.” |
| ③ 0.961 是泄漏 | “a naive model's AUC of 0.961 is leakage” | 18–19（26 反思） | 18：“and our third finding” | “The 0.961 was leakage.” |
| ④ 系统准备 +0.008 inconclusive；类别权重损害校准 | “moved AUC by only 0.008, inconclusive, and its class weights worsened calibration” | 21–22 | 21：“Our fourth finding in detail” | “careful preparation barely moved AUC; its value was valid data kept, at a cost in calibration.” |

画面上的回扣：03 的四张发现卡在细讲场景的侧卡里以缩小的“发现标签”出现（09、17、18、21、23，以及 14、26），并在 27 原位、同色回到画面。

### 2.5 其他贯穿线

| 线索 | 埋下 | 回收 |
|---|---|---|
| 全国 15.8 % | 01（问题情境） | 05（我们复现 15.79 % vs 15.8 %；我们的标签更窄） |
| “筛查时刻可得”规则 | 06（治理规则） | 13（Minimal 的唯一规则）、18（泄漏检查）、26（一条排除规则 0.131） |
| 保险 | 15（粗差距是年龄混杂） | 17（在高 HbA1c 者中，未参保者更常未确诊：另一种关系） |
| 尚未确诊者（蓝色空心方块） | 01（4.5 % 未确诊） | 17（152 人 → 第二个评估人群）、20（52 of 100）、23–24（0.781；+0.019）、25（留出集只有 25 个阳性） |
| 事先固定的 margin | 07（事先固定的假设） | 21、24（±0.01 判定 inconclusive） |
| 被删的 7.0 | 03 | 08、09、14、27 |
| 虚线框 = exploratory | 06（小群体只作探索） | 12（Simpson）、17（风险差） |

### 2.6 取舍

**删除（工程与流程琐事）。** 文件与列的计数、文件完整性校验、代码与执行结构、构建工具、notebook 运行机制、冻结标签、决策登记条数、外部评审六项、种子与置换检验、规格曲线、按调查单元分组的交叉验证、设计效应、ADA-lite、腰高比、亚裔 BMI、3×3 标签矩阵、缺失机制（逆概率加权、MNAR）、漏斗中间级。

**改写为与分析相关的治理。** 数据使用协议 → 讲它对标签来源与小群体报告的影响（06）；事先锁定的假设 → “locked before we saw any related data, our guard against cherry-picking”（07）；DB516 复现 → 讲它证明加权正确，并解释 14.0 % 与 15.8 % 的差别来自定义（05）。

**已核实但不上屏、不念。** −0.072、+0.055、+0.076、+0.060、0.964 / 0.848 / 0.851 / 0.791（留出集）、27 estimates、0.044 pp、30.5 %、85、11,933 及漏斗中间级、响应率 34.6 % / 25.7 %（只说 “low response”）、调整 OR 2.22、4,911。

**旁白中故意不用的说法。** “oversamples”（2021–23 周期没有过度抽样，notebook 1.10 节）；“70 percent agree”；“all 29 were 7.0”；“independent validation”；“the best screening model”。

### 2.7 诚实表述（不可改）

- +0.008 [0.000, 0.016]：inconclusive，underpowered；不是“没有效果”，也不是“等价”。
- Brier +0.074 只配 “from minimal to systematic”；原因是类别权重；不念 0.076。
- 0.836 vs 0.781：“mostly measures recognition” 加 “spectrum bias”；不说“我们的模型以 0.781 做筛查”。
- +0.019：下端落在 margin 内 → inconclusive。+23.2 pp：association，小样本。Simpson 与 DAG：exploratory。
- 留出集：重现泄漏下降；人群差距同向，但 25 个未确诊阳性不足以单独检验。
- 事先固定的 6 个假设只说 “locked before we saw any related data”；不说 “10 of 17 confirmed”。

### 2.8 分工、署名与交接

| 段 | 讲者 | 自我介绍 | 讲他人工作时的口头署名 | 意外发现 | 交接句 |
|---|---|---|---|---|---|
| 1 | `<Name:0>` | 01 开口第一句 | — | 07：6 个事先固定的假设只有 3 个得到支持 | “Next, `<Name:1>` on the quality of the data.” |
| 2 | `<Name:1>` | 08 | 11、12：“`<Name:2>`'s exploration …”“`<Name:2>` also scanned …” | 14：一步常规清洗删掉 29 个糖尿病 HbA1c 结果，标签把它藏住 | “But cleaning cannot fix the label itself. `<Name:2>` shows why.” |
| 3 | `<Name:2>` | 15 | 18、19：“run by `<Name:3>`”“`<Name:3>`'s shallow decision tree” | 20：同一阈值下 70 of 100 vs 52 of 100 | “`<Name:3>` now asks what systematic preparation adds.” |
| 4 | `<Name:3>` | 21 | 22：“`<Name:1>`'s class weights”；25：“`<Name:1>` led the robustness checks” | 26：一条排除规则 0.131 vs 全部准备 0.008 | —（26 之后是全片收尾 27） |

第 4 段的意外发现放在收尾之前，因为收尾要镜像摘要并以核心信息结束。交接句说完后约 0.3 s，0.6 s 溶解进下一段的段首卡。

---

## 3 时间轴总表

**mm:ss** 为场景起止（由时长求和）；**部分**为进度条当前段；**文件**在 `video/scenes/`，扩展名 `.html`；**模板**见第 5.4 节，“→”表示场景内换阶段。

| 场景 | 文件 | 讲者 | mm:ss | 部分 | 主标题 | 副标题 | 模板 |
|---|---|---|---|---|---|---|---|
| 01 | `s01_problem` | `<Name:0>` | 0:00–0:26 | Overview | Problem and motivation | Diagnosed and undiagnosed diabetes in US adults, and three label sources | T6 片头卡 → T4 |
| 02 | `s02_study_design` | `<Name:0>` | 0:26–0:51 | Overview | Study design | Data, label, three preparations and one fixed basic model | T2 |
| 03 | `s03_main_findings` | `<Name:0>` | 0:51–1:18 | Overview | Main findings | Four findings, each with a small chart of its evidence | T5 |
| 04 | `s04_team_roles` | `<Name:0>` | 1:18–1:31 | Overview | Team and roles | Four members, their roles, and the sections each presents | T5 |
| 05 | `s05_survey_weights` | `<Name:0>` | 1:31–1:53 | Data & governance | Survey design and weights | Unweighted vs weighted prevalence, and a check against official estimates | T1 |
| 06 | `s06_governance` | `<Name:0>` | 1:53–2:17 | Data & governance | Data governance | Data use agreement limits, and which features a model may use | T2 |
| 07 | `s07_reflection_hypotheses` | `<Name:0>` | 2:17–2:31 | Data & governance | Most unexpected finding | `<Name:0>` on the pre-specified hypotheses | T4 |
| 08 | `s08_missing_codes` | `<Name:1>` | 2:31–2:57 | Data quality | Missing-value codes | Numeric codes for 'refused' and 'don't know', recoded in every column | T6 段首卡 → T1 |
| 09 | `s09_label_effect` | `<Name:1>` | 2:57–3:16 | Data quality | Recode effect on diabetes labels | HbA1c-positive adults affected by the recode, and which labels changed | T1 |
| 10 | `s10_outliers` | `<Name:1>` | 3:16–3:34 | Data quality | Outlier handling | HbA1c values beyond the 1.5 × IQR fences, by diabetes status | T1 |
| 11 | `s11_redundancy_skew` | `<Name:1>` | 3:34–4:00 | EDA & preparation | Redundancy and skewness | Collinearity of weight and BMI; skewness of fasting triglycerides | T6 章节卡 → T3 |
| 12 | `s12_simpson_dag` | `<Name:1>` | 4:00–4:18 | EDA & preparation | Simpson's paradox check | Subgroup comparisons checked for sign reversal, and a causal diagram (DAG) | T2 |
| 13 | `s13_preparation_design` | `<Name:1>` | 4:18–4:48 | EDA & preparation | Preparation design | Three preparations of the same data for one logistic regression | T2 |
| 14 | `s14_reflection_recode` | `<Name:1>` | 4:48–5:01 | EDA & preparation | Most unexpected finding | `<Name:1>` on the missing-value recode | T4 |
| 15 | `s15_confounding` | `<Name:2>` | 5:01–5:23 | Labels & bias | Confounding check | Diabetes prevalence by insurance status, crude and age-standardised | T6 段首卡 → T1 |
| 16 | `s16_label_agreement` | `<Name:2>` | 5:23–5:50 | Labels & bias | Label agreement | Self-reported diabetes vs HbA1c ≥ 6.5 %, with treatment status | T1 |
| 17 | `s17_undiagnosed` | `<Name:2>` | 5:50–6:22 | Labels & bias | Undiagnosed diabetes | Adults with high HbA1c but no diagnosis, by insurance status | T1 |
| 18 | `s18_leakage_check` | `<Name:2>` | 6:22–6:53 | Experiments | Leakage check | Naive vs minimal preparation: same model, post-diagnosis items removed | T6 章节卡 → T1 |
| 19 | `s19_tree_and_50` | `<Name:2>` | 6:53–7:16 | Experiments | Decision tree on naive data | A depth-3 tree, and median imputation of age at diagnosis | T1 |
| 20 | `s20_reflection_detection` | `<Name:2>` | 7:16–7:30 | Experiments | Most unexpected finding | `<Name:2>` on detection by diagnosis status | T4 |
| 21 | `s21_prep_band` | `<Name:3>` | 7:30–7:56 | Experiments | Minimal vs systematic preparation | Paired AUC difference and interval, against a pre-specified equivalence margin | T6 段首卡 → T1 |
| 22 | `s22_brier` | `<Name:3>` | 7:56–8:18 | Experiments | Calibration and Brier score | Systematic vs minimal preparation, with and without class weights | T1 |
| 23 | `s23_recognition` | `<Name:3>` | 8:18–8:39 | Results & conclusions | AUC by evaluation population | Systematic preparation on all adults and on not-yet-diagnosed adults | T6 章节卡 → T1 |
| 24 | `s24_prior_care` | `<Name:3>` | 8:39–9:05 | Results & conclusions | Prior-care items | AUC change after removing two 'told by a doctor' items, per population | T1 |
| 25 | `s25_holdout` | `<Name:3>` | 9:05–9:23 | Results & conclusions | Internal hold-out check | Main comparisons repeated once on adults held out from development | T2 |
| 26 | `s26_reflection_leak_vs_prep` | `<Name:3>` | 9:23–9:31 | Results & conclusions | Most unexpected finding | `<Name:3>` on leakage vs preparation effects | T4 |
| 27 | `s27_close` | `<Name:3>` | 9:31–10:15 | Results & conclusions | a Main findings<br>b Limitations and use of AI<br>c Conclusion<br>d Who gets labelled diabetic?（片尾卡） | a Four findings from the opening, each with a one-line answer<br>b Limits of this study, and how generative AI was used<br>c Main message of the study<br>d — | T5 → T5 → T4 → T6 片尾卡 |

**分段与时长核对。**

| 部分 | 场景 | 起止 | 时长 | 讲者 | 开头标识 |
|---|---|---|---|---|---|
| Overview | 01–04 | 0:00–1:31 | 91 s | `<Name:0>` | 片头卡（01） |
| Data & governance | 05–07 | 1:31–2:31 | 60 s | `<Name:0>` | 无卡，05 的 0.4 s 溶解内切换 |
| Data quality | 08–10 | 2:31–3:34 | 63 s | `<Name:1>` | 段首卡（08） |
| EDA & preparation | 11–14 | 3:34–5:01 | 87 s | `<Name:1>` | 章节卡（11） |
| Labels & bias | 15–17 | 5:01–6:22 | 81 s | `<Name:2>` | 段首卡（15） |
| Experiments | 18–22 | 6:22–8:18 | 116 s | `<Name:2>` → `<Name:3>` | 章节卡（18）；段首卡（21）不换段 |
| Results & conclusions | 23–27 | 8:18–10:15 | 117 s | `<Name:3>` | 章节卡（23） |
| 合计 | 27 | 0:00–10:15 | 615 s | — | — |

场景时长：26 + 25 + 27 + 13 + 22 + 24 + 14 = 151（第 1 段）；26 + 19 + 18 + 26 + 18 + 30 + 13 = 150（第 2 段）；22 + 27 + 32 + 31 + 23 + 14 = 149（第 3 段）；26 + 22 + 21 + 26 + 18 + 8 + 44 = 165（第 4 段）；合计 615 s = 10:15。

**静默卡。** 片头卡 1.0 s（01）；段首卡 0.8 s（08、15、21）；章节卡 0.8 s（11、18、23）；片尾卡 1.5 s（27，全片结尾）；共 7.3 s。片头卡、段首卡和章节卡都只静默到讲者开口：讲者的第一句在卡上说，说完才溶解进第一页，所以卡片不会造成超过约 1.5 s 的无声。

---

## 4 逐场景设计

**读法。** 每个场景先列一张属性表，再列构建表：左列是旁白短语，右列是画面在这个短语上发生的变化。数字不早于念出它的词出现。每个场景的前 0.4 s 处在溶解中，不安排动作。“静默”指不配旁白的静默卡；“停顿”指旁白里的 `{pause}`，计入讲话时间。语速 = 词数 ÷（时长 − 静默卡）。坐标都是舞台坐标（1920×1080）；纸面内坐标写“纸面 x/y”。模板、颜色、动效编号见第 5 节。

**发现标签。** 03 的四张发现卡缩成 336×88 的小卡（图标 + “Finding n” + 主题词 + 该卡的色样），放在侧卡底部槽位，用来在细讲场景里回扣摘要。

---

### 4.01 场景 01 · Problem and motivation

| 项 | 内容 |
|---|---|
| 时间 | 0:00–0:26 · 26 s · `<Name:0>` · Overview |
| 主标题 / 副标题 | **Problem and motivation** / Diagnosed and undiagnosed diabetes in US adults, and three label sources |
| 模板 | T6 片头卡（0–1.0 s 静默，停到自我介绍结束）→ 0.4 s 溶解 → T4 |
| 署名 · 底栏 | — · Notebook: Summary |
| 颜色 | 蓝（未确诊段：浅底加描边，空心方块标记）；其余墨色与 `--ink-fill` |
| 数字（来源） | 15.8 %（`db516.json` `total_nchs`）· 4.5 %（`db516.json` `undiagnosed_nchs`） |
| 侧卡 | 面板标题 “Not yet diagnosed”；主数字 **4.5 %**（蓝，104 px）；标签 “of US adults have diabetes without a diagnosis”；出处 24 px “NCHS Data Brief 516”；图例槽：蓝色图例时刻 “□ Not-yet-diagnosed adults” |
| 转场 | 进：第 0 帧即片头卡，不从黑场淡入；自我介绍在片头卡上说完后 0.4 s 溶解进 T4；出：0.4 s 溶解 |
| 处理 | 重建（新场景；取代旧 `s01_hook_team` 的钩子页） |

**片头卡（T6）。** 第 1 行 88 px serif “Who gets labelled diabetic?”；第 2 行 34 px “Diabetes labels, data preparation and leakage in NHANES 2021–2023”；第 3 行 28 px mono 墨色 60 % “CA6003 · Group [no.]”。右栏（1416–1800 × 224–632）按出场顺序列四位讲者：名字 28 px semibold 加职责 24 px。进度条从第 0 帧起显示，Overview 为当前段。全舞台卡片母题。

**主纸面（T4）。** 纸面 x 32–760 是大图：面板标题 “Share of US adults, %”；竖轴 0–20 % 占满纸面 y 76–548；一根宽 200 px 的竖向堆叠柱（纸面 x 180–380），标注写在柱右侧（纸面 x 420–740），所以大图上下左右都被占满。纸面 x 792–1240 是标签来源三行（图标 32 px + 34 px 文字，行距拉开到占满纸面 y 76–548），上方 28 px 面板标题 “The label”。

| 旁白短语 | 画面 |
|---|---|
| （0–1.0 s 静默） | 片头卡 |
| “I'm `<Name>`; I led governance and integration.” | 片头卡停留（右栏四位成员中本讲者一行加粗），字幕照常 |
| “Nationally, 15.8 percent of US adults have diabetes,” | 0.4 s 溶解进 T4；主副标题；竖轴（M1）；柱从 0 生长到 15.8（M2），`--ink-fill`；柱顶标注 “15.8 % have diabetes” |
| “and 4.5 percent have it without a diagnosis.” | 柱顶 4.5 段分裂出来（M6）：蓝色浅底加 2 px 蓝描边，段上一个空心方块；标注 “4.5 % not diagnosed”；下段只标 “diagnosed”（不标数字）；侧卡主数字计数到 4.5 %（M10） |
| {pause 1.0} | 侧卡图例槽出现 “□ Not-yet-diagnosed adults”，2.5 s 后收进底栏 |
| “Screening models learn from a label, and someone decides who counts as diabetic:” | 右侧面板标题 “The label” |
| “a doctor's diagnosis, a blood test, or both.” | 三行依次出现（M13）：问卷板 “Doctor's diagnosis” · 试管 “Blood test (HbA1c)” · 两个图标 “Either one” |
| “That choice shapes what a model learns, and whom it misses.” | 从 “Doctor's diagnosis” 一行到蓝段画一根箭头（M11），标注 “missed by diagnosis-only labels” |

**旁白**（55 词 · 132 wpm · 静默 1.0 s · 停顿 1.0 s）：

> I'm `<Name>`; I led governance and integration. Nationally, 15.8 percent of US adults have diabetes, and 4.5 percent have it without a diagnosis. {pause 1.0} Screening models learn from a label, and someone decides who counts as diabetic: a doctor's diagnosis, a blood test, or both. That choice shapes what a model learns, and whom it misses.

---

### 4.02 场景 02 · Study design

| 项 | 内容 |
|---|---|
| 时间 | 0:26–0:51 · 25 s · `<Name:0>` · Overview |
| 主标题 / 副标题 | **Study design** / Data, label, three preparations and one fixed basic model |
| 模板 | T2：宽幅纸面放五节点流程；下条纸面放问题与“固定 / 变化”两行 |
| 署名 · 底栏 | — · Notebook: Summary · section 1.2 |
| 颜色 | 红斜纹、灰、青只出现在 Preparation 节点的三个小色样上（各自的首次出现，色样旁直接写名称）；其余墨色 |
| 数字（来源） | 5,730（`funnel.json` `n_cohort`）；6.5 % 是定义值（`funnel.json` `a1c_cut`） |
| 侧栏 | 宽幅纸面的右段（1416–1800）是第 5 个节点 “Score change” |
| 转场 | 进：0.4 s 溶解；出：0.4 s 溶解 |
| 处理 | 重建（取代旧 `s02_agenda` 与其空设计矩阵） |

**宽幅纸面。** 五个节点各宽 300，节点间距 36，从纸面 x 32 到 1648。节点不画框，上方一条 2 px 墨色标题线，标题线文字 28 px semibold。节点之间是墨色箭头。

| 节点 | 标题线文字 | 内容 |
|---|---|---|
| N1 | Survey data | “NHANES 2021–2023 (CDC)” / mono 56 px **5,730** / “adults” |
| N2 | Label | 问卷板 + 试管图标 / “told by a doctor or HbA1c ≥ 6.5 %” |
| N3 | Preparation · changes | 三个小色样：▨ Naive · ● Minimal · ■ Systematic |
| N4 | Basic model · fixed | S 形曲线小图 “L2 logistic regression” / 小树图 “depth-3 decision tree” |
| N5 | Score change | 差值小轴（零线 + 一个偏离零线的点）/ “what each decision did” |

**下条纸面。** 第 1 行 “Question  Who gets labelled diabetic, and what do preparation choices change?”（栏目名 28 px 墨色 60 %，内容 34 px）；第 2 行 “Fixed: model and folds · Changes: preparation only”。

| 旁白短语 | 画面 |
|---|---|
| “We audit that label,” | 宽幅纸面面板标题；N2 出现在最终位置（M13） |
| “and ask what data-preparation decisions change in a model trained on it.” | 下条第 1 行 Question |
| “The data: NHANES 2021 to 2023, a national CDC survey; 5,730 adults.” | N1 出现，5,730 计数（M10）；N1 → N2 箭头 |
| “The method: basic, interpretable models as measuring instruments.” | N4 出现（两个小图） |
| “The model stays fixed,” | N4 标题线后缀 “fixed” 加粗 |
| “the preparation changes, from naive to systematic,” | N3 的三个色样依次出现（M13），各带名称 Naive · Minimal · Systematic：这是红、灰、青的图例时刻；N2 → N3 → N4 箭头 |
| “and the score shift shows what each decision did.” | N5 出现在右段；N4 → N5 箭头；下条第 2 行 |

**旁白**（56 词 · 134 wpm · 停顿无）：

> We audit that label, and ask what data-preparation decisions change in a model trained on it. The data: NHANES 2021 to 2023, a national CDC survey; 5,730 adults. The method: basic, interpretable models as measuring instruments. The model stays fixed, the preparation changes, from naive to systematic, and the score shift shows what each decision did.

---

### 4.03 场景 03 · Main findings

| 项 | 内容 |
|---|---|
| 时间 | 0:51–1:18 · 27 s · `<Name:0>` · Overview |
| 主标题 / 副标题 | **Main findings** / Four findings, each with a small chart of its evidence |
| 模板 | T5：主纸面内 1×4 发现卡（每张 284×516，间距 24）；侧卡是颜色图例 |
| 署名 · 底栏 | — · Notebook: Summary |
| 颜色 | 四种语义色全部出现（摘要页例外，第 5.6 节）：红斜纹（卡 1 被划掉的 7.0、卡 3 的 0.961 柱）；灰圆与蓝方（卡 2）；青点（卡 4） |
| 数字（来源） | 7.0 %（定义常量：与代码 7 重合的真实 HbA1c 值；被删 28 个见 `blanket_recode.json` `a1c_lost_7_0`）· 0.961（`leak_gate.json` `auc_m0_eall`）· +0.008（`prep_band.json` `d_auc`） |
| 侧卡 | 面板标题 “Colour key”；四行图例（32 px 色样 + 28 px 文字），随对应的卡逐行出现：“▨ Harmed or leaked data” · “● Reference baseline” · “□ Not-yet-diagnosed adults” · “■ Systematic preparation” |
| 转场 | 进：0.4 s 溶解；出：0.4 s 溶解 |
| 处理 | 新建。四张卡的小图写成可缩放的共用组件，27 原位复用 |

**发现卡（每张从上到下）。** 图标 40 px 加主题词 28 px semibold；小图约 236×200；结论行 ≤ 8 词（34 px，≤ 2 行）。

| 卡 | 图标 · 主题词 | 小图 | 结论行 |
|---|---|---|---|
| 1 | 试管 · Data quality | 一个 HbA1c 单元格 “7.0” 被红线划掉，浅红底斜纹 | Cleaning shortcut destroys valid HbA1c results |
| 2 | 尺子 · Labels | AUC 小轴：灰圆在上、蓝方在下，不标数字 | AUC mostly measures recognition |
| 3 | 漏水桶 · Leakage | AUC 小轴 0.5–1.0（标 “axis starts at 0.5”）；红斜纹柱到 0.961，数字红色 56 px | 0.961 is leakage, not skill |
| 4 | 天平 · Preparation | 差值小轴：中性灰带 ±0.01，青点 +0.008 带晶须；旁边虚线框 “?” 与 “calibration ✗” | Small gain, inconclusive; calibration worse |

| 旁白短语 | 画面 |
|---|---|
| “Four findings.” | 四张卡的图标与主题词作为一个对象出现（M12 0.4 s） |
| “First, a common shortcut for missing-value codes destroys valid data,” | 卡 1 小图：7.0 单元格被红线划掉（M7 红）；侧卡第 1 行 “▨ Harmed or leaked data” |
| “including HbA1c results of 7.0 percent: diabetes cases.” | 卡 1 结论行 |
| “Second, the label partly records access to care,” | 卡 2 小图：灰圆、蓝方；侧卡第 2、3 行 |
| “so whole-sample AUC mostly measures recognition of known patients.” | 卡 2 结论行 |
| “Third, a naive model's AUC of 0.961 is leakage.” | 卡 3 小图：红斜纹柱生长（M2），数字 0.961；结论行 |
| “Fourth, systematic preparation moved AUC by only 0.008,” | 卡 4 小图：灰带、青点、晶须；侧卡第 4 行 “■ Systematic preparation” |
| “inconclusive, and its class weights worsened calibration.” | 卡 4 的 “?” 虚线框与 “calibration ✗”；结论行 |
| {pause 1.0} | 静止；末帧就是完整摘要 |

**旁白**（61 词 · 136 wpm · 停顿 1.0 s）：

> Four findings. First, a common shortcut for missing-value codes destroys valid data, including HbA1c results of 7.0 percent: diabetes cases. Second, the label partly records access to care, so whole-sample AUC mostly measures recognition of known patients. Third, a naive model's AUC of 0.961 is leakage. Fourth, systematic preparation moved AUC by only 0.008, inconclusive, and its class weights worsened calibration. {pause 1.0}

---

### 4.04 场景 04 · Team and roles

| 项 | 内容 |
|---|---|
| 时间 | 1:18–1:31 · 13 s · `<Name:0>` · Overview |
| 主标题 / 副标题 | **Team and roles** / Four members, their roles, and the sections each presents |
| 模板 | T5：主纸面内 2×2 角色卡（每张 592×262）；侧卡是七段路线 |
| 署名 · 底栏 | — · Notebook: Team and contributions |
| 颜色 | 墨色；侧卡路线里当前段 Overview 用靛蓝 4 px 左线 |
| 数字 | 无 |
| 侧卡 | 面板标题 “Sections”；七段竖排（28 px），每段右侧在念到讲者时出现该讲者名（24 px 墨色 60 %） |
| 转场 | 进：0.4 s 溶解；出：0.4 s 溶解（进度条在溶解中切到 Data & governance） |
| 处理 | 改编旧 `s01_hook_team` 的团队卡部分：去掉钩子，卡片改 2×2 铺满主纸面 |

**角色卡（每张四行）。** 名字 40 px serif；职责 28 px；“Presents: <段名> · <段名>” 28 px 墨色 60 %；一项成果 28 px。

| 卡 | 名字 | 职责 | Presents | 成果 |
|---|---|---|---|---|
| 1 | `<Name:0>` | Governance & integration | Overview · Data & governance | Governance · official-estimate check |
| 2 | `<Name:1>` | Data quality & preparation | Data quality · EDA & preparation | Missing-code audit · preparation design |
| 3 | `<Name:2>` | Exploration, labels & bias | Labels & bias · Experiments | Label agreement · undiagnosed adults |
| 4 | `<Name:3>` | Modelling & conclusions | Experiments · Results & conclusions | Leakage check · experiments and conclusions |

| 旁白短语 | 画面 |
|---|---|
| “We expand this in report order:” | 侧卡七段路线作为一个对象出现（M12），Overview 为当前段 |
| “I cover the data and governance;” | 卡 1（M13）；路线 Overview、Data & governance 旁出现 `<Name:0>` |
| “then `<Name:1>`, data quality and preparation;” | 卡 2；路线 Data quality、EDA & preparation 旁出现 `<Name:1>` |
| “`<Name:2>`, labels and bias;” | 卡 3；路线 Labels & bias、Experiments 旁出现 `<Name:2>` |
| “and `<Name:3>`, the experiments and results.” | 卡 4；路线 Experiments、Results & conclusions 旁出现 `<Name:3>` |

**旁白**（28 词 · 129 wpm · 停顿无）：

> We expand this in report order: I cover the data and governance; then `<Name:1>`, data quality and preparation; `<Name:2>`, labels and bias; and `<Name:3>`, the experiments and results.

---

### 4.05 场景 05 · Survey design and weights

| 项 | 内容 |
|---|---|
| 时间 | 1:31–1:53 · 22 s · `<Name:0>` · Data & governance |
| 主标题 / 副标题 | **Survey design and weights** / Unweighted vs weighted prevalence, and a check against official estimates |
| 模板 | T1 |
| 署名 · 底栏 | — · Notebook sections 4.3, 4.4, 9.8.2 |
| 颜色 | 灰（加权后的估计、我们的复现值：浅灰底加 2 px 灰描边，实心圆标记）；墨色（未加权：白底墨描边；官方公布值：墨色空心环） |
| 数字（来源） | 16.9 % / 14.0 %（`funnel.json` `prev_unw` / `prev_w`）· 15.79 % vs 15.8 %（`db516.json` `total_ours` / `total_nchs`）· 5,730 只在面板标题里（`funnel.json` `n_cohort`） |
| 侧卡 | 面板标题 “Official check”；主数字 **15.79 %**（灰，88 px）；标签 “ours, vs 15.8 % published”；判定槽 “✓ weighting checks out” |
| 转场 | 进：0.4 s 溶解（进度条切到 Data & governance）；出：0.4 s 溶解 |
| 处理 | 重建：复现部分借用旧 `s05_nchs_replication` 的数据与刻度；权重两柱新做。旧漏斗不再使用 |

**主纸面。** 左区（纸面 x 32–560）：面板标题 “Diabetes prevalence, 5,730 adults”；两根竖柱共用 0–20 % 轴，从 0 起。右区（纸面 x 600–1240）：面板标题 “Total diabetes, %”；横轴 0–20 %；两行：“NCHS definition”（墨色空心环 15.8，我们的灰点 15.79 落在环内）、“Our label”（灰色标记 14.0），两行之间一个括号标注 “no fasting-glucose criterion”。

| 旁白短语 | 画面 |
|---|---|
| “First, the data. Our 5,730 adults are a clustered sample,” | 左区面板标题与轴（M1） |
| “older than the population, so estimates need survey weights:” | 左区上方标注 “sample older than the population” |
| “unweighted, 16.9 percent are positive;” | “unweighted” 柱生长（M2），数字 16.9 % |
| “weighted, 14.0.” | “weighted” 柱生长，灰色，数字 14.0 % |
| {pause 1.0} | 静止 |
| “Re-running the official NCHS brief tests our weighting:” | 右区轴与墨色空心环 15.8（“published”）；侧卡面板标题 |
| “15.79 percent against the published 15.8.” | 灰点落进环（0.6 s）；侧卡主数字计数（M10）与 “✓ weighting checks out” |
| “Our label is narrower: it has no fasting-glucose criterion.” | 右区第 2 行灰标记 14.0（与左区加权柱同值）与括号标注 |

**旁白**（49 词 · 134 wpm · 停顿 1.0 s）：

> First, the data. Our 5,730 adults are a clustered sample, older than the population, so estimates need survey weights: unweighted, 16.9 percent are positive; weighted, 14.0. {pause 1.0} Re-running the official NCHS brief tests our weighting: 15.79 percent against the published 15.8. Our label is narrower: it has no fasting-glucose criterion.

---

### 4.06 场景 06 · Data governance

| 项 | 内容 |
|---|---|
| 时间 | 1:53–2:17 · 24 s · `<Name:0>` · Data & governance |
| 主标题 / 副标题 | **Data governance** / Data use agreement limits, and which features a model may use |
| 模板 | T2：宽幅纸面三栏；下条纸面是“筛查时刻”时间线 |
| 署名 · 底栏 | — · Notebook sections 1.3, 1.8 |
| 颜色 | 只用墨色（治理页没有语义对象；层次靠纸面、面板标题、图标和判定形状）。划线是墨线 = 有意移除 |
| 数字 | 无 |
| 侧栏 | 宽幅纸面右段（1416–1800）是第 3 栏 “Small groups” |
| 转场 | 进：0.4 s 溶解；出：0.4 s 溶解 |
| 处理 | 重建（旧 `s04_dua_minimisation` 只保留数据使用协议一行文字） |

**宽幅纸面。** 栏 1（纸面 x 32–520）面板标题 “Data use agreement”：两条禁止，各配图标并被墨线划掉：链接图标 “linkage to other records”、人形图标 “re-identification”。栏 2（纸面 x 560–1250）面板标题 “Label source”：问卷板 + 试管 “self-report and HbA1c, from the survey itself”。栏 3（纸面 x 1296–1648）面板标题 “Small groups”：三个虚线框小块 “reported as exploratory”（虚线框 = exploratory，在 12、17 再用）。栏 1 到栏 2、栏 3 各有一根墨色箭头。

**下条纸面。** 一根时间线，中间一条墨色竖线 “screening moment”。左侧是可用的例子 “age · BMI · blood pressure · insurance”（墨色 ✓）；右侧是 “treatment · diagnosis history · glucose testing”，依次被墨线划掉。

| 旁白短语 | 画面 |
|---|---|
| “Governance shaped the analysis.” | 宽幅纸面三栏的面板标题（作为一个对象） |
| “The data use agreement forbids re-identification and linkage,” | 栏 1 两条依次出现并被墨线划掉（M7 墨，第 1、2 次） |
| “so the label must come from the survey itself,” | 栏 1 → 栏 2 箭头；栏 2 内容 |
| “and small groups are reported only as exploratory.” | 栏 1 → 栏 3 箭头；栏 3 虚线框 |
| {pause 0.8} | 静止 |
| “And one rule covers every variable:” | 下条时间线与 “screening moment” 竖线（M1） |
| “a feature is allowed only if it is known at the moment of screening,” | 左侧例子带 ✓ 出现（M13） |
| “before any glucose test.” | 右侧三项出现，一道墨线同时划掉三项（M7 墨，第 3 次）；为 18 埋下伏笔 |

**旁白**（53 词 · 133 wpm · 停顿 0.8 s）：

> Governance shaped the analysis. The data use agreement forbids re-identification and linkage, so the label must come from the survey itself, and small groups are reported only as exploratory. {pause 0.8} And one rule covers every variable: a feature is allowed only if it is known at the moment of screening, before any glucose test.

---

### 4.07 场景 07 · Most unexpected finding（`<Name:0>`）

| 项 | 内容 |
|---|---|
| 时间 | 2:17–2:31 · 14 s · `<Name:0>` · Data & governance |
| 主标题 / 副标题 | **Most unexpected finding** / `<Name:0>` on the pre-specified hypotheses |
| 模板 | T4：大图是 2×3 假设卡；右侧一句话；左下交接行 |
| 署名 · 底栏 | — · Notebook sections 6.11, 10.2 |
| 颜色 | 墨色；判定只用形状：supported = 实心 ✓，inconclusive = 虚线框 + “?” |
| 数字（来源） | 6 · 3 · 3（`hypotheses.json` `prereg_n` / `prereg_supported` / `prereg_inconclusive`；逐条判定见第 11.3 节） |
| 侧卡 | 面板标题 “Fixed in advance”；主数字 **3 of 6**（墨色，88 px）；标签 “supported”；判定槽 “3 inconclusive” |
| 转场 | 进：0.4 s 溶解；出：交接 0.6 s 溶解进 08 的段首卡 |
| 处理 | 改编旧 `s07_reflection_hypotheses`：六个形状加白话名，铺满左区 |

**假设卡（纸面 x 32–760，2×3，每张约 352×160）。** 每张一个判定形状加白话名（28 px，≤ 5 词）：

| 卡 | 白话名 | 判定 |
|---|---|---|
| 1 | Systematic vs minimal AUC | ? inconclusive |
| 2 | Screening gap and its cause | ? inconclusive |
| 3 | Training label and who is missed | ? inconclusive |
| 4 | Tree root is a leaked item | ✓ supported |
| 5 | Class weights worsen calibration | ✓ supported |
| 6 | Survey weights cost little AUC | ✓ supported |

**右侧一句话（纸面 x 792–1240，40 px serif，分两次出现，结果不早于旁白）。** “Six hypotheses, fixed before we saw the related data: three supported, three inconclusive.” 下方标注 “a guard against cherry-picking”。 左下交接行（28 px 墨色 60 %）：“Next: Data quality · `<Name:1>`”。

| 旁白短语 | 画面 |
|---|---|
| “Most unexpected for me:” | 六张卡出现，判定位置先是中性细框 |
| “of six hypotheses locked before we saw any related data,” | 侧卡面板标题 “Fixed in advance”；右侧一句话前半 “Six hypotheses, fixed before we saw the related data:” 淡入 |
| “our guard against cherry-picking,” | 前半句下方 28 px 墨色 70 % 标注 “a guard against cherry-picking” 淡入 |
| “only three were supported.” | 六张卡的判定一起翻出（M12 0.4 s）；右侧一句话后半 “three supported, three inconclusive.” 淡入；侧卡主数字与 “3 inconclusive” |
| {pause 1.0} | 静止 |
| “Next, `<Name:1>` on the quality of the data.” | 交接行淡入 |

**旁白**（30 词 · 129 wpm · 停顿 1.0 s）：

> Most unexpected for me: of six hypotheses locked before we saw any related data, our guard against cherry-picking, only three were supported. {pause 1.0} Next, `<Name:1>` on the quality of the data.

---

### 4.08 场景 08 · Missing-value codes

| 项 | 内容 |
|---|---|
| 时间 | 2:31–2:57 · 26 s · `<Name:1>` · Data quality |
| 主标题 / 副标题 | **Missing-value codes** / Numeric codes for 'refused' and 'don't know', recoded in every column |
| 模板 | T6 段首卡（0–0.8 s 静默，留到自我介绍结束）→ 0.4 s 溶解 → T1 |
| 署名 · 底栏 | — · Notebook section 3.4 |
| 颜色 | 红（被误删的有效值：1,496 大条用大块斜纹档加 2 px 红描边；被划掉的单元格）；墨（真代码 57、表格） |
| 数字（来源） | 57（`blanket_recode.json` `genuine`）· 1,496（`blanket_recode.json` `destroyed`）· 7.0 %（定义常量；28 个 7.0 与 1 个 9.0 见 `a1c_lost_7_0` / `a1c_lost_9_0`，所以只说 “results of exactly 7.0”） |
| 侧卡 | 面板标题 “Missing-value recode”；主数字 **1,496**（红，104 px）；标签 “valid values destroyed”；区间槽 “57 genuine codes caught”（墨色 32 px）；底部槽 28 px 墨色文字 “Non-obvious finding”（无框） |
| 转场 | 进：交接 0.6 s 溶解进段首卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s08_struck_7_0` 的柱、表与划线代码，按新版式重排；加段首卡 |

**段首卡（T6）。** `<Name:1>`（56 px serif）/ “Data quality & preparation”（34 px）/ “Presents: Data quality · EDA & preparation”（28 px 墨色 60 %）；左侧靛蓝 4×120 细线；右栏七段路线，Data quality 与 EDA & preparation 为本讲者的段（靛蓝左线、semibold），前两段为墨色 60 % 加 ✓。

**主纸面。** 上带（纸面 y 76–300）：同一刻度、同一左端的两根横条：“genuine codes caught” 57（墨色实心，粗 24 px）；“valid values destroyed” 1,496（红色斜纹，粗 64 px），条内用细分隔线按变量族分段，只写族名：diastolic BP · pulse · systolic BP · age · body measures · cholesterol · HbA1c（各段长度取 `blanket_recode.json` 的 `family_*` 与 `var_*`）。下带（纸面 y 330–548）：示意小表（右上角 24 px “illustrative”）三列 Diastolic BP 77 / Pulse 99 / HbA1c 7.0；左边规则 “Rule: 7, 9, 77, 99 → missing, every column”。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 段首卡；进度条切到 Data quality |
| “I'm `<Name>`; I led data quality and preparation.” | 段首卡停留，字幕照常 |
| “I profiled before cleaning.” | 0.4 s 溶解进 T1；主副标题；侧卡面板标题 |
| “NHANES stores 'refused' or 'don't know' as codes such as 7, 9, 77 and 99.” | 下带示意小表与规则 |
| “A common shortcut sets those numbers to missing in every column.” | 表中三个测量值被红线依次划掉（M7 红，3 次） |
| “That catches 57 genuine codes,” | 57 条生长（M2） |
| “and destroys 1,496 valid values,” | 1,496 条生长，分段线出现；侧卡主数字计数（M10）与 “57 genuine codes caught” |
| “including HbA1c results of exactly 7.0 percent.” | HbA1c 段加墨色描边与箭头（M11）；随后推近表中被划掉的 7.0（M9，第 1 次，≤ 1.25），停到停顿结束再拉回 |
| {pause 1.2} | 推近停留；侧卡底部 “Non-obvious finding” |

**旁白**（55 词 · 131 wpm · 静默 0.8 s · 停顿 1.2 s）：

> I'm `<Name>`; I led data quality and preparation. I profiled before cleaning. NHANES stores 'refused' or 'don't know' as codes such as 7, 9, 77 and 99. A common shortcut sets those numbers to missing in every column. That catches 57 genuine codes, and destroys 1,496 valid values, including HbA1c results of exactly 7.0 percent. {pause 1.2}

---

### 4.09 场景 09 · Recode effect on diabetes labels

| 项 | 内容 |
|---|---|
| 时间 | 2:57–3:16 · 19 s · `<Name:1>` · Data quality |
| 主标题 / 副标题 | **Recode effect on diabetes labels** / HbA1c-positive adults affected by the recode, and which labels changed |
| 模板 | T1 |
| 署名 · 底栏 | — · Notebook section 3.4 |
| 颜色 | 红（被抹掉的 HbA1c 值、改变标签的 6 个：浅底斜纹 + 警示三角）；墨（其余阳性、轴、阈值） |
| 数字（来源） | 29 of 721（`blanket_recode.json` `a1c_lost` / `a1c_pos`）· 6（`flips`）；6.5 % 是定义值（`funnel.json` `a1c_cut`） |
| 侧卡 | 面板标题 “HbA1c-based positives”；一根 721 的墨描边横条，尾端 29 段红斜纹；主数字 **29**（红）；标签 “of 721 erased by the recode”；底部槽：发现标签 “Finding 1 · Data quality” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s09_erased_positives` 的几何，按新版式重排 |

**主纸面。** 上带：HbA1c 轴 6–10，阈值竖线 6.5 标 “≥ 6.5 % = diabetes”；被抹掉的值是红斜纹圆点，7.0 处堆 28 个，9.0 处 1 个。下带：29 个方块展开成一排：6 个红斜纹带三角 “label changed”，23 个墨色实心 “also self-reported: label unchanged”（只写文字，不写 23）。一条虚线把这排方块连回侧卡横条的 29 段。

| 旁白短语 | 画面 |
|---|---|
| “An HbA1c of 7.0 is above the 6.5 threshold: a diabetes case.” | 轴与阈值线（M1）；29 个红斜纹点落到 7.0 与 9.0 |
| “The shortcut erased 29 of 721 HbA1c-based positives.” | 侧卡 721 横条与 29 段；主数字 29 |
| {pause 1.0} | 静止 |
| “Only six changed label,” | 下带：6 个红斜纹方块加三角 |
| “because the rest had also self-reported, so the either-or label hid the damage.” | 23 个墨块与标签行；虚线连回侧卡 |
| “That is our first finding.” | 侧卡底部发现标签 “Finding 1 · Data quality” |

**旁白**（42 词 · 133 wpm · 停顿 1.0 s）：

> An HbA1c of 7.0 is above the 6.5 threshold: a diabetes case. The shortcut erased 29 of 721 HbA1c-based positives. {pause 1.0} Only six changed label, because the rest had also self-reported, so the either-or label hid the damage. That is our first finding.

---

### 4.10 场景 10 · Outlier handling

| 项 | 内容 |
|---|---|
| 时间 | 3:16–3:34 · 18 s · `<Name:1>` · Data quality |
| 主标题 / 副标题 | **Outlier handling** / HbA1c values beyond the 1.5 × IQR fences, by diabetes status |
| 模板 | T1 |
| 署名 · 底栏 | — · Notebook section 3.8 |
| 颜色 | 只用墨色与 `--ink-fill`（离群值不是受损数据，不用红） |
| 数字（来源） | 542（`iqr_fence.json` `flagged`）· 6.8 %（`fence`）· 519（`flagged_pos`）；1.5 × IQR 与 6.5 % 是定义 |
| 侧卡 | 面板标题 “Above the upper fence”；主数字 **519**（墨色）；标签 “diabetic by definition, not errors”；判定槽 “Flag → Review → Keep ✓” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s10_outliers_kept`：直方图拉宽到整个主纸面 |

**主纸面。** 面板标题 “HbA1c, %”；直方图铺满内框（HbA1c 3–17，0.2 分箱，`hist_geometry.json`）。下围栏与上围栏为墨色虚线；阈值 6.5 为墨色实线。围栏内的柱 `--ink-fill`，围栏外的柱墨色实心。

| 旁白短语 | 画面 |
|---|---|
| “Outliers next.” | 面板标题与轴（M1） |
| “The textbook 1.5 times IQR rule flags 542 HbA1c values.” | 直方图柱生长；两条围栏；围栏外柱加深；标注 “542 flagged” |
| {pause 0.8} | 静止 |
| “But its upper fence, 6.8 percent, lies above the diagnostic threshold,” | 阈值线 6.5；箭头（M11）与标注 “upper fence 6.8 % > threshold 6.5 %” |
| “so 519 of them are diabetes by definition, not errors.” | 右尾描边（M3）；侧卡主数字与标签 |
| “We reviewed them and kept them all.” | 侧卡判定槽 “Flag → Review → Keep ✓” 依次出现（M13） |

**旁白**（40 词 · 133 wpm · 停顿 0.8 s）：

> Outliers next. The textbook 1.5 times IQR rule flags 542 HbA1c values. {pause 0.8} But its upper fence, 6.8 percent, lies above the diagnostic threshold, so 519 of them are diabetes by definition, not errors. We reviewed them and kept them all.

---

### 4.11 场景 11 · Redundancy and skewness

| 项 | 内容 |
|---|---|
| 时间 | 3:34–4:00 · 26 s · `<Name:1>` · EDA & preparation |
| 主标题 / 副标题 | **Redundancy and skewness** / Collinearity of weight and BMI; skewness of fasting triglycerides |
| 模板 | T6 章节卡（0–0.8 s 静默，停到第一句说完）→ 0.4 s 溶解 → T3（左纸面 VIF，右纸面甘油三酯） |
| 署名 · 底栏 | EDA by `<Name:2>` · Notebook sections 4.9, 4.10 |
| 颜色 | 青（变换后的分布、三个 systematic 步骤）；墨（VIF 条、变换前的直方图） |
| 数字（来源） | 95.7 / 97.6（`vif_skew.json` `vif_weight` / `vif_bmi`）· 6.62（`skew_tg`）· “≈ 0 after”（`skew_tg_yj` = −0.009，只写文字）；参考线 10 是定义（`vif_threshold`） |
| 侧卡 | 面板标题 “Systematic steps”；三行青色小方块加 28 px 文字：“Drop weight” · “Average blood-pressure readings” · “Yeo-Johnson transform” |
| 转场 | 进：0.4 s 溶解进章节卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s11_redundancy_skew`：VIF 改为 6 个身体测量变量，排成双纸面 |

**章节卡（T6）。** “EDA & preparation”（56 px serif）/ “Redundancy, skewness, fallacies, and the preparation design they inform”（34 px）/ “Presented by `<Name:1>` · EDA by `<Name:2>`”（28 px）；右栏七段路线，当前段靛蓝。

**左纸面。** 面板标题 “Multicollinearity (VIF), body measures”；6 根横条（weight、BMI、height、hip、waist、arm），对数轴 1–100；参考线 10 标 “severe above 10”；weight 与 BMI 墨色实心并标值，其余 `--ink-fill`。**右纸面。** 面板标题 “Fasting triglycerides”；原始直方图为墨色描边柱（`tg_raw_hist`），变换后原位换成青色浅底加描边（`tg_yj_hist`）。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 章节卡；进度条切到 EDA & preparation |
| “`<Name:2>`'s exploration examined structure.” | 章节卡停留（第 3 行 “EDA by `<Name:2>`” 与旁白对应） |
| “Weight and BMI are redundant, with severe multicollinearity:” | 0.4 s 溶解进 T3；署名行；两张纸的面板标题与轴；VIF 条生长（M2），参考线 10 |
| “variance inflation factors of 95.7 and 97.6.” | weight、BMI 的数值 |
| {pause 0.8} | 静止 |
| “Fasting triglycerides are strongly right-skewed: skewness 6.62.” | 右纸面原始直方图；标注 “skewness 6.62” |
| {pause 0.8} | 静止 |
| “For a linear model, both matter.” | 侧卡面板标题 “Systematic steps” |
| “So systematic preparation drops weight,” | 侧卡第 1 行；左纸面 weight 条被墨线划掉（M7 墨） |
| “averages repeated blood-pressure readings,” | 侧卡第 2 行 |
| “and applies a Yeo-Johnson transform to skewed variables;” | 侧卡第 3 行 |
| “on triglycerides, it brings skewness to about zero.” | 右纸面直方图原位换成青色变换后分布（M8）；标注变为 “≈ 0 after” |

**旁白**（57 词 · 136 wpm · 静默 0.8 s · 停顿 0.8 s + 0.8 s）：

> `<Name:2>`'s exploration examined structure. Weight and BMI are redundant, with severe multicollinearity: variance inflation factors of 95.7 and 97.6. {pause 0.8} Fasting triglycerides are strongly right-skewed: skewness 6.62. {pause 0.8} For a linear model, both matter. So systematic preparation drops weight, averages repeated blood-pressure readings, and applies a Yeo-Johnson transform to skewed variables; on triglycerides, it brings skewness to about zero.

---

### 4.12 场景 12 · Simpson's paradox check

| 项 | 内容 |
|---|---|
| 时间 | 4:00–4:18 · 18 s · `<Name:1>` · EDA & preparation |
| 主标题 / 副标题 | **Simpson's paradox check** / Subgroup comparisons checked for sign reversal, and a causal diagram (DAG) |
| 模板 | T2：宽幅纸面放比较矩阵；下条纸面放 DAG |
| 署名 · 底栏 | EDA by `<Name:2>` · Notebook sections 4.7, 4.8 |
| 颜色 | 只用墨色；反转的格子用 2 px 墨描边；“exploratory” 用虚线框（与 06 一致） |
| 数字（来源） | 6 of 224（`simpson.json` `n_flips` / `n_comparisons`）；格子位置取 `hist_geometry.json` `simpson_cells`；“all within noise”与“most of them”出自 `results/metrics_S4.json` `simpson.flips`（6 个反转的区间都跨 0，4 个按中介 BMI 或教育分层，claims C13） |
| 侧栏 | 宽幅纸面右段是矩阵的右三分之一，含标注 “6 of 224 reversed” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s15_simpson_dag`：矩阵转成 7 行宽条 |

**宽幅纸面。** 面板标题 “Subgroup comparisons, by stratifying variable”；7 行（age、race、income、BMI、insurance、education、sex）× 32 列，格距 46，行标签在纸面 x 32–110。普通格 `--line`。**下条纸面。** DAG：Race → BMI → Diabetes，BMI 下标 “mediator”；右端虚线框 “exploratory”。

| 旁白短语 | 画面 |
|---|---|
| “`<Name:2>` also scanned for Simpson's paradox:” | 矩阵逐列淡入（M6，0.9 s） |
| “of 224 subgroup comparisons, six reversed sign,” | 6 格加墨描边（M3），其余降到 25 %；标注 “6 of 224 reversed” |
| “all within noise.” | 第二条标注 “every interval crosses zero” |
| {pause 1.0} | 静止 |
| “A causal diagram flags most of them:” | 下条 DAG 的三个节点与两条边 |
| “they adjust for a mediator, such as BMI between race and diabetes.” | BMI 节点标 “mediator”；BMI 行与 education 行的 4 个反转格用一根箭头指向 BMI 节点（M11）；age 行的 2 格保持描边、不加箭头 |
| “We report this as exploratory.” | 虚线框 “exploratory” |

**旁白**（40 词 · 133 wpm · 停顿 1.0 s）：

> `<Name:2>` also scanned for Simpson's paradox: of 224 subgroup comparisons, six reversed sign, all within noise. {pause 1.0} A causal diagram flags most of them: they adjust for a mediator, such as BMI between race and diabetes. We report this as exploratory.

---

### 4.13 场景 13 · Preparation design

| 项 | 内容 |
|---|---|
| 时间 | 4:18–4:48 · 30 s · `<Name:1>` · EDA & preparation |
| 主标题 / 副标题 | **Preparation design** / Three preparations of the same data for one logistic regression |
| 模板 | T2：宽幅纸面是泳道开关表；下条纸面是汇聚行与代号对照 |
| 署名 · 底栏 | — · Notebook sections 6.2, 6.9 |
| 颜色 | 红斜纹（Naive 泳道色样）、灰（Minimal 的开关）、青（Systematic 的开关）；关着的步骤是 `--line` 短横，不画空框 |
| 数字（来源） | 14（`arms.json` `n_steps`）· 13（`arms.json` `groups.toggles.S` 的项数） |
| 侧栏 | 宽幅纸面右段是最后一列 “Class and survey weights” 与计数 “14 steps” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 重建：合并旧 `s12_fourteen_steps` 与 `s13_three_versions`，借用泳道几何；删掉步骤卡与列数 |

**宽幅纸面。** 列是 6 个描述性分组（纸面 x 380–1648，各约 210 宽）：Value repair · Post-diagnosis exclusion · Redundancy · Missingness and top-codes · Skewness, splines, scaling · Class and survey weights。列头下 24 px 写证据来源：“from: profiling” · “from: feature rule” · “from: VIF” · “from: missingness” · “from: skewness” · “from: class balance, design”。行是三条泳道（行标签在纸面 x 32–340，各带色样）：Naive / Minimal / Systematic。

**下条纸面。** 第 1 行 “All three → one L2 logistic regression · same folds”；第 2 行 “no step uses the label”；泳道标签正下方 24 px 灰字 **“notebook: M0 · M1 · S”**（全片唯一一次，不念、不进字幕）；右端 24 px 脚注 “one further step tested separately”。

| 旁白短语 | 画面 |
|---|---|
| “Each finding became a preparation step,” | 6 个列头与 “from:” 行依次出现（M13） |
| “fourteen in all,” | 右段计数 “14 steps” |
| “and none reads the label.” | 下条第 2 行 “no step uses the label” |
| {pause 0.8} | 静止 |
| “From them we built three versions of the data.” | 三条泳道的行标签与色样；代号对照一行 |
| “Naive keeps every column.” | Naive 行：整行短横（全关） |
| “Minimal adds one rule: drop items that exist only after a diagnosis, such as treatment.” | Minimal 行在 Post-diagnosis exclusion 列亮一个灰方块 |
| “Systematic applies thirteen steps, from per-variable missing codes to transforms and weights.” | Systematic 行从左到右亮起青方块（每个 120 ms）；行尾 “13 steps on” |
| “All three feed the same logistic regression on the same folds.” | 下条第 1 行与三条泳道指向它的汇聚箭头 |

**旁白**（65 词 · 130 wpm · 停顿 0.8 s）：

> Each finding became a preparation step, fourteen in all, and none reads the label. {pause 0.8} From them we built three versions of the data. Naive keeps every column. Minimal adds one rule: drop items that exist only after a diagnosis, such as treatment. Systematic applies thirteen steps, from per-variable missing codes to transforms and weights. All three feed the same logistic regression on the same folds.

---

### 4.14 场景 14 · Most unexpected finding（`<Name:1>`）

| 项 | 内容 |
|---|---|
| 时间 | 4:48–5:01 · 13 s · `<Name:1>` · EDA & preparation |
| 主标题 / 副标题 | **Most unexpected finding** / `<Name:1>` on the missing-value recode |
| 模板 | T4 |
| 署名 · 底栏 | — · Notebook section 3.4 |
| 颜色 | 红（被划掉的 7.0、29 段）；墨 |
| 数字（来源） | 29（`blanket_recode.json` `a1c_lost`） |
| 侧卡 | 面板标题 “Erased by one recode”；主数字 **29**（红）；标签 “diabetic HbA1c results”；底部槽：发现标签 “Finding 1 · Data quality” |
| 转场 | 进：0.4 s 溶解；出：交接 0.6 s 溶解进 15 的段首卡 |
| 处理 | 改编旧 `s14_b_reflection` |

**大图（纸面 x 32–760）。** 放大的单元格 “7.0 · diabetic” 被红线划掉；下面是 09 的 721 横条与 29 段红斜纹（缩小）。**右侧一句话。** “One routine recode erased 29 HbA1c-positive results; the either-or label hid it.” 左下交接行 “Next: Labels & bias · `<Name:2>`”。

| 旁白短语 | 画面 |
|---|---|
| “Most unexpected for me:” | 大图出现；侧卡面板标题与发现标签 |
| “one routine cleaning step erased 29 diabetic HbA1c results,” | 右侧一句话淡入；侧卡主数字 29 |
| “and the label hid it.” | 29 段描边（M3） |
| {pause 1.0} | 静止 |
| “But cleaning cannot fix the label itself. `<Name:2>` shows why.” | 交接行淡入 |

**旁白**（28 词 · 129 wpm · 停顿 1.0 s）：

> Most unexpected for me: one routine cleaning step erased 29 diabetic HbA1c results, and the label hid it. {pause 1.0} But cleaning cannot fix the label itself. `<Name:2>` shows why.

---

### 4.15 场景 15 · Confounding check

| 项 | 内容 |
|---|---|
| 时间 | 5:01–5:23 · 22 s · `<Name:2>` · Labels & bias |
| 主标题 / 副标题 | **Confounding check** / Diabetes prevalence by insurance status, crude and age-standardised |
| 模板 | T6 段首卡（0–0.8 s 静默，留到自我介绍结束）→ 0.4 s 溶解 → T1 |
| 署名 · 底栏 | —（讲者即作者）· Notebook sections 4.5, 4.6 |
| 颜色 | 只用墨色（保险分组不属于任何语义）：粗差值为空心圆加虚线晶须，标准化后为实心圆加实线晶须 |
| 数字（来源） | +5.3 pp（`age_std.json` `crude`；晶须 `crude_lo` / `crude_hi` 只画不标）· +0.7 pp [−2.6, +3.9]（`std` / `std_lo` / `std_hi`）；60 岁以上两柱只画几何不标值（`older_insured` / `older_uninsured`） |
| 侧卡 | 面板标题 “Age-standardised gap”；主数字 **+0.7 pp**（墨色，88 px）；区间 “[−2.6, +3.9]”；标签 “insured minus uninsured”；判定槽 “interval includes 0” |
| 转场 | 进：交接 0.6 s 溶解进段首卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s06_age_confounding`：两行区间并存加箭头；新增 60 岁以上两柱 |

**段首卡（T6）。** `<Name:2>` / “Exploration, labels & bias” / “Presents: Labels & bias · Experiments”；右栏路线中本讲者的两段为靛蓝。

**主纸面。** 左区（纸面 x 32–760）：面板标题 “Diabetes gap, insured minus uninsured, pp”；轴 −4…+10，零线墨色；两行 “crude” 与 “age-standardised”。右区（纸面 x 800–1240）：小 DAG，Age 在上，Insurance 与 Diabetes 在下两角；Age → Insurance、Age → Diabetes 为实线，Insurance ⇢ Diabetes 为虚线加 “?”。DAG 下方两根横柱 “aged 60 or older: insured / uninsured”（墨色，0–40 % 轴，不标值），一条细虚线连到 Age → Insurance 这条边。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 段首卡；进度条切到 Labels & bias |
| “I'm `<Name>`; I led exploration, labels and bias.” | 段首卡停留 |
| “First, a fallacy check.” | 0.4 s 溶解进 T1；左区轴与零线（M1） |
| “Crude rates show 5.3 percentage points more diabetes among insured adults than uninsured.” | crude 行：空心点 +5.3 与虚线晶须；标注 “+5.3 crude” |
| {pause 0.8} | 静止 |
| “That is confounding by age:” | 右区 DAG 的三个节点与边 |
| “the insured are much older.” | 60 岁以上两柱生长（M2）；细虚线连到 Age → Insurance |
| “Age-standardised, the gap shrinks to 0.7 points,” | age-standardised 行：实心点 +0.7 与晶须；从上点指向下点的箭头（M11）；侧卡主数字与区间 |
| “and its interval includes zero.” | 零线加粗一次（M3）；侧卡判定槽 |

**旁白**（47 词 · 133 wpm · 静默 0.8 s · 停顿 0.8 s）：

> I'm `<Name>`; I led exploration, labels and bias. First, a fallacy check. Crude rates show 5.3 percentage points more diabetes among insured adults than uninsured. {pause 0.8} That is confounding by age: the insured are much older. Age-standardised, the gap shrinks to 0.7 points, and its interval includes zero.

---

### 4.16 场景 16 · Label agreement

| 项 | 内容 |
|---|---|
| 时间 | 5:23–5:50 · 27 s · `<Name:2>` · Labels & bias |
| 主标题 / 副标题 | **Label agreement** / Self-reported diabetes vs HbA1c ≥ 6.5 %, with treatment status |
| 模板 | T1 |
| 署名 · 底栏 | — · Notebook sections 5.1, 5.2 |
| 颜色 | 只用墨色：两个圆为墨描边；用药者为墨色实心点，未用药者为空心点 |
| 数字（来源） | κ 0.70（`label_split.json` `kappa_unw`）· 250 of 819（`masked` / `self`）· 165（`masked_med`）；圆的面积比取 `circle_ratio` 0.938 |
| 侧卡 | 面板标题 “Agreement, Cohen's κ”；主数字 **0.70**（墨色）；下面一根 0–1 小刻度，0.6–0.8 浅带标 “substantial”，点在 0.70；标签 “self-report vs HbA1c” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 重建（旧 `s16_label_trap` 的半圆仪表删除；Venn 借用 `_label_venn.js`，改为面积按比例） |

**主纸面。** 左区（纸面 x 32–700）：问卷板与试管图标在两个圆上方；圆 “self-report” 与圆 “HbA1c ≥ 6.5 %”，面积 ∝ n，交叠。右区（纸面 x 740–1240）：250 个小点（10×25），165 个墨色实心、85 个空心；标注 “165 on insulin or pills”。左区的自报独有月牙用虚线连到右区点阵。

| 旁白短语 | 画面 |
|---|---|
| “Now the label.” | 面板标题 “Two sources of the label” 与两个图标 |
| “It combines a self-reported diagnosis with HbA1c,” | 两个圆依次画出（M6，面积 ∝ n） |
| “and the two agree substantially but far from perfectly: Cohen's kappa is 0.70.” | 侧卡 κ 刻度与主数字 |
| {pause 1.0} | 静止 |
| “Of 819 adults who report a diagnosis, 250 test below 6.5 percent,” | 自报圆标 “819 self-report”；自报独有月牙描边（M3），标注 “250 below 6.5 %” |
| “and 165 of those take insulin or pills.” | 右区点阵出现，165 个变实心；标注 |
| “Treatment lowers the very marker we label by, so a blood-test-only label would call treated patients negative.” | 从月牙指向 HbA1c 圆的箭头（M11），标注 “missed by a blood test alone” |

**旁白**（60 词 · 133 wpm · 停顿 1.0 s）：

> Now the label. It combines a self-reported diagnosis with HbA1c, and the two agree substantially but far from perfectly: Cohen's kappa is 0.70. {pause 1.0} Of 819 adults who report a diagnosis, 250 test below 6.5 percent, and 165 of those take insulin or pills. Treatment lowers the very marker we label by, so a blood-test-only label would call treated patients negative.

---

### 4.17 场景 17 · Undiagnosed diabetes

| 项 | 内容 |
|---|---|
| 时间 | 5:50–6:22 · 32 s · `<Name:2>` · Labels & bias |
| 主标题 / 副标题 | **Undiagnosed diabetes** / Adults with high HbA1c but no diagnosis, by insurance status |
| 模板 | T1 |
| 署名 · 底栏 | — · Notebook sections 1.4, 5.3, 5.4 |
| 颜色 | 蓝（152 人、风险差点、第二人群轨道：空心方块）；灰（All adults 轨道：实心圆）；墨（零线、轴） |
| 数字（来源） | 152（`label_split.json` `a1c_only`）· +23.2 pp [6.2, 40.1]（`undiagnosed.json` `rd_uninsured` / `_lo` / `_hi`）；脚注 “uninsured n = 49”（`n_uninsured`） |
| 侧卡 | 面板标题 “Never diagnosed”；主数字 **152**（蓝）；标签 “HbA1c ≥ 6.5 %, no diagnosis”；底部槽：发现标签 “Finding 2 · Labels” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s17_undiagnosed_screening` 的人群轨道；风险差改为单行区间图 |

**主纸面。** 上左（纸面 x 32–520，y 76–300）：152 个蓝色空心方块（19×8）。上右（纸面 x 560–1240）：面板标题 “More often undiagnosed, uninsured vs insured, pp”；轴 −10…+45，零线墨色；一行蓝方点加静态晶须。下带（纸面 y 360–548）：两条人群轨道：“All adults”（灰圆）与 “Not-yet-diagnosed adults”（蓝方，152 个阳性在轨道上以描边小块标出）。

| 旁白短语 | 画面 |
|---|---|
| “The other direction: 152 adults have HbA1c of 6.5 or more but no diagnosis.” | 152 方块淡入；侧卡主数字计数（M10）；推近方块（M9，第 2 次，≤ 1.25） |
| {pause 1.0} | 推近停留后拉回 |
| “Among adults with high HbA1c, the uninsured are 23.2 percentage points more often undiagnosed,” | 上右轴与蓝方点 +23.2（M1 → 点） |
| “interval 6.2 to 40.1:” | 静态晶须 |
| “an association, from a small group.” | 虚线框 “association · exploratory”；脚注 “uninsured n = 49” |
| {pause 0.8} | 静止 |
| “So the label records access to care as well as disease: our second finding.” | 侧卡底部发现标签 “Finding 2 · Labels” |
| “That is why every model is also scored on adults not yet diagnosed, the people screening is for.” | 下带两条人群轨道依次出现（M13）；152 小块在第二条轨道上描边 |

**旁白**（70 词 · 131 wpm · 停顿 1.0 s + 0.8 s）：

> The other direction: 152 adults have HbA1c of 6.5 or more but no diagnosis. {pause 1.0} Among adults with high HbA1c, the uninsured are 23.2 percentage points more often undiagnosed, interval 6.2 to 40.1: an association, from a small group. {pause 0.8} So the label records access to care as well as disease: our second finding. That is why every model is also scored on adults not yet diagnosed, the people screening is for.

---

### 4.18 场景 18 · Leakage check

| 项 | 内容 |
|---|---|
| 时间 | 6:22–6:53 · 31 s · `<Name:2>` · Experiments |
| 主标题 / 副标题 | **Leakage check** / Naive vs minimal preparation: same model, post-diagnosis items removed |
| 模板 | T6 章节卡（0–0.8 s 静默，停到第一句说完）→ 0.4 s 溶解 → T1 |
| 署名 · 底栏 | Experiment by `<Name:3>` · Notebook section 7.5 |
| 颜色 | 红斜纹（Naive 柱，原位过渡为灰）；灰（Minimal 柱：浅灰底加描边）；墨（划掉的项、差值、✓） |
| 数字（来源） | 0.961 → 0.828（`leak_gate.json` `auc_m0_eall` / `auc_m1_eall`）· −0.131 [−0.148, −0.114]（`diff_eall` / `_lo` / `_hi`）；轴起点 0.5 是定义 |
| 侧卡 | 面板标题 “AUC change”；主数字 **−0.131**（墨色）；区间 “[−0.148, −0.114]”；标签 “paired across folds”；判定槽 “✓ correct deterioration”；底部槽：发现标签 “Finding 3 · Leakage” |
| 转场 | 进：0.4 s 溶解进章节卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s18_leak_gate`：去掉尚未确诊者的差值，按 T1 重排 |

**章节卡（T6）。** “Experiments” / “Naive, minimal and systematic preparation: one model, same folds” / “Presented by `<Name:2>` · Experiments by `<Name:3>`”。

**主纸面。** 左区（纸面 x 32–700）：面板标题 “AUC, all adults”；竖轴 0.5–1.0，标 “axis starts at 0.5”；一根柱。右区（纸面 x 760–1240）：面板标题 “Post-diagnosis items”，三行项目；上方一个小标记 “screening moment”（回扣 06）。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 章节卡；进度条切到 Experiments |
| “Now the experiments, run by `<Name:3>`.” | 章节卡停留（第 3 行 “Experiments by `<Name:3>`” 与旁白对应） |
| “The first is a leakage check.” | 0.4 s 溶解进 T1；主标题 Leakage check；署名行；左区轴（M1） |
| “Naive preparation scores an AUC of 0.961.” | 红斜纹柱生长到 0.961（M2），数字红色 |
| “Minimal preparation removes only the items that exist after a diagnosis:” | 右区面板标题与 “screening moment” 小标记 |
| “treatment, diagnosis history and glucose testing.” | 三项依次出现并被墨线划掉（M7 墨，3 次） |
| “Same model, same folds: AUC falls to 0.828,” | 柱原位缩到 0.828（M8），填充过渡为灰，标签变为 “Minimal”；原长度留墨色虚线与 “0.961” |
| “a paired drop of 0.131.” | 侧卡主数字与区间、标签 |
| {pause 1.5} | 静止 |
| “A deterioration we wanted,” | 侧卡判定 “✓ correct deterioration” |
| “and our third finding: the 0.961 was the label leaking back in.” | 侧卡底部发现标签 “Finding 3 · Leakage” |

**旁白**（65 词 · 129 wpm · 静默 0.8 s · 停顿 1.5 s）：

> Now the experiments, run by `<Name:3>`. The first is a leakage check. Naive preparation scores an AUC of 0.961. Minimal preparation removes only the items that exist after a diagnosis: treatment, diagnosis history and glucose testing. Same model, same folds: AUC falls to 0.828, a paired drop of 0.131. {pause 1.5} A deterioration we wanted, and our third finding: the 0.961 was the label leaking back in.

---

### 4.19 场景 19 · Decision tree on naive data

| 项 | 内容 |
|---|---|
| 时间 | 6:53–7:16 · 23 s · `<Name:2>` · Experiments |
| 主标题 / 副标题 | **Decision tree on naive data** / A depth-3 tree, and median imputation of age at diagnosis |
| 模板 | T1 |
| 署名 · 底栏 | Experiment by `<Name:3>` · Notebook section 7.5 |
| 颜色 | 红（泄漏节点、插补出的 50：浅底斜纹加三角）；墨（其余节点细描边，叶子 25 %） |
| 数字（来源） | 86 %（`tree.json` `did040_missing`）· 50（`did040_fill`）· 分裂点 49.5 / 50.5 作一处标注（`did040_split_lo` / `_hi`） |
| 侧卡 | 面板标题 “Median imputation”；主数字 **50**（红）；标签 “filled into every blank”；区间槽 “86 % never asked” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s19_tree_and_50`：左右对调，树放右侧宽区 |

**主纸面。** 左区（纸面 x 32–420）：面板标题 “Age at diagnosis”；两根竖柱 “answered”（墨描边）与 “never asked”（红斜纹，标 86 %）。右区（纸面 x 460–1240）：深度 3 的树，宽排；根 “taking diabetes pills?”；一支第二层 “age at diagnosis”；其余节点墨色细描边，叶子 25 %。

| 旁白短语 | 画面 |
|---|---|
| “`<Name:3>`'s shallow decision tree shows the mechanism.” | 树自上而下画出（M1 级的绘入） |
| “Its root is a treatment item: taking diabetes pills.” | 根节点变为红斜纹加三角 |
| “On one branch it then splits on age at diagnosis.” | 第二层节点描边（M3），分裂标注 “49.5 / 50.5” |
| “But 86 percent were never asked that question,” | 左区两柱生长（M2），86 % |
| “and median imputation filled every blank with 50.” | 侧卡主数字 50 与标签；“never asked” 柱下标 “imputed as 50” |
| {pause 1.0} | 静止 |
| “So 'age 50' became a code for 'never diagnosed'.” | 从左区柱到分裂节点的箭头（M11），标注 “'age 50' = never diagnosed”；该节点改为红斜纹 |

**旁白**（51 词 · 133 wpm · 停顿 1.0 s）：

> `<Name:3>`'s shallow decision tree shows the mechanism. Its root is a treatment item: taking diabetes pills. On one branch it then splits on age at diagnosis. But 86 percent were never asked that question, and median imputation filled every blank with 50. {pause 1.0} So 'age 50' became a code for 'never diagnosed'.

---

### 4.20 场景 20 · Most unexpected finding（`<Name:2>`）

| 项 | 内容 |
|---|---|
| 时间 | 7:16–7:30 · 14 s · `<Name:2>` · Experiments |
| 主标题 / 副标题 | **Most unexpected finding** / `<Name:2>` on detection by diagnosis status |
| 模板 | T4：大图是两个 10×10 点阵 |
| 署名 · 底栏 | — · Notebook sections 8.2, 8.3 |
| 颜色 | 蓝（尚未确诊者：被标出的为浅底加 3 px 描边的方块，未标出的为 45 % 透明细描边）；墨（已确诊者：被标出的为实心圆，未标出的为 45 % 空心圆） |
| 数字（来源） | 70 / 52 per 100（`tpr_100.json` `per100_diag` / `per100_undx`，由 TPR 0.70 / 0.52 换算）· 特异度 0.80（`spec`） |
| 侧卡 | 面板标题 “Flagged per 100”；主数字 **52**（蓝）；标签 “of 100 not yet diagnosed”；区间槽 “70 of 100 diagnosed”；脚注 24 px “one shared cut-off · specificity 0.80” |
| 转场 | 进：0.4 s 溶解；出：交接 0.6 s 溶解进 21 的段首卡 |
| 处理 | 改编旧 `s20_100_diabetics` |

**大图（纸面 x 32–760）。** 两个 10×10 点阵并排（格距 32），面板标题 “Diagnosed” / “Not yet diagnosed”。**右侧一句话。** “At one cut-off, 70 of 100 diagnosed but 52 of 100 undiagnosed are flagged.” 左下交接行 “Next: Experiments · `<Name:3>`”。

| 旁白短语 | 画面 |
|---|---|
| “Most unexpected for me:” | 两个点阵的空格与面板标题 |
| “at one shared cut-off,” | 侧卡面板标题与脚注 |
| “the model flags 70 of every 100 diagnosed diabetics,” | 左阵 70 个变为墨色实心（M10 式逐行填充 0.8 s）；侧卡区间槽 |
| “but only 52 of 100 undiagnosed ones.” | 右阵 52 个变为蓝色；侧卡主数字；右侧一句话淡入 |
| {pause 1.0} | 静止 |
| “`<Name:3>` now asks what systematic preparation adds.” | 交接行淡入 |

**旁白**（31 词 · 133 wpm · 停顿 1.0 s）：

> Most unexpected for me: at one shared cut-off, the model flags 70 of every 100 diagnosed diabetics, but only 52 of 100 undiagnosed ones. {pause 1.0} `<Name:3>` now asks what systematic preparation adds.

---

### 4.21 场景 21 · Minimal vs systematic preparation

| 项 | 内容 |
|---|---|
| 时间 | 7:30–7:56 · 26 s · `<Name:3>` · Experiments |
| 主标题 / 副标题 | **Minimal vs systematic preparation** / Paired AUC difference and interval, against a pre-specified equivalence margin |
| 模板 | T6 段首卡（0–0.8 s 静默，留到自我介绍结束）→ 0.4 s 溶解 → T1 |
| 署名 · 底栏 | Preparation steps by `<Name:1>` · Notebook sections 7.7, 10.2.1 |
| 颜色 | 青（差值点与晶须）；中性灰带（`--band` 加虚线边）；墨（判定形状） |
| 数字（来源） | +0.008 [0.000, 0.016]（`prep_band.json` `d_auc` / `d_auc_lo` / `d_auc_hi`）· ±0.01（`sesoi`，事先固定）；脚注 0.011（`mdd`） |
| 侧卡 | 面板标题 “AUC change, all adults”；主数字 **+0.008**（青）；区间 “[0.000, 0.016]”；标签 “systematic minus minimal”；判定槽 虚线框 “? inconclusive”；底部槽：发现标签 “Finding 4 · Preparation” |
| 转场 | 进：交接 0.6 s 溶解进段首卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s21_prep_band`：轴拉宽到整个主纸面；去掉大号数字 |

**段首卡（T6）。** `<Name:3>` / “Modelling & conclusions” / “Presents: Experiments · Results & conclusions”。进度条不换段（仍是 Experiments）。

**主纸面（两带，避免一行图留下大片空白）。** 上带（纸面 y 76–330）：面板标题 “AUC difference, same model and folds”；差值轴 −0.04…+0.04，铺满内框宽；一行 “All adults”，点、晶须与 ±0.01 灰带都画大（带高 160 px）；轴下方两个区段标注：零附近 “no gain”，+0.01 以上 “worthwhile gain”。下带（纸面 y 360–548）：面板标题 “Reading an interval against the margin”；三行墨色小示意（同一根缩小的轴与灰带，各一条示意晶须，不带数字）：“inside the margin → equivalent” · “above the margin → better” · “crosses the margin edge → inconclusive”。脚注 24 px “smallest detectable difference 0.011”。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 段首卡 |
| “I'm `<Name>`; I led modelling and conclusions.” | 段首卡停留 |
| “Our fourth finding in detail: the same model, minimal against systematic preparation.” | 0.4 s 溶解进 T1；署名行；轴（M1）；侧卡发现标签 “Finding 4 · Preparation” |
| “AUC rises by 0.008,” | 青点（M4 第一步） |
| “interval 0.000 to 0.016.” | 晶须（M4 第二步）；侧卡主数字与区间 |
| {pause 1.2} | 静止 |
| “Our margin, fixed in advance, was 0.01.” | ±0.01 灰带（M4 第三步），带上方标 “margin fixed in advance”；晶须越过带边的端点脉冲一次（全片唯一一次） |
| “The interval spans no gain and a worthwhile gain,” | 轴下两个区段标注；下带三行示意淡入（M13，作为一组） |
| “so the result is inconclusive: underpowered, not evidence of no effect.” | 下带第 3 行 “crosses the margin edge → inconclusive” 描边（M3），其余两行降到 25 %；侧卡判定槽 “? inconclusive”；脚注 |

**旁白**（54 词 · 129 wpm · 静默 0.8 s · 停顿 1.2 s）：

> I'm `<Name>`; I led modelling and conclusions. Our fourth finding in detail: the same model, minimal against systematic preparation. AUC rises by 0.008, interval 0.000 to 0.016. {pause 1.2} Our margin, fixed in advance, was 0.01. The interval spans no gain and a worthwhile gain, so the result is inconclusive: underpowered, not evidence of no effect.

---

### 4.22 场景 22 · Calibration and Brier score

| 项 | 内容 |
|---|---|
| 时间 | 7:56–8:18 · 22 s · `<Name:3>` · Experiments |
| 主标题 / 副标题 | **Calibration and Brier score** / Systematic vs minimal preparation, with and without class weights |
| 模板 | T1 |
| 署名 · 底栏 | Class-weight step by `<Name:1>` · Notebook section 7.10 |
| 颜色 | 青（systematic 两行：实心点；去掉类别权重的版本为空心虚线点；Brier 条为青色浅底加描边）；灰（Minimal 点）；墨（观察率参考线、✗）。不用红：这是建模取舍，不是受损数据 |
| 数字（来源） | Brier +0.074（`brier.json` `d_brier`，只配 “from minimal to systematic”）· 41 % vs 17 %（`meanp_s` / `prevalence`，训练部分）· +0.007（`nocw_auc`） |
| 侧卡 | 面板标题 “Brier score change”；一根短条（青色浅底，晶须 0.066–0.081 只画不标）；主数字 **+0.074**（墨色）；标签 “minimal → systematic”；判定槽 “✗ worse calibration”；底部一行 28 px “without class weights: AUC +0.007” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s22_brier`：去掉 +0.076 大号数字，改为点图加侧卡 |

**主纸面。** 面板标题 “Mean predicted risk vs observed rate, %”；横轴 0–50 %（纸面 x 380–1240）；三行（行标签在纸面 x 32–340）：Minimal（灰点 16.8 %）、Systematic（青点 40.9 %，标 “41 %”）、Systematic without class weights（青色空心虚线点 16.7 %）。竖向墨色虚线 “observed 17 %”。

| 旁白短语 | 画面 |
|---|---|
| “One step did harm.” | 面板标题与轴（M1） |
| “From minimal to systematic, the Brier score worsens by 0.074.” | 侧卡短条生长，主数字与 “✗ worse calibration” |
| {pause 1.0} | 静止 |
| “The cause is `<Name:1>`'s class weights:” | 三行行标签 |
| “the systematic model predicts an average risk of 41 percent” | 青点 41 %，箭头（M11） |
| “where the observed rate is 17.” | “observed 17 %” 竖线与落在线上的灰点（Minimal） |
| “Removing only the class weights restores calibration,” | 青色空心虚线点落回 17 % 线 |
| “and AUC stays 0.007 above minimal.” | 侧卡底部一行 |

**旁白**（49 词 · 134 wpm · 停顿 1.0 s）：

> One step did harm. From minimal to systematic, the Brier score worsens by 0.074. {pause 1.0} The cause is `<Name:1>`'s class weights: the systematic model predicts an average risk of 41 percent where the observed rate is 17. Removing only the class weights restores calibration, and AUC stays 0.007 above minimal.

---

### 4.23 场景 23 · AUC by evaluation population

| 项 | 内容 |
|---|---|
| 时间 | 8:18–8:39 · 21 s · `<Name:3>` · Results & conclusions |
| 主标题 / 副标题 | **AUC by evaluation population** / Systematic preparation on all adults and on not-yet-diagnosed adults |
| 模板 | T6 章节卡（0–0.8 s 静默，停到第一句说完）→ 0.4 s 溶解 → T1 |
| 署名 · 底栏 | Population defined by `<Name:2>` · Notebook section 7.9 |
| 颜色 | 灰（All adults：实心圆）；蓝（尚未确诊者：空心方块；堆叠条中的未确诊段为蓝色浅底加描边）；墨（已确诊段：白底墨描边） |
| 数字（来源） | 0.836 / 0.781（`recognition.json` `auc_eall` / `auc_escreen`）· 84 %（`known_share`）；不显示两者之差 |
| 侧卡 | 面板标题 “Positives already diagnosed”；主数字 **84 %**（墨色）；标签 “so the score rewards recognition”；判定槽 “spectrum bias”；底部槽：发现标签 “Finding 2 · Labels” |
| 转场 | 进：0.4 s 溶解进章节卡；出：0.4 s 溶解 |
| 处理 | 改编旧 `s23_recognition` |

**章节卡（T6）。** “Results & conclusions” / “Performance by population, prior-care items, hold-out check and conclusions” / “Presented by `<Name:3>`”。

**主纸面。** 上带：面板标题 “AUC, systematic preparation”；横轴 0.5–1.0（标 “axis starts at 0.5”）；哑铃图：灰圆 0.836 与蓝方 0.781 用墨色细线相连。下带：面板标题 “Positives, by diagnosis status”；一根 100 % 横条：84 % “already diagnosed”，16 % “not yet diagnosed”。

| 旁白短语 | 画面 |
|---|---|
| （0–0.8 s 静默） | 章节卡；进度条切到 Results & conclusions |
| “Results: whom does the score serve?” | 章节卡停留（第 1 行 “Results & conclusions”） |
| “On all adults, the systematic model scores 0.836;” | 0.4 s 溶解进 T1；署名行；上带轴（M1）；灰圆 0.836 |
| “on adults not yet diagnosed, 0.781.” | 蓝方 0.781 与连线 |
| {pause 1.2} | 静止 |
| “84 percent of positives were already diagnosed,” | 下带横条分成两段（M6）；侧卡主数字 |
| “so the all-adults AUC mostly measures recognition of known patients:” | 括号把 84 % 段连到灰圆，标注 “recognition of known patients” |
| “spectrum bias, as our second finding said.” | 侧卡判定槽 “spectrum bias”；发现标签 “Finding 2 · Labels” |

**旁白**（44 词 · 131 wpm · 静默 0.8 s · 停顿 1.2 s）：

> Results: whom does the score serve? On all adults, the systematic model scores 0.836; on adults not yet diagnosed, 0.781. {pause 1.2} 84 percent of positives were already diagnosed, so the all-adults AUC mostly measures recognition of known patients: spectrum bias, as our second finding said.

---

### 4.24 场景 24 · Prior-care items

| 项 | 内容 |
|---|---|
| 时间 | 8:39–9:05 · 26 s · `<Name:3>` · Results & conclusions |
| 主标题 / 副标题 | **Prior-care items** / AUC change after removing two 'told by a doctor' items, per population |
| 模板 | T1（与 21 同一根差值轴、同位置、同灰带） |
| 署名 · 底栏 | — · Notebook sections 7.9, 10.4 |
| 颜色 | 灰（All adults 行：实心圆）；蓝（尚未确诊者行：空心方块）；中性灰带；墨（划掉的项、判定形状） |
| 数字（来源） | −0.016（`care_flip.json` `eall`；晶须 `eall_lo` / `eall_hi` 只画不标）· +0.019 [0.004, 0.034]（`escreen` / `escreen_lo` / `escreen_hi`） |
| 侧卡 | 面板标题 “Not yet diagnosed”；主数字 **+0.019**（蓝）；区间 “[0.004, 0.034]”；标签 “AUC change after removal”；判定槽 虚线框 “? lower end inside margin” |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 改编旧 `s24_care_flip`：删掉连接两点的斜线；轴代码与 21 共用 |

**主纸面。** 左区（纸面 x 32–360）：面板标题 “Removed items”；两行 “told high blood pressure” · “told high cholesterol”。右区（纸面 x 400–1240）：差值轴 −0.04…+0.04，±0.01 灰带通高；两行 “All adults” / “Not yet diagnosed”，按 `Kit.fit` 撑满纸面高度（行高约 220 px，点与晶须放大），不留下半张空纸。

| 旁白短语 | 画面 |
|---|---|
| “As a direct test, we drop two items that mark earlier care:” | 右区轴与灰带（静态出现） |
| “told of high blood pressure or cholesterol.” | 左区两项出现并被墨线划掉（M7 墨，2 次） |
| “On all adults, AUC falls by 0.016.” | 灰圆 −0.016 与静态晶须 |
| “On adults not yet diagnosed, it rises by 0.019, interval 0.004 to 0.034,” | 蓝方 +0.019 与静态晶须；侧卡主数字与区间 |
| “consistent with recognition and screening pulling apart.” | 两点之间一对相背的小箭头（M11），标注 “pulling apart” |
| {pause 1.0} | 静止 |
| “But the lower end lies inside our margin, so this stays inconclusive.” | 蓝方晶须下端描边（M3）；侧卡判定槽 |

**旁白**（58 词 · 134 wpm · 停顿 1.0 s）：

> As a direct test, we drop two items that mark earlier care: told of high blood pressure or cholesterol. On all adults, AUC falls by 0.016. On adults not yet diagnosed, it rises by 0.019, interval 0.004 to 0.034, consistent with recognition and screening pulling apart. {pause 1.0} But the lower end lies inside our margin, so this stays inconclusive.

---

### 4.25 场景 25 · Internal hold-out check

| 项 | 内容 |
|---|---|
| 时间 | 9:05–9:23 · 18 s · `<Name:3>` · Results & conclusions |
| 主标题 / 副标题 | **Internal hold-out check** / Main comparisons repeated once on adults held out from development |
| 模板 | T2：宽幅纸面左段是开发与留出的划分，右段是两组对照点；下条纸面是三个判定 |
| 署名 · 底栏 | **Robustness checks led by `<Name:1>`** · Notebook section 9.11 |
| 颜色 | 红（Naive 点）、灰（Minimal 与 All adults 点）、蓝（尚未确诊者方块）；交叉验证值为空心，留出集值为实心 |
| 数字（来源） | 1,146（`holdout.json` `n`）· 25（`pos_screen`）；点位只作几何、不标数值（`holdout.json` 的 AUC 与 `leak_gate.json`、`recognition.json`） |
| 侧栏 | 宽幅纸面右段是 “Population gap” 那组对照点 |
| 转场 | 进、出：0.4 s 溶解 |
| 处理 | 重建（旧 `s25_holdout` 的时间线不再使用） |

**宽幅纸面。** 左段（纸面 x 32–620）：面板标题 “Development and internal hold-out”；一根横条分两块：“development: cross-validated folds”（墨描边）与 “hold-out: 1,146 adults”（墨色加粗描边）。右段（纸面 x 680–1648）：面板标题 “AUC, cross-validation vs hold-out”；横轴 0.5–1.0；两组：“Leakage drop”（Naive 红、Minimal 灰）与 “Population gap”（All adults 灰圆、Not yet diagnosed 蓝方），每个对象两个点：空心 = 交叉验证，实心 = 留出集。**下条纸面。** 三个判定：“✓ leakage drop repeats” · “✓ population gap: same direction” · 虚线框 “? 25 not-yet-diagnosed positives: too few to test alone”。

| 旁白短语 | 画面 |
|---|---|
| “`<Name:1>` led the robustness checks.” | 署名行强调（M3 0.4 s）；左段面板标题 |
| “On an internal hold-out of 1,146 adults,” | 左段横条两块，标 1,146 |
| “scored once at the end,” | 留出块上标 “scored once, at the end” |
| “the leakage drop repeats” | 右段轴与 “Leakage drop” 组的空心与实心点；下条第 1 个判定 |
| “and the population gap points the same way,” | “Population gap” 组的点；下条第 2 个判定 |
| “though 25 undiagnosed positives are too few to test it alone.” | 下条第 3 个判定 |

**旁白**（40 词 · 133 wpm · 停顿无）：

> `<Name:1>` led the robustness checks. On an internal hold-out of 1,146 adults, scored once at the end, the leakage drop repeats and the population gap points the same way, though 25 undiagnosed positives are too few to test it alone.

---

### 4.26 场景 26 · Most unexpected finding（`<Name:3>`）

| 项 | 内容 |
|---|---|
| 时间 | 9:23–9:31 · 8 s · `<Name:3>` · Results & conclusions |
| 主标题 / 副标题 | **Most unexpected finding** / `<Name:3>` on leakage vs preparation effects |
| 模板 | T4：大图是同一轴上的两根横条 |
| 署名 · 底栏 | — · Notebook section 10.4 |
| 颜色 | 红斜纹（0.131）；青（0.008） |
| 数字（来源） | 0.131（`leak_gate.json` `diff_eall` 的绝对值）· 0.008（`prep_band.json` `d_auc`） |
| 侧卡 | 面板标题 “From the opening”；两张发现标签 “Finding 3 · Leakage”（红色样）与 “Finding 4 · Preparation”（青色样） |
| 转场 | 进：0.4 s 溶解；出：0.4 s 溶解进收尾 |
| 处理 | 改编旧 `s27_leak_vs_prep` |

**大图（纸面 x 32–760）。** 面板标题 “AUC change”；横轴 0–0.15；两行 “one exclusion rule”（红斜纹条，带晶须）与 “all careful preparation”（青条，带晶须）。**右侧一句话。** “One exclusion rule moved AUC by 0.131; all careful preparation, by 0.008.” 无交接行（接收尾）。

| 旁白短语 | 画面 |
|---|---|
| （0.4–1.0 s） | 侧卡两张发现标签与大图的轴（溶解结束后一次出现） |
| “Most unexpected for me: one exclusion rule moved AUC by 0.131;” | 红斜纹条生长（M2），数字 0.131 |
| “all our careful preparation, by 0.008.” | 青条生长，数字 0.008；右侧一句话淡入 |
| {pause 1.0} | 静止 |

**旁白**（17 词 · 128 wpm · 停顿 1.0 s）：

> Most unexpected for me: one exclusion rule moved AUC by 0.131; all our careful preparation, by 0.008. {pause 1.0}

---

### 4.27 场景 27 · 收尾（Main findings → Limitations and use of AI → Conclusion → 片尾卡）

| 项 | 内容 |
|---|---|
| 时间 | 9:31–10:15 · 44 s · `<Name:3>` · Results & conclusions |
| 主标题 / 副标题 | a **Main findings** / Four findings from the opening, each with a one-line answer<br>b **Limitations and use of AI** / Limits of this study, and how generative AI was used<br>c **Conclusion** / Main message of the study<br>d 片尾卡 “Who gets labelled diabetic?” |
| 模板 | a T5（与 03 同位置、同颜色）→ b T5（2×2 局限卡）→ c T4 → d T6 片尾卡；阶段之间用 M12 0.4 s 整层溶解；c → d 用 0.6 s 溶解 |
| 署名 · 底栏 | — · Notebook section 10.9 · Generative-AI declaration（片尾卡无底栏） |
| 颜色 | a：四种语义色（与 03 相同，摘要页例外）；b、c：墨色（局限卡 “Few undiagnosed positives” 带一个蓝方小图）；d：墨色 |
| 数字（来源） | 0.961（`leak_gate.json` `auc_m0_eall`，卡 3 原样回来） |
| 侧卡 | a、c：03 的颜色图例原样保留（同一对象，不变化）；b：GenAI 卡 “Generative AI drafted code and text · reviewed by us · every number recomputed”；d：右栏四位成员姓名与职责 |
| 转场 | 进：0.4 s 溶解；出：片尾卡停到全片结束，声音在最后 0.5 s 淡出，画面不淡出 |
| 处理 | 重建，复用 03 的发现卡组件（旧 `s28_close` 只借片尾卡；旧 `s26_three_answers` 不再使用） |

**阶段时刻（按 133 wpm 估计，录像后按实测重定）。** a 0–21 s；b 21–35 s；c 35–42.5 s；d 42.5–44 s（1.5 s 静默）。

**a 的回答行（每张卡的结论行下面加一行 34 px，带判定形状）。**

| 卡 | 回答行 |
|---|---|
| 1 Data quality | Shortcut destroys valid diabetes results |
| 2 Labels | Whole-sample AUC rewards recognition |
| 3 Leakage | ✓ The 0.961 was leakage |
| 4 Preparation | ? Barely moved AUC; valid data kept; calibration cost |

**b 的局限卡（2×2，每张 592×262，一行 34 px 加一个小图）。** “One survey cycle” · “Low response” · “Few undiagnosed positives”（蓝方小图）· “A data audit, not a screening tool”。

**c。** 大图（纸面 x 32–760）是四张发现卡的 2×2 缩略图（同色），右侧一句话 40 px serif：“The score is not the finding; what it reveals about the data is.”

**d 片尾卡（T6）。** 第 1 行 120 px serif “Who gets labelled diabetic?”；第 2 行 34 px “Group [no.] · Thank you”；底部 24 px “Data: NHANES 2021–2023, CDC/NCHS public-use files”；右栏四位成员姓名与职责；进度条七段全部“已讲完”；没有字幕。

| 旁白短语 | 画面 |
|---|---|
| “Back to our four findings.” | a：四张卡原位回到画面，降到 25 %；侧卡颜色图例 |
| “A common cleaning shortcut destroys valid diabetes results.” | 卡 1 回到 100 %，回答行 |
| “The label records care as well as disease, so whole-sample AUC rewards recognition.” | 卡 2 回到 100 %，回答行 |
| “The 0.961 was leakage.” | 卡 3 回到 100 %，回答行加 ✓ |
| “And careful preparation barely moved AUC; its value was valid data kept, at a cost in calibration.” | 卡 4 回到 100 %，回答行加 “?” |
| “Limits: one survey cycle, low response, few undiagnosed positives;” | M12 溶解到 b；三张局限卡依次出现（M13） |
| “a data audit, not a screening tool.” | 第 4 张局限卡 |
| “Generative AI drafted much of our code and text; we reviewed it and recomputed every number.” | 侧卡 GenAI 卡 |
| {pause 0.8} | M12 溶解到 c，缩略图出现 |
| “The score is not the finding; what it reveals about the data is.” | 一句话淡入一次（M12） |
| “Thank you.” | 静止 |
| （最后 1.5 s 静默） | 0.6 s 溶解进片尾卡 |

**旁白**（94 词 · 133 wpm · 静默 1.5 s · 停顿 0.8 s）：

> Back to our four findings. A common cleaning shortcut destroys valid diabetes results. The label records care as well as disease, so whole-sample AUC rewards recognition. The 0.961 was leakage. And careful preparation barely moved AUC; its value was valid data kept, at a cost in calibration. Limits: one survey cycle, low response, few undiagnosed positives; a data audit, not a screening tool. Generative AI drafted much of our code and text; we reviewed it and recomputed every number. {pause 0.8} The score is not the finding; what it reveals about the data is. Thank you.

---

## 5 视觉系统

### 5.1 原则

1. **一页一主张。** 先写一句 “viewer can point at ___”；无关数据不上屏，细节留给 notebook。
2. **画面跟着旁白走。** 每一步构建绑定一个旁白短语；数字不早于念出它的词；末帧能独立读懂。
3. **亮一个、暗其余。** 焦点 100 %，其余 25 %，不用模糊。
4. **画出不确定性。** 效应量都带晶须，并画在 ±0.01 margin 带旁。
5. **对照公平。** 同轴、同基线，柱从 0 起；AUC 轴从 0.5 起时标 “axis starts at 0.5”。
6. **按比例作图。** 几何与数字都由脚本从 JSON 算出，不手摆、不手敲。
7. **文字极少。** 主标题 + 副标题 + ≤ 3 个图内标注（各 ≤ 5 词）+ 1 行脚注。
8. **颜色承载信息。** 没有语义对象的页面保持墨色，层次靠纸面、面板标题、图标和判定形状。
9. **右侧永远有内容。** 小窗是右栏的底座，上面压着本页的关键数字、判定或图例。

### 5.2 令牌

| 令牌 | 值 | 用途 |
|---|---|---|
| `--stage` | #F6F7F9 | 舞台底色；母题只画在这一层 |
| `--paper` / `--paper-edge` | #FFFFFF / #E3E7EC | 纸面；1 px 边；圆角 8 px |
| `--paper-shadow` | `0 1px 2px rgba(21,32,43,.05), 0 6px 20px rgba(21,32,43,.07)` | 双层阴影，压缩后仍可见 |
| `--card` | #FBFCFD | 纸上的中性内卡；圆角 6 px，1 px 边，无阴影 |
| `--ink` / `--ink-70` | #15202B / rgba(21,32,43,.70) | 正文、轴、标题；副标题与面板标题用 70 % |
| `--line` / `--band` / `--ink-fill` | #DCE1E6 / #F1F3F5 / #D5DAE0 | 细线；margin 带；非语义直方图与条 |
| `--leak` / `--leak-tint` | #B42318 / #FBE7E5 | 红：受损或泄漏的数据 |
| `--systematic` / 浅底 | #0D7A63 / #E2F2EE | 青：systematic preparation 及其步骤 |
| `--screen` / 浅底 | #1D64B0 / #E3EEF8 | 蓝：尚未确诊者 |
| `--reference` / `--reference-tint` | #5A6672 / #EBEDEF | 灰：对照基线（Minimal、All adults） |
| `--structure` | #3B2F8F | 靛蓝：当前位置 |
| `--motif-opacity` / `--motif-major-opacity` / `--motif-card-opacity` | .08 / .12 / .07 | 母题强度 |
| `--fs-subtitle` | 32 px | 副标题（原 34 px） |
| `--fs-panel-head` | 28 px | 面板标题 |
| `--fs-side-num` / `--fs-side-num-s` | 104 px / 88 px | 侧卡主数字（≤ 5 字符 / 6–7 字符） |

**字体。** 标题 Source Serif 4 600；正文 IBM Plex Sans；数字 IBM Plex Mono（tabular-nums）；底栏指引用 Mono。本地打包，离线有备用栈。

### 5.3 纸面与分层

| 层 | 元素 | 规则 |
|---|---|---|
| 1 舞台 | 全帧底色 | `--stage`；母题只在这一层 |
| 2 纸面 | 主纸面、侧卡、宽幅纸面、下条纸面、双纸面 | `--paper`、1 px 边、8 px 圆角、双层阴影 |
| 2.5 内卡 | 发现卡、角色卡、局限卡、假设卡 | `--card` 或语义浅底；1 px 边；6 px 圆角；无阴影 |
| 3 内容 | 图形、数字、标注 | 语义色只出现在第 2、2.5 层 |
| 4 焦点 | M3 | 2 px 墨色描边，偏移 4 px，其余降到 25 % |
| 固定件 | 名签、小窗 | 名签：纸色底加 1 px 边，无阴影；小窗：1 px 细边画在外侧，无阴影、无动画 |

**全局网格（舞台坐标，1920×1080）。** 左右边距都是 120 px。整个画面是“左 1272 : 右 384”的两栏，小窗是右栏的一部分。

| 区域 | x | y | 尺寸 | 说明 |
|---|---|---|---|---|
| 进度条 | 120–1800 | 40–74 | 1680×34 | 七段；段名 24 px，基线 y 60；细线 y 70–74 |
| 主标题 | 120–1800 | 96–160 | 64 px serif | 单行 |
| 标题行母题带 | 主标题文字右端 + 96 到 1800 | 84–160 | 自适应 | 主标题右端超过 x 1200 时不画 |
| 副标题 + 署名 | 120–1800 | 172–206 | 32 px | 署名右对齐到 1800；副标题在署名左侧 48 px 处结束 |
| 内容区 | 120–1800 | 224–836 | — | 按模板放纸面 |
| 右栏 | 1416–1800 | 224–964 | 384 宽 | 侧卡 224–632 → 名签 656–740 → 小窗 748–964，左右边缘对齐 |
| 名签 | 1416–1800 | 656–740 | 384×84 | “Presented by `<Name>`”（28 px semibold）/ 职责（28 px） |
| 小窗 | 1416–1800 | 748–964 | 384×216 | 固定，直角；全片同一坐标 |
| 字幕区 | 120–1392 | 852–964 | 1272×112 | 在舞台上，不在纸上；底边与小窗底边对齐 |
| 底栏 | 120–1800 | 1000–1028 | 1680×28 | 左侧图例，右侧 notebook 指引 |
| 避让区 | 1392–1824 | 632–988 | — | 名签与小窗外扩 24 px；任何内容（含推近后的包围盒）不得进入 |

**对齐。** 主纸面与侧卡顶边都在 y 224；字幕区与小窗底边都在 y 964；主纸面右边 1392 与右栏之间隔 24 px。

**侧卡槽位（侧卡内坐标，内边距 24 px）。** 面板标题基线 y 52；主数字基线 y 176；区间 y 224；标签 28 px ≤ 2 行 y 262–300；图例 / 判定 / 发现标签槽 y 336–384。

### 5.4 构图模板 T1–T6

| 模板 | 纸面（舞台坐标） | 右栏 y 224–632 | 用在 |
|---|---|---|---|
| **T1 图 + 关键数字栏**（默认） | 主纸面 x 120–1392，y 224–836（1272×612，内框 1208×548） | 侧卡 1416–1800（384×408，内框 336×360）：关键数字、区间、标签、判定或发现标签 | 05、08–10、15–19、21–24 |
| **T2 宽幅图** | 宽幅纸面 x 120–1800，y 224–632（1680×408）；下条纸面 x 120–1392，y 656–836（1272×180） | 宽幅纸面的右段就是侧栏：图的最后一段或右侧节点 | 02、06、12、13、25 |
| **T3 双纸面对比** | 左纸面 x 120–744，右纸面 x 768–1392，y 224–836（各 624×612），同轴同尺度 | 侧卡：两者的关系、差值或决定 | 11 |
| **T4 一句话 + 一张大图** | 主纸面同 T1；纸面 x 32–760 放大图，纸面 x 792–1240 放一句话（40 px serif，≤ 4 行，每行 ≤ 22 字符），左下一行 28 px 墨色 60 %（交接行或出处） | 侧卡：一个关键数字、图例或发现标签 | 01、07、14、20、26、27c |
| **T5 卡片网格** | 主纸面同 T1；内卡 1×4（每张 284×516，间距 24）或 2×2（每张 592×262） | 侧卡：卡片之间的关系、颜色图例、路线或 GenAI 卡 | 03、04、27a、27b |
| **T6 满幅卡** | 无纸面；舞台 + 卡片母题；文字块左对齐 x 192，y 380–640；段首卡与章节卡左侧 4×120 靛蓝细线（x 152，y 392–512） | 右栏 1416–1800 × 224–632：片头卡与片尾卡放四位成员；段首卡与章节卡放七段路线竖排 | 01 片头卡；08、15、21 段首卡；11、18、23 章节卡；27 片尾卡 |

**T1（场景 18 末帧）**

```text
x 120                                                     1392 1416              1800
y 40  Overview  Data & governance  ...  Experiments━━━━  Results & conclusions       (进度条)
y 96  Leakage check                                       ░░░░░░░░░░░░░░░░░░░░░░░░░░ 母题带
y172  Naive vs minimal preparation: same model, post-diagnosis items removed | Experiment by <Name:3>
y224 ┌─────────────────────────────────────────────────────┐ ┌────────────────────┐
     │ AUC, all adults            Post-diagnosis items     │ │ AUC change          │
     │ 1.0┤ ┌╌╌╌╌┐ 0.961          · screening moment       │ │  −0.131   (ink)     │
     │    │ ┊    ┊                ──treatment──            │ │  [−0.148, −0.114]   │
     │ 0.9┤ ┊    ┊                ──diagnosis history──    │ │  paired across folds│
     │    │ ┌────┐                ──glucose testing──      │ │  ✓ correct          │
     │ 0.8┤ │░░░░│ 0.828 Minimal                           │ │    deterioration    │
     │ 0.5┤ └────┘ axis starts at 0.5                      │ │ [Finding 3·Leakage] │
     └─────────────────────────────────────────────────────┘ └────────────────────┘ y632
y852    A deterioration we wanted, and our third finding:   ┌ Presented by <Name:2>┐ y656
        the 0.961 was the label leaking back in. (caption)  └ Exploration, labels.. ┘ y740
                                                            ┌────────────────────┐ y748
y964                                                        │  speaker 384×216    │
                                                            └────────────────────┘ y964
y1000 ▨ Harmed or leaked data   ● Reference baseline               Notebook section 7.5
```

**T2（场景 13 末帧）**

```text
y 96  Preparation design                                  ░░░░░░░░░░░░░░░░░░░░░░░░░░
y172  Three preparations of the same data for one logistic regression
y224 ┌───────────────────────────────────────────────────────────────────────────────┐
     │            Value      Post-diag.  Redun-   Missing-  Skewness,   Class and     │
     │            repair     exclusion   dancy    ness      splines     survey wts    │
     │            from: ...  from: ...   from:VIF from: ... from: ...   14 steps      │
     │ ▨ Naive      ─          ─           ─        ─         ─           ─          │
     │ ● Minimal    ─          ■           ─        ─         ─           ─          │
     │ ■ Systematic ■          ■           ■        ■         ■           ■  13 on   │
     └───────────────────────────────────────────────────────────────────────────────┘ y632
     ┌─────────────────────────────────────────────────────┐ ┌ Presented by <Name:1>┐ y656
     │ notebook: M0 · M1 · S                                │ └ Data quality & prep. ┘ y740
     │ All three → one L2 logistic regression · same folds  │ ┌────────────────────┐ y748
     │ no step uses the label     one further step tested.. │ │  speaker 384×216    │
     └─────────────────────────────────────────────────────┘ │                     │ y836
y852    All three feed the same logistic regression ...     │                     │
y964                                                        └────────────────────┘
```

**T3（场景 11 末帧）**

```text
x 120                   744 768                  1392 1416              1800
y224 ┌──────────────────────┐ ┌──────────────────────┐ ┌────────────────────┐
     │ VIF, body measures   │ │ Fasting triglycerides│ │ Systematic steps    │
     │ weight ████████ 95.7 │ │   ▁▃█▅▂▁ (teal)      │ │ ■ Drop weight       │
     │ BMI    ████████ 97.6 │ │   ≈ 0 after          │ │ ■ Average blood-    │
     │ height ███  ¦10      │ │                      │ │   pressure readings │
     │ hip    █    ¦        │ │                      │ │ ■ Yeo-Johnson       │
     │ waist  █    ¦        │ │                      │ │   transform         │
     │ arm    █    ¦ severe │ │                      │ └────────────────────┘ y632
     │             above 10 │ │                      │ ┌ name tag ──────────┐ y656
     └──────────────────────┘ └──────────────────────┘ ┌ speaker ───────────┐ y748
y852   (caption)                                       └────────────────────┘ y964
```

**T4（场景 20 末帧）**

```text
y224 ┌─────────────────────────────────────────────────────┐ ┌────────────────────┐
     │ Diagnosed        Not yet diagnosed  │ At one cut-off,│ │ Flagged per 100     │
     │ ●●●●●●●●●●       ■■■■■■■■■■         │ 70 of 100      │ │  52   (blue)        │
     │ ●●●●●●●●●●       ■■■■■■■■■■         │ diagnosed but  │ │ of 100 not yet      │
     │ ... 70 filled    ... 52 filled      │ 52 of 100      │ │ diagnosed           │
     │ ○○○○○○○○○○       □□□□□□□□□□         │ undiagnosed    │ │ 70 of 100 diagnosed │
     │                                     │ are flagged.   │ │ one shared cut-off ·│
     │ Next: Experiments · <Name:3>                         │ │ specificity 0.80    │
     └─────────────────────────────────────────────────────┘ └────────────────────┘ y632
```

**T5（场景 03 末帧）**

```text
y224 ┌─────────────────────────────────────────────────────┐ ┌────────────────────┐
     │┌──────────┐┌──────────┐┌──────────┐┌──────────┐     │ │ Colour key          │
     ││vial      ││ruler     ││bucket    ││balance   │     │ │ ▨ Harmed or leaked  │
     ││Data      ││Labels    ││Leakage   ││Prepar-   │     │ │   data              │
     ││quality   ││          ││          ││ation     │     │ │ ● Reference baseline│
     ││ ╳7.0╳    ││ ●        ││ ▨▨ 0.961 ││ ░░●░░ ?  │     │ │ □ Not-yet-diagnosed │
     ││          ││   ■      ││          ││ cal. ✗   │     │ │   adults            │
     ││Cleaning  ││AUC mostly││0.961 is  ││Small gain│     │ │ ■ Systematic        │
     ││shortcut..││measures..││leakage.. ││inconcl.. │     │ │   preparation       │
     │└──────────┘└──────────┘└──────────┘└──────────┘     │ └────────────────────┘ y632
     └─────────────────────────────────────────────────────┘
```

**T6（场景 08 段首卡）**

```text
y 40  Overview ✓  Data & governance ✓  Data quality━━  EDA & preparation  ...       (进度条)
      ░░░░ 母题（整个舞台，文字块与右栏周围渐隐为 0）░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
y224 ░░                                                     Overview            ✓ 60 %
     ░░                                                     Data & governance   ✓ 60 %
y392 ░░ ┃  <Name:1>                         (56 px serif)  ┃ Data quality  (indigo, 600)
     ░░ ┃  Data quality & preparation       (34 px)        ┃ EDA & preparation (indigo)
y512 ░░ ┃  Presents: Data quality · EDA & preparation (28 px) Labels & bias       60 %
     ░░                                                     Experiments         60 %
     ░░                                                     Results & conclusions 60 %
y656 ░░                                                   ┌ Presented by <Name:1> ┐
y748 ░░   I'm <Name:1>; I led data quality ...  (caption)  ┌ speaker 384×216 ──────┐
y964 ░░                                                   └───────────────────────┘
```

**共同规则。** 每个模板的纸面只按上表摆，不出现别的尺寸。场景内换模板或换标题时，用 M12 整层溶解（0.4 s）。纸面从不移动、缩放或变形，只有内容动。

### 5.5 防空白规则

| 规则 | 阈值 | 检查方式 |
|---|---|---|
| R1 最大空白矩形 | 末帧中每张纸内框里最大的空白矩形 ≤ 内框面积的 15 % | 自动：内容包围盒栅格化到 24 px 网格后求最大全空矩形 |
| R2 内容铺满 | 内容包围盒宽 ≥ 内框宽的 85 %，高 ≥ 内框高的 80 % | 自动 |
| R3 侧卡不空 | 场景开始 1.5 s 后侧卡必须有内容，内容高度 ≥ 侧卡内框的 60 % | 自动 |
| R4 纸不空着出现 | 任何纸面空着的时间 ≤ 1.5 s；构建的第一步就画出面板标题或轴 | 每 0.5 s 抽一帧 |
| R5 图按内容定尺寸 | 绘图区 = 内框减去标签宽度；条形粗细 = min(64, (绘图区高 − 间距) / n)；最长的条用到绘图区的 ≥ 80 % | `Kit.fit()` |
| R6 少内容换模板 | 正文 ≤ 3 行的页面不用整张主纸面放文字，改用 T4 | 人工审 |
| R7 重心 | 内容面积加权重心（不含固定件）落在 x 0.36–0.55 W、y 0.34–0.55 H | 自动 |
| R8 不留装饰性空框 | 不画空表格、空设计矩阵、空占位框；示意表必须有内容并标 “illustrative” | 人工审 |

侧卡只放本页的关键数字、判定、图例或发现标签，内容必须来自旁白说到的东西；没有可放的内容时改用 T2，不硬塞。

### 5.6 颜色与面积

**颜色角色（每种颜色只有一个含义）。**

| 角色 | 令牌 | 唯一含义 | 非颜色编码 | 首次出现与图例时刻 |
|---|---|---|---|---|
| 语义 红 | `--leak` | 受损或泄漏的数据：naive 结果、被误删的值、泄漏项、插补出的 50 | 45° 斜纹 + 警示三角 | 02（Naive 色样旁写名称）；03 侧卡图例 |
| 语义 青 | `--systematic` | 只表示 systematic preparation 及组成它的步骤 | 实心填充 | 02（Systematic 色样）；03 侧卡图例 |
| 语义 蓝 | `--screen` | 尚未确诊者（全国未确诊、152 人、第二个评估人群） | 空心方块 | 01（侧卡图例槽的图例时刻）；03 侧卡图例 |
| 语义 灰 | `--reference` | 对照基线：Minimal、All adults、加权后的估计 | 实心圆 | 02（Minimal 色样）；03 侧卡图例 |
| 结构 靛蓝 | `--structure` | 只表示当前位置：进度条当前段的填充线；段首卡与章节卡左侧细线；右栏路线里的当前段 | 位置 + 细线 | 第 0 帧 |
| 反馈 | `--ink` | supported = 实心 ✓；inconclusive = 虚线框 + “?”；worse = ✗ | 形状 | 03 |
| 中性 | `--ink`、`--line`、`--ink-fill` | 轴、文字、已确诊者、保险分组、离群值直方图、有意移除的划线（墨线） | — | — |

**面积规则。**
1. 饱和色只用于小面积：线、点、晶须、描边、≤ 24 px 粗的条、≤ 2,400 px² 的小块、图标、关键数字。
2. 大面积形状（粗于 24 px 的条、> 2,400 px² 的块、卡片）一律用同色相浅底加 2–3 px 同色饱和描边。灰色大条用 `--reference-tint` 加 2 px `--reference` 描边。
3. 红色斜纹分两档：小块 3.5 px 条纹 / 14 px 间距，铺在 `--leak-tint` 上；> 40,000 px² 的大块 2 px / 12 px，铺在浅底上并加 2 px 红描边。
4. 关键数字用所属对象的颜色：0.961 红，0.828 灰，+0.008 青，152、0.781、+0.019、4.5 % 蓝，1,496 与 29 红，50 红。两组之差和非语义的量（−0.131、+0.7 pp、κ、84 %、519）用墨色。语义色数字字号 ≥ 56 px；更小的文字一律墨色，颜色只放在旁边的色样上。
5. 每帧最多 3 种语义色相（不计墨色和靛蓝）。**例外：** 摘要页 03 与收尾 27a，四种颜色并排读才是它们的作用。全帧饱和色像素占比 1.5–6 %，不超过 8 %。
6. 标题、副标题、字幕、名签、底栏文字永远是墨色。
7. 讲者不用颜色编码；名签、角色卡一律墨色。
8. 同一张图里颜色只编码一个变量：比较准备方式时颜色按方式（红 / 灰 / 青），人群用形状（圆 / 方）；比较人群时用灰圆对蓝方。

**有意的单色页。** 04（团队）、06（治理）、10（离群值）、12（Simpson）、15（混杂）、16（标签一致性）、27b（局限）没有语义对象，保持墨色。

### 5.7 母题与纵深

**问卷 / 编码表网格母题。**

| 项 | 值 |
|---|---|
| 线 | 1 px 墨色；行高 24 px；列宽按 `[72,144,48,96,192,60,120,84,168,36,108]` 循环，模仿 codebook 的不等宽列 |
| 强度 | 普通行 8 %，每第 6 行 12 %；渐隐遮罩从外缘 100 % 线性降到内侧 0 |
| 内页区域 | 左右外边距（x 0–120、1800–1920）；顶部 y 0–40；底部 y 1028–1080；标题行母题带 |
| 卡片页区域 | 片头卡、段首卡、章节卡、片尾卡整个舞台都画，强度 7 %；文字块外扩 120 px、右栏外扩 24 px 的范围内遮罩为 0，160 px 内渐隐 |
| 禁止 | 不画在纸面、文字、数字、字幕区、小窗或名签下面；完全静止 |
| 验收 | 最终成片帧里，外缘 48 px 内的网格线比舞台色暗 ≥ 6 个亮度级；缩小到 50 % 看时有层次，原尺寸下不干扰阅读 |

**纵深。** 每张纸都用双层阴影；多张纸（主纸面 + 侧卡，或宽幅 + 下条）共同形成两栏节奏。面板标题（每张纸左上角 28 px，墨色 70 %，基线在纸面 y 52）写这张图量的是什么，图形从纸面 y 76 开始。

**图标（墨色线描，viewBox 40，描边 2.5，圆角端点；永远和文字一起出现）。**

| 图标 | 含义 | 出现处 |
|---|---|---|
| 试管 | HbA1c 血检；数据质量发现 | 01、02、03 卡 1、06、16、27 |
| 尺子 | 标签发现 | 03 卡 2、27 |
| 漏水桶 | 泄漏发现 | 03 卡 3、27 |
| 天平 | 准备发现 | 03 卡 4、27 |
| 问卷板 | 自报诊断 | 01、02、06、16 |
| 链接、人形 | 数据使用协议的两条禁止 | 06 |
| 警示三角 | 只跟红色一起出现 | 红色对象旁，28 px |

发现标签的图标与 03 的卡相同。进度条上不加图标。

### 5.8 字号层次

| 层级 | 字体 | 字号 | 颜色 |
|---|---|---|---|
| 卡片标题 | Source Serif 4 600 | 88（片头）/ 56（段首卡讲者名、章节卡段名）/ 120（片尾） | 墨色 |
| 主标题 | Source Serif 4 600 | 64 | 墨色 |
| 副标题 | IBM Plex Sans 400 | 32 | 墨色 70 % |
| 面板标题 | IBM Plex Sans 600 | 28 | 墨色 70 % |
| 反思句 / 收束句 | Source Serif 4 | 40 | 墨色 |
| 主数字 | IBM Plex Mono 500 | 136（主纸面）/ 104 或 88（侧卡） | 所属对象的语义色或墨色；一页最多 1 个 |
| 次级数字 | IBM Plex Mono 500 | 56 | 同上；≤ 3 个 |
| 区间 | IBM Plex Mono 400 | 36（侧卡 32） | 墨色；数字之后 0.3 s 出现 |
| 标注 | IBM Plex Sans 400 | 34 | 墨色；≤ 3 条 |
| 下限 | IBM Plex Sans | 28 | 刻度、图内小字 |
| 字幕 | IBM Plex Sans 500 | 34 | 墨色，舞台上 |
| 底栏与脚注 | 图例 Sans 24 / 指引 Mono 24 | 24 | 墨色 / 墨色 60 % |

### 5.9 动效语汇 M1–M13

缓动：入场 `cubic-bezier(.2,0,0,1)`；形变、换值和推近 `cubic-bezier(.4,0,.2,1)`；数据驱动的连续量用线性。

| # | 动作 | 作用 | 时长与细节 | 场景 |
|---|---|---|---|---|
| M1 | 轴绘入 | 交代对象 | 0.6 s；刻度错开 30 ms，标签在轴线画完后 0.3 s 淡入 | 01、05、06、10、15、18、19、21、22、23、24 |
| M2 | 柱从基线生长 | 状态出现 | 0.7 s；柱间错开 120 ms；数值随旁白出现 | 01、03、05、08、10、11、15、18、19、26 |
| M3 | 聚焦：描边 + 暗其余 | 标示焦点 | 0.4 s；2 px 墨描边，偏移 4 px，其余 25 % | 全片 |
| M4 | 点 → 晶须 → margin 带 | 不确定性 | 点 0.3 s → 晶须 0.5 s → 带 0.6 s；越带边的端点脉冲一次。**只在 21 以动画呈现**；其他区间静态出现 | 21 |
| M5 | 漏斗收窄 | 状态转变 | 本版不使用（漏斗已删） | — |
| M6 | 集合分裂或形变 | 状态转变 | 0.9 s；圆面积 ∝ n | 01、12、16、23 |
| M7 | 划线 | 标示删除 | 0.25 s，标签 0.3 s；**红线 = 被误删的有效值，墨线 = 有意移除的项**；每场景 ≤ 3 次 | 红：03、08；墨：06、11、18、24 |
| M8 | 原位换值 | 状态转变 | 0.8 s；长度缓动、数字线性倒数、填充交叉淡变同时完成，位置不动 | 11、18 |
| M9 | 推近 | 标示焦点 | 推 0.9 s，停 ≥ 2 s，拉回 0.6 s；**缩放 ≤ 1.25，全片 2 次**；推近后的包围盒不得超出所在纸面 | 08、17 |
| M10 | 计数 | 连续量 | 0.8 s，线性起、末尾减速 | 01、02、05、08、17、20 |
| M11 | 标注箭头 | 标示焦点 | 箭头 0.4 s，标签 0.3 s；每次 1 个 | 01、08、10、12、15、16、19、22、24 |
| M12 | 溶解 / 卡片 | 过渡 | 0.4 s；场景内换阶段、卡片进出 | 03、07、08、11、15、18、21、23、27 |
| M13 | 依次出现 | 按阅读顺序交代对象 | 每项 0.3 s 原位淡入，不位移；由旁白里对应的词触发；相邻两项间隔 ≥ 1.2 s（旁白连续列举时 ≥ 0.6 s）；已出现的项保持 100 %，末帧即完整小结 | 01、02、03、04、06、10、11、13、17、21、27 |

**克制规则。**
- 每个运动都必须对应上表的一个作用，找不到作用就保持静止。
- 同一时刻只动一个对象；两个动作之间停 ≥ 1.5 s（M13 列举除外）。
- 动效总时长 ≤ 场景时长的 40 %；场景切走前，末帧必须能独立读懂。
- 每个场景的前 0.4 s 不动（处在溶解中）。
- 纸面不动，只有内容动；小窗与名签不加动画；字幕只做 0.1 s 淡入淡出。
- 禁止：飞入、弹跳、旋转、视差、粒子、闪烁、持续的背景动画、打字机效果、3D 翻转、印章砸下。

### 5.10 转场

全片只用三种转场，都是线性交叉溶解；不用推、擦、缩放、模糊、闪白或黑场。

| 位置 | 转场 | 时长 |
|---|---|---|
| 同一段内，场景之间 | 交叉溶解 | 0.4 s |
| 场景内换阶段（换标题或换模板） | 整层溶解（M12） | 0.4 s |
| 讲者交接（07→08、14→15、20→21） | 上一段末帧冻结，溶解到下一段的段首卡；小窗与名签随整帧一起溶解；段首卡静默 ≤ 0.8 s，新讲者在卡上做自我介绍，随后 0.4 s 溶解进第一页 | 0.6 s + 静默 0.8 s + 自我介绍 + 0.4 s |
| 章节卡（11、18、23） | 场景之间照常 0.4 s 溶解进章节卡；卡静默 0.8 s，讲者的第一句在卡上说，说完 0.4 s 溶解进第一页 | 0.4 s + 静默 0.8 s + 第一句 + 0.4 s |
| 片头 | 第 0 帧就是片头卡，不从黑场淡入；静默 1.0 s 后讲者在卡上自我介绍，说完 0.4 s 溶解进 01 的正文 | 1.0 s + 自我介绍 + 0.4 s |
| 片尾 | 27c 溶解到片尾卡；片尾卡停 1.5 s；声音在最后 0.5 s 淡出，画面不淡出 | 0.6 + 1.5 s |

**交接时序。** −0.3 s 上一位讲者说完最后一个词；0–0.6 s 溶解；0.8 s 新讲者开口。从上一位说完到新讲者开口约 1.1 s，不超过“1.5 s 无声”的限制。

**无声上限。** 每段是一次连续录像，场景之间的无声就是讲者自己的停顿。以 `{pause}` 结尾的场景（03、08、26），下一场景的第一句要紧接着说，停顿加上句间空隙合计 ≤ 1.5 s；章节卡前的上一句说完后，卡的 0.8 s 静默加句间空隙同样 ≤ 1.5 s。

### 5.11 可读性与无障碍

| 项 | 规则 |
|---|---|
| 字号 | 内容文字 ≥ 28 px；主数字 ≥ 88 px；字幕 34 px；只有底栏与脚注可用 24 px |
| 对比度 | 正文 ≥ 4.5:1，大字 ≥ 3:1；白纸上 ink 16.5、structure 10.6、red 6.6、blue 6.0、grey 5.9、teal 5.3；墨色 70 % 在舞台上约 6.9:1 |
| 不只靠颜色 | 红 = 斜纹 + 三角；青 = 实心 + 文字；蓝 = 空心方块；灰 = 实心圆；结构色 = 位置与细线；反馈 = ✓ / 虚线框 + “?” / ✗ |
| 动效敏感 | 不闪烁；每个动画 ≤ 1 s；推近 2 次，缩放 ≤ 1.25 |
| 音频 | 人声 −16 LUFS；不加背景音乐 |

### 5.12 整体自检

每个场景做出末帧后、每段成片看完后回答；有一个答“否”就回到第 5 节修改。

1. 右侧（侧卡或宽幅右段）有本页的内容吗？有没有大于约 400×300 的空白？
2. 每种颜色的含义能用一句话说清吗？饱和色是否少而集中？
3. 去掉母题与阴影后，末帧依然完整、清楚吗？母题在 50 % 缩放下看得出层次吗？
4. 每个画面变化都对应一个旁白短语吗？有没有旁白说着、画面却静止或无关？
5. 整体像一次数据审计的项目汇报，而不是营销海报吗？
6. 字幕从不压到图形、小窗、名签或图例行吗？

---

## 6 屏幕文字规范

### 6.1 标题规则与自检

**主标题。**

| # | 规则 |
|---|---|
| T1 | 名词短语，命名本页主题；≤ 5 个词，只有 “A vs B” 结构可到 6 个词 |
| T2 | 讲师一眼能懂：只用课程标准术语，或前面某页已经介绍过的词 |
| T3 | 不写结论：不用判定词（fails、hides、removed、worse、inconclusive、trap、surprise、cheat），不用 →、=、≫、✓、✗，不放区间 |
| T4 | 不用问句；唯一例外是片头卡与片尾卡上的报告名 “Who gets labelled diabetic?” |
| T5 | 不放数字，年份也不放 |
| T6 | 不用内部代号与成员代号 |
| T7 | 不用冒号 |
| T8 | 句首大写，结尾无标点；连接词用 “and”，不用 “&”（“&” 只用在进度条与职责标签里） |
| T9 | 全片用词一致：同一主题在进度条、卡片、标题、标注和旁白里用同一个词（例如旁白说 “leakage check”，标题就写 Leakage check） |
| T10 | 一页一个标题；分阶段的场景只在换阶段时换标题 |

**副标题。**

| # | 规则 |
|---|---|
| S1 | 说明本页展示什么：数据、度量、比较或方法 |
| S2 | 单行，≤ 12 个词，约 ≤ 72 个字符；有署名行时再短一些 |
| S3 | 不写结论和结果数字；定义性的数字可以写（HbA1c ≥ 6.5 %、1.5 × IQR） |
| S4 | 不用问句，不以 How、Why、What、Does 开头 |
| S5 | 不重复主标题 |
| S6 | 最多一个冒号 |
| S7 | 项目自定义的词第一次出现时，同一行里就把意思说清楚 |

**自检清单（每个标题逐条回答，有一条“否”就不通过）。**
- [ ] 主标题是名词短语，≤ 5 个词（vs 结构 ≤ 6）？
- [ ] 没看过项目的专家讲师读主标题，能立刻说出这一页讲什么？
- [ ] 主标题里没有数字、问号、冒号、箭头、判定词？
- [ ] 副标题单行、≤ 12 个词，写的是“展示什么”而不是“发现了什么”？
- [ ] 副标题里的数字只有定义或方法？
- [ ] 没有内部代号或成员代号？
- [ ] 每个项目自定义的词都已在本页或前面的页上解释过？
- [ ] 用词与进度条、旁白、其他页一致？
- [ ] 去掉标题后，标注里的结论仍有图形证据支撑？
- [ ] 可见文字不超过：主标题 + 副标题 + 3 个标注 + 1 行脚注（概览、回答、角色卡等正文页按第 6.8 节）？

**结果。** 第 3 节的 27 个场景、29 对主副标题（27 有三个阶段）全部按上表核对通过。三处说明：
- 07、14、20、26 的主标题固定为 “Most unexpected finding”，副标题写 `<Name> on <topic>`，只写主题。
- 18 用 “Leakage check”，与旁白 “The first is a leakage check” 一致（T9）。
- 27b 的副标题写 “Limits of this study, and how generative AI was used”，避免以 What 开头（S4）。

### 6.2 进度条

```text
Overview · Data & governance · Data quality · EDA & preparation · Labels & bias · Experiments · Results & conclusions
```

| 项 | 规格 |
|---|---|
| 位置 | x 120–1800，y 40–74；从第 0 帧（片头卡）到片尾卡全程可见 |
| 段名 | 只写段名，不加序号、图标或 “§”；进度条、段首卡、章节卡、角色卡、交接行里的段名一字不差 |
| 段宽 | 段名宽 + 32 px，段间隙 16 px，从 x 120 左对齐；总宽约 1,560 px |
| 已讲完 | 段名墨色 60 %，细线墨色 |
| 当前段 | 段名墨色 100 % semibold；细线为结构靛蓝，按本段已用时间从左往右填充（全局时间的纯函数，段起止由 `timeline.json` 求和） |
| 未讲到 | 段名墨色 60 %，细线 `--line` |
| 切换 | 在段首卡、章节卡或场景溶解的 0.4 s 内完成 |
| 片尾卡 | 七段全部为“已讲完” |

| 段 | 场景 | 起止 | 讲者 |
|---|---|---|---|
| Overview | 01–04 | 0:00–1:31 | `<Name:0>` |
| Data & governance | 05–07 | 1:31–2:31 | `<Name:0>` |
| Data quality | 08–10 | 2:31–3:34 | `<Name:1>` |
| EDA & preparation | 11–14 | 3:34–5:01 | `<Name:1>` |
| Labels & bias | 15–17 | 5:01–6:22 | `<Name:2>` |
| Experiments | 18–22 | 6:22–8:18 | `<Name:2>` → `<Name:3>` |
| Results & conclusions | 23–27 | 8:18–10:15 | `<Name:3>` |

### 6.3 卡片

| 卡 | 场景 | 静默 | 文字 | 右栏 |
|---|---|---|---|---|
| 片头卡 | 01 | 1.0 s，然后停到自我介绍结束 | 88 px “Who gets labelled diabetic?” / 34 px “Diabetes labels, data preparation and leakage in NHANES 2021–2023” / 28 px mono 墨色 60 % “CA6003 · Group [no.]” | 四位成员（出场顺序）：名字 + 职责 |
| 段首卡 | 08、15、21 | ≤ 0.8 s，然后停到自我介绍结束 | 56 px serif `<Name>` / 34 px 职责 / 28 px 墨色 60 % “Presents: <段名> · <段名>” | 七段路线竖排：本讲者的段为靛蓝 4 px 左线加 semibold；已讲完的段墨色 60 % 加小 ✓；未讲到的段墨色 60 % |
| 章节卡 | 11、18、23 | 0.8 s，然后停到第一句说完 | 56 px serif 段名 / 34 px 范围行 / 28 px 讲者行 | 七段路线竖排，当前段靛蓝 |
| 反思页 | 07、14、20、26 | — | 主标题 “Most unexpected finding”；副标题 `<Name> on <topic>`；一句话 40 px serif（≤ 16 词，可写结果）；左下交接行 | 侧卡：关键数字或发现标签 |
| 片尾卡 | 27 | 1.5 s | 120 px “Who gets labelled diabetic?” / “Group [no.] · Thank you” / 底部 24 px “Data: NHANES 2021–2023, CDC/NCHS public-use files” | 四位成员姓名与职责 |

段首卡、章节卡、片头卡和片尾卡没有主副标题和底栏；进度条照常显示。

**段首卡与章节卡文字。**

| 场景 | 第 1 行 | 第 2 行 | 第 3 行 |
|---|---|---|---|
| 08 段首卡 | `<Name:1>` | Data quality & preparation | Presents: Data quality · EDA & preparation |
| 11 章节卡 | EDA & preparation | Redundancy, skewness, fallacies, and the preparation design they inform | Presented by `<Name:1>` · EDA by `<Name:2>` |
| 15 段首卡 | `<Name:2>` | Exploration, labels & bias | Presents: Labels & bias · Experiments |
| 18 章节卡 | Experiments | Naive, minimal and systematic preparation: one model, same folds | Presented by `<Name:2>` · Experiments by `<Name:3>` |
| 21 段首卡 | `<Name:3>` | Modelling & conclusions | Presents: Experiments · Results & conclusions |
| 23 章节卡 | Results & conclusions | Performance by population, prior-care items, hold-out check and conclusions | Presented by `<Name:3>` |

**反思页文字。**

| 场景 | 副标题 | 一句话（数据） | 交接行 |
|---|---|---|---|
| 07 | `<Name:0>` on the pre-specified hypotheses | Six hypotheses, fixed before we saw the related data: three supported, three inconclusive.（`hypotheses.json`） | Next: Data quality · `<Name:1>` |
| 14 | `<Name:1>` on the missing-value recode | One routine recode erased 29 HbA1c-positive results; the either-or label hid it.（`blanket_recode.json`） | Next: Labels & bias · `<Name:2>` |
| 20 | `<Name:2>` on detection by diagnosis status | At one cut-off, 70 of 100 diagnosed but 52 of 100 undiagnosed are flagged.（`tpr_100.json`） | Next: Experiments · `<Name:3>` |
| 26 | `<Name:3>` on leakage vs preparation effects | One exclusion rule moved AUC by 0.131; all careful preparation, by 0.008.（`leak_gate.json`、`prep_band.json`） | —（接收尾） |

### 6.4 署名行

格式 `<Work> by <Name>`，放在副标题行右端：28 px，左侧一条 2 px 墨色竖线，无框，≤ 5 词。只在讲者与作者不同时显示，旁白同时点名。

| 场景 | 署名行 | 旁白中的点名 |
|---|---|---|
| 11、12 | EDA by `<Name:2>` | “`<Name:2>`'s exploration …”“`<Name:2>` also scanned …” |
| 18、19 | Experiment by `<Name:3>` | “run by `<Name:3>`”“`<Name:3>`'s shallow decision tree” |
| 21 | Preparation steps by `<Name:1>` | — |
| 22 | Class-weight step by `<Name:1>` | “`<Name:1>`'s class weights” |
| 23 | Population defined by `<Name:2>` | — |
| 25 | **Robustness checks led by `<Name:1>`**（固定措辞） | “`<Name:1>` led the robustness checks.” |

### 6.5 图例

| 颜色 | 图例文字（图例时刻与底栏同措辞） |
|---|---|
| 红 | ▨ Harmed or leaked data |
| 灰 | ● Reference baseline |
| 青 | ■ Systematic preparation |
| 蓝 | □ Not-yet-diagnosed adults |

- **图例时刻都在第一分钟。** 蓝：01 侧卡图例槽，0.3 s 淡入，停 2.5 s，0.4 s 收进底栏。红、灰、青：02 Preparation 节点的色样旁直接写名称。03 侧卡是完整的颜色图例，四行随对应的发现卡逐行出现并留在侧卡上；27a、27c 原样保留。之后的页面不再有图例时刻。
- **底栏只列本页出现的颜色**，不按“已出现过”累积。
- 靛蓝只表示当前位置，不进图例。
- 图例时刻放在旁白停顿处，不与数字标注同时出现，也不需要旁白。

### 6.6 底栏

- 左侧：本页的图例（第 6.5 节），24 px。
- 右侧：notebook 指引，24 px mono，墨色 60 %，右对齐到 x 1800。单节写 `Notebook section 7.5`；多节写 `Notebook sections 4.7, 4.8`；无编号的小节写 `Notebook: Summary`、`Notebook: Team and contributions`。不写 “§”，不写 notebook 原标题（原标题里有内部代号）。
- 片头卡、段首卡、章节卡、片尾卡没有底栏。

**指引核对。** 下表的节号已按 `notebooks/final/CA6003_NHANES_Diabetes.ipynb` 的标题逐条核对（`.venv/Scripts/python` + nbformat，2026-10-14）。

| 场景 | 指引 | notebook 标题 |
|---|---|---|
| 01、03 | Notebook: Summary | Summary |
| 02 | Notebook: Summary · section 1.2 | Summary；1.2 Research question and use case |
| 04 | Notebook: Team and contributions | Team and contributions |
| 05 | sections 4.3, 4.4, 9.8.2 | 4.3 External anchor: NCHS Data Brief 516；4.4 Weighted vs unweighted prevalence；9.8.2 V2: why our prevalence is 14.0 % and not 15.8 % |
| 06 | sections 1.3, 1.8 | 1.3 Feature-availability rule；1.8 Data user agreement and disclosure controls |
| 07 | sections 6.11, 10.2 | 6.11 Hypotheses and pre-registration lock；10.2 Hypothesis scoreboard |
| 08、09、14 | section 3.4 | 3.4 Cost of a blanket recode |
| 10 | section 3.8 | 3.8 Outliers: a three-layer rule |
| 11 | sections 4.9, 4.10 | 4.9 Redundancy and collinearity；4.10 Skewness |
| 12 | sections 4.7, 4.8 | 4.7 Simpson scan；4.8 Causal structure (DAG) |
| 13 | sections 6.2, 6.9 | 6.2 Step catalogue；6.9 Arms |
| 15 | sections 4.5, 4.6 | 4.5 Age standardisation；4.6 Insurance: attenuation, not reversal |
| 16 | sections 5.1, 5.2 | 5.1 Three labels and their agreement；5.2 Treatment masking |
| 17 | sections 1.4, 5.3, 5.4 | 1.4 Evaluation populations；5.3 What "undiagnosed" means；5.4 Who is undiagnosed |
| 18、19 | section 7.5 | 7.5 Leak gate |
| 20 | sections 8.2, 8.3 | 8.2 Group metrics at the fixed threshold；8.3 Gaps and permutation baseline |
| 21 | sections 7.7, 10.2.1 | 7.7 Cumulative path；10.2.1 H2b in detail |
| 22 | section 7.10 | 7.10 Precision–recall and calibration |
| 23 | section 7.9 | 7.9 E-ALL vs E-SCREEN |
| 24 | sections 7.9, 10.4 | 7.9；10.4 Improvements and deteriorations（含 prior-care 项的消融） |
| 25 | section 9.11 | 9.11 Internal hold-out check |
| 26 | section 10.4 | 10.4 Improvements and deteriorations |
| 27 | section 10.9 · Generative-AI declaration | 10.9 Limitations register；Generative-AI declaration |

### 6.7 术语表

| 内部代号 | 屏幕名称（首次） | 之后 | 首次出现 |
|---|---|---|---|
| M0 | Naive preparation（all columns） | Naive | 02 色样；13 完整定义 |
| M1 | Minimal preparation（post-diagnosis items removed） | Minimal | 同上 |
| S | Systematic preparation | Systematic | 同上 |
| 三者对照 | 只在 13 的泳道标签下用 24 px 灰字注一次 “notebook: M0 · M1 · S” | — | 13 |
| E-ALL | All adults | All adults | 03、17 |
| E-SCREEN / Screening group | Not-yet-diagnosed adults | Not yet diagnosed | 01 图例；17 定义 |
| Leak gate | Leakage check | 同左 | 18 |
| availability rule / P03 | Post-diagnosis items（treatment, diagnosis history, glucose testing）；规则本身叫 feature availability | post-diagnosis items | 06、18 |
| blanket / sentinel recode | Missing-value recode；codes for 'refused' and 'don't know' | the recode | 08 |
| L_comb | Label：told by a doctor or HbA1c ≥ 6.5 % | the label | 02 |
| P01–P14、B1–B6、arm | Preparation steps；6 个描述性分组 | — | 13 |
| B6 / class weighting | Class weights | 同左 | 03、22 |
| S−B6a | Systematic without class weights | 同左 | 22 |
| care traces | Prior-care items（'told by a doctor' items） | prior-care items | 24 |
| SESOI | Margin fixed in advance（±0.01） | margin | 21 |
| MDD | Smallest detectable difference（只放脚注） | — | 21 |
| prereg | Pre-specified hypotheses（“fixed in advance”） | 同左 | 07 |
| 假设编号 | 不上屏；用白话名 | — | 07 |
| DUA | Data use agreement | 同左 | 06 |
| DB516 | NCHS Data Brief 516（只作出处） | — | 01、05 |
| hold-out | Internal hold-out | 同左 | 25 |
| RQ1、RQ2a、RQ2b、Trap | 不编号、不上屏；四条发现按主题称呼：Data quality · Labels · Leakage · Preparation | — | 03 |
| 成员代号 | 真名（未填时 “[Name]”） | — | 全片 |

**永不上屏、不进旁白：** SHA-256、hash、文件计数、列计数、执行模式、冻结、post-audit、notebook 机制、代码与执行结构、“trap”、“arm”、§。

**照用的标准术语（第一次出现时括号里的解释只写一次）：** AUC · HbA1c · Cohen's κ · VIF · multicollinearity · skewness · Yeo-Johnson transform · outliers / 1.5 × IQR · confounding · age standardisation · survey weights · percentage points（之后写 pp）· interval（不写 95 %）· data leakage · median imputation · L2 logistic regression · decision tree (depth 3) · folds · class weights · calibration · Brier score · spectrum bias · Simpson's paradox · causal diagram (DAG) · mediator · equivalence margin · internal hold-out。

**代号对照的去处。** YouTube 说明里放一行：“Naive = M0, Minimal = M1, Systematic = S; All adults = E-ALL; Not-yet-diagnosed adults = E-SCREEN.”

### 6.8 页面文字预算

| 项 | 上限 |
|---|---|
| 主标题 | 1 个，≤ 5 词 |
| 副标题 | 1 行，≤ 12 词 |
| 图内标注 | ≤ 3 条，各 ≤ 5 词；可以带数字，但每个数字当场有标签或单位 |
| 脚注 | 1 行，24 px |
| 坐标轴与图形标签 | 不计入上限，但不得写成句子 |
| 正文页（03、04、07、27） | 卡片内每张 ≤ 4 行，每行 ≤ 14 词 |
| 署名行、图例、底栏 | 按第 6.4–6.6 节 |

每一个可见的词都要有作用；删掉后讲师仍能看懂的词，就删掉。

---

## 7 字幕与姓名

### 7.1 姓名规则

- **不用单个字母代称成员**：屏幕（名签、角色卡、段首卡、署名行、片头片尾卡、字幕）和语音里都不出现，也不写 “Member …” 或 “Analysis by …” 加字母。
- **唯一来源：** `notebooks/final/team.json` 的 `members[].name` 与 `group_number`。场景、字幕和合成脚本都从这里读，不在任何文件里手写名字。
- **占位：** 名字仍是占位值（单个字母，或含 “[TEAM TO FILL”）时显示为 “[Name]”，组号为 “[no.]”；字幕同样。
- **方案里的写法：** `<Name>`（本场景讲者）与 `<Name:i>`（成员 i）；口头自我介绍写成 “I'm `<Name>`”。
- **名字填好后**必须重新生成字幕并重新合成，否则画面里会留下 “[Name]”。

### 7.2 角色与名签

| 成员 | 名签第 2 行（职责） | 讲的部分 | 角色卡成果行 |
|---|---|---|---|
| `<Name:0>` | Governance & integration | Overview · Data & governance | Governance · official-estimate check |
| `<Name:1>` | Data quality & preparation | Data quality · EDA & preparation | Missing-code audit · preparation design |
| `<Name:2>` | Exploration, labels & bias | Labels & bias · Experiments | Label agreement · undiagnosed adults |
| `<Name:3>` | Modelling & conclusions | Experiments · Results & conclusions | Leakage check · experiments and conclusions |

名签全程常驻：“Presented by `<Name>`” / 职责。换讲者只在 2:31、5:01、7:30 三处交接，名签随整帧溶解换字。

### 7.3 字幕样式与字幕区

| 项 | 规格 |
|---|---|
| 形式 | 烧录进画面的开放字幕；同一份文字另出 `full.srt` 供 YouTube |
| 字幕区 | 舞台 x 120–1392，y 852–964（1272×112），在舞台上而不在纸上；底边与小窗底边对齐 |
| 对齐 | 区内水平居中、底端对齐 |
| 字体 | IBM Plex Sans 500，34 px，行高约 42 px（ASS 写 Fontsize 44，因为 libass 按 1.3 em 计字号）；墨色，2 px 舞台色描边；无阴影、无底板 |
| 行数与长度 | 最多 2 行，每行最多 42 个字符 |
| 显示时长 | 每条 1.0–6.0 s；相邻两条间隔不足 0.3 s 时前一条延到后一条开始 |
| 阅读速度 | 目标 ≤ 17 字符/秒，只作警告；录像后用 `overrides.json` 修正最差的几条 |
| 出入 | 0.1 s 淡入淡出 |
| 不出字幕 | 片头卡、段首卡与章节卡的静默部分（讲者在卡上开口后字幕照常）；片尾卡；停顿期间；每段最后 0.2 s |

### 7.4 断句与文字转换

- 文字就是该场景的旁白，名字记号换成真名（未填时为 “[Name]”），去掉 `{pause}`。
- 与屏幕一致：“percent” 写 “%”，“percentage points” 写 “pp”，“kappa” 写 “κ”；数字一律用阿拉伯数字，与屏幕精度相同。
- 优先在句末断条，其次在逗号、冒号、分号处；同一条的两行尽量等长。
- 不拆开：数字与单位、区间（“interval 0.000 to 0.016”）、人名、“HbA1c”、“Cohen's κ”。
- 行首不放标点；不在冠词或介词后断行。
- 术语与屏幕一致：写 “adults not yet diagnosed” 或 “not-yet-diagnosed adults”，不写 “screening group”。
- 字幕不重复标题；旁白念出的标题词照常显示。

### 7.5 生成与重新定时

1. **生成：** `node video/subtitles/build_subs.mjs` 读 `video/timeline/timeline.json` 与 `team.json`，写出 `full.srt`、`full.ass`、每段的 `block_<n>.srt` / `.ass` 与 `words.json`（逐词时钟，场景的构建 cue 也从这里取）。
2. **录像前（估计）：** 讲话窗口 `[silentLead + 0.3, (speechEnd 或 duration) − 0.5]`；窗口内按估计音节数分配时间，标点处加短停顿，`{pause}` 处加读数停顿。名字记号按 2 个音节计，填入真名不会移动 cue。
3. **录像后（重新定时）：** 在 `video/subtitles/overrides.json` 里按场景写入 `shift`、`speechEnd`、额外停顿或逐条的起止，重跑 `build_subs.mjs`，再重做受影响的场景与该段。动画 cue 读同一个 `words.json`，字幕与动画一起移动。场景实测时长变化时先改 `timeline.json` 的 `duration`。
4. **检查：** 每段抽查 3 处，字幕出现与开口相差 ≤ 0.3 s；没有一条超过 2 行 × 42 字符；字幕区无冲突。

### 7.6 烧录与 YouTube

- `compose_block.mjs` 用 libass 把 `block_<n>.ass` 烧进该段成片。
- 上传时把 `full.srt` 作为 English 字幕上传，避免 YouTube 自动字幕；CC 默认关闭（画面已有开放字幕）。
- 说明栏放代号对照一行与章节时间：0:00 Overview · 1:31 Data & governance · 2:31 Data quality · 3:34 EDA & preparation · 5:01 Labels & bias · 6:22 Experiments · 8:18 Results & conclusions。

---

## 8 制作流程

### 8.1 工具与规格

HTML/SVG 场景 → Playwright 逐帧截图 → ffmpeg。场景复用项目的令牌和字体，画面是时间 t 的纯函数（逐帧确定、可重复），数字从 `video/data/*.json` 读取。渲染用 `playwright-core`（只装在 `video/render/`），驱动本机 Chrome；需要 PATH 上带 libass 的 ffmpeg。

| 项 | 值 |
|---|---|
| 画面 | 1920×1080，30 fps，SDR，BT.709 |
| 场景中间文件 | 无声 MP4，H.264 yuv420p，CRF 18 |
| 段中间文件（供成片再编码） | CRF 12 |
| 讲者录像 | 每段一条连续录像，1080p30，MP4，音频 48 kHz；`video/takes/block_<n>.mp4`（不进 git） |
| 小窗 | 缩放并居中裁成 384×216，叠在 x 1416，y 748 |
| 成片 | H.264 High，CRF 18；AAC 192 kbps；−16 LUFS，真峰值 ≤ −1 dBTP |
| 字幕 | 烧录（libass）+ `full.srt` |

### 8.2 现有 `video/` 的状态

| 部分 | 现状 | v3 要做的 |
|---|---|---|
| `video/kit/tokens.css`、`kit.js`（kit v2） | 单一版式：一张 1728×764 的大纸把小窗、名签和字幕包在里面；进度条、标题、署名、名签、底栏、字幕区、审计 | 改成多张纸与六种模板（第 8.3 节） |
| `video/timeline/timeline.json` | 26 个场景、旧的七段（Problem & data … Reflection）、旧时长与旁白 | 换成本方案的 27 个场景与七段（第 8.4 节） |
| `video/scenes/` | s01–s07 已按 kit v2 重做（第 1 段）；s08–s28 仍是第一版的文件（带右栏、陷阱条、字母徽章） | 按第 8.6 节逐个新建或改编 |
| `video/subtitles/build_subs.mjs` | 字幕区在纸上（x 96，y 872） | 改到舞台（第 8.5 节） |
| `video/render/compose_block.mjs` | 场景 mp4 直接拼接（`-c copy`），场景之间硬切 | 改为 0.4 s 溶解（第 8.5 节） |
| `video/render/compose_film.mjs` | 四段直接拼接再做响度归一 | 改为交接处 0.6 s 溶解（第 8.5 节） |
| `video/data/*.json` | 全部数字已在；命名仍有 “Screening group”“Naive (M0)” | 改屏幕名称（第 8.7 节） |

### 8.3 kit 改动

**`tokens.css`。**
- 新增：`--reference-tint`、`--ink-fill`、`--ink-70`、`--card`、`--motif-opacity`、`--motif-major-opacity`、`--motif-card-opacity`、`--fs-side-num`、`--fs-side-num-s`、`--fs-panel-head`。
- 改值：`--paper-shadow` 改为双层；`--fs-subtitle` 34 → 32；副标题颜色改为 `--ink-70`。
- 几何：进度条、标题、副标题、底栏的 x 改为 120–1800；`.kit-panel` 改为 `.kit-paper` 加模板类（`.paper-main`、`.paper-side`、`.paper-wide`、`.paper-strip`、`.paper-left`、`.paper-right`）；`.kit-captions` 改到 x 120，y 852，1272×112；`.kit-pointer` 改用 mono。
- 新增类：`.kit-panelhead`、`.kit-route`（右栏路线竖排）、`.kit-legendslot`（侧卡图例槽）、`.kit-findingtag`（发现标签）。

**`kit.js`。**

| 改动 | 内容 | 工作量 |
|---|---|---|
| `GRID` | 新增 `GRID.tpl`：T1–T6 的纸面矩形（舞台坐标与纸面坐标）；`captions`、`keepOut`、`bottom` 换成新坐标 | 小 |
| `buildChrome` | 按 `cfg.template`（或 `cfg.phases[i].template`）建立多张纸，每张纸有自己的 SVG 与 HTML 层：`ui.papers.main / side / wide / strip / left / right`；保留 `ui.fig` 作为 `ui.papers.main.fig` 的别名，方便迁移 | 中 |
| 卡片 | `buildCard({kind: 'title' / 'blockstart' / 'chapter' / 'end'})`，含右栏路线或成员列表；增加 `fadeIn` / `fadeOut`；段首卡 `fadeIn: 0`（进卡由合成负责） | 小 |
| 进度条 | 从第 0 帧起显示；七段新名；首段 Overview | 小 |
| `motif()` | 新强度与主线；标题行母题带（测量标题宽度后决定是否画）；卡片模式下整舞台画并留出文字块空洞 | 小 |
| 图例 | 图例条进入侧卡图例槽；`legendList: true` 时逐行累积（03）；底栏只列本页出现的颜色（`cfg.legend` 显式列出，或从 SVG 的 `data-role` 推断） | 小 |
| 样式 | `BAR_STYLES` 增加 `referenceTint`、`screenTint`、`systematicTint`；`bar()` 粗于 24 px 时自动用浅底加描边；`hatchPattern` 增加大块档 | 小 |
| 图标 | 恢复 `ICONS.bucket / ruler / balance`，新增 `clipboard`、`vial`、`link`、`person` | 小 |
| 共用组件 | `findingCard(i, scale)`（03、27a、27c、发现标签共用）；`diffAxis()`（21、24 与 03 卡 4 共用）；`aucAxis()`（03 卡 3、18、23、25） | 中 |
| 动效 | `M13_sequence(t, cues, o)`；`Kit.motion` 记录每个 M 动作的起止 | 小 |
| 辅助 | `Kit.fit(paper, {labels, n})` 返回绘图区与条形粗细（R5） | 小 |

### 8.4 `timeline.json` 改动

| 字段 | 新内容 |
|---|---|
| `sections[]` | 7 段：Overview（Problem, project, findings and team）· Data & governance（Survey design, weights, data-use terms and pre-specified hypotheses）· Data quality（Profiling, missing-value codes and outliers）· EDA & preparation（Redundancy, skewness, fallacies, and the preparation design they inform）· Labels & bias（Confounding, label agreement and undiagnosed diabetes）· Experiments（Naive, minimal and systematic preparation: one model, same folds）· Results & conclusions（Performance by population, prior-care items, hold-out check and conclusions） |
| `members[]` | `role`、`presents` 按第 7.2 节 |
| `blocks[]` | 1：01–07；2：08–14；3：15–20；4：21–27；每段 `handover: 0.6` |
| `scenes[]` | 27 个，`file` 与 `duration` 按第 3 节；`silentLead`：01 = 1.0，08 / 15 / 21 = 0.8，11 / 18 / 23 = 0.8；27 写 `speechEnd: 42.5`（片尾卡 1.5 s 静默）；`narration` 取第 4 节原文；新增 `template`（T1–T6）与 `in`（默认 `dissolve`） |

起止时间不存，由时长求和。录像后按实测回填 `duration`。署名行写在场景配置的 `credit` 字段。

### 8.5 合成与字幕脚本改动

**`compose_block.mjs`（段内 0.4 s 溶解，不多一次编码）。**
1. 除最后一个场景外，每个场景末尾 `tpad=stop_mode=clone:stop_duration=0.4` 冻结末帧 0.4 s。
2. 依次 `xfade=transition=fade:duration=0.4:offset=O_k`，`O_k = d_1 + … + d_k`，即第 k+1 个场景的起点；总时长仍为 Σd，字幕时间不用改。
3. 输入统一 `fps=30,settb=AVTB,format=yuv420p,setsar=1`。
4. 小窗与字幕在溶解之后叠加（顺序不变）。
5. 场景 `in: "cut"` 时 duration 0。增加 `--crf`（段中间文件用 12）；合成后用 ffprobe 断言时长 = Σd ± 1 帧。

```text
[0:v]fps=30,settb=AVTB,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.4[s0];
[1:v]fps=30,settb=AVTB,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.4[s1];
[2:v]fps=30,settb=AVTB,format=yuv420p[s2];
[s0][s1]xfade=transition=fade:duration=0.4:offset=D0[x1];
[x1][s2]xfade=transition=fade:duration=0.4:offset=D0+D1[base];
[N:v]...scale/crop...[cam]; [base][cam]overlay=x=1416:y=748,ass=...,format=yuv420p[v]
```

**`compose_film.mjs`（交接 0.6 s 溶解）。** 第 1–3 段末尾 `tpad=stop_mode=clone:stop_duration=0.6`，再 `xfade=fade:duration=0.6:offset=段累计起点`；视频重编码 CRF 18。音频直接 concat（重叠的 0.6 s 落在下一段开头的静默里），每段首尾各加 20 ms `afade`，片尾加 0.5 s `afade` 淡出；之后 loudnorm 不变。成片时长 = Σ段时长，`full.srt` 不用改。

**`build_subs.mjs`。** `ZONE = { x: 120, y: 852, w: 1272, h: 112 }`；文字转换（percent → %，percentage points → pp，kappa → κ）；断言每段最后 0.2 s 没有字幕、段首卡的静默内没有字幕。

### 8.6 场景迁移

| 新文件 | 来源 | 处理 | 优先级 |
|---|---|---|---|
| `s01_problem` | — | 新建（片头卡 + T4） | P1 |
| `s02_study_design` | — | 新建（T2 流程） | P1 |
| `s03_main_findings` | — | 新建（发现卡组件） | P1 |
| `s04_team_roles` | `s01_hook_team` 的团队卡 | 改编 | P1 |
| `s05_survey_weights` | `s05_nchs_replication` | 重建，借用复现刻度 | P1 |
| `s06_governance` | `s04_dua_minimisation` | 重建 | P1 |
| `s07_reflection_hypotheses` | 同名 | 改编 | P1 |
| `s08_missing_codes` | `s08_struck_7_0` | 改编 | P2 |
| `s09_label_effect` | `s09_erased_positives` | 改编 | P2 |
| `s10_outliers` | `s10_outliers_kept` | 改编 | P2 |
| `s11_redundancy_skew` | 同名 | 改编 | P2 |
| `s12_simpson_dag` | `s15_simpson_dag` | 改编 | P2 |
| `s13_preparation_design` | `s12_fourteen_steps` + `s13_three_versions` | 重建 | P2 |
| `s14_reflection_recode` | `s14_b_reflection` | 改编 | P2 |
| `s15_confounding` | `s06_age_confounding` | 改编 | P2 |
| `s16_label_agreement` | `s16_label_trap`、`_label_venn.js` | 重建 | P2 |
| `s17_undiagnosed` | `s17_undiagnosed_screening` | 改编 | P2 |
| `s18_leakage_check` | `s18_leak_gate` | 改编 | P2 |
| `s19_tree_and_50` | 同名 | 改编 | P2 |
| `s20_reflection_detection` | `s20_100_diabetics` | 改编 | P2 |
| `s21_prep_band` | 同名 | 改编 | P2 |
| `s22_brier` | 同名 | 改编 | P2 |
| `s23_recognition` | 同名 | 改编 | P2 |
| `s24_prior_care` | `s24_care_flip` | 改编 | P2 |
| `s25_holdout` | `s25_holdout` | 重建 | P2 |
| `s26_reflection_leak_vs_prep` | `s27_leak_vs_prep` | 改编 | P2 |
| `s27_close` | `s28_close` 的片尾卡 | 重建 | P2 |

**不再使用：** `s02_agenda`、`s03_cohort_funnel`、`s26_three_answers`，以及被合并或改名的旧文件。改编的文件用 `git mv` 保留历史。

**改编的通用步骤。** 主纸面横向几何与 kit v2 同为 1272 宽，横向坐标可以沿用；纵向从 648 降到 612，y > 576 的元素上移或用 `Kit.fit` 重算。第一版文件里的右栏、陷阱条、字母徽章、来源 mono 标签全部删掉；原先放在副区的内容改画进侧卡。每个证据页都要补侧卡内容（关键数字、区间、标签、判定或发现标签），这是工作量最大的部分。

### 8.7 数据改动

- **屏幕名称：** `build_data.py` 的 `_meta.naming` 与 `label` 改为第 6.7 节的名称（“Naive (M0)” → “Naive”；“Screening group” → “Not-yet-diagnosed adults”；“Systematic (S) − Minimal (M1)” → “Systematic − Minimal”），场景代码不手改。
- **显示格式（不是新数字）：** `brier.json` 的 “41 %”“17 %”；`leak_gate.json` 的 0.131 绝对值显示（26）；`arms.json` 的 13（`groups.toggles.S` 的项数）。
- **不需要新算的数字。** 所有上屏数字都已在 `video/data/*.json` 中；补登见第 11.4 节。

### 8.8 审计

渲染后每帧抽查并打印；P3 来不及自动化的项改为人工对照末帧检查。
- 文字小于 28 px（底栏与脚注除外）、文字重叠、超出所在纸面；
- 任何内容进入避让区或字幕区（推近按 1.25 倍包围盒计算）；
- 主标题超宽、副标题与署名重叠；
- 渲染文字含 “§”、内部代号（`M0|M1|E-ALL|E-SCREEN|P\d{2}|B[1-6]|Trap|RQ\d`，白名单只有 13 的 “notebook: M0 · M1 · S”）或单字母人名；
- 渲染文字含工程用语（`hash|SHA|of 175|columns kept|files|pipeline|freeze`）；
- 结构靛蓝出现在进度条、卡片细线与路线之外；
- R1–R4、R7（第 5.5 节）；饱和色大块（带 `data-role` 的 rect 面积 > 2,400 px² 且为饱和填充）；每帧语义色相 ≤ 3（03、27a 例外）；
- 场景前 0.4 s 内有动作；同一时刻有两个以上 M 动作重叠。

### 8.9 优先级与日程（截止 10/18）

**优先级。**
- **P0 外壳（所有场景自动受益）：** `tokens.css`、`kit.js` 的多张纸与模板、卡片、进度条、母题、图例槽、发现卡组件；`timeline.json`；`build_subs.mjs` 字幕区；`compose_block` / `compose_film` 的溶解。先用 2–3 个场景的测试时间轴跑通。
- **P1 开场与第 1 段（01–07）：** 讲师最先看到的部分，六个是新建或重建。做完渲出 `block_1.mp4` 交用户审阅（首个交付）。
- **P2 第 2–4 段（08–27）：** 多数是改编；先保证侧卡内容与配色，再细化动效。
- **P3 审计自动化：** R1–R7 与色相检查；来不及就人工检查末帧。

**旁白已定稿**，录像不必等画面：四人可以在 10/15–10/16 录制，画面按录像重新定时（第 7.5 节）。

| 日期 | 任务 |
|---|---|
| 10/14 | 本方案定稿；P0 外壳与 `timeline.json`；测试时间轴跑通溶解与字幕 |
| 10/15 | P1：01–07 → `block_1.mp4` 交审；各人计时朗读；发邮件问讲师；能录的成员开始录像 |
| 10/16 | 按反馈改第 1 段；P2：08–27；录完四段录像 |
| 10/17 | 标 cue 与重新定时；合成四段与成片；排练第 3 轮；填真名与组号；上传；无痕窗口核验 |
| 10/18 | 缓冲；提交 |

单人在本地开发，每完成一个中等步骤（例如一个场景、一项外壳改动）就提交一次，便于回退。

### 8.10 制作风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 只剩 4 天，所有场景都要按新版式重排 | 来不及 | 按 P0–P3 做；P2 场景必要时先把原图缩放放进主纸面，只补侧卡的关键数字与标签 |
| xfade 报时间基或尺寸不一致 | 合成失败 | 每路输入先统一 `fps=30,settb=AVTB,format=yuv420p,setsar=1`；先跑测试时间轴 |
| tpad 或 xfade 引起时长漂移 | 字幕不同步 | ffprobe 断言时长 = Σd ± 1 帧 |
| 交接处冻结帧上残留字幕 | 字幕“粘住” 0.6 s | 断言每段最后 0.2 s 没有字幕 |
| 两次有损编码 | 细线变糊 | 段中间文件 CRF 12；母题可见度在最终成片上验收 |
| 母题太重 | 抢注意力 | 外缘最高 8 %，主线 12 %，内侧渐隐到 0；50 % 与 100 % 各看一次 |
| 侧卡变成凑数的盒子 | 用户再次否决 | 侧卡只放旁白说到的东西；没有就改用 T2 |
| 录像后场景时长变化 | 画面错位 | 进度条、起止、字幕都从 `timeline.json` 与 `overrides.json` 读 |
| 名字迟迟未定 | 画面残留占位 | 一律 “[Name]”；名字填好后重跑脚本 |
| 本机 ffmpeg 无 libass | 不能烧字幕 | 先用 `ffmpeg -filters` 确认 `ass` 滤镜可用 |

---

## 9 讲解、录制与排练

### 9.1 表达

- **语速：** 场景平均约 132 wpm（含停顿），单场 128–135。超时就删句，不加快语速。
- **停顿：** 只在旁白稿标出的 `{pause}` 处停 0.8–1.5 s；其他地方不留长于约 1.5 s 的空白。
- **画幅与视线：** 胸像，头顶留一拳，眼睛在上三分线；看镜头，脚本放在镜头正下方。小窗只有 384×216，脸要占画面高度的约 45 %。
- **状态：** 能量比日常说话高一档；重点词前停顿；句尾下沉；不做手势指向（画面是后期合成的）。
- **脚本用法：** 每人把自己的段落压成“一拍一句”的卡片按拍练习。数字、术语、署名句和措辞边界必须一字不差。
- **非母语表达：** 重读数字和否定词（not、no、barely、only）；说错时停 1 秒，从那一句开头重说，剪辑时只去掉错误部分（若讲师要求不剪辑，则整段重录）。
- **对齐：** 新元素出现后 0.5 s 再开口；数字的出现与念出相差 ≤ 0.5 s。

### 9.2 数字念法

念出的数字与屏幕精度相同；区间读 “interval … to …”；下降用动词（“falls by”）；百分点读 “percentage points”。

| 屏幕 | 念法 |
|---|---|
| 15.8 % / 4.5 % | “fifteen point eight percent … four point five percent” |
| 16.9 % / 14.0 % | “sixteen point nine percent … fourteen point zero” |
| 15.79 vs 15.8 | “fifteen point seven nine percent against the published fifteen point eight” |
| 1,496 | “one thousand four hundred and ninety-six” |
| 0.961 → 0.828 | “zero point nine six one … falls to zero point eight two eight” |
| −0.131 | “a paired drop of zero point one three one” |
| +0.008 [0.000, 0.016] | “rises by zero point zero zero eight, interval zero point zero zero zero to zero point zero one six” + “inconclusive” |
| κ = 0.70 | “Cohen's kappa is zero point seven zero”；不说 “70 percent agree” |
| +23.2 pp [6.2, 40.1] | “twenty-three point two percentage points … interval six point two to forty point one” + “an association” |
| 70 / 52 of 100 | “70 of every 100 … only 52 of 100” |
| Brier +0.074 | “worsens by zero point zero seven four” |

**发音表（四人统一）。** HbA1c “H-B-A-one-C”；NHANES “EN-haynz”；AUC “A-U-C”；κ “kappa”；Brier “BRY-er”；DAG “dag”；Yeo-Johnson “YO-johnson”。

### 9.3 措辞边界

证据等级取自 `governance/claims.csv`：E1 “confirms”，E2 “shows”，E3 “is consistent with”，E4 “suggests”。不用因果动词。

| 主张 | 可以说 | 不要说 |
|---|---|---|
| 泄漏检查（C01，E2） | “AUC falls to 0.828, a paired drop of 0.131 … the 0.961 was the label leaking back in.” | “The model is 96 % accurate.” “Leakage is gone for good.” |
| 缺失值代码（C03–C04） | “Erased 29 of 721 HbA1c-based positives; only six changed label.” 只说 “results of exactly 7.0” | “Deleted 29 diabetic labels.” “All 29 were 7.0.” |
| 离群值 | “Its upper fence lies above the diagnostic threshold, so 519 of them are diabetes by definition.” | 把 519 说成一个发现 |
| minimal vs systematic（C05，E3） | “Rises by 0.008, interval 0.000 to 0.016 … inconclusive: underpowered, not evidence of no effect.” | “Preparation improves AUC.” “No difference.” “Equivalent.” |
| 类别权重（C06，E2） | “From minimal to systematic, the Brier score worsens by 0.074.” | 念 0.076；把 41 % 说成对美国成人的风险估计；把训练部分的 17 % 与加权的 14.0 % 混用 |
| 识别 vs 筛查（C07，E2） | “The all-adults AUC mostly measures recognition of known patients: spectrum bias.” | “Our model screens diabetes at AUC 0.781.” |
| prior-care 项（C08，E3） | “Consistent with recognition and screening pulling apart … the lower end lies inside our margin, so this stays inconclusive.” | “Care items hurt screening.” “The best screening model.” |
| 年龄混杂（C11，E2） | “Confounding by age … its interval includes zero.” | “Insurance has no effect.” “Insurance causes diabetes.” |
| Simpson 与 DAG（C13，E3） | “Six reversed sign, all within noise … A causal diagram flags most of them … We report this as exploratory.” | “We explained Simpson's paradox.” 把 6 个反转说成真实的反转 |
| 治疗掩盖（C14，E1） | “250 test below 6.5 percent, and 165 of those take insulin or pills.” | “All 250 are controlled by treatment.” “HbA1c is the truth.” |
| 未确诊不平等（C15，E3） | “An association, from a small group.” | “Lacking insurance causes missed diagnoses.” |
| 复现（C23，E2） | “15.79 percent against the published 15.8.” | “Our 14.0 percent matches NCHS.” |
| 留出集（C25，E3） | “The leakage drop repeats and the population gap points the same way, though 25 undiagnosed positives are too few to test it alone.” | “Independent validation.” 提外部评审 |
| 事先固定的假设 | “Of six hypotheses locked before we saw any related data … only three were supported.” | “10 of 17 hypotheses confirmed.” |
| 公平性 | “The model flags 70 of every 100 diagnosed diabetics, but only 52 of 100 undiagnosed ones.” | 把每 100 人的点阵说成实际人数 |
| 署名 | “`<Name:2>`'s exploration …”“run by `<Name:3>`” | 讲他人的工作却用 “I found …” |
| GenAI | “Generative AI drafted much of our code and text; we reviewed it and recomputed every number.” | “No AI was used.” “The AI found the results.” |

### 9.4 设备与录制

- **声音：** 耳机麦克风，嘴距约一拳；峰值 −12 至 −6 dB；开录前录 10 s 房间静音；关窗、关空调和风扇。
- **画面：** 1080p30，摄像头与眼睛同高；窗户在前方，不背光；浅色中性背景，无个人信息，不用虚拟背景；四人同一构图、同一侧主光。
- **文件：** 本地录 MKV，录完转 MP4，命名 `block_<n>_take<k>.mp4`；选定的一条复制为 `video/takes/block_<n>.mp4`。每人至少两条完整可用的 take；原始素材保留到成绩公布。
- **分工：** `<Name:0>` 录第 1 段（01–07，2:31）；`<Name:1>` 录第 2 段（08–14，2:30）；`<Name:2>` 录第 3 段（15–20，2:29）；`<Name:3>` 录第 4 段（21–27，2:45）。
- **主方案：** 每人一次连续录完自己的段落，后期合成；动画与字幕按选定的 take 定时；成片只有 3 个切点，都在交接处。
- **回退方案（讲师要求一次连续录制，或到 10/15 仍未回复）：** OBS 一次连续录制，四人依次讲，正在讲的成员开摄像头和麦克风，其余关闭；摄像头放在 x 1416，y 748，384×216；场景在浏览器里按 N / P 步进；字幕录完后叠加 `full.ass` 或只上传 `.srt`；每人本地同时录备份轨。

### 9.5 排练轮次

| 轮次 | 内容 | 目标 |
|---|---|---|
| 1 | 各人单独朗读自己的段落并计时 | 每段与第 0 节相差 ≤ 5 %；**第 4 段 ≤ 2:50**；实测值回填 `timeline.json` |
| 2 | 四人在线顺读一遍，只听不看 | 交接句、署名句、发音表、措辞边界、名字念法 |
| 3 | 对照第 1 段成片与其余粗剪完整播放 | 数字出现与念出相差 ≤ 0.5 s；字幕与开口相差 ≤ 0.3 s |
| 4 | 各人按正式方式连续录一遍 | 总长 ≤ 11:00，记录卡顿点 |

### 9.6 时间检查点

| 检查点 | 场景 | 目标时刻 | 段长目标 | 容差 |
|---|---|---|---|---|
| 摘要结束 | 03 | 1:18 | — | ±5 s |
| 第 1 段结束 | 07 | 2:31 | 2:31 | ±10 s |
| 第 2 段结束 | 14 | 5:01 | 2:30 | ±10 s |
| 泄漏检查结束 | 18 | 6:53 | — | ±10 s |
| 第 3 段结束 | 20 | 7:30 | 2:29 | ±10 s |
| 第 4 段结束 | 27 | 10:15 | **2:45，硬上限 3:00** | 超过 2:50 即触发砍减 |
| 全片 | — | 10:15 | — | 排练上限 11:00 |

各段保持在约 2:15–2:35（第 4 段 ≤ 3:00）；某段实测比目标长 10 s 以上，先在该段内按下表砍，不把内容挪到别的段。

### 9.7 超时砍减顺序

**第一优先：第 4 段 ≤ 2:50。**

| 顺序 | 场景 | 砍什么 | 节省 |
|---|---|---|---|
| 1 | 24 | 删 “consistent with recognition and screening pulling apart”（画面上的相背箭头保留） | 约 3 s |
| 2 | 22 | 删 “and AUC stays 0.007 above minimal”（侧卡保留小号一行） | 约 3 s |
| 3 | 23 | 删 “as our second finding said”（侧卡发现标签保留） | 约 1.5 s |

**第二优先：全片超过 11:00。**

| 顺序 | 场景 | 砍什么 | 节省 |
|---|---|---|---|
| 1 | 全片 | 停顿统一缩到 0.8 s | 约 5 s |
| 2 | 13 | 删 “from per-variable missing codes to transforms and weights” | 约 3 s |
| 3 | 02 | 删 “a national CDC survey” | 约 1.5 s |
| 4 | 12 | 删 DAG 一句，保留 Simpson 与 “We report this as exploratory.” | 约 6 s |

**不砍：** 每段的自我介绍、署名句、意外发现与交接句；摘要 01–03；08–09（非显然发现）；16–18；21–22；27 的四条回答与核心信息。

### 9.8 同伴反馈（每轮，1–5 分加一句话）

1. 第一分钟后，我能说出项目做了什么、怎么做、发现了什么吗？
2. 我看到的、听到的和字幕一致吗？有没有在读屏幕？
3. 讲他人工作时，我听得出是谁做的吗？
4. 最让我困惑的数字是哪个？哪一句最像在背稿？
5. 语速和停顿合适吗？有没有空等的地方？

另请两位非组员看第 1 段成片与粗剪：两人都能复述四条发现，才算主线通过。

---

## 10 上传前检查清单

**内容。**
- [ ] 两名非组员看完第一分钟就能说出问题、做法与四条发现
- [ ] 每页一个主张；27 个场景的主副标题都通过第 6.1 节自检；没有一个标题是结论、问句或带数字
- [ ] 每页右侧都有内容（侧卡、宽幅右段或右栏路线）；没有空框、空矩阵
- [ ] 每个画面变化都对应一个旁白短语；数字出现与念出相差 ≤ 0.5 s（抽查 01、03、08、18、21、23）
- [ ] 每个 AUC 后面都有一句“这说明什么”；全片没有代码画面
- [ ] 改进与恶化都讲到：18（正确的恶化）、22（Brier）、24（−0.016 与 +0.019）、27（准备的得与失）
- [ ] 每个带区间的数字都说了区间和结论强度；措辞符合第 9.3 节；全片不念 0.076
- [ ] 画面与旁白里没有工程琐事：文件或列的计数、完整性校验、代码与执行结构
- [ ] 每位成员只出现在自己的一段里，顺序固定；没有同框镜头
- [ ] 第 2–4 段以段首卡和自我介绍开头；每段末尾有意外发现与交接句
- [ ] 讲他人工作的场景（11、12、18、19、21、22、23、25）都有口头点名或署名行；25 署 “Robustness checks led by” 加真名
- [ ] **屏幕、字幕和语音里没有单字母成员代号**；没有残留 “[Name]” 或 “[no.]”
- [ ] 颜色角色符合第 5.6 节；四种语义色在第一分钟内都有图例；底栏只列本页的颜色
- [ ] 推近只有 2 次（08、17）；晶须脉冲只有 1 次（21）
- [ ] 内部代号只在 13 出现一次（“notebook: M0 · M1 · S”）
- [ ] 段长 2:31 / 2:30 / 2:29 / 2:45（实测 ±10 s），**第 4 段 ≤ 3:00**
- [ ] 所有上屏和口述的数字都在 `numbers_on_slides.csv` 中（含第 11.4 节的补登行），notebook 10.11 节的断言通过
- [ ] 全部旁白由四位成员亲口录制，没有合成语音

**字幕。**
- [ ] 每条 ≤ 2 行 × 42 字符；字幕区与图形、小窗、名签、图例行无冲突
- [ ] 字幕与开口相差 ≤ 0.3 s；停顿、静默卡、每段最后 0.2 s 没有字幕
- [ ] `full.srt` 与烧录字幕文字一致；%、pp、κ 与屏幕一致；HbA1c、NHANES 拼写正确

**画面质量。**
- [ ] 母题在成片里可见但不抢眼；纸面阴影可见
- [ ] 交接处 0.6 s 溶解平滑，段首卡静默 ≤ 0.8 s；段内 0.4 s 溶解
- [ ] 片头第 0 帧即片头卡；进度条从第 1 秒起可见

**技术与合规。**
- [ ] 总长 ≤ 12:00（目标 10:15）；上传后以 YouTube 显示的时长再核对
- [ ] 响度约 −16 LUFS；没有爆音；四段音量一致
- [ ] 画面里没有个人数据：姓名以外的学号、邮箱、路径中的用户名、浏览器书签或通知
- [ ] `full.srt` 已作为 English 字幕上传
- [ ] 可见性为 Public；标题含组号；片尾卡写组号
- [ ] 无痕窗口打开链接，确认未登录也能播放
- [ ] 缩略图：片名 “Who gets labelled diabetic?” 加 03 的四张发现卡，没有小字
- [ ] 说明里有代号对照一行与章节时间（第 7.6 节）
- [ ] 链接写入 `notebooks/final/team.json` 的 `video_url`，运行 `.venv/Scripts/python tools/build_final.py --fill-team notebooks/final/CA6003_NHANES_Diabetes.ipynb`，再运行 `--validate-only` 确认没有残留的 [TEAM TO FILL]
- [ ] 提交前由一位非负责人再检查一遍

---

## 11 数字核对与待补登

### 11.1 核对方法

每个上屏或口述的数字都来自 `video/data/*.json`。这些文件由 `video/data/build_data.py` 只读已保存的结果生成，并与 `results/S10/numbers_on_slides.csv` 断言一致；逐值出处见 `video/data/SOURCES.md`。场景里不手敲数字。第 4 节每个场景的“数字（来源）”一行写明了文件与键；本方案没有新增或改动数值，只换了用法。

若结果文件或 CSV 有变动：先运行 `.venv/Scripts/python video/data/build_data.py`（及 `build_geometry_s10_11_15.py`），再重做受影响的场景。

### 11.2 各场景数字一览

| 场景 | 数字 | 文件 |
|---|---|---|
| 01 | 15.8 %、4.5 % | `db516.json` |
| 02 | 5,730 | `funnel.json` |
| 03 | 7.0 %、0.961、+0.008 | 常量；`leak_gate.json`；`prep_band.json` |
| 05 | 16.9 %、14.0 %、15.79 % vs 15.8 % | `funnel.json`；`db516.json` |
| 07 | 6、3、3 | `hypotheses.json` |
| 08 | 57、1,496、7.0 % | `blanket_recode.json`；常量 |
| 09 | 29 of 721、6 | `blanket_recode.json` |
| 10 | 542、6.8 %、519 | `iqr_fence.json` |
| 11 | 95.7、97.6、6.62（≈ 0） | `vif_skew.json` |
| 12 | 6 of 224 | `simpson.json` |
| 13 | 14、13 | `arms.json` |
| 14 | 29 | `blanket_recode.json` |
| 15 | +5.3 pp、+0.7 pp [−2.6, +3.9] | `age_std.json` |
| 16 | 0.70、250 of 819、165 | `label_split.json` |
| 17 | 152、+23.2 pp [6.2, 40.1]、n = 49 | `label_split.json`；`undiagnosed.json` |
| 18 | 0.961、0.828、−0.131 [−0.148, −0.114] | `leak_gate.json` |
| 19 | 86 %、50、49.5 / 50.5 | `tree.json` |
| 20 | 70、52 per 100、0.80 | `tpr_100.json` |
| 21 | +0.008 [0.000, 0.016]、±0.01、0.011 | `prep_band.json` |
| 22 | +0.074、41 % vs 17 %、+0.007 | `brier.json` |
| 23 | 0.836、0.781、84 % | `recognition.json` |
| 24 | −0.016、+0.019 [0.004, 0.034] | `care_flip.json` |
| 25 | 1,146、25 | `holdout.json` |
| 26 | 0.131、0.008 | `leak_gate.json`；`prep_band.json` |
| 27 | 0.961 | `leak_gate.json` |

### 11.3 六个事先固定假设的判定（07）

按 `results/metrics_S10.json` 的 `scoreboard` 中 `prior_exposure = none` 的 6 行逐条核对（2026-10-14）。`verdict_counts_prereg_none` = supported 3、inconclusive 3、refuted 0，与 `video/data/hypotheses.json` 的 `prereg_n` 6、`prereg_supported` 3、`prereg_inconclusive` 3 一致。假设编号只出现在本表，不上屏。

| 07 卡上的白话名 | 编号 | 锁定判定 | 估计与区间 | 说明 |
|---|---|---|---|---|
| Systematic vs minimal AUC | H2b | inconclusive | ΔAUC +0.0079 [0.00001, 0.0158] | 子判定：AUC inconclusive；Brier refuted（等价不成立：变差）；BMI 系数比不可检验，按锁定规则记 inconclusive |
| Screening gap and its cause | H2c | inconclusive | AUC 差 +0.055 [0.028, 0.086] | 子判定：两人群之差 supported；去掉 prior-care 项后全体成人 supported、尚未确诊者 inconclusive；对 ADA-lite supported |
| Training label and who is missed | H3 | inconclusive | −0.016 [−0.079, 0.028] | 三个分层全部 inconclusive |
| Tree root is a leaked item | B2t | supported | — | 树的根节点是泄漏项 |
| Class weights worsen calibration | B6a | supported | ΔAUC +0.0006 [−0.0017, 0.0028] | AUC 不变、Brier 变差、阈值 0.5 下平衡准确率升高，三项都 supported |
| Survey weights cost little AUC | B6b | supported | ΔAUC −0.0027 [−0.0062, 0.0008] | 非劣效成立 |

所以 07 的六张卡是 3 个 ✓（4、5、6 号）与 3 个虚线框 “?”（1、2、3 号），旁白 “only three were supported” 与之一致。

### 11.4 需补登到 `numbers_on_slides.csv` 的数字

补登方式：在 `notebooks/sections/09_synthesis.py` 的 `NUM` 列表中加行（slide、label、source key、format），重跑 §10，让 10.11 节的断言覆盖这些值。CSV 由脚本生成，不能手改。标 * 的行目前没有标量键，需要先把对应标量存入 metrics。

| # | 值 | label（英文，入 CSV） | source key | 场景 |
|---|---|---|---|---|
| 1* | 15.8 | DB516 published total prevalence (%) | `results/S4/db516_replication.csv`（total, All, crude, nchs）→ 建议存为 `S4:db516.nchs_total` | 01、05 |
| 2* | 4.5 | DB516 published undiagnosed prevalence (%) | 同上（undiagnosed）→ 建议存为 `S4:db516.nchs_undiagnosed` | 01 |
| 3 | 16.9 | unweighted prevalence, combined label (%) | `S1:prevalence_comb.unweighted` | 05 |
| 4* | 6 | pre-specified hypotheses (prior exposure none) | 由 `S10:scoreboard` 计数 → 建议存为 `S10:prereg_none_n` | 07 |
| 5 | 3 | pre-specified hypotheses supported | `S10:verdict_counts_prereg_none.supported` | 07 |
| 6 | 3 | pre-specified hypotheses inconclusive | `S10:verdict_counts_prereg_none.inconclusive` | 07 |
| 7 | 57 | genuine codes caught by blanket recode | `S3:blanket_recode.questionnaire_only_cells` | 08 |
| 8 | 6.8 | HbA1c IQR fence, upper (%) | `S3:outliers.a1c_iqr_fence_upper` | 10 |
| 9* | 14 | preparation steps | `results/S6/step_catalogue.csv`（14 行）→ 建议存为 `S6:n_steps` | 13 |
| 10* | 13 | steps switched on in systematic preparation | `arms.json` `groups.toggles.S` 计数 → 建议存为 `S6:n_steps_S` | 13 |
| 11 | −2.6 / +3.9 | insurance gap, age-standardised, interval low / high (pp) | `S4:standardisation.insured_uninsured.std_ci[0]` / `[1]` | 15 |
| 12 | 0.70 | kappa self-report vs HbA1c (unweighted) | `S5:labels.agreement_unweighted.kappa` | 16 |
| 13 | 165 | self-reported below 6.5 on medication | `S5:masking.below_6_5_on_med` | 16 |
| 14 | 49 | uninsured adults with HbA1c >= 6.5 (n) | `S5:undiagnosed_inequality.proportions.uninsured.n` | 17 |
| 15 | 0.80 | specificity of the shared threshold | `S8:spec` | 20 |
| 16* | 40.9 / 17.0 | systematic mean predicted risk / observed prevalence, training part (%) | `results/S7/calibration.csv`（arm=S，pop=E-ALL）→ 建议存为 `S7:calibration.S.mean_p` / `.prevalence` | 22 |
| 17 | 0.004 / 0.034 | prior-care removal, not-yet-diagnosed adults, interval low / high | `S7:headline.minus_care_escreen.lo` / `.hi` | 24 |
| 18 | 25 | hold-out positives among not-yet-diagnosed adults | `S9:holdout.metrics[arm=S&tier=1&pop=E-SCREEN].n_pos` | 25 |

旧方案补登表里的 175、78、27、0.044 与晶须端点 +1.8 / +8.8 不再上屏或口述，删去。

### 11.5 定义常量与外部参考值（不入 CSV，脚本中以常量注明出处）

| 值 | 含义 | 出处 | 场景 |
|---|---|---|---|
| 0.5 | AUC 轴起点 | 定义 | 03、18、23、25 |
| 6.5 % | HbA1c 诊断阈值（标签定义） | notebook 5.1 节；`funnel.json` `a1c_cut` | 02、09、16、17 |
| 1.5 × IQR | 教科书的离群值规则 | notebook 3.8 节 | 10 |
| ±0.01 | 事先固定的 margin | `governance/hypotheses.md`；`prep_band.json` `sesoi` | 03、21、24 |
| 10 | VIF 参考线 | notebook 4.9 节 | 11 |
| 7.0 %、9.0 %；示例值 7、9、77、99 | 与缺失值代码重合的真实值；示意值 | notebook 3.4 节 | 03、08、14 |
| 49.5 / 50.5 | 树的分裂点（图注文字） | `tree.json`（取自树的文字输出） | 19 |
| “of 100” | 把 TPR 0.70 / 0.52 换算成每 100 人 | `tpr_100.json` | 20 |

### 11.6 不使用的数字

- **已核实但不上屏：** −0.072、+0.055、+0.076、+0.060、0.964 / 0.848 / 0.851 / 0.791（留出集）、27 estimates、0.044 pp、30.5 %、85、11,933 及漏斗中间级、4,911、971、569、23（29 − 6）、响应率 34.6 % / 25.7 %、调整 OR 2.22、60 岁以上的 34 % / 10 %（只画柱，不标值）。
- **不念：** 0.011（只放脚注）；晶须端点 +1.8 / +8.8、−0.022 / −0.009、0.066 / 0.081（只画不标）。

---

## 12 评分覆盖与风险

### 12.1 课程 brief 覆盖

| 要求 | 场景 | 讲到什么 |
|---|---|---|
| 全员出镜，贡献可区分 | 小窗与名签全程；04 团队页；段首卡 08、15、21；署名 11、12、18、19、21、22、23、25 | 一人一段；口头署名 |
| 治理（与分析相关） | 05、06、07、21、24、25、27 | 调查设计与权重（16.9 % vs 14.0 %）与官方复现；数据使用协议 → 标签只能来自调查、小群体只作探索；“筛查时刻可得”规则；事先固定的假设与 margin；留出集只评一次；GenAI 声明 |
| 剖析与数据质量，含非显然发现 | 08、09、10、14 | 统一重编码删掉 1,496 个有效值与 29 个 HbA1c 阳性（标签藏住损害）；IQR 离群值是病人 |
| EDA：冗余、多重共线 | 11 | 体重与 BMI 的 VIF 95.7 / 97.6；重复血压读数取平均 |
| EDA：偏度 | 11 | 甘油三酯偏度 6.62 → Yeo-Johnson 后约 0 |
| EDA：谬误 | 12、15、23 | Simpson（6 of 224）与 DAG 中介；年龄混杂（+5.3 → +0.7 pp）；spectrum bias |
| minimal vs systematic，同一基础模型 | 02、13、18、21 | 三种准备，同一 logistic regression、同一折；naive → minimal（泄漏）；minimal → systematic（+0.008） |
| 改进与恶化 | 09、18、21、22、24、27 | 恶化：−0.131（正确的恶化）、Brier +0.074（有害）、−0.016（全体成人）；改进：保住有效值、+0.008 与 +0.019（都 inconclusive）、去掉类别权重后 +0.007；27 汇总 |
| 偏差分析 | 15、16、17、20、23、24 | 混杂；治疗掩盖 HbA1c；未参保者更常未确诊；检出率 70 vs 52（每 100 人）；spectrum bias |
| 贡献与反思（新颖或意外） | 01、04、08、15、21；07、14、20、26；27 | 自我介绍与分工；四个“最意外”；局限与 GenAI |
| ML 是证据，不是目标 | 02、18、19、26、27 | “models as measuring instruments”；树揭示泄漏机制；核心信息句 |
| ≤ 12:00，第 4 段 ≤ 3:00 | — | 10:15；第 4 段 2:45 |

| 准则 | 场景 | 观众看到的证据 |
|---|---|---|
| Appropriateness | 05、08、10、11、16–18、20–23 | 加权对比、得失对比条、IQR 围栏、VIF 与偏度、按比例的 Venn、泄漏检查、点阵、差值与 margin 带、哑铃图 |
| Correctness & Clarity | 01–04、07、14、20、26、27 | 摘要式开场；团队页；一人一段；名签；段首卡；署名；意外发现；底栏指引 |
| Data Interpretation | 11、12、15–17、21–24 | VIF、偏度、混杂、Simpson、中介、κ、区间与 margin、spectrum bias |
| Novelty & depth | 03、08–09、18–19、23–24、26 | 被删的 7.0；插补出的 50；全体成人 AUC 度量的是识别；模型当量具与泄漏探测器 |

### 12.2 内容风险

| 风险 | 对策 |
|---|---|
| +0.008 被看成失败 | 03 先把它说成“发现”；21 画出区间与 margin；22、27 说明准备的价值在保住有效值，代价在校准 |
| 摘要说出结论后，后面变成重复 | 每个细讲场景都给出摘要没有的证据（机制、区间、对照），并用发现标签明确“这是哪一条的证据” |
| 讲他人的工作，贡献变模糊 | 口头点名 + 署名行；段首卡 “Presents” 行；团队页成果行；`team.json` 记录各人负责的章节 |
| 第 4 段超时 | 目标 2:45；第 1 轮排练即检查；第 9.7 节先砍第 4 段 |
| 数字太密 | 每场景上屏 ≤ 3 组；补登表之外不加数字 |
| 画面空、右侧空 | 模板与 R1–R8；侧卡只放旁白说到的东西 |
| 不允许剪辑 | 第 9.4 节回退方案 |
| 夸大主张 | 第 9.3 节措辞边界；第 2 轮排练专查 |
| 名字没填就上传 | 检查清单；审计拦截单字母人名；上传前人工核对没有 “[Name]” |

---

## 13 关键决定

### 13.1 决定

| # | 决定 | 要点 |
|---|---|---|
| 1 | 故事稿为准 | 27 个场景、旁白、时长、数字与成员时长（2:31 / 2:30 / 2:29 / 2:45，共 10:15）以 v3 故事稿为准 |
| 2 | 七段进度条 | Overview · Data & governance · Data quality · EDA & preparation · Labels & bias · Experiments · Results & conclusions；摘要与议程属于 Overview；进度条从第 1 秒起可见。故事稿的 “Exploration & preparation” 映射为 EDA & preparation |
| 3 | 标题只写主题 | 按标题稿的规则逐个映射；故事稿多出的场景（02 Study design、03 Main findings、05 Survey design and weights）按同一规则自写；屏幕上不给研究问题编号 |
| 4 | “Leakage check” | 18 的主标题用 Leakage check，与旁白一致（T9）；标题稿的 “Leakage test” 不用 |
| 5 | 多张纸与六种模板 | 视觉稿的网格与 T1–T6；配对稿与视觉稿坐标冲突时以视觉稿为准；右侧永远有内容 |
| 6 | 只画旁白说到的东西 | 配对稿的 971 格开场网格不用（01 的旁白讲全国 15.8 % 与 4.5 %）；漏斗底图与 11,933 不用；17 只画一行风险差；21 不画尚未确诊者那一行；25 用对照点图而不用执行时间线 |
| 7 | 语义色与图例在第一分钟 | 01 蓝；02 红、灰、青；03 侧卡完整图例；03 与 27a 允许四种色相同帧；底栏只列本页颜色 |
| 8 | 母题、纵深、图标恢复 | 母题 8–12 %，标题行母题带；双层阴影；面板标题；试管、尺子、漏水桶、天平、问卷板 |
| 9 | 发现标签作回扣 | 03 的四张发现卡缩成侧卡底部的小标签，在细讲场景出现；27a 原位回到画面 |
| 10 | 反思页统一 T4 | 07、14、20、26 都是“一句话 + 一张大图”，侧卡放关键数字或发现标签 |
| 11 | 转场 | 段内 0.4 s 溶解；交接 0.6 s 溶解进段首卡，段首卡静默 0.8 s（故事稿的 1.2 s 改为 0.8 s，场景时长不变，08 / 15 / 21 的语速变为 131 / 133 / 129 wpm）；章节卡与片头卡也只静默 0.8 / 1.0 s，第一句在卡上说，避免超过 1.5 s 的无声（评审修订） |
| 12 | 片头卡 1.0 s、片尾卡 1.5 s | 场景时长按故事稿不变；视觉稿建议的 2.0 s 与 ≥ 3.0 s 不采用，以保持成员时长并避免开头的空等 |
| 13 | 推近两次 | 08（被划掉的 7.0）与 17（152 人） |
| 14 | 不讲工程琐事 | 屏幕与旁白不出现文件或列的计数、完整性校验、代码与执行结构、构建工具；治理只讲与分析有关的部分 |
| 15 | 名字与代号 | `<Name>` 记号；不用单字母代称成员；底栏 “Notebook section N.M”；保留 “Robustness checks led by `<Name:1>`” 与 13 的 “notebook: M0 · M1 · S” |
| 16 | 假设判定已核对 | 6 个事先固定的假设：3 supported（B2t、B6a、B6b），3 inconclusive（H2b、H2c、H3），0 refuted（第 11.3 节） |
| 17 | 底栏节号已核对 | 按最终 notebook 的标题逐条核对；17 补 5.3，20 补 8.2，24 补 7.9 |
| 18 | 首个交付 | 第 1 段（01–07）新版式成片先交用户审阅 |

### 13.2 待确认

1. **给讲师的邮件。** 草稿：
   > “Dear [lecturer], our group plans to submit one YouTube video under 12 minutes. Each member presents one continuous part, in turn, in a small camera window beside animated charts; no shot shows more than one member. Each part is recorded in one continuous take, and captions are added afterwards. May the four takes be joined into one video, or must the whole video be recorded in a single session? Thank you, Group [no.]”
   - 回复“可以拼接” → 第 9.4 节主方案；
   - 回复“必须一次录制”，或 10/15 仍未回复 → 回退方案。
2. **真名与组号。** 填进 `notebooks/final/team.json` 的 `members[].name` 与 `group_number`；之后重新生成字幕并重新合成。
3. **同步仓库文档。** `team.json` 的 `video_segment`、`docs/team_roles.md` §5、notebook 团队表的 “Video” 列改为：`members[0]` 0:00–2:31；`members[1]` 2:31–5:01；`members[2]` 5:01–7:30；`members[3]` 7:30–10:15。内容列也要更新：第 2 段讲冗余与偏度、Simpson（`<Name:2>` 的探索）；第 3 段讲年龄混杂（本人）与泄漏检查、决策树（`<Name:3>` 的实验）；稳健性核查署 `<Name:1>`，由第 4 段讲。更新后运行 `tools/build_final.py --fill-team` 与 `--validate-only`（交 main 处理）。
4. **CSV 补登。** 第 11.4 节的 18 行；标 * 的需先存标量。
5. **成员确认跨作者讲解。** 11、12 用 `<Name:2>` 的探索；18、19 用 `<Name:3>` 的实验；21、22 用 `<Name:1>` 的准备步骤与类别权重；25 署 `<Name:1>`。原作者在第 2 轮排练时核对措辞。
6. **GenAI 声明。** 27 的措辞须与 `governance/genai_log.csv` 和 `docs/team_roles.md` §6 一致，由 `<Name:0>` 在排练时核对。
7. **字幕校对人。** 指定一人校对 `full.srt` 与烧录字幕（建议 `<Name:0>`）。
