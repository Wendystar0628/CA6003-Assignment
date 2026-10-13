# CA6003 讲解视频方案

合并自四份研究稿：叙事结构（01）、视觉系统（02）、分镜与旁白（03）、质量与录制（04），并按“全片无合影”约束改写。旁白与屏幕文字为英文，其余为中文。所有数字已对照 `results/S10/numbers_on_slides.csv`（下称 CSV）、`results/final_metrics.json`、`results/metrics_S*.json` 与 `governance/claims.csv` 核对，见第 12 节。

---

## 0 一页摘要

**核心信息。** “The score is not the finding. What the score reveals about the data is.” 分数本身不是发现，分数暴露出的数据问题才是。

**结构。**

```text
Ch1 Hook        A  0:00 ─┐  0.961 — good?  + 角色卡片（无合影）
Ch2 Rules       A  0:35  │  问题 · 三个陷阱 · 队列 · DUA · NCHS 复现
Ch3 Data clues  B  2:00  │  先看后洗：1,496 vs 57 · 29 of 721（非显然发现）· 离群值 · 14 步 · M0/M1/S
Ch4 EDA         C  4:00  │  VIF · 偏度 · 年龄混杂 · Simpson/DAG
Ch5 Label       C  5:11  │  陷阱二：κ 0.70 · 250 of 819 · 152 未确诊 · E-ALL/E-SCREEN
Ch6 One model   D  6:15  │  陷阱一：0.961 → 0.828 · 插补 50；陷阱三：+0.008 不确定 · Brier 恶化
Ch7 Screening   D→B 8:07 │  0.836 vs 0.781 · 就诊痕迹反转 · B：留出集与事后核查
Ch8 Answers     D  9:20  │  三个陷阱，三个回答
Ch9 Reflection  A B C D A 9:44 ─┘  四段单人短片（各 10–14 s）+ A 收尾 → 10:56
```

**总时长 10:56**（656 s），上限 12:00，余量 1:04；28 个场景；旁白 1,473 词，平均 135 wpm。

| 成员 | 出镜时长 | 占比 | 旁白词数 | 场景 |
|---|---|---|---|---|
| A | 2:33（153 s） | 23 % | 341 | 1–5、24、28 |
| B | 2:30（150 s） | 23 % | 330 | 6–10、22、25 |
| C | 2:29（149 s） | 23 % | 335 | 11–15、26 |
| D | 3:24（204 s） | 31 % | 467 | 16–21、23、27 |
| 合计 | 10:56（656 s） | 100 % | 1,473 | 28 |

**五个最重要的决定。**
1. **单人出镜。** 任何画面只出现一位成员，并且只在其说话时出现；团队用动画角色卡片介绍；02 的四人画廊版式（G）删除。
2. **一条时间轴。** 03 的 28 个场景是唯一时间轴；01 的 9 章按场景边界重新计时；签名视觉、检查点和砍减顺序都用同一套场景编号。
3. **成员再平衡。** 稳健性场景（22）由 B 讲（B 负责 §9）；收尾段压缩 3 s。D 从 3:38 降到 3:24，B 从 2:13 升到 2:30，总长仍为 10:56。
4. **数字口径。** 每个上屏数字都有 source key；Brier 一律说清对比：S − M1 = +0.074，类别权重单独贡献 +0.076；CSV 缺的 24 个值在制作前补登（第 12 节）。
5. **录制方式。** 各人分别录制、后期合成；“single continuous video”是否允许剪辑，今天发邮件问讲师。回退方案：在一次连续的 OBS/Zoom 录制里，成员按顺序单独出镜，画面共享已渲染的动画。

---

## 1 目标与约束

**目标。** 这是一段设计过的讲解视频，不是随意的谈话。讲师应能轻松看懂项目及其核心价值：主线连贯，内容逐层展开，视觉和动效专业，强调什么、省略什么都经过取舍，旁白与画面同步。

**作业硬性规则（摘自课程 brief）。**

| 规则 | 落实 |
|---|---|
| “12-minute (maximum)”，超出部分不计 | 10:56；排练上限 11:30 |
| “all group members must appear and present” | 每人出镜 2:29 以上 |
| “single continuous video” | 问讲师；回退方案见 9.6 节 |
| 内容要求（治理、剖析、EDA、准备、对 ML 的影响、非显然发现、最简 vs 系统、贡献与反思） | 逐项对应见 13.2 节 |
| “reasoning, evidence, and interpretation rather than code or model accuracy” | 无代码画面；每个 AUC 后接“这说明什么” |
| 文字简洁、不要大段文字 | 每屏 1 个标题 + ≤ 3 个标注 |
| YouTube 公开链接 + 组号 | 第 11 节 |

**评分（各 25 %）。**

| 准则 | 核心要求 | 本方案的主要抓手 |
|---|---|---|
| Appropriateness | 探索、剖析、清洗、偏差分析、EDA、模型评估各阶段使用恰当的技术与可视化 | 每个阶段一个签名视觉（第 7 节） |
| Correctness & Clarity | 各阶段技术正确，解释清楚；**各成员的贡献区分清楚并有记录** | 单人主讲段、lower-third、第一人称贡献句、贡献链（视觉 12） |
| Data Interpretation | 统计量、分布、关系；冗余、多重共线、偏度、分析谬误；有证据的结论 | 场景 11–15、18–21 |
| Novelty & depth | 问题、数据、准备策略、偏差分析的原创性；用 basic ML 为数据准备决定提供证据 | 三个陷阱；被删的 7.0；插补出的 50；识别与筛查之分 |

**项目约束。** 不用幻灯片：画面是之后由 Claude 制作的定制动画场景，加上成员单人出镜。只用 basic models，不用 LLM。截止日期 10/18，今天 10/13。

---

## 2 核心信息与叙事结构

### 2.1 核心信息与三条支撑

| # | 支撑信息 | 关键证据 | 场景 |
|---|---|---|---|
| S1 | 高 AUC 可能是泄漏 | 0.961 → 0.828（−0.131 [−0.148, −0.114]）；树在被插补成 50 的“确诊年龄”上分裂（86 % 缺失） | 16–17 |
| S2 | 标签是一次测量 | κ 0.70；819 名自报者中 250 人 HbA1c 低于 6.5 %，其中 165 人在用药；152 人未确诊；无保险者 +23.2 pp [6.2, 40.1] | 14–15、20 |
| S3 | 认真准备几乎不动 AUC，价值在别处 | +0.008 [0.000, 0.016]，不确定；保住 1,496 个有效值；0.836 vs 0.781；去掉就诊痕迹后 −0.016 vs +0.019 | 6–7、18–21 |

### 2.2 三个陷阱

- **名称与编号**与 notebook §1、§10 一致：Trap 1 **Leak**，Trap 2 **Label**，Trap 3 **Little gain**。
- **揭示顺序**是 Label（C，场景 14）→ Leak（D，场景 16）→ Little gain（D，场景 18）。要先讲清标签，D 才能使用 E-SCREEN。
- **陷阱条**从场景 2 起常驻在标题区右侧，当前所在的陷阱高亮；章卡上同时写陷阱编号和问句，例如 “Trap 2 · Is the label the truth?”。顺序因此虽然跳号，观众始终知道自己在哪个陷阱里。

### 2.3 叙事弧

采用 01 推荐的混合结构：开场提出三个问题；A、B、C、D 依次在自己的章节里“埋线索、收证据”；Ch8 逐个回答；Ch9 是贡献与反思。成员段落连续，贡献好区分；陷阱提供悬念；“问题 → 证据 → 回答”对应 brief 的 “reasoning, evidence, interpretation”。纯生命周期结构会变成清单，纯陷阱结构没有剖析与 EDA 的位置，所以都不单用。

### 2.4 渐进分层

| 层 | 章 / 场景 | 观众此时新知道的 | 只依赖 |
|---|---|---|---|
| L1 Hook | Ch1–Ch2 开头（1–2） | 0.961 这个分数值得怀疑；三个陷阱；模型只是仪器 | 无 |
| L2 Context | Ch2（3–5） | 5,730 人；标签 = 自报或 HbA1c ≥ 6.5 %；治理规则；官方数字已复现 | L1 |
| L3a 数据线索 | Ch3（6–10） | 清洗本身会毁掉信息（7.0）；离群值大多是病人；14 个步骤；M0/M1/S | L1–L2 |
| L3b 解读与标签 | Ch4–Ch5（11–15） | 冗余、偏度、谬误各对应一个决定；标签里有就医接触；152 人与 E-SCREEN | L1–L3a |
| L3c 实验 | Ch6–Ch7（16–22） | 同一模型下 M0→M1→S 的变化；哪些是改进、哪些是恶化及其原因；E-ALL 与 E-SCREEN 的差 | L1–L3b |
| L4 Synthesis | Ch8（23） | 三个陷阱各一句回答 | L1–L3 |
| L5 Reflection | Ch9（24–28） | 各人的贡献与意外发现；局限；GenAI 声明 | L1–L4 |

### 2.5 贯穿对象

**决定：不用 01 的合成人物 “Adult X”。** 理由：03 已经有真实的贯穿对象，而在一部讲数据治理的视频里，合成人物容易被当成伪造记录，每次出现都要加 “synthetic” 声明，占用时间。

真实的贯穿对象有三个，每个都在开头出现、中间回收、结尾回到画面：

| 对象 | 出现 | 回收 | 收尾 |
|---|---|---|---|
| 0.961 | 1（钩子） | 16（裂开成 0.828） | 23（Leak 的回答）、27（D 的意外） |
| 被删的 HbA1c 7.0 单元格 | 6（被划掉） | 7（29 of 721） | 23（“values kept”）、25（B 的意外） |
| 152 名未确诊者 | 15（蓝色方块） | 20–21（E-SCREEN） | 26（52 of 100）、28（局限） |

### 2.6 章节衔接

| 边界 | 衔接句（旁白原文）或章卡 | 画面 |
|---|---|---|
| Ch1→Ch2 | “So, is that good?” → 章卡 “02 · The question” | 角色卡片收进右栏的字母徽章 |
| Ch2→Ch3 | A：“Now B asks whether the data deserve the same trust.” | 章卡 “03 · Data clues” + B 徽章 |
| Ch3→Ch4 | B：“But no cleaning fixes a bad label. C shows why.” | 章卡 “04 · Reading the data” + C 徽章 |
| Ch4→Ch5 | C：“These stay exploratory.” → 章卡 “Trap 2 · Is the label the truth?” | DAG 缩小，Venn 出现 |
| Ch5→Ch6 | C：“Next, D asks what a model makes of this.” | 章卡 “Trap 1 · Is 0.961 skill?” + D 徽章 |
| Ch6→Ch7 | D：“AUC still gains 0.007.” → 章卡 “07 · Whom does the score serve?” | Brier 图缩到角落 |
| Ch7 内 D→B | D：“B checked whether it holds.” | 摄像头硬切到 B，图区不变 |
| Ch7→Ch8 | B：“D, the answers.” | 章卡 “08 · Three answers” |
| Ch8→Ch9 | D：“…and a fair screening test.” | 章卡 “09 · Each of us, one surprise” |

---

## 3 时间轴总表

评分列缩写：**Ap** = Appropriateness，**CC** = Correctness & Clarity，**DI** = Data Interpretation，**NV** = Novelty。wpm 按 词数 ÷ 场景时长计；有章卡的场景，旁白在章卡之后开口，扣除 1.2 s 后的语速也都不超过 150。

| 场景 | 章 | 讲者 | 起止 | 时长 | 词 | wpm | 要点 | 评分 |
|---|---|---|---|---|---|---|---|---|
| 1 | Ch1 Hook | A | 0:00–0:35 | 35 | 75 | 129 | 0.961 好吗？四人四角色 | NV、CC |
| 2 | Ch2 Rules | A | 0:35–0:55 | 20 | 43 | 129 | 问题不是“多准”；三个陷阱 | NV |
| 3 | Ch2 | A | 0:55–1:17 | 22 | 50 | 136 | 5,730 人，标签规则，14.0 % | Ap |
| 4 | Ch2 | A | 1:17–1:35 | 18 | 41 | 137 | DUA；保留 78 / 175 列；哈希锁定 | Ap、CC |
| 5 | Ch2 | A | 1:35–2:00 | 25 | 56 | 134 | 复现 NCHS：15.79 vs 15.8 | CC |
| 6 | Ch3 Data clues | B | 2:00–2:30 | 30 | 64 | 128 | 统一重编码：捕获 57，毁掉 1,496 | Ap、NV |
| 7 | Ch3 | B | 2:30–2:51 | 21 | 47 | 134 | 非显然发现：29 / 721 阳性被删 | NV、DI |
| 8 | Ch3 | B | 2:51–3:13 | 22 | 49 | 134 | 离群值 542 个中 519 个是糖尿病：保留 | DI |
| 9 | Ch3 | B | 3:13–3:38 | 25 | 53 | 127 | 14 个可开关的步骤，各有证据 | Ap |
| 10 | Ch3 | B | 3:38–4:00 | 22 | 50 | 136 | M0 / M1 / S，同一模型 | Ap |
| 11 | Ch4 EDA | C | 4:00–4:31 | 31 | 69 | 134 | VIF 95.7 / 97.6；偏度 6.62 → 决定 | DI |
| 12 | Ch4 | C | 4:31–4:51 | 20 | 44 | 132 | 相关≠因果：+5.3 → +0.7 pp | DI |
| 13 | Ch4 | C | 4:51–5:11 | 20 | 45 | 135 | Simpson：224 次比较中 6 次翻转；中介 | DI |
| 14 | Ch5 Label | C | 5:11–5:40 | 29 | 67 | 139 | 陷阱二：κ 0.70；250 / 819；165 | DI、NV |
| 15 | Ch5 | C | 5:40–6:15 | 35 | 81 | 139 | 152 未确诊；+23.2 pp；E-SCREEN | Ap、NV |
| 16 | Ch6 One model | D | 6:15–6:50 | 35 | 77 | 132 | 陷阱一：0.961 → 0.828，正确的恶化 | NV、Ap |
| 17 | Ch6 | D | 6:50–7:15 | 25 | 58 | 139 | 跳问题项被插补成 50 | NV、DI |
| 18 | Ch6 | D | 7:15–7:45 | 30 | 71 | 142 | 陷阱三：+0.008 [0.000, 0.016]，不确定 | DI、CC |
| 19 | Ch6 | D | 7:45–8:07 | 22 | 50 | 136 | 恶化：Brier +0.074，原因是类别权重 | DI |
| 20 | Ch7 Screening | D | 8:07–8:35 | 28 | 64 | 137 | 识别 0.836 vs 筛查 0.781 | NV、Ap |
| 21 | Ch7 | D | 8:35–9:03 | 28 | 67 | 144 | 去掉就诊痕迹：−0.016 vs +0.019 | NV、DI |
| 22 | Ch7 | B | 9:03–9:20 | 17 | 39 | 138 | 留出集只评一次；六项事后核查 | CC |
| 23 | Ch8 Answers | D | 9:20–9:44 | 24 | 56 | 140 | 三个陷阱，三个回答 | DI、NV |
| 24 | Ch9 Reflection | A | 9:44–9:54 | 10 | 21 | 126 | A：6 个假设只有 3 个被支持 | CC |
| 25 | Ch9 | B | 9:54–10:07 | 13 | 28 | 129 | B：一行清洗代码删掉 29 个阳性 | CC、NV |
| 26 | Ch9 | C | 10:07–10:21 | 14 | 29 | 124 | C：70 vs 52 / 100 被检出 | CC、Ap |
| 27 | Ch9 | D | 10:21–10:33 | 12 | 24 | 120 | D：泄漏 ≫ 准备 | CC |
| 28 | Ch9 | A | 10:33–10:56 | 23 | 55 | 143 | 结论、局限、GenAI | CC |
| 合计 | 9 章 | — | 0:00–10:56 | 656 | 1,473 | 135 | — | — |

