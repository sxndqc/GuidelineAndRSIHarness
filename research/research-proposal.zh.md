# 少量例证驱动的标注规范适应：ACL 研究方案

日期：2026-10-06。状态：文献与 benchmark 初审、实验协议草案；没有运行模型实验，没有样本效率的实测结论。本方案经过三个 AI 子 agent 的贡献、方法学和 benchmark 审查及复审；它们不是实际 ACL 人类审稿人。

## 1. 判断与核心问题

建议保留 UMR 的研究动机，以 **UMR + SNACS/STREUSLE + GUM/DISRPT** 为主要任务组合，用 **UD EWT 的规范修订**做专项迁移实验。先用 UD 与 SNACS 建立低成本 pilot，但二者共享部分原始文本，不能被称为独立语料复现。本次核验的候选资源中，尚未确认有单一 benchmark 同时提供可信规范缺口、可计量的主动例证获取、持久状态演化与严格隔离的测试；贡献应是建立在现有资源上的评估协议和机制发现。

最值得问的问题：

> 在相同示例、反馈和计算预算下，把标注经验保留为可检索原例、精炼后的自然语言规范或可执行程序，如何影响未见构式的标注迁移、达到目标质量所需的新标注量，以及规范变化后的退化？

固定模型权重，研究外部状态的持续适配。主线不是证明 agent 拥有人类式理解，也不是把读文档、检索和写代码的组合包装成新方法。更准确的关键词是 annotation-policy adaptation / persistent external-state adaptation；self-evolution 必须明确更新对象，不能当作解释。

应撤回两个未经验证的前提：

- “机器学习不能使用 guideline”不成立。GoLLIE、guideline-conditioned IE 及 instruction-tuned LLM 都是反例。合理比较对象包括强 guideline/few-shot/RAG 系统。
- “人少量例子就足够”是值得验证的观察。人可能已有多年语言学经验；若作为论文结论，需要测量经验匹配和任务匹配的人类学习曲线，否则仅作为动机。

## 2. 最近邻工作改变了创新定位

已核实官方 ACL Anthology XML 的题名与摘要，并读取部分官方代码仓库 README；**没有完成所有论文全文阅读**。网络策略阻止了 ACL 网站直接访问，元数据来自 ACL 官方 GitHub 镜像。检索包括 2024–2026 ACL/Findings 与 2024–2025 EMNLP，非穷尽的系统综述。

