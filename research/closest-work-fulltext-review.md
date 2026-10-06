# 最近邻全文与公开实现复审

日期：2026-10-06。对象：Kim, Kon Woo; Kim, Jin-Dong; Aizawa, Akiko. **Refining and Reusing Annotation Guidelines for LLM Annotation**, ACL 2026, pp. 37951–37964，DOI `10.18653/v1/2026.acl-long.1760`。[官方论文](https://aclanthology.org/2026.acl-long.1760/)；[公开实现](https://github.com/KonWooKim/llm-guideline-moderation)。

本次已用 `pdftotext -layout` 阅读论文正文、表格和附录，并检查公开代码，不再局限于摘要。当地 PDF 为 `data/raw/papers/refining-2026.pdf`，SHA-256 `0f0b205eea63f7bf4855fa9453423bc46c36f2c9261af50e49024cf60f40e15f`。代码 checkout `/tmp/closest-guideline-moderation`，commit `33d58d6603ab2c6cfd5aa98e4b14ae17b1ed2ac4`。未调用付费 API、未上传 PubAnnotation、未生成新的 LLM 复现结果。

## 1. 必须更新的旧结论

该工作不只是给 guideline 的静态提示，而是已有**固定权重、少量 gold、跨轮持久精炼、独立保留集验证**的完整近邻。其正文明确将应用规范视为演绎、从错误归纳规范视为归纳，并分析规则修补带来的新假阳性。不能再把“少例子补充规范”“观察修补副作用”“在未见样本上验证”当成本研究独有贡献。

其研究具有真实的独立评测：moderation 使用从官方 train 抽出的 10 文档，最终评测使用官方 dev 的 100 文档，官方 test 未使用。不能声称它只在自我修补集合上自评或必然测试泄漏。

仍存在的明确空间：它没有测不同新增 gold 数量的学习曲线，§6.2 明确把扩大 development 样本量列为 future work；没有同已购原例库的冻结检索对照，也没有可执行程序状态相对精炼规范的因果干预。研究可进一步量化样本复杂度、不同状态表示的增量价值、模型构造/执行瓶颈及跨领域/模态的失败边界。但这是一项延伸和机制研究，不是首次“自演化标注”。

## 2. 方法、反馈与停止条件：全文核实

### 任务与预测

§3、§4.1：文档级 biomedical NER，仅实体，不做关系抽取。实体由字符开始/结束 offset 和 type 表示；主评估为严格 **span + type** micro-F1。指南作为 prompt 中的文本提供，模型固定权重，模型重复标注 adaptation 文档。

NCBI 使用四类 `SpecificDisease`、`DiseaseClass`、`Modifier`、`CompositeMention`，不能用折叠成单一 Disease 标签的常见 NER 版本冒充同任务。论文引用的常规 benchmark 分数也明确说与本设置不直接可比。

### 反馈不是只有 scalar reward

§3.4：控制器比较全部 adaptation predictions 与 gold；soft overlap（至少一个字符重合）只用于错误诊断，主评分仍 strict。四种互斥诊断类别按论文描述优先区分：标签错误、边界错误、漏标 FN、误标 FP。按 gold/predicted label pair 和错误类分组，选择最常见错误组。错误片段带 predicted/gold 标签、mention 与周围窗口（论文 window size=60）。

每轮 moderation 有三个 LLM 步骤：

1. **Pattern explanation**：比较该组错误与 verified true positives，输出一个格式化的泛化模式；可涉及语义与结构证据。
2. **Principle generation**：产生一个 IF/THEN 原则，包含明确 negative constraint，避免只记 token 或过度扩张规则。
3. **Guideline refinement**：将原则并入原指南，以已正确案例作为不应破坏的检查；输出完整新版指南，保留原结构。

随后重新标注同一 adaptation 集，评估与选择新版。§3.3–3.4：F1 达到阈值或新轮不再改善则停止；不改善时丢弃最近一次修改。附录阈值为 **0.9**，作者明确说是参考 IAA 的停止 heuristic，不是匹配人类质量的证明。

因此公平基线必须同样获得已购 gold 的标签、错误类别和正确案例，或者分别操纵反馈丰富度；不能只给冻结组 scalar F1，而给精炼组完整差异后把差异归因于记忆。反复看相同 10 文档并不增加 unique-document 标签预算，但增加反馈/计算量和适应集过拟合风险。

## 3. 样本量、评测与模型

§4.2：每个数据集随机抽 **10 个 train 文档**作为 moderation development。独立评测是 **100 个官方 development 文档**：NCBI 与 BioRED 用整个 dev，BC5CDR 从其 500 文档 dev 抽 100。没有将 10 文档解释为最优样本量，§6.2 明确承认选择偏差与停止统计不稳定。

§4.3：GPT 使用 `gpt-5-2025-08-07` 的 low/high reasoning effort；Gemini 用 `gemini-2.5-pro` 的 min/max thinking budget；DeepSeek 比较 `deepseek-chat` 与 `deepseek-reasoner`。这是推理配置/模型变体比较，不是纯参数规模因果实验。moderation 主实验只用 reasoning 版本。

附录 Table 4 实际还报告了 Llama3-8B、Gemma3-12B、Gemma3-27B 的小模型 pilot，并因为低表现、不稳定和无一致提升而排除出主实验。所以不能声称前作完全没看弱模型；本研究可贡献系统的、避免事后排除弱模型的学习曲线和失败分析。

S/G/M 分别为最小任务说明、原始 guideline、moderated guideline。Table 1 报最终独立评测，Figure 3 的逐轮错误矩阵只是 10 文档 adaptation 诊断，两者必须区分。NCBI GPT 约 G=0.7264、M=0.7588；BioRED GPT 约 0.7630→0.8165。Table 6 对 held-out 文档做配对 bootstrap/approximate randomization；不同模型增益不都显著，不能概括为所有模型都得到确证。

§6.3 的成本是最后一轮成本乘迭代数的估计，不是每次调用完整相加的精确 ledger。这给本研究精确反馈和运行预算审计留出改进空间，但仅“记录成本更细”不足以成为论文中心贡献。

## 4. 已经取得的真实公开数据与配置

README 明确称其为重组后的 refinement workflow release，不保证 bit-for-bit 复现。实查文件统计如下，数字来自此次 checkout，不是抄论文：

| 数据 | train 文档 / denotations | valid 文档 / denotations |
|---|---:|---:|
| NCBI Disease | 593 / 5,148 | 100 / 791 |
| BC5CDR | 500 / 9,643 | 100 / 2,146 |
| BioRED | 400 / 13,351 | 100 / 3,533 |

BioRED 公开 checkout 的 3,533 与论文 Table 1/5 的 3,531 不一致，需检查版本、重复实体与排除规则，不能掩盖。NCBI 与 BC5CDR 的 valid 实体数符合论文。guideline 文本均已存在：NCBI 7,629 bytes、BioRED 7,153、BC5CDR 8,403；不是仅有标签名。

NCBI spec：`experiments/ncbi_disease_valid_round1.spec.json`，sample_size=10、seed=42、n_examples=5、threshold_f1=0.9，models 共享抽样。运行其纯本地抽样函数得到如下 source IDs：

`10196379, 10484772, 10545613, 10577908, 10724160, 1303173, 1345170, 1671881, 6859721, 8326491`。

这 10 个文档总计 **74 个 gold annotation、12,000 个文本字符**。`n_examples=5` 只是错误组 prompt 截断，不是“只看五个 gold”；代码的 TP 证据最多取 5 个文档、每个最多 5 个正确实体，且带完整文档文本。指南自身也含例子。样本预算必须计入这些通道。

## 5. 公开实现与论文设置的差异：复现前必须标记

- 发布 spec 默认 `gpt-5`，论文为日期固定版本；CLI 构造 provider 只传 model，未传论文 high reasoning 配置。直接运行默认命令不能声称严格复现。
- `OpenAIProvider` 使用 Chat Completions endpoint，但 payload 使用 `max_tokens`，并把可选 reasoning 配置写成 `reasoning: {effort: ...}`。需要对照实际 provider 官方接口、做最小真实调用核实，不能在未成功调用时声称高 reasoning 已启用。不要为获得响应默默删除配置。
- 代码增加 `SAFE_MAX_ITERATIONS=20`；与论文主要停止规则并存，复现实验要记录。
- 代码 `generate_moderation_principle` 的调用传 schema、discrepancy pattern 与例子，未把 current guideline 单独传入；论文该步骤描述包含 current guideline。使用公开代码 vs 按正文重实现必须区分。
- 代码 overlap 匹配按循环次序处理，并非单独先完成所有 label mismatch 再做 boundary；遇到复杂多重重叠应测试。TP 例子从集合交集中截断，跨进程次序可能变化，需保留实际 prompt；若排序保证确定性，记录为本地复现修正。
- 原文 NCBI 表记 3 moderation iterations，而正文讨论 A0–A3 为四个 annotation states，不能混淆为迭代数矛盾。

这些是忠实度审计问题，不证明原论文结果错误。优先使用官方代码与输入，并透明记录必要兼容性修正。

## 6. 最小复现实验：可以直接推进的设置

以 **NCBI Disease** 作为单任务校准，数据、guideline、schema、抽样 ID 已取得，不再需要等待额外语料。保持四类型 strict span+type 任务，使用上述 10 train / 100 valid 划分和原始全文指南。

第一步核实一个真实、版本明确的推理 backend；目前父任务最新运行证据为网络已可达、Codex 返回 **401 登录失效**，不是继续等待 403 解封。本文未自己再次探测 credentials；只记录父任务最新诊断。它也不等于已具有 OpenAI/Gemini/DeepSeek API 授权。

其次运行一次原指南 G；按公开 moderation 流程运行 M，完整保存初始/每轮 predictions、prompts、gold反馈、接受/回滚决策、最终 guideline 与 exact token/cost ledger；然后冻结最终 guideline 标注 100 valid。至少运行 G/M；若要复现论文三条件，增加 S。一个模型一次配置是**工作流校准**，不是新的稳健科学结论。

若指定历史模型仍可用并配置一致，可报告 attempted numerical reproduction；否则明确是换模型的 workflow replication，并说明不能预期逐位复现 0.7264/0.7588。评测本地完成即可，无需向 PubAnnotation 发布或上传任何内容。进一步确认 corpus 的原始许可和代码再分发许可，公开仓库可读不等于自动授权复制全部原始资产到论文仓库。

校准后，把该 moderation 作为主实验的规范精炼 baseline，再对照共享全部已购例子的冻结检索与规范+程序条件。使用 development 调试，把新构式/政策测试保留，增加 B=0 及多预算、多轨迹；按模型/领域精度和成本需要推进，不能把 calibration 单次提升包装成新机制发现。

## 7. 对当前稿件的修订要求（本次未改 paper 源码）

关于此文的“仅核实官方摘要、未读全文”现已过时，应替换为本次全文+公开代码审计；其他论文仍按各自阅读状态描述，不能整体升级为全部全文核实。最近邻复现仍未实际调用模型，不能替换成“已复现”。

novelty paragraph 应承认既有独立保留集验证、10 文档 moderation、规则副作用和弱模型 pilot，再限定到**预算曲线、反馈匹配的原例/规范/程序表示比较，以及构式/政策/跨域边界**。把全部网络仍遭 403 的现状描述更新为实际证据：网络已恢复，现阶段真实推理因登录/可用授权仍受阻。过去的 403 日志作为历史记录保留，不再作为当前阻塞原因。