**章级汇总。**

| 章 | 场景 | 起止 | 时长 | 讲者 | 核心要点 |
|---|---|---|---|---|---|
| Ch1 Hook | 1 | 0:00–0:35 | 0:35 | A | 0.961 值得怀疑；团队分工 |
| Ch2 Question & rules | 2–5 | 0:35–2:00 | 1:25 | A | 判断的对象、规则和可信度 |
| Ch3 Data clues & preparation | 6–10 | 2:00–4:00 | 2:00 | B | 清洗会毁掉病人；发现变成步骤 |
| Ch4 Reading the data | 11–13 | 4:00–5:11 | 1:11 | C | 冗余、偏度、谬误各变成一个决定 |
| Ch5 Label (Trap 2) | 14–15 | 5:11–6:15 | 1:04 | C | 标签是测量；152 人与 E-SCREEN |
| Ch6 One model, three datasets (Traps 1, 3) | 16–19 | 6:15–8:07 | 1:52 | D | 泄漏被证实；准备的增益很小；一个恶化 |
| Ch7 Screening verdict & robustness | 20–22 | 8:07–9:20 | 1:13 | D、B | 全样本 AUC 度量“认出已确诊”；稳健性 |
| Ch8 Three answers | 23 | 9:20–9:44 | 0:24 | D | 三个陷阱各一句 |
| Ch9 Contributions & reflection | 24–28 | 9:44–10:56 | 1:12 | A、B、C、D、A | 各人一个意外；收尾 |

D 仍然最长（31 %）：同一模型的对比实验是作业要求的核心，再压缩会损失陷阱一和陷阱三的证据。

---

## 4 逐场景分镜与台词

**字段约定。**
- **版式**代码见 6.3 节（F / R / X / S），**动效**代码 M1–M12 见 6.4 节；每个构建步骤由一个旁白词触发。
- **数字**：每场景口述 ≤ 3 个（区间算 1 个）；同屏 1 个主数字 + ≤ 2 个次级数字；灰色数据标签不计。
- **来源**：`V3 · key` = CSV 已有行；**待补登** = 已在 metrics 核实、尚未进 CSV（12.4 节）；**定义** = 常量。
- **术语**：首次出现时在旁白或画面标注里用一句话解释。A–D 录制时换成真名。

### Ch1 Hook · A · 0:00–0:35

#### 场景 01 · 钩子与角色卡片 · 0:00–0:35 · 35 s · A

- **版式：** 0:00–0:15 用 S（A 在左半，右半是 AUC 刻度尺），lower-third “A · Governance & integration · §0–§2” 显示 4 s；0:15–0:35 用 R（A 在右栏，图区是角色卡片）。
- **构建：**
  1. M1 画出竖向 AUC 轴 0.5–1.0，0.5 处标 “coin flip”，1.0 处标 “perfect”。
  2. 念到 “0.961” 时，墨色指针随 M10 计数升到 0.961。此时不用红色，红色要留到场景 16 揭示泄漏时才用。
  3. 念到 “coin flip” 时，0.5 处用 M3 高亮一次。
  4. 念到 “is that good?” 时，其余元素暗到 25 %，只留标题 “AUC 0.961 — good?”。
  5. 四张角色卡片依次原位出现（M3，每张 0.4 s），每张只有墨色字母徽章、角色和节次，没有照片：A “Governance & integration · §0–§2”，B “Data quality & preparation · §3 §6 §9”，C “Exploration, labels & bias · §4 §5 §8”，D “Modelling & conclusions · §7 §10”。
  6. 念到哪位成员，哪张卡保持 100 %，其余暗到 25 %。
  7. 四张卡用 0.9 s 形变（M6 的缓动）缩成右栏底部的 A B C D 徽章，之后常驻；当前讲者的徽章为实心。
- **旁白：**
  > **A**（0:00–0:15）：A basic model scores 0.961 at spotting diabetes. AUC is the chance it ranks someone with diabetes above someone without. 0.5 is a coin flip. So, is that good?
  > **A**（0:15–0:35）：Four of us, four roles. I'm A: I led governance and put the project together. B owns data quality and preparation. C owns exploration, labels and bias. D owns modelling and conclusions. Each will introduce themselves when their part begins.
- **词数：** 75（35 / 15 s = 140 wpm；40 / 20 s = 120 wpm）
- **屏幕文字：** “AUC 0.961 — good?”
- **数字：** 口述 `0.961` ← V3 · S7:headline.auc_M0_eall_T1；`0.5` ← 定义（AUC 的随机基线）
- **衔接：** 徽章落定后，M12 章卡 “02 · The question”（1.2 s）。

### Ch2 Question & rules · A · 0:35–2:00

#### 场景 02 · 问题与三个陷阱 · 0:35–0:55 · 20 s · A

- **版式：** 章卡 1.2 s → F 6 s → R。
- **构建：**
  1. 标题 “How accurate can we get?” 出现；念到 “not” 时暗到 25 %（M3），不用划线。
  2. M12 溶解出新标题 “Who gets labelled diabetic?”，下方标注 “What do data decisions change?”。
  3. 念到 “One / Two / Three” 时，三张陷阱卡依次原位出现（M3），墨色线描图标，不填色：“Leak · High AUC = skill?”（漏水的桶）、“Label · Label = truth?”（尺子）、“Little gain · Does prep pay?”（天平）。
  4. 三卡用 0.9 s 形变缩成标题区右侧的陷阱条，之后常驻。
- **旁白：**
  > **A**：Our question is not 'how accurate?' It is: who gets labelled diabetic, and what do our data decisions change? Three traps wait. One: a high AUC may be leakage. Two: the label is a measurement. Three: careful preparation may barely move the AUC.
- **词数：** 43 / 20 s = 129 wpm
- **屏幕文字：** “3 traps: Leak · Label · Little gain”
- **术语：** leakage（画面标注 “the model peeks at the answer”）
- **数字：** 无
- **衔接：** 陷阱条落定，漏斗从图区左侧画入。

#### 场景 03 · 数据与队列 · 0:55–1:17 · 22 s · A

- **版式：** R
- **构建（视觉 2 Cohort funnel）：**
  1. M2 画出顶条 `11,933`（灰）。
  2. M5 逐级收窄：`7,809` age ≥ 20 → `6,064` examined → `5,767` HbA1c measured → `5,730` not pregnant；每级的掉出部分变成幽灵条，淡出到 20 %。
  3. 念到 “5,730” 时，末条变青色，数字放大。
  4. 念到 “Positive means” 时，两个小圆 “self-report” ∪ “HbA1c ≥ 6.5 %” 合成 “positive”（M3）。
  5. 念到 “Weighted” 时，出现 `14.0 %` callout，标签为 “weighted to US adults”。
  - 标题区角标：“NHANES 2021–23 · CDC/NCHS public files”。
- **旁白：**
  > **A**：The data: NHANES, a US health survey from the CDC. We study 5,730 adults with an HbA1c result, a blood test for average sugar. Positive means a self-reported diagnosis, or HbA1c of 6.5 percent or more. Weighted, 14.0 percent are positive.
- **词数：** 50 / 22 s = 136 wpm
- **屏幕文字：** “5,730 adults · 14.0 % positive”
- **数字：**
  - 口述：`5,730` ← V1 · S1:n_cohort；`6.5 %` ← 定义（标签阈值，§5.1）；`14.0 %` ← V1 · S1:prevalence_comb.weighted
  - 仅画面：`11,933` ← V1 · S1:funnel.DEMO_L participants；`7,809` / `6,064` / `5,767` ← 待补登 · S1:funnel.*（12.4 节第 1–3 行）
- **衔接：** 14.0 % 缩成角标，DUA 清单出现。

#### 场景 04 · 数据使用协议与最小化 · 1:17–1:35 · 18 s · A

- **版式：** R
- **构建：**
  1. 清单第一项 “DUA: no re-identification · no linkage”，打上青色对勾。
  2. 175 个小方块组成的网格中，97 个暗到 25 %（M3），计数 175 → 78（M10）。
  3. 两枚指纹图标：“files: SHA-256 verified”、“hypotheses: SHA-256 locked”；底部一行 “simple models only: L2 logistic · shallow tree”。
- **旁白：**
  > **A**：Governance came first. The data user agreement forbids re-identification and linkage, so we did neither. We kept only 78 of 175 columns. Files are verified by fingerprint, and hypotheses were locked by fingerprint before any experiment.
- **词数：** 41 / 18 s = 137 wpm
- **屏幕文字：** “Keep 78 of 175 columns”
- **数字：** 口述 `78` ← 待补登 · S1:minimisation.kept；`175` ← 待补登 · S1:minimisation.raw_columns
- **衔接：** 网格缩成 “verified” 徽章；标题换成 “Can we trust the numbers?”。

#### 场景 05 · NCHS 复现 · 1:35–2:00 · 25 s · A

- **版式：** R；最后 5 s 切 F，A 在全屏中说交接句。
- **构建：**
  1. 两栏表 “Ours / NCHS Data Brief 516” 逐行出现，每行打勾：Total 15.79 / 15.8；Diagnosed 11.30 / 11.3；Undiagnosed 4.49 / 4.5（单位 %）。
  2. 徽章 “27 estimates · max gap 0.044 pp”。
- **旁白：**
  > **A**：Can you trust our survey code? We re-ran a published NCHS report, Data Brief 516. Overall prevalence: 15.79 percent for us, 15.8 for NCHS. Diagnosed and undiagnosed shares match too. In all, 27 published estimates match closely. Now B asks whether the data deserve the same trust.
- **词数：** 56 / 25 s = 134 wpm
- **屏幕文字：** “Ours 15.79 % = NCHS 15.8 %”
- **数字：**
  - 口述：`15.79` ← V7 · S4:db516.total；`15.8` ← 待补登（外部发布值）· results/S4/db516_replication.csv（total / All / crude，列 nchs）；`27` ← 待补登 · S4:db516.n_estimates
  - 仅画面：`11.30`、`4.49` ← V7 · S4:db516.diagnosed / undiagnosed；`11.3`、`4.5` ← 同一 CSV 的 nchs 列；`0.044` ← 待补登 · S4:db516.max_abs_diff_pp
- **衔接：** 交接句说完 → M12 章卡 “03 · Data clues”（B 徽章）→ 摄像头硬切到 B。

### Ch3 Data clues & preparation · B · 2:00–4:00

#### 场景 06 · 先看后洗：统一重编码 · 2:00–2:30 · 30 s · B

- **版式：** 章卡 1.2 s → F 12 s（B 首次出镜，lower-third “B · Data quality & preparation · §3 §6 §9” 显示 4 s）→ R → X（念到 1,496 时，≤ 10 s）。
- **构建（视觉 3 The struck 7.0，步骤 ①–④）：**
  1. 一张小表（舒张压、脉搏、HbA1c 三列），示例值标 “illustrative”。旁边一行规则 “Rule: 7, 9, 77, 99 → missing, every column”。不出现代码。
  2. 念到 “57 genuine codes” 时，切 X 版式：灰柱 `57` 用 M2 长出，标签 “genuine codes caught”。
  3. 念到 “deletes” 时，表中 3 个合法读数（77、99、7.0）依次被 M7 红线划掉（本场景最多 3 次）；红色斜纹柱 `1,496` 用 M2 长出，标签 “valid cells destroyed”。两柱按比例绘制。
  4. 念到 “7.0 percent” 时，M9 推近被划掉的 HbA1c 单元格 “7.0”，停 2 s。
- **旁白：**
  > **B**：I'm B. I led the data-quality audit and the preparation steps. Before cleaning anything, I looked. NHANES stores 'refused' and 'don't know' as short numeric codes. The common shortcut turns those codes into missing in every column. It catches 57 genuine codes. It also deletes 1,496 valid measurements, including HbA1c values of exactly 7.0 percent.
- **词数：** 64 / 30 s = 128 wpm（扣除章卡后 133 wpm）
- **屏幕文字：** “1,496 valid cells lost · 57 codes caught”
- **数字：** 口述 `57` ← 待补登 · S3:blanket_recode.questionnaire_only_cells；`1,496` ← V2 · S3:blanket_recode.valid_cells_destroyed_cohort；`7.0 %` ← 数据值（§3.4：被删的 29 个 HbA1c 值中 28 个是 7.0 %、1 个是 9.0 %，S3:blanket_recode.per_variable.LBXGH = 29）。示例值 77、99 ← 定义（示意，非结果）。
- **衔接：** 被划掉的 7.0 留在画面上，成为下一场景的主角。