| 工作 | 已覆盖的方向 | 对本研究的约束 |
|---|---|---|
| [Refining and Reusing Annotation Guidelines for LLM Annotation, ACL 2026](https://aclanthology.org/2026.acl-long.1760/) | 迭代 moderation 精炼 guideline；少量监督；推理模型；NCBI Disease、BC5CDR、BioRED | 最近邻。不能将“少量示例改指南”当主要创新；必须全文审读并比较其方法 |
| [Can LLMs Follow Concept Annotation Guidelines?, Findings ACL 2024](https://aclanthology.org/2024.findings-acl.478/) | factual/counterfactual guideline，概念标注，模型差异 | 反事实规范与强弱模型比较本身不是新贡献 |
| [GuideBench, ACL 2025](https://aclanthology.org/2025.acl-long.557/) | 多规则、规则更新、agent guideline following | 不宜声称首个 guideline agent benchmark；本研究必须突出标注证据学习与冻结迁移 |
| [GoLLIE](https://github.com/hitz-zentroa/GoLLIE)；[Instruction-Tuning LLMs for Event Extraction with Annotation Guidelines, Findings ACL 2025](https://aclanthology.org/2025.findings-acl.677/) | 根据标注规范做 IE、低数据与跨 schema 泛化 | guideline-conditioned prediction 是必须承认的基线方向 |
| [Contextual Experience Replay, ACL 2025](https://aclanthology.org/2025.acl-long.694/)；[Gödel Agent, ACL 2025](https://aclanthology.org/2025.acl-long.1354/) | 持久经验记忆；修改自身逻辑 | 笔记与代码演化部件本身没有充分新意 |
| [Can External Validation Tools Improve Annotation Quality for LLM-as-a-Judge?, ACL 2025](https://aclanthology.org/2025.acl-long.779/) | 工具增强标注与条件性收益 | 必须分离语义学习与格式/外部验证收益 |
| [GEPA](https://github.com/gepa-ai/gepa) | 从反馈优化提示、代码等文本参数 | 至少需要认真选择一种现代自动优化基线；是否纳入完整比较须读其设置与成本 |
| [Guidelines as Environments, ACL 2026](https://aclanthology.org/2026.acl-long.741/) | 显式规则状态与相互作用 | 规则组合/执行分析需与该方向区分 |

最近邻论文全文仍可能覆盖目前设想的部分迁移分析，故现在不能保证新颖性，不能使用“首次”。建议在其三个 biomedical NER 数据集中选择一个可获取任务做**复现校准**，不加入完整任务×预算矩阵。保持其人工反馈、更新轮数等原条件；再另做预算匹配版本。若只能根据论文实现或模型版本变了，明确称重实现/概念复现。

## 3. Benchmark 推荐与资源证据

详见 [benchmark-audit.md](benchmark-audit.md)，其中列出实际核验的官方文件、许可限制和未完成的审计。

### 3.1 UMR：研究锚点与复杂结构任务

资源：[UMR 数据](https://github.com/umr4nlp/umr-data)、[UMR guideline](https://github.com/umr4nlp/umr-guidelines/blob/master/guidelines.md)。读到的数据 README 为 3.0，规范文件题头为 0.9（2022）。**版本号不同不自动证明不兼容**，但不能未经核验就把不一致称为 guideline 缺口。

保留用户观察的职业同位语作为候选现象，扩展到非动词谓词、角色与身份、隐含论元、跨句关系等。公开规范确实已有 have-org-role / have-rel-role 等相关条目；需要检查“规则缺失”“相关规则散落且难检索”“规则已有但无法映射到同位构式”三种可能，不能仅用关键词未命中证明缺失。

第一阶段限定一种语言、句子级图与预注册现象；文档级 temporal/coreference 单独扩展。图总体分数、合法性、目标关系与重入等现象分数分别报告。正式实验前必须落实与选定 UMR 版本兼容的评分器、句/文档层评价、训练测试划分与许可。此次尚未核实这些完整条件，**不能称已可直接运行**。不要简单把 AMR Smatch 当作覆盖全部 UMR 的评测。

### 3.2 SNACS / STREUSLE：最适合先做的语义规范任务

资源：[STREUSLE](https://github.com/nert-nlp/streusle)、[SNACS guideline v2.6](https://arxiv.org/abs/1704.02134)、[psseval.py](https://github.com/nert-nlp/streusle/blob/master/psseval.py)。

标注介词/所有格的 scene role 和 lexical function。该区别及一词多义适合观察例子能否转化为可迁移的决策规则。先给定目标表达，预测 Role/Function 及联合标签；官方 scorer 有 goldid 与 autoid 模式。随后才研究目标识别+标注，避免把识别失败混作规范学习失败。Gold `??` 的排除遵循官方 scorer，并明确报告。

现象候选：角色与功能不一致、多词表达、所有格、同一词汇在不同语境下的解释、跨词汇迁移。它们不是已经证明的文档缺口，必须经专家审计。

有既定 splits，标注 CC BY-SA 4.0；源文本和 POS 的再分发有 README 所述权限。STREUSLE 基于 EWT reviews。**不能与 EWT 互相偷看 gold，也不能算完全独立语料。**

### 3.3 GUM / DISRPT：独立的篇章层验证

资源：[DISRPT 2023](https://github.com/disrpt/sharedtask2023)、[GUM 任务说明](https://github.com/disrpt/sharedtask2023/blob/main/data/eng.rst.gum/README.md)、[GUM RST guideline](https://wiki.gucorpling.org/gum/rst)、[官方关系 scorer](https://github.com/disrpt/sharedtask2023/blob/main/utils/rel_eval.py)。

建议从给定 discourse units、关系候选及官方允许的方向信息的 relation classification 开始。能研究 elaboration/explanation/contrast 等决策、隐式关系与体裁迁移；**这不是完整 discourse parsing**。官方指标 accuracy，另报 macro-F1 和现象分数。

DISRPT 2023 的 GUM v9 将 32 个原始细标签映射为 15 个目标粗标签。`.rels` 中 `orig_label` 直接泄漏目标；不能仅删最后一列。原 GUM 包含其他标注层，同文档的 gold syntax/coreference 等不得直接交给 agent。

GUM 当前 README 的 GENTLE/test2 是另一版本，不能混入旧版 DISRPT 数字。首轮可用可再分发的非 Reddit 子集，但应预先声明并报告数量。标注许可与底层文本许可不同，不能把全部文本都称为无条件 CC BY。完整指南页面尚未逐条核验。

### 3.4 UD English EWT：真实规范迁移专项

资源：[EWT README](https://github.com/UniversalDependencies/UD_English-EWT/blob/master/README.md)、[appos 文档](https://github.com/UniversalDependencies/docs/blob/pages-source/_en/dep/appos.md)、[UD scorer](https://github.com/UniversalDependencies/tools/blob/master/eval.py)。

版本记录包含 title/name 的 nmod:desc、you guys 从 appos 到 nmod:unmarked 等变更线索。这提供自然 policy revision 候选，但每项必须对齐同一文本与分词，并通过变更文档/专家区分政策改变与普通纠错。

先给定 token，预测 basic heads 与依存标签。官方 LAS 忽略 subtype，因此必须同时报告 **full-label LAS、目标边准确率、相关构式成功率**；不然关键规范更新可能根本不计分。MISC 中包含 STREUSLE 等标注，必须剥离非授权层。

主线用随机例子检验利用证据能力，专项用政策变更前后同文本配对、受影响/未受影响构式评价适应和负迁移。若每种政策的自然实例不够，降为描述性分析，不以自动 diff 冒充政策 gold。

### 3.5 暂缓而非排除

- **MAVEN-ARG**：[论文](https://aclanthology.org/2024.acl-long.224/)、[仓库](https://github.com/THU-KEG/MAVEN-Argument)。官方 README 有 162 类型、612 角色及专家定义/例子，适合后续 schema 长尾研究。隐藏测试需提交；本次未验证在线评测服务与全部数据许可。
- **MAVEN-ERE**：[仓库](https://github.com/THU-KEG/MAVEN-ERE)。跨事件时间、因果、共指提供全局一致性挑战。训练格式的 gold coreference clusters 和测试候选差异要消除；RED 规范与任务自有修订需对齐。
- **AMR** 与 UMR 太接近，增加任务数不等于增加独立证据，常用全量资源还需核查 LDC 权限。
- **ACE/RAMS/WikiEvents** 并非不合适，但尚未完成完整 guideline、数据许可和评测器的组合审计。
- **GuideBench** 是必读近邻，适合作为外部 guideline-following 对照，而不是代替语言学标注任务。
- **Biomedical NER** 只先用于最近邻 moderation 方法的复现校准。

## 4. 可证伪假设

H1：同底层模型、同标注证据、相近计算预算下，持久规范精炼较冻结的原例检索提高未见构式标注质量。若只提高相似模板的表现，不支持规则迁移解释。

H2：在规范精炼基础上允许自写程序，对语义决策有增量价值。若只提高格式合法率，结论应是结构执行改善，而非语义学习。

H3：学习瓶颈随规范条件变化：显式规则可用但难找、隐含规则可从例子推断、例子不足以辨识规则，表现不同。Oracle 证据干预可区分检索与执行失败。

H4：较强模型的优势可以分解为适应资产生成与执行。交换强弱模型产生的笔记/程序，观察迁移收益与失效。强→弱若提升不能单独证明“理解”；必须核查没有运行时偷偷调用强模型，并记录教师成本。

H5：可执行规则可能降低原政策错误，也可能在政策改变后产生更大负迁移。该风险需要实测，不预设代码优于笔记。

## 5. Agent 与可信评测的边界

Agent 可按需 read/search guideline、检索已授权例库、获取计费 gold、修改自己的持久文件与代码、执行自写程序。基础模型权重固定。允许的持久状态：规则笔记、例外清单、例库索引、提示/流程、标注代码与自检器。

Agent 自写的是**标注 harness**；benchmark controller、权限网关、预算账本、测试数据、gold 和评分器由研究者锁定且 agent 无法修改。仅提示“不准看测试”不够，需文件系统/进程层隔离。完整原始数据仓库不要挂载给 agent。测试网络默认关闭，只允许已审计的材料，不能网上搜测试句的标准答案。

四类资源：

1. 版本化 guideline 及其内含例子：作为已有监督单独计量。
2. 适应池：可看未标注输入；gold 经工具揭示。主实验随机嵌套序列，所有方法重放相同例子。
3. 开发集：研究者 pilot 与系统调试使用，永不作为正式测试。主少样本实验中，agent 的有标签反馈只来自已购买样本；额外开发评分若开放，单列次数、涉及样本与信息来源。
4. 封闭测试：冻结方法、阈值与资产后评价；每个实例从同一冻结状态启动，禁跨测试实例更新。在线 prequential 学习另立实验，先预测评分，再揭示当前答案。

每轮保留 artifact hash、代码/笔记 diff、来源例子 ID、工具调用、gold 曝光账本、失败/超时/回滚与成本。代码执行受限，不允许改依赖的评测标准，不能从 evaluator 的错误日志读出 gold。

## 6. 对照与归因

| 条件 | 信息与权限 | 回答什么 |
|---|---|---|
| Guideline-only | 同规范，无新增标注例子 | 模型先验与规范的基点 |
| Full-context few-shot | 规范及同样例子在上下文中；容量允许时运行 | 工具按需读是否真有优势；不能故意截断制造弱基线 |
| 冻结工具 Agent | 同 guideline、全部已购买原例、固定工具与校验器；无持久规范/程序改写 | 强 RAG/工具基线 |
| 规范精炼 | 上述条件+持久笔记/规范补丁 | 相同证据的组织与归纳收益；纳入最近邻 moderation |
| 规范精炼+自写程序 | 在上项上增加代码修改权限 | 代码的条件增量收益 |
| 主动选例 | 对最有价值的若干条件独立加上选择权限 | 获得证据的效率，与利用证据的效率分开 |
| Oracle evidence / 更完整规范 | 提供专家定位的相关规则或样例 | 诊断检索瓶颈；不是可部署系统，也非理论上界 |

所有核心组可访问相同原始材料和固定语法检查器。冻结组也能反复读已购买例子并在单实例内推理，不能因为“冻结”而被削弱成一次性回答。预算 0 若组的初始状态相同可共享，否则保留各组从 guideline 自行编译/精炼的差异。

同预算不等于单纯 token 相同。分别报告同监督、相同推理上限、同费用三个视角；适应成本与预测成本分开，额外学习时间不能免费。有数据的监督 parser 作为任务性能参考，不能直接与预训练 LLM 宣称公平的从零样本复杂度比较。

## 7. 多少例子足够

主口径是**新增暴露的唯一带标签实例数**，而非仅检索次数或写入笔记的例子数；重复读取计计算，不重复计实例。记录 guideline 原生标注例子、token、标注决策/节点/边、专家分钟与反馈。文档、句子和单个关系不同量，不能直接相加比较。

公开语料、规范及其中例子可能已进入模型预训练，无法据此估计从零学习的样本复杂度；本文测量的是给定预训练系统在部署时所需的新增标注量。政策修订专项提供进一步诊断，但不能保证完全消除预训练污染。可加由专家制定且自洽的新约定和新收集的私有保留实例做诊断；简单标签改名不足以排除既有知识，也不能将受控约定实验当成真实规范缺口。

正式预算点可取 0、1、2、4、8、16、32、64、128；这是待 pilot 收缩的候选网格，不是必须全矩阵。预先指定实用阈值 τ（专家协议支持的业务要求或独立参考系统 Qref−δ），报告达到阈值的最小实测预算 B* 与不确定性。阈值选择、允许误差与停止规则不能事后从测试调整；若只在 16 未到、32 到，不能声称精确需要 17 个。

若置信下界未越过阈值，报告“在预算≤128内未确认达到”，而非证明128仍绝对不够。曲线非单调时，区分首次观测达到与此后持续达到。另报以 log₂(1+B) 为预算横轴、在所有方法共享预算区间上计算并归一化的学习曲线面积，预先固定离散点间插值方法；同时报告关键预算的配对差、成本—质量关系，避免所有方法都未达阈值时无从分析。

长尾说明：独立随机抽样下，频率 p 的现象在 n 例中至少出现一次的概率是 1−(1−p)^n。若 p=1%，达到95%“见到一次”的概率约需299例。这只是覆盖的示意计算，不是学习所需数量；说明为何“32例足够”必须与现象覆盖和主动选择一起报告。

## 8. 失效边界与专家审计

预先定义而非看完模型错例才发明分组：

- 已见规则→新词汇/新句法表达；规则 A、B 分别见过→未见 A+B；新体裁/领域。
- 规则明确且已定位；规则明确但分散；规则没有明确写出而例子可区分；规范/例子冲突；信息根本不足以辨识。
- 稀有构式、复杂图、跨句依赖，以及增加无关指南章节后的检索失败。
- 加入少量错例后的规则污染；新政策适应后旧能力的负迁移。

若两个政策对已见规范和例子都兼容、对新实例要求不同，没有算法能可靠猜出任意选定政策。这类不可辨识实例应看弃权/请求例子的策略及 coverage-risk，而不是笼统判为模型弱。所有方法仍报告强制预测质量，避免只靠弃权提高表面准确率。

对“未见表达”和“A+B 未见组合”的结论，须在 guideline 原生例子、已购买例子及其他授权材料中审计相应表达/组合的曝光；适应池与测试按预定义构式或来源分组。只满足随机实例划分时，结论限于未见实例，不称未见构式泛化；预训练阶段的曝光仍无法排除。

自然 guideline gap 由至少两名相关领域专家独立审计并裁决，记录支持段落、可推导性、冲突、合理替代 gold。人工删除规则的实验与自然缺口分开；还需同步审计指南中内含例子，避免“删除文字规则但答案仍在示例中”。更完整规范仅是诊断参照，不声称能够穷尽语言现象。

若要比较人类少样本学习，另做经验分层、材料/监督预算匹配和顺序平衡的人类研究，报告人类时间与一致性。两名专家审核缺口不等于测出了人类学习曲线。

## 9. 强弱模型与统计

预先按模型系列/独立指标选两个能力档，固定版本、日期、推理设置、上下文与工具协议；不能事后用本任务成绩把模型分为强弱。优先同家族比较规模，再对关键结论跨家族复核。若使用闭源不同档位，结论是所测系统差异，不是纯参数规模因果效应。

多条独立适应轨迹，在方法间共享示例顺序和测试文档。预算点是同一轨迹的重复测量；同文档的标签也非独立。以整条轨迹衡量运行变异，文档/来源 cluster bootstrap 衡量测试抽样不确定性；配对差异保留对应关系，避免把多预算多标签当成大量独立样本。依据 pilot 方差与目标效应规划运行数，不默认3次或5次足够。

预注册主要比较，次要细分类分析控制多重比较或明确探索性质。报告所有运行、超时和无效输出，不能挑最成功的演化轨迹。

## 10. 最小可执行路线

阶段 A：锁定版本、材料、许可、标注投影与 scorer。官方 scorer 做 gold 自评分与错误/非法输出检查。完成原生示例、跨语料文本重叠与隐藏 gold 审计。UMR 需先解决版本/评分器适配，不能拿未准备好的任务开始宣传结果。

阶段 B：最近邻全文审读；选择一个 biomedical NER 任务复现 moderation 校准。此阶段可以与数据审计并行，不能用弱化替代实现当作原方法。

阶段 C：UD+SNACS pilot，2模型×3状态条件×3预算(0,8,32)×2轨迹×2任务≈72评测单元。每任务先用约50–100独立开发实例做成本/隔离/指标检查；这些数值是工程规划，不是统计功效保证。不调用最终测试，不以本方法必须赢作为进入正式实验的门槛。

阶段 D：加入 UMR 和 GUM 正式测试，选择必要预算点和更多轨迹。UD留作政策变化专项；主动选择、强弱资产交换、代码回滚、oracle 条件只在解释核心结论的子矩阵上做。避免笛卡尔积爆炸。

进入正式实验的门槛：可追溯版本与许可、scorer可信、标签隔离、预算记账完整、成本可承受、目标现象有足够独立评测实例。方法无收益也是有效结果，不应据此筛掉任务。

## 11. ACL 稿件应该承诺什么

可承诺的产物是：版本化数据适配器与受审计材料清单；预算/权限可复现协议；规范缺口与变更现象集；持久状态轨迹；学习与成本曲线；专家审计与负结果。

待实验证明的发现是：何时精炼规范优于原例检索，何时代码有语义增益或仅改善合法性，何时模型瓶颈在归纳/检索/执行，何时更多例子仍无法达到目标。当前没有这些结果。

不能写成贡献：“第一个能读guideline的agent”“人只需要几个例子而parser做不到”“我们在四个benchmark证明通用标注能力”“少量样例必然足够”。范围限定为所测语言学标注与约定适应。

当前最关键的未决项：最近邻全文与实现差异；UMR 用户实际规范版本及职业同位语 gold；完整指南覆盖专家审计；各数据版本可复现的评测与许可。没有预算或模型 API 配置时，继续完成研究方案不受阻，但不能把模型实验描述为已经执行。