#### 场景 07 · 非显然发现：被删掉的阳性 · 2:30–2:51 · 21 s · B

- **版式：** R
- **构建（视觉 3，步骤 ⑤）：**
  1. HbA1c 条带图，6.5 % 阈值线；7.0 与 9.0 处的点变成红色斜纹。
  2. 账本：`721` 个 HbA1c 阳性组成一条横条，其中 `29` 个用 M5 掉出。
  3. 掉出的 29 个里，大部分挂上 “also self-reported” 徽章、变回灰色；剩下 `6` 个保持红色，标签 “flipped to negative”。
  4. 右上角出现墨色标签 “Non-obvious finding”（M3），不做印章动画。
- **旁白：**
  > **B**：Those values are diabetes by definition. The shortcut erased 29 of 721 HbA1c-based positives. Six people flipped to negative; the rest also reported a diagnosis, so self-report hid the damage. No summary table shows this. You find it only by looking.
- **词数：** 47 / 21 s = 134 wpm
- **屏幕文字：** “Non-obvious: 29 of 721 positives erased”
- **数字：** 口述 `29`、`721`、`6` ← V2 · S3:blanket_recode.a1c_positives_lost / a1c_positives / l_comb_flips。被自报“救回”的人数只用图形表示，不标数（理由见 12.3 节）。
- **衔接：** HbA1c 直方图淡入，右尾被点亮。

#### 场景 08 · 离群值保留 · 2:51–3:13 · 22 s · B

- **版式：** R
- **构建：**
  1. M1 画轴；HbA1c 直方图，右尾很长。
  2. 6.8 % 处画出围栏，M11 箭头标 “1.5 × IQR fence”。
  3. 围栏外的 `542` 个值点亮：`519` 个青色（diabetic，保留下来的有效值），23 个灰色。
  4. 先出现标签 “delete?”，再用 M12 溶解成三格 “Flag → Review → Keep”。
- **旁白：**
  > **B**：Second decision: outliers. The textbook rule deletes anything beyond one and a half interquartile ranges. For HbA1c that flags 542 adults, and 519 of them have diabetes. Those are not errors. They are the disease. We flagged them, checked them, and kept every one.
- **词数：** 49 / 22 s = 134 wpm
- **屏幕文字：** “519 of 542 flagged values are diabetic”
- **数字：** 口述 `1.5` ← 定义；`542`、`519` ← V2 · S3:outliers.a1c_iqr_flagged / a1c_iqr_flagged_positive。仅画面：`6.8 %` ← 待补登 · S3:outliers.a1c_iqr_fence_upper
- **衔接：** 保留下来的点缩成一张卡片，成为 14 张步骤卡中的第一张。

#### 场景 09 · 十四个准备步骤 · 3:13–3:38 · 25 s · B

- **版式：** R
- **构建：**
  1. 14 张小卡片 P01–P14 排成两行，按 B1–B6 六个块分组，初始为灰色描边。
  2. 旁白每念到一组，该组卡片变青（M3），露出纯文字证据标签：P01 “file zeros”、P02 “codes per variable”、P03 “availability rule”、P04–P05 “redundancy”、P06–P07 “top-code flags”、P08–P10 “skew · scale”、P11–P12 “class & survey weights”、P13 “splines”、P14 “waist-to-height”。
  3. 全部点亮后，上方出现锁形标签 “no step reads the label · permuted-label test”。
- **旁白：**
  > **B**：Every finding became a switchable preparation step, fourteen in all. Repair file-format zeros. Recode codes variable by variable. Keep only what exists at screening. Merge repeated readings and prune near-duplicate columns. Flag top-coded ages. Tame skew, scale, and weight. Each step cites its evidence, and none ever sees the label.
- **词数：** 53 / 25 s = 127 wpm
- **屏幕文字：** “14 steps, each with its evidence”
- **数字：** 口述 `14` ← 待补登 · results/S6/step_catalogue.csv（14 行，P01–P14）。卡片上不放数字。
- **衔接：** 14 张卡收成三条泳道。

#### 场景 10 · 三个数据版本 · 3:38–4:00 · 22 s · B

- **版式：** R 16 s → F 6 s（B 在全屏中说交接句）
- **构建：**
  1. 三条泳道（参照 `figures/S6_arm_matrix.png`）：M0 红色斜纹描边、内部空白，标签 “every column”；M1 灰色，只点亮 P03；S 青色，14 格全亮。
  2. 每条泳道末端标出列数（数据标签）：88 / 46 / 42 columns。
  3. 三条泳道汇入同一个盒子 “one L2 logistic regression · same folds”，盒子上方出现挂锁 “hypotheses locked”。
  4. 泳道暗下去，只留文字 “the label?”。
- **旁白：**
  > **B**：We built three versions of the data. M0: the naive analyst, every column. M1: naive, plus only the rule that bars post-diagnosis items. S: all fourteen steps. One simple logistic regression for all three, hypotheses locked first. But no cleaning fixes a bad label. C shows why.
- **词数：** 50 / 22 s = 136 wpm
- **屏幕文字：** “M0 naive · M1 minimal · S systematic”
- **术语：** L2 logistic regression（画面标注 “a simple, penalised linear model”）
- **数字：** 口述 `14`（同场景 9）。仅画面：`88` / `46` / `42` ← 待补登 · S6:arms.M0 / M1 / S.n_features_t1
- **衔接：** 章卡 “04 · Reading the data”（C 徽章）→ 硬切到 C。

### Ch4 Reading the data · C · 4:00–5:11

#### 场景 11 · 冗余与偏度 · 4:00–4:31 · 31 s · C

- **版式：** 章卡 → F 12 s（C 首次出镜，lower-third “C · Exploration, labels & bias · §4 §5 §8”）→ R
- **构建：**
  1. 左半：两根 VIF 柱 `95.7`（weight）、`97.6`（BMI），用 M2 长出；背后一条浅色参考带 “VIF > 10: severe”。
  2. 右半：空腹甘油三酯直方图，右尾极长，标 `skew 6.62`。
  3. 直方图原位形变为 Yeo-Johnson 变换后的分布，标签变成 `−0.009`。
  4. 两个箭头收束到决定：“→ prune weight (P05)”、“→ transform skew (P08)”，旁注 “implemented by B”。
- **旁白：**
  > **C**：I'm C. I led exploratory analysis, the label audit and bias checks. Two structural problems. Weight and BMI are nearly the same column: their variance inflation factors, which measure how predictable a column is from the others, are 95.7 and 97.6. Fasting triglycerides have a skewness of 6.62: a few huge values dominate. We prune weight and transform the skew.
- **词数：** 69 / 31 s = 134 wpm（扣除章卡后 139 wpm）
- **屏幕文字：** “VIF 95.7 / 97.6 · skew 6.62”
- **数字：**
  - 口述：`95.7`、`97.6` ← V4 · S4:vif.raw_anthropometry.BMXWT / BMXBMI；`6.62` ← V4 · S4:skew.LBXTLG|fasting (WTSAF2YR > 0).raw
  - 仅画面：`−0.009` ← V4（同一键的 `.yj`）；来源角标 “fasting n = 2,820” ← V4（同一键的 `.n`）；`10` ← 定义（VIF 参考线）
- **衔接：** 两个决定收进标签；画面转向保险组的柱图。

#### 场景 12 · 谬误：年龄混杂 · 4:31–4:51 · 20 s · C

- **版式：** R
- **构建：**
  1. M1 画轴；灰柱 `+5.3 pp`，M4 画出区间 [1.8, 8.8]。
  2. 念到 “Standardised for age” 时，柱子原位缩成 `+0.7 pp`，区间变为 [−2.6, 3.9]，跨过 0 的一端变琥珀色。
  3. 右侧小 DAG：Age → Insurance、Age → Diabetes 为实线，Insurance → Diabetes 为带 “?” 的虚线。
  4. 底部标签 “Correlation ≠ causation · confounding”。
  - 颜色：本场景用灰色和墨色，不用蓝色（蓝色专指筛查人群）。
- **旁白：**
  > **C**：Now fallacies. Insured adults show 5.3 points more diabetes than uninsured adults. Does insurance cause diabetes? That would confuse correlation with causation. Age confounds it: the insured are older. Standardised for age, the gap shrinks to 0.7 points, same sign.
- **词数：** 44 / 20 s = 132 wpm
- **屏幕文字：** “Confounding by age: +5.3 → +0.7 pp”
- **数字：** 口述 `5.3`、`0.7` ← V5 · S4:standardisation.insured_uninsured.crude / std。仅画面：两个区间 ← 待补登 · S4:standardisation.insured_uninsured.crude_ci / std_ci
- **衔接：** 两柱缩到角落，224 格矩阵展开。

#### 场景 13 · 谬误：Simpson 与 DAG · 4:51–5:11 · 20 s · C

- **版式：** R
- **构建：**
  1. 224 个小方块作为一个整体出现（不逐个出现）。
  2. 念到 “Six flipped” 时，6 块换成 “↔” 符号并用 M3 高亮；不闪烁，不用红色。
  3. 矩阵缩小，出现 DAG：Race → BMI → Diabetes；M11 箭头指向 BMI 节点，标签 “mediator”。
  4. 角标 “exploratory”。
- **旁白：**
  > **C**：Then we scanned 224 comparisons for Simpson's paradox, where splitting by a third variable flips a sign. Six flipped. A causal diagram, or DAG, suggests why: BMI sits between race and diabetes, so adjusting for it distorts the comparison. These stay exploratory.
- **词数：** 45 / 20 s = 135 wpm
- **屏幕文字：** “224 scanned · 6 flips · exploratory”
- **数字：** 口述 `224`、`6` ← V5 · S4:simpson.n_comparisons / n_flips
- **衔接：** 章卡 “Trap 2 · Is the label the truth?”，陷阱条中的 Label 格点亮。

### Ch5 Label (Trap 2) · C · 5:11–6:15

#### 场景 14 · 标签即测量：治疗掩盖 · 5:11–5:40 · 29 s · C

- **版式：** 章卡 → R
- **构建（视觉 6 Label split，步骤 ①–②）：**
  1. κ 仪表盘（0–1），指针随 M10 停在 `0.70`，刻度带标 “substantial”。
  2. 仪表盘暗下，两个圆按面积比例出现：“told by a doctor”（819）与 “HbA1c ≥ 6.5 %”（721），重叠区标 “both”，不标数。
  3. 念到 “250” 时，仅自报区用 M3 点亮，琥珀色虚线描边，callout `250 of 819`。
  4. 念到 “165” 时，250 中的一部分点染成琥珀实心，标 “on insulin or pills”；其余点标 “untreated”，不标数。
  5. 标题 “Low HbA1c = controlled, not healthy”。
- **旁白：**
  > **C**：Trap two: the label is a measurement. A doctor's diagnosis and a blood test agree only substantially: Cohen's kappa, an agreement score, is 0.70. Of the self-reported diabetics, 250 test below the diabetes threshold, and 165 of those take insulin or pills, so their blood test looks controlled. A blood-test-only label would call treated patients healthy.
- **词数：** 67 / 29 s = 139 wpm（扣除章卡后 145 wpm）
- **屏幕文字：** “κ = 0.70 · 250 of 819”
- **注意：** 不能把 κ 说成 “70 percent agree”。
- **数字：**
  - 口述：`0.70` ← 待补登 · S5:labels.agreement_unweighted.kappa（0.6986）；`250` ← V6 · S5:masking.below_6_5；`165` ← 待补登 · S5:masking.below_6_5_on_med
  - 仅画面：`819` ← V1 · S1:labels.L_self；`721` ← V2 · S3:blanket_recode.a1c_positives
- **衔接：** 仅 HbA1c 区（右圆独占部分）开始发蓝。

#### 场景 15 · 未确诊者与 E-SCREEN · 5:40–6:15 · 35 s · C

- **版式：** R → X（推近 152，≤ 10 s）→ R → F 最后 6 s（C 在全屏中说交接句）
- **构建（视觉 6 步骤 ③–④，视觉 7）：**
  1. 仅 HbA1c 区的 `152` 用蓝色空心方块点亮，M9 推近，callout “152 not yet diagnosed”。
  2. 视觉 7：M1 画出 0 线，点 `+23.2` 落位，M4 晶须画到 `6.2` 与 `40.1`，整段在 0 右侧；标签 “pp, uninsured − insured · association · uninsured n = 49 · exploratory”。
  3. 人群分成两轨：上轨 “E-ALL: every adult · 5,730”（灰色实心圆），下轨 “E-SCREEN: not yet diagnosed · 4,911 · 152 positives”（蓝色空心方块）。下轨加粗，后面 D 将使用它。
- **旁白：**
  > **C**：In total, 152 adults have a high HbA1c and no diagnosis. Among those with high HbA1c, the uninsured are 23.2 percentage points more often undiagnosed, interval 6.2 to 40.1: an association, not proof of cause. Since most positives are already diagnosed, we score two ways. E-ALL: every adult. E-SCREEN: only adults not yet diagnosed, where screening has something to find. Next, D asks what a model makes of this.
- **词数：** 81 / 35 s = 139 wpm
- **屏幕文字：** “E-ALL: everyone · E-SCREEN: not yet diagnosed”
- **数字：**
  - 口述：`152` ← V1 · S1:e_screen.positives；`23.2` ← V6 · S5:undiagnosed_inequality.risk_differences_pp.uninsured - insured.rd_pp；`6.2 to 40.1` ← V6（同一键的 ci_low_pp / ci_high_pp）
  - 仅画面：`5,730` ← V1；`4,911` ← V1 · S1:e_screen.rows；`49` ← 待补登 · S5:undiagnosed_inequality.proportions.uninsured.n
  - 人群定义：H1a 的人群是 “adults with HbA1c of 6.5 or more”（`governance/hypotheses.md`），旁白与之一致。
- **衔接：** 章卡 “Trap 1 · Is 0.961 skill?”（D 徽章）→ 硬切到 D。

### Ch6 One model, three datasets (Traps 1, 3) · D · 6:15–8:07

#### 场景 16 · 陷阱一：泄漏门 · 6:15–6:50 · 35 s · D

- **版式：** 章卡 → F 12 s（D 首次出镜，lower-third “D · Modelling & conclusions · §7 §10”）→ R → X（裂开时刻，≤ 15 s）
- **构建（视觉 4 Leak gate crack）：**
  1. M1 画出 E-ALL 轴，从 0.5 开始，轴底标 “axis starts at 0.5”。
  2. M0 柱长到 `0.961`，红色斜纹（红色第一次出现）。
  3. 柱旁出现三个被移除项的标签 “treatment”、“diagnosis history”、“glucose testing”；念到 “One rule” 时出现 “availability rule”，三个标签暗到 25 %。
  4. 停 1.5 s。M8 裂开：裂纹划过 `0.961`，数字倒数到 `0.828`，柱子缩短并变灰（M1 色）。本片只用这一次 M8。
  5. 右侧用 M4 画出差值 `−0.131 [−0.148, −0.114]`，标签 “paired across folds”。次级数字 “E-SCREEN: −0.072”。
  6. 墨色标签 “correct deterioration”，配青色对勾。
- **旁白：**
  > **D**：I'm D. I led modelling and conclusions. Trap one. The naive model, M0, scores 0.961. One rule: keep only what exists at a screening visit. That removes treatment, diagnosis history and prior glucose testing. Same model, same folds. The AUC falls to 0.828, 0.131 lower. A correct deterioration: the 0.961 was not skill. It was the label leaking back in.
- **词数：** 77 / 35 s = 132 wpm（扣除章卡后 137 wpm）
- **屏幕文字：** “0.961 → 0.828: leakage removed”
- **数字：**
  - 口述：`0.961`、`0.828` ← V3 · S7:headline.auc_M0_eall_T1 / auc_M1_eall_T1；`0.131` ← V3 · S7:leak_gate.T1_E-ALL.est（逐折配对差的均值；两柱相减为 0.133，所以画面标 “paired”）
  - 仅画面：`[−0.148, −0.114]` ← V3（同一键的 lo / hi）；`−0.072` ← V3 · S7:leak_gate.T1_E-SCREEN.est
- **衔接：** 两柱缩成角标，决策树从下方生长出来。

#### 场景 17 · 插补常数 50 · 6:50–7:15 · 25 s · D

- **版式：** R
- **构建（视觉 5 Tree and the 50）：**
  1. 深度 3 的决策树自上而下出现（节点 0.3 s，边 0.4 s）。根节点是 “taking diabetes pills?”（治疗项，红色斜纹）；下一层的分裂节点是 “age at diagnosis ≈ 50”。
  2. 左侧出现 “age at diagnosis” 直方图：`86 %` 为空白，“median” 把它们都填成 `50`，在 50 处堆出一根红色斜纹高柱。
  3. M11 箭头从高柱指向树的分裂节点，标签 “imputed, not measured”。
  - 注意：根节点是治疗项，不是年龄，画面和旁白都不能把年龄说成根节点。
- **旁白：**
  > **D**：How did the model cheat? A shallow decision tree shows it. Its root is a treatment question. Then it splits on age at diagnosis. But 86 percent were never asked that, so filling blanks with the median put 50 in all of them. The tree learned a code for 'never diagnosed'. A skip pattern became a label.
- **词数：** 58 / 25 s = 139 wpm
- **屏幕文字：** “86 % never asked → imputed 50”
- **数字：** 口述 `86`、`50` ← V3 · S7:tree_m0.did040_missing_share / did040_fill
- **衔接：** 树淡出，差值轴与 ±0.01 带出现；陷阱条中的 Little gain 格点亮。

#### 场景 18 · 陷阱三：最简准备对系统准备 · 7:15–7:45 · 30 s · D

- **版式：** R
- **构建（视觉 9 Preparation against the band）：**
  1. M1 画出差值轴 −0.04 … +0.04（场景 21 复用同一根轴）。
  2. SESOI 带 ±0.01 淡入（0.6 s），中性浅灰，虚线边，标签 “±0.01 margin, fixed in advance”。
  3. 青色点 `+0.008` 落位。
  4. 晶须画到 `0.000` 与 `0.016`；右端越过带边，在越界处脉冲一次并变琥珀色。
  5. 次级标签 “smallest detectable: 0.011”；琥珀虚线框 “inconclusive — underpowered, not zero”。
- **旁白：**
  > **D**：Trap three. Does careful preparation help? Compare M1, the minimal arm, with S, the systematic one. The AUC difference is plus 0.008, interval 0.000 to 0.016. Our margin, the smallest effect of interest, was fixed in advance at 0.01. The interval is neither inside it nor beyond it: inconclusive. Underpowered, not proof of no effect.
- **词数：** 71 / 30 s = 142 wpm
- **屏幕文字：** “+0.008 [0.000, 0.016] · inconclusive”
- **数字：**
  - 口述：`+0.008`、`0.000 to 0.016` ← V7 · S7:headline.S_minus_M1_T1_eall.est / lo / hi；`0.01` ← 定义（`governance/hypotheses.md` H2b 的 SESOI）
  - 仅画面：`0.011` ← V7 · S7:headline.S_minus_M1_T1_eall.mdd
- **衔接：** 差值轴缩到角落，校准图出现。

#### 场景 19 · 一个恶化：类别权重与 Brier · 7:45–8:07 · 22 s · D

- **版式：** R
- **构建：**
  1. 校准图（参照 `figures/S7_pr_calibration.png`）：对角线标 “predicted = observed”；S（带类别权重）的曲线远离对角线；“S without class weights”的曲线贴近对角线。
  2. 下方是三行差值条，共用一根轴：
     - “S − M1: Brier +0.074 (worse)”：主数字，红色斜纹；
     - “class weights alone: +0.076”；
     - “S without weights vs M1: Brier ≈ M1 · AUC +0.007”。
- **旁白：**
  > **D**：One step did hurt. From M1 to S, the Brier score, which checks whether predicted risks match reality, worsens by 0.074. The cause is class weights: removing only them improves Brier by 0.076. AUC still gains 0.007.
- **词数：** 50 / 22 s = 136 wpm
- **屏幕文字：** “S vs M1: Brier +0.074 (worse)”
- **数字口径（必须一致）：**
  - S − M1 的 Brier 变化是 **+0.074** ← V7 · S7:scoreboard_detail[hyp_id=H2b&sub=(b) Brier&role=primary].est；
  - 类别权重单独造成 **+0.076**（S − S-B6a）← V7 · S7:scoreboard_detail[hyp_id=B6a&sub=(b) Brier&role=primary].est；
  - 去掉类别权重后，相对 M1 的 AUC 变化为 **+0.007** ← V7 · S7:pure_preparation_S_B6a_vs_M1[pop=E-ALL&metric=roc_auc].diff；Brier 变化为 −0.002（同一键的 brier.diff），画面写 “≈ M1”。
  - 0.074 和 0.076 不能混着念：0.074 永远配 “from M1 to S”，0.076 永远配 “class weights alone / removing only them”。
- **衔接：** 章卡 “07 · Whom does the score serve?”。

### Ch7 Screening verdict & robustness · D, B · 8:07–9:20

#### 场景 20 · 识别与筛查 · 8:07–8:35 · 28 s · D

- **版式：** 章卡 → R
- **构建（视觉 8 Recognition vs screening）：**
  1. M1 画出 0.5–1.0 轴，标 “axis starts at 0.5”。
  2. E-ALL 点（灰色实心圆）`0.836`。
  3. E-SCREEN 点（蓝色空心方块）`0.781`。
  4. 两点之间连线（0.5 s），中间标 `+0.055`。
  5. 念到 “84 percent” 时，下方出现阳性人群的堆叠条：84 % “already diagnosed”（灰）与其余 “not yet diagnosed”（蓝）。标签 “spectrum bias”。
- **旁白：**
  > **D**：Now the second population. On all adults, the prepared model scores 0.836. On adults not yet diagnosed, the people screening is meant to find, it scores 0.781. This is spectrum bias. 84 percent of positives were already diagnosed, so the whole-sample AUC mostly measures recognising known patients. Report the screening number, not the headline.
- **词数：** 64 / 28 s = 137 wpm（扣除章卡后 143 wpm）
- **屏幕文字：** “Recognition 0.836 vs screening 0.781”
- **数字：** 口述 `0.836`、`0.781` ← V7 · S7:headline.auc_S_eall_T1 / auc_S_escreen_T1；`84` ← V1 · S1:labels.known_share_of_comb。仅画面：`+0.055` ← V7 · S7:headline.eall_minus_escreen_S_T1.est
- **衔接：** E-SCREEN 点保留，复用场景 18 的差值轴。

#### 场景 21 · 就诊痕迹反转 · 8:35–9:03 · 28 s · D

- **版式：** R
- **构建（视觉 10 Care traces flip）：**
  1. 被移除的两张卡 “told high blood pressure”、“told high cholesterol” 出现，标 “traces of care”。
  2. 复用场景 18 的轴与 ±0.01 带。E-ALL 点（灰色圆）落在 `−0.016`。
  3. 停 1.5 s。E-SCREEN 点（蓝色方块）落在 `+0.019`，晶须 [0.004, 0.034] 整段在 0 右侧；下端低于 +0.01，在该处脉冲一次并变琥珀色。
  4. 两点之间画一条细折线，表示“换了人群，符号翻转”。标签 “consistent with · not settled”。
- **旁白：**
  > **D**：The twist: remove two items that mark prior care, told high blood pressure and told high cholesterol. On all adults, AUC falls by 0.016. On the not-yet-diagnosed, it rises by 0.019, interval 0.004 to 0.034. Consistent with recognition and screening pulling apart; not settled. B checked whether it holds.
- **词数：** 67 / 28 s = 144 wpm
- **屏幕文字：** “Without care traces: −0.016 vs +0.019”
- **数字：** 口述 `0.016`、`0.019` ← V7 · S7:headline.minus_care_eall.est / minus_care_escreen.est；`0.004 to 0.034` ← 待补登 · S7:headline.minus_care_escreen.lo / hi
- **衔接：** 摄像头硬切到 B（同一章，不出章卡），图区换成时间轴。

#### 场景 22 · 留出集与事后核查 · 9:03–9:20 · 17 s · B

- **版式：** R；B 的 lower-third 重现 4 s：“B · robustness checks · §9”。
- **构建：**
  1. M1 画出时间轴，三个节点依次点亮：“hypotheses locked (SHA-256)” → “experiments frozen” → “hold-out: scored once”。
  2. 念到 “1,146” 时，1,146 个小点作为一个整体出现，标签 “internal check, not independent”。
  3. 账本两行：“6 issues from an external review · checked”、“no locked verdict changed”。
- **旁白：**
  > **B**：Is it robust? I led the robustness checks. An internal hold-out of 1,146 adults, scored once, kept the pattern. An external review raised six issues; none changed a locked verdict. D, the answers.
- **词数：** 39 / 17 s = 138 wpm
- **屏幕文字：** “Hold-out 1,146 · internal check”
- **数字：** 口述 `1,146` ← V7 · S9:holdout.log.n_test；`six` ← 待补登 · S9:postaudit.summary（6 行，register DR-S9-16 至 DR-S9-21；notebook §9.12）。不显示留出集差值 +0.060：每个 E-SCREEN 只有 25 个阳性，差值本身无法单独检验（claims C25）。
- **衔接：** 章卡 “08 · Three answers”（D 徽章）→ 硬切到 D。

### Ch8 Three answers · D · 9:20–9:44

#### 场景 23 · 三个陷阱的回答 · 9:20–9:44 · 24 s · D

- **版式：** 章卡 → F 10 s → R
- **构建（视觉 1 Three traps，回答）：**
  1. 陷阱条的三格用 0.9 s 形变回到图区中央，变成三张卡。
  2. 每念到一个陷阱，对应卡片的内容用 M12 溶解成答案并填色（不做 3D 翻转）：
     - Leak（红）：“0.961 = leakage, not skill”；
     - Label（琥珀）：“Label records care, too”；
     - Little gain（青）：“+0.008, inconclusive”，下面一行 “value: 1,496 values kept · fair screening test”。
- **旁白：**
  > **D**：Trap one: the 0.961 was leakage, not skill. Trap two: the label records care as well as disease, so whole-sample AUC rewards recognising the diagnosed. Trap three: preparation moved AUC by only plus 0.008, inconclusive. Its value lies elsewhere: valid values kept, and a fair screening test.
- **词数：** 56 / 24 s = 140 wpm（扣除章卡后 147 wpm）
- **屏幕文字：** “Three traps, three answers”
- **数字：** 口述 `0.961` ← V3；`0.008` ← V7。仅画面：`1,496` ← V2
- **衔接：** 章卡 “09 · Each of us, one surprise”。

### Ch9 Contributions & reflection · A, B, C, D, A · 9:44–10:56

四段单人短片都用 S 版式：人像在左，“Most unexpected” 卡片在右；lower-third 重现 3 s。图区底部是视觉 12（贡献链），每段点亮该成员的节点。讲者之间用硬切，不出章卡。

#### 场景 24 · A：贡献与意外 · 9:44–9:54 · 10 s · A

- **版式：** 章卡 → S
- **构建：** 卡片上 6 个方块代表 6 个真正事先注册的假设：3 个青色（supported），3 个琥珀虚线（inconclusive），标题 “Locked before testing”。贡献链上 A 的外框点亮：“A · integrates & checks every number”。
- **旁白：**
  > **A**：I led governance and checked every number on screen. Most unexpected: of six hypotheses locked before testing, only three were supported.
- **词数：** 21 / 10 s = 126 wpm（扣除章卡后 143 wpm）
- **屏幕文字：** “Most unexpected: 3 of 6 supported”
- **数字：** 口述 `six`、`three` ← 待补登 · S10:verdict_counts_prereg_none.supported（3）与 inconclusive（3）。不能说成 “10 of 17 confirmed”：那 10 个 supported 中多数属于 analysis_seen。
- **衔接：** 硬切到 B。

#### 场景 25 · B：贡献与意外 · 9:54–10:07 · 13 s · B

- **版式：** S
- **构建：** 卡片上是一个 HbA1c 结果标签 “7.0 · diabetic”，被 M7 划掉一次；计数 “29 positives erased”；小字 “self-report hid it”。贡献链上 B 的节点点亮：“implements · 14 steps”。
- **旁白：**
  > **B**：I led the data-quality audit and the fourteen preparation steps. Most unexpected: one routine cleaning line erased 29 diabetic HbA1c results, and self-report hid it.
- **词数：** 28 / 13 s = 129 wpm
- **屏幕文字：** “Most unexpected: 29 positives erased”
- **数字：** 口述 `14` ← 待补登（同场景 9）；`29` ← V2 · S3:blanket_recode.a1c_positives_lost
- **衔接：** 硬切到 C。

#### 场景 26 · C：贡献与意外 · 10:07–10:21 · 14 s · C

- **版式：** S
- **构建（视觉 11 100 diabetics）：**
  1. 两块 10×10 点阵：左块 “100 diagnosed”，右块 “100 undiagnosed”。
  2. 左块逐行点亮 `70` 个（灰色实心），右块点亮 `52` 个（蓝色）；计数 M10 同步，未点亮的点为空心。
  3. 两块之间相差的 18 个点用 M3 高亮。
  4. 标签 “one shared cut-off · specificity 0.80 · rates per 100”。
  5. 贡献链上 C 的节点点亮：“finds · interprets”。
- **旁白：**
  > **C**：I led exploration, labels and bias. Most unexpected: at one cut-off, the model flags 70 of 100 diagnosed diabetics, but only 52 of 100 undiagnosed.
- **词数：** 29 / 14 s = 124 wpm
- **屏幕文字：** “Flagged: 70 vs 52 of 100”
- **数字：** 口述 `70`、`52`（每 100 人）← V6 · S8:gap_decomposition.tpr_diagnosed（0.70）/ tpr_undiagnosed（0.52）。仅画面：`0.80` ← 待补登 · S8:spec。点阵是把比率换算成每 100 人的示意，不代表两组的实际人数。
- **衔接：** 硬切到 D。

#### 场景 27 · D：贡献与意外 · 10:21–10:33 · 12 s · D

- **版式：** S
- **构建：** 同一根轴上两根柱：“leakage 0.131”（红色斜纹，很高）、“preparation 0.008”（青色，极矮），轴标 “AUC change”。贡献链上 D 的节点点亮：“evaluates”。
- **旁白：**
  > **D**：I led modelling and conclusions. Most unexpected: leakage moved the score far more than careful preparation did. A data problem, not a model problem.
- **词数：** 24 / 12 s = 120 wpm
- **屏幕文字：** “Most unexpected: leakage ≫ preparation”
- **数字：** 仅画面 `0.131` ← V3；`0.008` ← V7
- **衔接：** 硬切到 A。

#### 场景 28 · 收尾：结论、局限、GenAI · 10:33–10:56 · 23 s · A

- **版式：** F 14 s → R 9 s → 片尾卡
- **构建：**
  1. F 期间，标题带 “The score is not the finding”。
  2. 切 R：三枚局限标签依次出现（M3）：“One survey cycle”、“Low response”、“152 undiagnosed positives”。
  3. GenAI 声明卡：“GenAI drafted code & text · reviewed by us · no LLM in the pipeline · every number recomputed”。
  4. 片尾卡：完整的视觉 12（A 外框围住 C finds → B implements → D evaluates → C interprets），标题 “Who gets labelled diabetic?”，下方 “Group [no.] · Thank you”。链接不念。
- **旁白：**
  > **A**：The takeaway: the score is not the finding; what it reveals about the data is. Limits: one survey cycle, low response, only 152 undiagnosed positives. This is a data audit, not a screening tool. Generative AI drafted much of our code and text; we reviewed it and recomputed every number. Thank you.
- **词数：** 55 / 23 s = 143 wpm
- **屏幕文字：** “Audit, not a screening tool”
- **数字：** 口述 `152` ← V1 · S1:e_screen.positives
- **衔接：** 片尾，无。

---

## 5 取舍

判断标准：删掉这一项后，观众还能说清核心思想及其理由吗？能说清，就收起或删除。

| 内容 | 处理 | 场景 | 理由 |
|---|---|---|---|
| 可用性规则与 M0→M1→S 对照 | 主线 | 10、16 | 删掉就无法解释 0.961 为何不可信 |
| 统一重编码删掉 7.0（1,496 vs 57；29 of 721；6 个翻转） | 主线 | 6–7、25 | 非显然发现，也是陷阱三“价值在别处”的证据 |
| DID040 插补成 50，树在它上面分裂 | 主线 | 17 | 泄漏的机制 |
| κ、250 / 819、165、152、+23.2 pp | 主线 | 14–15 | 陷阱二的证据 |
| E-ALL vs E-SCREEN；就诊痕迹 −0.016 vs +0.019 | 主线 | 20–21 | 回答“这个分数为谁服务” |
| 类别权重使 Brier 变差 | 主线 | 19 | 作业要求讲恶化，这是最清楚的一例 |
| VIF、偏度、年龄混杂、Simpson | 主线，压缩到 71 s | 11–13 | brief 点名，每项只讲“发现 → 决定” |
| HbA1c 离群值 542 / 519 | 主线（22 s） | 8 | 离群值是病人，不能删 |
| 公平性：TPR 0.70 vs 0.52 | 一段单人短片 | 26 | 覆盖“bias analysis”，并与陷阱二相连 |
| 留出集、事后六项核查 | 一句话 | 22 | 可信度证据；不念 +0.060 |
| NCHS DB516 复现 | 一句话 + 表 | 5 | 证明调查加权代码没有错 |
| 预注册锁定 | 一句话 | 4、10、24 | 证明结论不是事后挑选 |
| DAG、中介调整 | 一句话 | 13 | 点名“相关不等于因果”的另一种形式 |
| GenAI 声明 | 一句话 + 卡片 | 28 | 如实声明 |
| 响应率 34.6 % / 25.7 % | 只说 “low response”，不念数字 | 28 | 不影响三个陷阱 |
| 亚裔 BMI（51.1 % vs 7.2 %）、WHtR | 删除 | — | E4 探索性，n = 47；让位给公平性 |
| 3×3 标签矩阵、H3 | 删除 | — | 结论不确定，区间都跨 0；要讲清需要整张表 |
| ADA-lite 基线 | 删除 | — | 留出集没有复现（区间跨 0），口头容易听成“优于 ADA” |
| 缺失机制（OR、IPW、Manski、MNAR） | 删除 | — | 结论是“基本不影响” |
| XPT 零值、top-coding、零权重 | 只出现在步骤卡上 | 9 | 不是非显然发现 |
| 置换检验、噪声列、种子、规格曲线、PSU 分组 CV、nested C | 删除 | — | 可信度细节，留在 notebook |
| 系数稳定性 SD 比 | 删除 | — | 事后审计已改为“不可检验” |
| 设计效应、jackknife、自由度 | 删除 | — | 技术上正确，但与理解无关 |
| 树的 E-SCREEN AUC 0.633 / 0.701 | 删除 | — | 只是描述性探针，容易被当成模型比较 |
| Adult X | 删除 | — | 见 2.5 节 |
| 合影、四人画廊、四人轮流钩子、结尾四人同框 | 删除 | — | 单人出镜约束 |

---

## 6 视觉系统

### 6.1 原则

教学网页的规则搬到不可暂停的线性视频，需要改写：

1. **一场景一主张**：先写一句 “viewer can point at ___”；无关数据不上屏，细节留给 notebook。
2. **亮一个、暗其余**：焦点 100 %，其余 25 %，不用模糊；由旁白触发。
3. **渐进构建**：3–6 步，每步对应一个旁白短语；末帧自足可读，兼作缩略帧。
4. **数字随口播出现**：不早于念出它的那个词。
5. **画出不确定性**：效应量都带晶须，并画在 ±0.01 SESOI 带旁。
6. **对照公平**：同轴、同基线，柱从 0 起；AUC 轴从 0.5 起时标 “axis starts at 0.5”。
7. **按比例作图**：几何与数字都由脚本从 CSV/JSON 算出，不手摆、不手敲。
8. **文字极少**：1 个标题（≤ 6 词）+ ≤ 3 个标注（各 ≤ 5 词）；旁白不逐字读屏。
9. **先抛问题**：陷阱章用问句章卡开场。
10. **一个视觉动词**：每场景在 reveal、compare、split、shrink 中只选一个。

### 6.2 视觉识别

**色板（一色一义，全片不变；白底）。**

| 令牌 | 色值 | 唯一含义 | 非颜色编码 |
|---|---|---|---|
| `--ink` | #15202B | 正文、轴线、标题、讲者徽章 | — |
| `--muted` | #5A6672 | 次要文字、M1、E-ALL | 实心圆 |
| `--bad` | #B42318（浅底 #FBE7E5） | 泄漏、伤害、错误：M0、被误删的单元格、0.961 | 45° 斜纹 + 警示三角 |
| `--a` teal | #0D7A63（浅底 #E2F2EE） | 系统准备 S、保留下来的有效值、可用性规则 | 实心 + 对勾 |
| `--b` blue | #2E4DB0（浅底 #E5EAF8） | 筛查人群：E-SCREEN、152 名未确诊者 | 空心方块 |
| `--warn` amber | #A8690E（文字用 #8A5508） | 标签不确定、结论不明（inconclusive） | 虚线描边 |
| `--line` | #DCE1E6 | 网格、SESOI 带的边 | 虚线 |

- 同一张图里，颜色只编码一个变量。比较方案时，颜色按方案（M0 红 / M1 灰 / S 青），人群用形状（圆 = E-ALL，方 = E-SCREEN）；比较人群时反过来。
- notebook 原图里 E-ALL 蓝、E-SCREEN 橙的配色在视频里不沿用。
- **讲者不用颜色编码**：A–D 一律用墨色字母徽章。03 里的“成员专属色”和“色块 wipe”取消。
- 对比度（白底）：ink 16.5，muted 5.9，teal 5.3，blue 7.5，red 6.6；amber 文字一律用 #8A5508。大面积用浅底加同色描边，饱和色只用于线、点、数字和小色块。
- 全片统一用浅色，不做深色版。

**字体**（本地打包，不在线加载）：标题 Source Serif 4（72–88 px）；正文 IBM Plex Sans（标注 34 px，下限 28 px）；数字 IBM Plex Mono tabular-nums（主数字 120–168 px，次级 48–64 px，区间 36 px）；来源标签 24 px，是唯一允许的 24 px。

**网格与固定元素。**
- 画布 1920×1080，外边距左右 96 px、上下 60 px；12 列网格。标题区 y 60–150，图区 y 168–960，底栏 y 984–1020。
- **右栏**：x 1344–1824。顶部是摄像头 480×270（画面宽度的 1/4）；下面是 lower-third；底部是 A B C D 墨色徽章，当前讲者实心，下面一行写各人的节次。
- **陷阱条**：标题区右侧，三格 Leak / Label / Little gain，当前格高亮。
- **数字 callout**：大号 mono 数字加一行 28 px 标签；区间用方括号，在数字之后 0.3 s 淡入。
- **来源标签**：左下角，24 px mono，例如 `§7.5 · V3`，随场景常驻，没有动画。
- **lower-third**：成员第一次开口时显示 4 s（短片里 3 s）：墨色圆形字母徽章 + 两行字（“Member B” / “Data quality & preparation · §3 §6 §9”）。

### 6.3 讲者版式

| 版式 | 构成 | 用途 | 时长限制 |
|---|---|---|---|
| **F** 全屏人像 | 摄像头满幅 + lower-third | 每人首次出镜的前 12 s；交接句；场景 23、28 开头 | 每次 ≤ 15 s |
| **R** 图区 + 右栏（默认） | 左侧 1248 px 图区 + 右栏摄像头 480×270 | 全部数据讲解，约 75 % 的时间 | — |
| **X** 满屏图 | 图区占满全宽；摄像头仍是 480×270，放在右下安全区，图在那个角留空 | 高光时刻：场景 6（1,496 vs 57）、15（152）、16（裂开） | 每次 ≤ 15 s |
| **S** 分屏 | 左侧人像 960×1080（裁成 8:9）+ 右侧图 960×1080 | 场景 1 钩子、场景 24–27 单人短片 | 每次 ≤ 15 s |
| ~~G 四人画廊~~ | — | **删除**（单人出镜约束） | — |

**切换规则。**
1. 任何一帧只出现一位成员，并且是正在说话的那位。不说话的成员不出镜，也没有“陪站”镜头。
2. 换人只换摄像头层，图区不换；换人用硬切，切点放在句间停顿（≥ 0.3 s 静音）处，不做滑动或擦除转场。
3. 章与章之间用 M12 章卡（1.2 s，静止，居中）：章号、短标题、讲者徽章，陷阱章再加问句。章卡计入下一场景的时长，旁白在章卡之后开口。
4. 每位成员第一次出现时，先在 F 或 S 停留 ≥ 3 s（本方案为 12–15 s），再退到 R。
5. 所有成员的人像用同一种构图：胸像，双眼在上三分线，浅色中性背景，同一侧主光，1080p30。人像画面上不加任何动画。

### 6.4 动效语汇

只用下面 12 个动作。缓动：入场用 `cubic-bezier(.2,0,0,1)`；形变和推近用 `cubic-bezier(.4,0,.2,1)`；数据驱动的连续量用线性。

| # | 动作 | 作用 | 时长与细节 | 场景 |
|---|---|---|---|---|
| M1 | 轴绘入 | 交代对象 | 0.6 s；刻度错开 30 ms，刻度标签在轴线画完后 0.3 s 淡入 | 1、3、8、12、16、18、20、22 |
| M2 | 柱从基线生长 | 状态出现 | 0.7 s；柱间错开 120 ms；数值标签随旁白出现 | 3、6、11、16 |
| M3 | 亮一个、暗其余 | 标示焦点 | 0.4 s；其余降到 25 % | 全片 |
| M4 | 晶须 + SESOI 带 | 不确定性 | 点 0.3 s → 晶须 0.5 s → 带 0.6 s；越界端点脉冲一次并变琥珀色 | 12、15、16、18、21 |
| M5 | 漏斗收窄 | 状态转变 | 每级 0.5 s，级间停 0.4 s；掉出部分为幽灵条，淡出到 20 % | 3、7 |
| M6 | 集合分裂或形变 | 状态转变 | 0.9 s；圆面积 ∝ n | 1、2、14、23 |
| M7 | 误删划线 | 标示错误 | 红线 0.25 s，标签 0.3 s；只用于被误删的有效值；每场景 ≤ 3 次 | 6、25 |
| M8 | 数字裂开 | 状态转变 | 裂纹 0.35 s → 错位 0.5 s → 倒数 0.8 s；全片只用一次 | 16 |
| M9 | 镜头推近 | 标示焦点 | 推 0.9 s，停 ≥ 2 s，拉回 0.6 s；缩放 1.0→1.6；每场景 ≤ 1 次 | 6、15 |
| M10 | 计数 | 连续量 | 0.8 s，线性起、末尾减速 | 1、4、14、26 |
| M11 | 标注箭头 | 标示焦点 | 箭头 0.4 s，标签 0.3 s；每次 1 个箭头 | 8、13、17 |
| M12 | 溶解 / 章卡 | 过渡 | 溶解 0.4 s；章卡 1.2 s，静止 | 章边界、2、8、23 |

**禁止无意义的动画。**
- 每个运动都必须对应上表里的一个作用，找不到作用就保持静止。
- 同一时刻只动一个物体；两个动作之间停 ≥ 1.5 s，供观众读数。
- 禁止：飞入、弹跳、旋转、视差、粒子、闪烁、持续的背景动画、打字机效果、3D 翻转、印章砸下。03 中的这些效果已全部改写为上表动作（见 15 节）。
- 动效总时长不超过场景时长的 40 %；场景切走前，末帧必须能独立读懂。
- 背景只用极淡的方格纸纹（≤ 4 % 不透明），完全静止。

### 6.5 可读性与无障碍

| 项 | 规则 |
|---|---|
| 字号 | 内容文字 ≥ 28 px；主数字 ≥ 96 px；只有来源标签可以用 24 px |
| 对比度 | 正文 ≥ 4.5:1，大字 ≥ 3:1 |
| 不只靠颜色 | 红 = 斜纹 + 三角；青 = 实心 + 对勾；蓝 = 空心方块；琥珀 = 虚线；关键区分都有文字标签 |
| 色觉差异 | 红与青在红绿色弱下难分，所以红色永远带斜纹，青色永远不带 |
| 字幕 | 上传 SRT（字幕稿 = 脚本原文，每行 ≤ 42 字符、≤ 2 行），不烧录进画面 |
| 动效敏感 | 不闪烁；每个动画 ≤ 1 s |
| 音频 | 人声 −16 LUFS；不加背景音乐，若加则 ≤ −30 LUFS 且在人声时压低 |

---

## 7 签名视觉清单

| # | 视觉 | 场景 | 讲者 | 上屏 | 数据来源 |
|---|---|---|---|---|---|
| 1 | Three traps | 2（构建）、3–22（陷阱条）、23（回答） | A、D | 0:12 + 常驻 + 0:20 | notebook §1、§10；23 中的数字来自 V2、V3、V7 |
| 2 | Cohort funnel | 3 | A | 0:18 | V1；S1:funnel.*（待补登） |
| 3 | The struck 7.0 | 6–7（回调 25） | B | 0:40 + 0:08 | V2；S3:blanket_recode.questionnaire_only_cells（待补登）；`figures/S3_blanket_recode_damage.png` |
| 4 | Leak gate crack | 16（回调 27） | D | 0:20 | V3；`figures/S7_leak_gate.png` |
| 5 | Tree and the 50 | 17 | D | 0:22 | V3；`figures/S7_tree_m0.png` |
| 6 | Label split | 14–15 | C | 0:35 | V1、V2、V6；S5:masking.below_6_5_on_med（待补登）；`figures/S5_label_strata.png` |
| 7 | Who is undiagnosed | 15 | C | 0:12 | V6；`results/S5/undiagnosed_risk_differences.csv` |
| 8 | Recognition vs screening | 20 | D | 0:25 | V7、V1；`figures/S10_recognition_vs_screening.png` |
| 9 | Preparation against the band | 18（回调 23、27） | D | 0:28 | V7；`figures/S10_scoreboard_forest.png` |
| 10 | Care traces flip | 21 | D | 0:25 | V7；S7:headline.minus_care_escreen.lo/hi（待补登） |
| 11 | 100 diabetics | 26 | C | 0:12 | V6；S8:spec（待补登）；`figures/S8_group_tpr.png` |
| 12 | The chain | 24–27（逐个点亮）、28（片尾完整） | A、B、C、D | 0:49 + 0:05 | `docs/team_roles.md`；无新数字 |

**构建步骤**（细节见对应场景）。
1. **Three traps**：三卡原位出现 → 收成陷阱条 → 场景 23 回到中央，溶解成答案并填红 / 琥珀 / 青（青只表示“系统准备”，不表示“结论成立”）。
2. **Cohort funnel**：灰色顶条 → 四级收窄 + 幽灵条 → 末条 5,730 变青。
3. **The struck 7.0**：示例表（“illustrative”）→ 57 vs 1,496 按比例两柱 → M7 划掉 3 个有效值 → M9 推近 7.0 →（场景 7）721 中 29 掉出、6 个翻转。
4. **Leak gate crack**：轴从 0.5 起 → 0.961 红柱 → 停 1.5 s → M8 裂成 0.828 → 差值晶须；不加 E-SCREEN 面板。
5. **Tree and the 50**：树自上而下（根节点是治疗项）→ 86 % 被填成 50 的高柱 → 箭头指向分裂节点。
6. **Label split**：κ 仪表盘 → 两圆面积 ∝ n（半径比 0.938）→ 250 琥珀虚线 → 其中 165 → 152 蓝色并推近。
7. **Who is undiagnosed**：0 线 → +23.2 → 晶须 6.2–40.1，标 “association · n = 49 · exploratory”。
8. **Recognition vs screening**：哑铃图 0.836（灰圆）/ 0.781（蓝方）+ 0.055 → 84 % 堆叠条。
9. **Preparation against the band**：轴 ±0.04 → 带 ±0.01 → +0.008 → 晶须越界变琥珀 → MDD 0.011。
10. **Care traces flip**：同一根轴 → −0.016 → 停 1.5 s → +0.019 [0.004, 0.034] → 对折线。
11. **100 diabetics**：两块 10×10 点阵 70 / 52，差额 18 高亮；必须标 “one shared cut-off · specificity 0.80 · rates per 100”。
12. **The chain**：无人像；A 外框围住 C finds → B implements → D evaluates → C interprets；单人短片逐个点亮节点，场景 28 显示整条链。

次级图示（刻度尺、角色卡片、DUA 网格、DB516 表、IQR 围栏、步骤卡、泳道、VIF 与偏度、年龄标准化、Simpson 矩阵、校准与 Brier、留出集时间轴）套用同一套动作，数据来源写在各场景中。

---

## 8 制作管线

### 8.1 方案比较与选择

**采用 HTML/SVG 场景 → Playwright 逐帧截图 → ffmpeg。** 它直接复用项目页的令牌和字体，动画是时间 t 的纯函数（逐帧确定、可重复），并可直接读 CSV/JSON。其他工具的分工：OBS 录人像（也是回退方案的现场合成工具）；DaVinci Resolve 免费版做收尾；matplotlib 只作应急静帧。Manim 安装重、风格脱节，CapCut 可能带水印，都不用。

环境：本机有 ffmpeg 与 Node 24；`.venv` 没有 Playwright，可用系统 Edge（`channel: 'msedge'`）。

### 8.2 规格

| 项 | 值 |
|---|---|
| 画面 | 1920×1080，30 fps，SDR，BT.709 |
| 场景中间文件 | 无声 MP4，`libx264 -crf 14 -pix_fmt yuv420p`，BT.709 标签 |
| 人像素材 | 1080p30，MP4 或 MKV；音频 48 kHz |
| 成片 | H.264 High 约 12 Mbps；AAC 192 kbps；−16 LUFS，真峰值 ≤ −1 dBTP |
| 字幕 | 单独的 SRT 文件 |

### 8.3 步骤

1. **锁定脚本。** 以第 4 节为准，成员只改读法，不改数字和措辞边界。
2. **补登数字。** 12.4 节中的值进入 CSV，并通过 §10.11 的断言（见 14 节第 3 项）。
3. **样板。** 先做视觉 4（Leak gate crack），渲染 10 s 验证整条管线：令牌（`tokens.css`）、动作（`motion.js`）、逐帧截图、ffmpeg 合成。
4. **录制。** 各人按场景录制人像和声音（9.6–9.6 节），文件名如 `B_s06_take2.mp4`。
5. **标 cue。** 在音频上标出每个构建步骤的时刻，写成 `cues.json`（场景、步号、秒数）。先录音再做画面，因为每人语速不同。
6. **逐帧渲染。** 每个场景一个 HTML 页，暴露 `window.__seek(t)`；Playwright 按帧调用后截图，经管道送入 ffmpeg。成片约 19,700 帧，图形约占 70 %；分四个进程并行约 15 分钟。
7. **合成。** 右栏的固定元素（徽章、lower-third、陷阱条、来源标签）与图区一起渲染，摄像头区域留空；ffmpeg `overlay` 按剪辑清单（EDL JSON，含 F/R/X/S 版式和时间码）贴入人像，音频只取成员录音。
8. **收尾。** 在 Resolve 里检查时序与响度，导出 SRT，上传。

场景代码一律写成“步骤状态机”，同一份代码既支持逐帧渲染，也支持按空格键手动步进（供回退方案使用）。

### 8.4 日程（截止 10/18）

| 日期 | 任务 |
|---|---|
| 10/13 | 给讲师发邮件；锁定脚本；补登 CSV；做视觉 4 样板 |
| 10/14 | 各人第 1 轮计时朗读；录制人像与声音；标 cue |
| 10/15 | 渲染全部场景；合成粗剪 |
| 10/16 | 第 3–4 轮排练对照粗剪；修正同步问题和超时 |
| 10/17 | 定稿、字幕、上传、无痕窗口核验；填写 team.json |
| 10/18 | 缓冲，提交 |

---

## 9 讲解与录制

### 9.1 表达

- **语速：** 平均 135 wpm，单个场景 120–150 wpm；数字密集的场景不超过 145 wpm。超时就删句，不加快语速。
- **画幅与视线：** 胸像，头顶留一拳空间，眼睛在上三分线；看镜头，脚本放在镜头正下方或贴近镜头的窗口里。
- **状态：** 能量比日常说话高一档；重点词前停顿；句尾下沉。人像画面不做手势指向（画面是后期合成的，指向会错位）。
- **脚本用法：** 每人把自己的段落压成“一拍一句”的卡片（8–10 拍）按拍练习。句子可以略有变化，但数字、术语和措辞边界必须一字不差。
- **非母语表达：** 每句 ≤ 20 词；在语义组之间停顿；重读数字和否定词（not、no、barely、only）；说错时停 1 秒，从那一句开头重说，剪辑时去掉错误部分。
- **对齐：** 新元素出现后 0.5 s 再开口；数字的出现与念出相差 ≤ 0.5 s；关键数字后停 1 s，区间和对比后停 1.5 s。

### 9.2 数字念法

规则：念出的数字与屏幕上的完全一致（精度相同）；先说含义再说数字，或在同一句里说清；区间读 “interval … to …”；下降用动词（“falls by”），不读 “minus zero point”；百分点读 “percentage points”，不读成 “percent”。

| 屏幕 | 念法 |
|---|---|
| 0.961 → 0.828 | “zero point nine six one … falls to zero point eight two eight” |
| −0.131 | “zero point one three one lower” |
| +0.008 [0.000, 0.016] | “plus zero point zero zero eight, interval zero to zero point zero one six” + “inconclusive” |
| κ = 0.70 | “Cohen's kappa … is zero point seven”；不说 “70 percent agree” |
| 1,496 | “one thousand four hundred and ninety-six”（屏幕上是精确值，不念成 “about fifteen hundred”） |
| +23.2 pp [6.2, 40.1] | “twenty-three point two percentage points … interval six point two to forty point one” + “an association” |
| 14.0 % | “fourteen percent” |
| 15.79 vs 15.8 | “fifteen point seven nine … fifteen point eight” |
| 70 / 52 of 100 | “70 of 100 … only 52 of 100” |

**发音表（四人统一）。** HbA1c “H-B-A-one-C”；NHANES “EN-haynz”；AUC “A-U-C”；κ “kappa”；Brier “BRY-er”；DAG “dag”；Yeo-Johnson “YO-johnson”；E-SCREEN “E-screen”；SHA-256 只在画面上出现，旁白说 “fingerprint”。

### 9.3 交接句

所有交接都是单人对单人：讲者看着镜头说完交接句，停 0.5 s，然后硬切。

| 交接 | 场景 | 句子 |
|---|---|---|
| A → B | 5 | “Now B asks whether the data deserve the same trust.” |
| B → C | 10 | “But no cleaning fixes a bad label. C shows why.” |
| C → D | 15 | “Next, D asks what a model makes of this.” |
| D → B | 21 | “B checked whether it holds.” |
| B → D | 22 | “D, the answers.” |
| D → A | 23→24 | 无交接句；章卡 “Each of us, one surprise” |
| 单人短片之间 | 24→28 | 无交接句；硬切，lower-third 重现 3 s |

### 9.4 措辞边界

证据等级取自 `governance/claims.csv`：E1 “confirms”，E2 “shows”，E3 “is consistent with”，E4 “suggests”。不用因果动词。

| 主张 | 可以说 | 不要说 |
|---|---|---|
| 泄漏门（C01，E2） | “The AUC falls to 0.828, 0.131 lower. The 0.961 was not skill.” | “The model is 96 % accurate.” “Leakage is gone for good.” |
| 统一重编码（C03–C04） | “Erased 29 of 721 HbA1c-based positives; six flipped.” | “Deleted 29 diabetic labels.” “Cleaning errors ruined the model.” |
| 最简 vs 系统（C05，E3） | “Plus 0.008, interval 0.000 to 0.016: inconclusive, underpowered.” | “Preparation improves AUC.” “No difference.” “Equivalent.” |
| 类别权重（C06，E2） | “From M1 to S, Brier worsens by 0.074; class weights alone account for 0.076.” | 把 0.074 和 0.076 混着说；把平衡准确率的上升说成改进 |
| 识别 vs 筛查（C07，E2） | “Whole-sample AUC mostly measures recognising known patients.” | “Our model screens diabetes at AUC 0.781.” |
| 就诊痕迹（C08，E3） | “Consistent with recognition and screening pulling apart; not settled.” | “Care traces hurt screening.” “The best screening model.” |
| 年龄混杂（C11，E2） | “Confounding by age; same sign.” | “Insurance has no effect.” “Insurance causes diabetes.” |
| Simpson / DAG（C13，E3） | “Suggests BMI is a mediator; exploratory.” | “We explained Simpson's paradox.” |
| 治疗掩盖（C14，E1） | “250 of 819 are below 6.5; 165 of them take insulin or pills.” | “All 250 are controlled by treatment.” “HbA1c is the truth.” |
| 未确诊不平等（C15，E3） | “An association … interval 6.2 to 40.1.” | “Lacking insurance causes missed diagnoses.” |
| 复现（C23，E2） | “Our survey code reproduces the published 15.8.” | “Our 14.0 percent matches NCHS.”（差别来自标签定义） |
| 留出集（C25，E3） | “An internal hold-out, scored once, kept the pattern.” | “Independent validation.” “Confirmed on new data.” |
| 预注册 | “Of six hypotheses locked before testing, three were supported.” | “10 of 17 hypotheses confirmed in advance.” |
| 公平性 | “At one cut-off, 70 of 100 diagnosed vs 52 of 100 undiagnosed are flagged.” | 把每 100 人的点阵说成实际人数 |
| GenAI | “Generative AI drafted much of our code and text; we reviewed it and recomputed every number.” | “No AI was used.” “The AI found the results.” |

### 9.5 设备与文件

- **声音：** 耳机或有线耳机麦克风，嘴距约一拳，不用笔记本自带麦克风；峰值 −12 至 −6 dB；每次先录 10 s 房间静音供降噪取样；关窗、关空调和风扇，回声大就挂毯子。
- **画面：** 1080p30，摄像头与眼睛同高；窗户在前方，不背光；浅色中性背景，无个人信息，不用虚拟背景；笔记本接电源。
- **文件：** 本地录 MKV，录完转 MP4，命名 `A_s03_take2.mp4`；每个场景至少两条可用 take；原始素材保留到成绩公布。
- **分工：** A 录 1–5、24、28；B 录 6–10、22、25；C 录 11–15、26；D 录 16–21、23、27。

### 9.6 录制方式

**主方案：分别录制，后期合成。** 全片没有同框镜头，每人单独录自己的场景，再按 8.3 节合成，这与单人出镜的设计完全契合；声画质量最高，并且能逐句重录。

**未决：“single continuous video” 的含义。** 这句话可以理解为“提交一个完整的视频文件”，也可以理解为“一次不间断录制、不能剪辑”。今天给讲师发邮件确认（14 节第 1 项）。

**回退方案：一次连续录制。** 如果讲师要求不剪辑，或到 10/15 仍未回复：
- 用 OBS（或 Zoom 的 spotlight 视图）做一次连续录制。正在讲的成员开摄像头、开麦克风，其余成员关摄像头、静音，所以画面里始终只有一个人。
- 渲染好的场景做成可步进的 HTML 播放器，由讲者本人或一名不出镜的成员按空格推进；OBS 中预设 F / R / X / S 四个场景并绑定热键。
- 交接时，上一位关摄像头，下一位开摄像头，OBS 切到对应场景；交接句与章卡照常。
- 每人在本地同时录一份备份轨。画质略低于主方案，口播与画面的同步靠排练（第 10 节的第 4 轮）。

---

## 10 排练与时间控制

### 10.1 排练轮次

| 轮次 | 内容 | 目标 |
|---|---|---|
| 1 | 各人单独朗读自己的场景并计时 | 每个场景与第 3 节的时长相差 ≤ 10 %；把实测值回填到第 3 节 |
| 2 | 四人在线顺读一遍，只听不看 | 检查交接句、发音表、措辞边界 |
| 3 | 配合粗剪动画完整播放 | 数字出现与念出相差 ≤ 0.5 s |
| 4 | 不停顿的完整彩排（回退方案的实录也按这一轮执行） | 总长 ≤ 11:00，记录卡顿点 |
| 5（可选） | 针对卡顿点补练 | — |

### 10.2 时间检查点

| 检查点 | 场景 | 目标时刻 | 容差 |
|---|---|---|---|
| Ch1 结束 | 1 | 0:35 | ±5 s |
| Ch2 结束（A → B） | 5 | 2:00 | ±10 s |
| Ch3 结束（B → C） | 10 | 4:00 | ±10 s |
| Ch4 结束 | 13 | 5:11 | ±10 s |
| Ch5 结束（C → D） | 15 | 6:15 | ±10 s |
| Ch6 结束 | 19 | 8:07 | ±10 s |
| Ch7 结束（B → D） | 22 | 9:20 | ±10 s |
| Ch8 结束 | 23 | 9:44 | ±10 s |
| 全片结束 | 28 | 10:56 | 上限 11:30 |

某个检查点超出容差时，下一轮先压缩超时的那一章；累计超过 +20 s 时，按 10.4 节的顺序砍减。

### 10.3 同伴反馈（每轮，1–5 分加一句话）

1. 我能用一句话复述这一章的结论吗？
2. 我看到的和听到的一致吗？有没有在读屏幕？
3. 最让我困惑的数字是哪个？
4. 哪一句最像在背稿？
5. 语速和清晰度合适吗？

另请两位非组员看粗剪：两人都能说出三个陷阱，才算主线通过。

### 10.4 超时砍减顺序

| 顺序 | 场景 | 砍什么 | 节省 |
|---|---|---|---|
| 1 | 3、9、13 | 动画停顿从 1.5 s 缩到 1.0 s（不动内容） | 约 6 s |
| 2 | 1 | 删 “Each will introduce themselves when their part begins.” | 约 4 s |
| 3 | 9 | 步骤列举只留三个例子 | 约 6 s |
| 4 | 5 | 删 “Diagnosed and undiagnosed shares match too.” | 约 3 s |
| 5 | 4 | 删指纹一句（场景 10 仍说 “hypotheses locked first”） | 约 5 s |
| 6 | 17 | 删 “How did the model cheat?”，压缩树的描述 | 约 4 s |
| 7 | 13 | 删 DAG 一句，保留 Simpson 与 “exploratory” | 约 7 s |

合计可省约 35 s。**不砍：** 场景 6–7（非显然发现）、14–16、18–21（陷阱证据，含恶化与不确定）、22（B 的可区分贡献）、23–28（回答、贡献与反思）；单人短片不短于 10 s；lower-third 不删。

---

## 11 上传前检查清单

**内容验收。**
- [ ] 两名非组员看完都能说出三个陷阱
- [ ] 每个场景只有一个主张、一个主图或主数字；屏幕上没有完整句子
- [ ] 数字出现与念出相差 ≤ 0.5 s（抽查场景 3、6、16、18、20）
- [ ] 每个 AUC 后面都有一句“这说明什么”；全片没有代码画面
- [ ] 改进和恶化都讲到：场景 16（正确的恶化）、19（Brier）、21（反转）
- [ ] 每个带区间的数字都说了区间和结论强度
- [ ] 措辞符合 9.4 节；0.074 与 0.076 没有混用
- [ ] 每位成员：lower-third、一整段主讲、一段单人短片、至少一句 “I led …”
- [ ] **全片没有任何同框镜头**；任何时刻只出现一位正在说话的成员
- [ ] 所有上屏和口述的数字都在 CSV 中（含 12.4 节的补登行），§10.11 断言通过
- [ ] 全部旁白由四位成员亲口录制，没有合成语音

**技术与合规。**
- [ ] 总长 ≤ 12:00（目标 10:56）；上传后以 YouTube 显示的时长为准再核对
- [ ] 响度约 −16 LUFS；没有爆音；四人音量一致
- [ ] 画面里没有个人数据：姓名以外的学号、邮箱、文件路径中的用户名、浏览器书签或通知
- [ ] SRT 已上传；自动字幕已人工校对（HbA1c、NHANES、kappa 必须手改）
- [ ] 可见性为 Public；标题含组号；片尾卡写组号
- [ ] 用无痕窗口打开链接，确认未登录也能播放
- [ ] 缩略图：一个主数字（0.961）加三陷阱简图，没有小字
- [ ] 链接写入 `notebooks/final/team.json` 的 `video_url`，运行 `.venv/Scripts/python tools/build_final.py --fill-team notebooks/final/CA6003_NHANES_Diabetes.ipynb`，再运行 `--validate-only` 确认没有残留的 [TEAM TO FILL]
- [ ] 提交前由一位非负责人再检查一遍

---

## 12 数字核对与待补登

### 12.1 核对方法

逐个对照第 4 节的口述与仅画面数字：CSV 行（值与展示精度）、`final_metrics.json` 与 `metrics_S*.json` 的键、`claims.csv`、`hypotheses.md`、`results/S4/db516_replication.csv`、`results/S6/step_catalogue.csv`、`governance/register/S9.csv`。保留的数字全部有来源，没有与来源不符的值；24 个值已核实但不在 CSV（12.4 节）；定义常量与外部参考值见 12.5 节；删除项见 12.3、12.6 节。

### 12.2 02 标记的待核项

| 项 | 核对结果 | 来源 | 处理 |
|---|---|---|---|
| 漏斗中间级 7,809 / 6,064 / 5,767 | 正确 | `metrics_S1.json` funnel：Age >= 20；Interviewed and MEC-examined (RIDSTATR = 2)；HbA1c measured (LBXGH present) | 场景 3 上屏，补登 |
| 57 | 正确，含义是“统一重编码捕获的真实拒答/不知道代码” | S3:blanket_recode.questionnaire_only_cells；notebook §3.4（“harm exceeds gain about 26-fold”） | 场景 6 口述，补登 |
| E-SCREEN 0.844 / 0.772 | 正确：M0 0.8441，M1 0.77227，二者之差与 −0.072 一致 | S7:arm_metrics[arm=M0&tier=1&model=lr].escr_auc；S7:baselines.M1.escr_auc | **不使用**；场景 16 只显示差值 −0.072（已在 CSV） |
| 165 | 正确 | S5:masking.below_6_5_on_med；claims C14 | 场景 14 口述，补登 |


### 12.3 相对 03 的修正

| 场景 | 03 原稿 | 修正 | 理由 |
|---|---|---|---|
| 5 | “27 published estimates are reproduced”；徽章 “27 / 27 reproduced” | “match closely”；徽章 “27 estimates · max gap 0.044 pp” | 27 个点估计中有 24 个落在发布的区间内（S4:db516.kg_matches_published_ci = 24） |
| 6 | 没有 57 | 加入 “It catches 57 genuine codes” | 让“得 57、失 1,496”的取舍可见 |
| 7 | 画面上有 23 和 971 | 改为图形，不标数 | 23 是差值，无法写成断言键；971 不是焦点 |
| 9 | 卡片上有 95.7、6.62、80、5 | 只用文字标签 | 降低数字密度；这些数字在场景 11 才由 C 引出 |
| 11 | 画面上有对数偏度 0.60 | 删除 | 每屏数字超限；值本身正确（S4:skew.….log = 0.604） |
| 12 | “almost all older adults have Medicare” | “the insured are older” | 原句没有存储的数字支持 |
| 13 | 角标 “4 of 6 flips involve mediators” | 删除 | 只能由列表计数得到，没有可断言的键；场景内数字已够多 |
| 14 | 画面上有 30.5 %、85 | 删除 | 每屏最多 1 个主数字 + 2 个次级数字 |
| 16 | “about 0.13 lower” | “0.131 lower”，画面标 “paired” | 念出的数字与屏幕一致 |
| 17 | 末帧小注：树的 AUC 0.633 / 0.701 | 删除 | 只是描述性探针，容易被当成模型比较 |
| 19 | “Balanced class weights cause it” | 明确 +0.074 = S − M1，+0.076 = 类别权重单独造成 | 避免两个数字混淆 |
| 22 | D 讲，画面上有 +0.060 | 改由 B 讲；删除 +0.060 | B 负责 §9；该差值无法单独检验（C25） |
| 25 | “deleted 29 diabetic labels” | “erased 29 diabetic HbA1c results” | 按组合标签只有 6 个翻转 |
| 26 | 亚裔 BMI 51.1 % vs 7.2 %（n = 47，E4） | TPR 0.70 vs 0.52（每 100 人） | 覆盖偏差分析，并与陷阱二相连 |
| 28 | “Generative AI helped draft code and text” | “drafted much of our code and text; we reviewed it” | 与 `docs/team_roles.md` §6 的如实表述一致 |

### 12.4 制作前需补登到 `numbers_on_slides.csv` 的数字

补登方式：在 `notebooks/sections/09_synthesis.py` 的 `NUM` 列表中加行（slide、label、source key、format），重跑 §10，让 §10.11 的断言覆盖这些值。CSV 由脚本生成，不能手改。标 * 的行目前还没有标量键，需要先把对应的标量存入 metrics（见 14 节第 3 项）。

| # | 值 | label（英文，入 CSV） | source key | slide_id | 场景 |
|---|---|---|---|---|---|
| 1 | 7,809 | funnel: age >= 20 | `S1:funnel.Age >= 20` | V1 | 3 |
| 2 | 6,064 | funnel: interviewed and MEC-examined | `S1:funnel.Interviewed and MEC-examined (RIDSTATR = 2)` | V1 | 3 |
| 3 | 5,767 | funnel: HbA1c measured | `S1:funnel.HbA1c measured (LBXGH present)` | V1 | 3 |
| 4 | 175 | raw columns before minimisation | `S1:minimisation.raw_columns` | V1 | 4 |
| 5 | 78 | columns kept after minimisation | `S1:minimisation.kept` | V1 | 4 |
| 6 | 27 | DB516 estimates compared | `S4:db516.n_estimates` | V7 | 5 |
| 7 | 0.044 | DB516 max absolute difference (pp) | `S4:db516.max_abs_diff_pp` | V7 | 5 |
| 8* | 15.8 | DB516 published total prevalence (%) | `results/S4/db516_replication.csv`（total, All, crude, nchs）→ 建议存为 `S4:db516.nchs_total` | V7 | 5 |
| 9 | 57 | genuine codes caught by blanket recode | `S3:blanket_recode.questionnaire_only_cells` | V2 | 6 |
| 10 | 6.8 | HbA1c IQR fence, upper (%) | `S3:outliers.a1c_iqr_fence_upper` | V2 | 8 |
| 11* | 14 | preparation steps | `results/S6/step_catalogue.csv`（14 行）→ 建议存为 `S6:n_steps` | V2 | 9、10、25 |
| 12 | 88 | design columns, M0 | `S6:arms.M0.n_features_t1` | V2 | 10 |
| 13 | 46 | design columns, M1 | `S6:arms.M1.n_features_t1` | V2 | 10 |
| 14 | 42 | design columns, S | `S6:arms.S.n_features_t1` | V2 | 10 |
| 15* | +1.8 / +8.8 | insurance gap crude CI low / high (pp) | `S4:standardisation.insured_uninsured.crude_ci`（列表 [0] / [1]，需确认 get 语法支持下标，否则另存 lo / hi） | V5 | 12 |
| 16* | −2.6 / +3.9 | insurance gap standardised CI low / high (pp) | `S4:standardisation.insured_uninsured.std_ci`（同上） | V5 | 12 |
| 17 | 0.70 | kappa self-report vs HbA1c (unweighted) | `S5:labels.agreement_unweighted.kappa` | V6 | 14 |
| 18 | 165 | self-reported below 6.5 on medication | `S5:masking.below_6_5_on_med` | V6 | 14 |
| 19 | 49 | uninsured adults with HbA1c >= 6.5 (n) | `S5:undiagnosed_inequality.proportions.uninsured.n` | V6 | 15 |
| 20 | +0.004 / +0.034 | minus care traces E-SCREEN CI low / high | `S7:headline.minus_care_escreen.lo` / `.hi` | V7 | 21 |
| 21* | 6 | post-audit issues checked | `S9:postaudit.summary`（6 行）→ 建议存为 `S9:postaudit.n_issues` | V7 | 22 |
| 22 | 3 | pre-registered (prior exposure none) hypotheses supported | `S10:verdict_counts_prereg_none.supported` | V8 | 24 |
| 23 | 3 | pre-registered (prior exposure none) hypotheses inconclusive | `S10:verdict_counts_prereg_none.inconclusive` | V8 | 24 |
| 24 | 0.80 | specificity of the shared threshold (TPR audit) | `S8:spec` | V6 | 26 |

### 12.5 定义常量与外部参考值（不入 CSV，脚本中以常量注明出处）

| 值 | 含义 | 出处 | 场景 |
|---|---|---|---|
| 0.5 | AUC 的随机基线 | 定义 | 1 |
| 6.5 % | HbA1c 诊断阈值（标签定义） | §5.1；`src/labels.py` | 3、14 |
| 1.5 × IQR | 教科书的离群值规则 | §3 | 8 |
| ±0.01 | SESOI | `governance/hypotheses.md` H2b | 18、21 |
| 10 | VIF 参考线 | §4（“VIF > 10 class”） | 11 |
| 7.0 %、9.0 %；示例值 77、99 | 与哨兵代码重合的真实值；示意值 | notebook §3.4 | 6、25 |
| “of 100” | 把 TPR 换算成每 100 人 | 由 0.70 / 0.52 换算 | 26 |

### 12.6 删除而不使用的数字

- **无法写成可断言的键：** 23（29 − 6）、569（819 − 250）、“4 of 6 flips involve mediators”，改为图形或删除。
- **没有存储数字支持：** “almost all older adults have Medicare”，已改写。
- **已核实但不用：** 0.844 / 0.772、0.60、85、30.5 %、51.1 % / 7.2 %（n = 47）、+0.060、0.633 / 0.701、133 条登记、17 条局限、26 条主张。

---

## 13 评分覆盖矩阵与风险

### 13.1 评分覆盖

| 准则 | 场景 | 观众看到的证据 |
|---|---|---|
| Appropriateness（各阶段的技术与可视化） | 3、4、6、8、11、14–16、18、20、26 | 漏斗（探索）、得失对比柱（剖析）、IQR 围栏（清洗）、VIF / 偏度前后（EDA）、Venn 与风险差森林图（偏差）、泄漏门与哑铃图（评估）、点阵（公平性） |
| Correctness & Clarity（含贡献区分） | 1、5、6、11、16、22、24–28 | 角色卡片；lower-third；“I led …” 句；右栏徽章；贡献链；每个数字的来源标签；DB516 复现 |
| Data Interpretation | 11–15、18–21 | 冗余（VIF 95.7 / 97.6）、偏度 6.62、混杂（+5.3 → +0.7）、Simpson（224 / 6）、中介（DAG）、κ、区间与 SESOI、谱偏差 |
| Novelty & depth | 2、6–7、16–17、20–21、23 | 7.0 被删；插补出的 50 被当成标签；全样本 AUC 度量的是“认出已确诊”；模型被当作泄漏探测器，而不是目标 |

### 13.2 brief 硬性要求

| 要求 | 场景 |
|---|---|
| 全员出镜并讲解 | A 1–5、24、28；B 6–10、22、25；C 11–15、26；D 16–21、23、27 |
| governance、profiling、EDA、preparation、对 ML 的影响 | 2–5；6–8；11–13；9–10；16–21 |
| 关键数据质量问题 + 至少一个非显然发现 | 6–8；7（明确标为 “Non-obvious finding”） |
| 重要准备决定的理由 | 8、9、11 |
| 最简准备与系统准备，同一个 basic model | 10、18–19 |
| 改进与恶化都解释 | 16、19、21 |
| 冗余、多重共线、偏度、谬误 | 11、12、13 |
| 偏差与标签 | 14、15、26 |
| 主要贡献与反思（新颖、意外、有启发） | 23–28 |
| ML 是证据，不是目标 | 2、23、27、28 |

### 13.3 风险

| 风险 | 对策 |
|---|---|
| +0.008 被看成失败 | 钩子先说“分数不动”是问题的一部分；场景 18 画出区间与带，19–21、23 说明价值在别处 |
| 陷阱顺序 2 → 1 → 3 令人困惑 | 常驻陷阱条；章卡写编号与问句；场景 23 按 1、2、3 回答 |
| 分段变成清单 | 每章以问题开场、以发现结尾；三个贯穿对象；结论集中在 Ch8 |
| 数字太密 | 每场景口述 ≤ 3 个；每屏 1 + 2 个；补登表之外不加数字 |
| 单人出镜被理解成“没有全员出现” | 每人出镜 ≥ 2:29，有贡献句与 lower-third；邮件中一并确认 |
| 不允许剪辑 | 9.6 节回退方案 |
| 夸大主张 | 9.4 节措辞边界；第 2 轮排练专查 |
| 渲染管线出问题 | 先做视觉 4 样板；应急用 matplotlib 静帧 + M3 / M12 |
| 表达不清或过快 | 135 wpm；发音表；按拍练习；超时删句，不加速 |
| 补登触碰冻结规则 | 只做 `fix` 提交，跑 FAST clean-room（14 节第 3 项） |

---

## 14 待确认事项

1. **给讲师的邮件（今天发）。** 草稿：
   > “Dear [lecturer], our group plans to submit one YouTube video under 12 minutes. Each member presents their own part on camera, one at a time; there are no shots with all four together. May the parts be recorded separately and edited into one video, or must it be recorded in one continuous take? Thank you, Group [no.]”
   - 回复“可以剪辑” → 9.6 节主方案；
   - 回复“必须一次录制”，或 10/15 仍未回复 → 9.6 节回退方案。
2. **定稿后同步视频分段。** `notebooks/final/team.json` 的 `video_segment` 和 `docs/team_roles.md` §5 的分段表仍是旧方案（A 0:30–2:40 等，并且都写着 “plus opening and closing”，与单人出镜冲突）。按最终实测时长更新，当前值为：

   | 成员 | video_segment |
   |---|---|
   | A | 0:00–2:00; 9:44–9:54; 10:33–10:56 |
   | B | 2:00–4:00; 9:03–9:20; 9:54–10:07 |
   | C | 4:00–6:15; 10:07–10:21 |
   | D | 6:15–9:03; 9:20–9:44; 10:21–10:33 |

   更新后运行 `tools/build_final.py --fill-team` 和 `--validate-only`。
3. **CSV 补登。** 12.4 节的 24 个值通过修改 `09_synthesis.py` 的 `NUM` 列表加入。其中 4 项（标 *）需要先把标量存入 metrics：`S4:db516.nchs_total`、`S6:n_steps`、`S9:postaudit.n_issues`，以及插补区间的 lo / hi（若 get 语法不支持列表下标）。仓库已过 content-freeze，按开发流程只能做 `fix` 提交，并在提交后跑 FAST clean-room 检查。
4. **成员确认分工变化。**
   - B 讲场景 22（留出集与事后核查，对应 B 负责的 §9）；
   - C 的单人短片改讲公平性（对应 C 负责的 §8），不讲亚裔 BMI。
5. **真名与组号。** 旁白中的 “I'm B” 等，以及 lower-third 和片尾卡，都换成真名和组号；组号目前在 `team.json` 中仍是占位符。
6. **实测时长回填。** 第 1 轮朗读后，把每个场景的实测时长回填到第 3 节，并重算检查点与 `video_segment`。
7. **GenAI 声明。** 场景 28 的措辞须与 `governance/genai_log.csv` 和 `docs/team_roles.md` §6 保持一致，由 A 核对。
8. **字幕。** 由谁校对 SRT 和 YouTube 自动字幕，需要指定一人（建议由 A 统筹）。

---

## 15 合并决定

| # | 议题 | 冲突 | 决定 |
|---|---|---|---|
| 1 | 时间轴 | 01 9 章 10:50；03 28 场景 10:56；04 10:45 | 以 03 场景为准，章边界 = 场景边界，总长 10:56 |
| 2 | 成员时间 | 03：A 2:36、B 2:13、C 2:29、D 3:38 | 场景 22 归 B；19 +2 s、23 −2 s、28 −3 s → A 2:33、B 2:30、C 2:29、D 3:24 |
| 3 | 同框镜头 | 01 开场 “all”、Ch9 四人；02 G 版式；04 “D → 全员”、Zoom 画廊 | 全部删除：角色卡片、单人交接、D 回答、四段单人短片、A 收尾 |
| 4 | 贯穿对象 | 01 Adult X；03 无 | 不用 Adult X，改用 0.961、7.0、152 三个真实对象 |
| 5 | 语速 | 01 130；03 120–150；04 140–150 wpm | 平均 135，单场景 120–150，数字密集 ≤ 145 |
| 6 | 顺序 | 揭示 Label → Leak → Little gain；讲者 A → D | 讲者 A → B → C → D（Ch7 插入 B）；揭示 2 → 1 → 3，回答 1 → 2 → 3 |
| 7 | 讲者标识 | 03 成员色 + 色块 wipe；02 墨色徽章 | 墨色徽章；章卡 + 硬切 |
| 8 | 版式 | 02 F/R/X/S/G；03 全屏 → 右下画中画 | F/R/X/S，删 G；摄像头始终 480×270；短片用 S |
| 9 | 章标题 | 04 3 s + 1 s 留白；02 1.2 s | 1.2 s 章卡，计入场景时长 |
| 10 | 屏幕文字 | 02 标题 ≤ 6 词 + 3 标注；03 ≤ 8 词；04 ≤ 12 词 | 02 的结构上限；关键文字行 ≤ 8 词 |
| 11 | 仅画面数字 | 02 不念不上屏；03 大量“仅画面” | 允许 ≤ 2 个次级数字和灰色数据标签；主数字必须念出 |
| 12 | 数字念法 | 04 取整；03 与屏幕一致 | 与屏幕一致（“about 0.13” 改为 “0.131”） |
| 13 | 动效 | 03 打字机、滑入、翻牌、闪烁、印章、wipe | 全部改用 M1–M12；M8 只在场景 16 |
| 14 | 公平性 | 03 删去，C 讲亚裔 BMI；02 有视觉 11 | C 的短片用视觉 11；亚裔 BMI 删除 |
| 15 | Brier | 0.074 与 0.076 易混 | 0.074 = “from M1 to S”；0.076 = “class weights alone” |
| 16 | 交接句 | 03、04 各一套 | 用 03 的，补 D → B、B → D |
| 17 | 录制 | 02、04 分录合成；04 保守方案为四人同时在线 | 分录合成；回退为连续录制、轮流单独出镜 |
| 18 | 检查点 | 04 用 team.json 旧时段 | 按章检查点；砍减顺序用场景编号 |
| 19 | 代码画面 | 03 场景 6 有代码卡；04 禁止 | 改为文字规则 |
| 20 | 音频码率 | 02 192 kbps；04 ≥ 128 kbps | 192 kbps |
