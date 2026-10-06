# 无账户跨领域任务选择：CAP Pennsylvania 与 ContractNLI

2026-10-06，实际访问官方页面、下载公开原始材料并检查字段；没有运行模型。

## 选择

**优先选择 CAP Pennsylvania Bills and Resolutions 的“给定立法摘要，按PA规范预测主题代码”作为下一项受控pilot。** 它拥有真实的领域决策规则和实例，不只是标签名称。当前为有条件GO：可立即开发投影和分组协议，但最终主实验必须先处理规范覆盖、重复冲突及摘要信息不足。不要将其称为已核实的完整立法全文标注流程。

**ContractNLI暂不满足本研究的full-guideline准入条件。** 其公开gold、split、许可非常好，但逐hypothesis的原始例证型标注guideline在本次检视的官方发行包及仓库中未找到。不能拿17条hypothesis与三标签定义当完整指南。

## CAP官方来源与已落地材料

- [项目与人工建设背景](https://www.comparativeagendas.net/project/pennsylvania)：官方说明项目由faculty-supervised students构建；这支持人工整理来源，但不构成逐行双标、全部人工或一致率证明。
- [官方数据目录](https://www.comparativeagendas.net/datasets_codebooks)：Pennsylvania Bills and Resolutions条目直接链接以下CSV与Part2手册。
- [CSV](https://minio.la.utexas.edu/compagendas/datasetfiles/AlltopicsBillsandResolutionsRegularSessions1979_2019_11132019_CAP.csv)，44,766,133 bytes，SHA-256 `0d9909058b2f00d6005840484d5fb711930e039c49b060dd6d48e2ba4d1bded3`。
- [Part 2: Policy Topics Codebook](https://minio.la.utexas.edu/compagendas/codebookfiles/II._Policy_Topics_Coding_061719_1.pdf)，387,121 bytes，73页，SHA-256 `d68c499a6f1f877294936ab8dc3cdde41c3df28a34dd1d81c8e4f76fc65d6944`。
- [许可](https://www.comparativeagendas.net/pages/Copyright-and-Legal)：项目编码及项目生成变量为CC BY-NC-SA 4.0；原始材料另有版权时仍适用其权利。[引用要求](https://www.comparativeagendas.net/pages/How-to-cite)另列国家/项目归属。

均保存在ignored `data/raw/cap-pa/`。包括`bills_resolutions.csv`、`policy_topics_codebook.pdf/.txt`、许可/引用HTML、`source.json`、`audit_stats.json`、`manifest.json`。未绕过账户限制，下载路径直接来自官方公开目录。

注意文件名写1979_2019，但**实际102,727行的year范围是1979–2016**，与目录实际介绍相符。不能照文件名报2019覆盖。

## 手册究竟提供了什么

Part2不是只有类别表：抽取240个三/四位code heading，194处`Rule:`，并有大量`Examples:`和`See also:`。实读例子包括：

- 105：Pennsylvania general appropriations act固定编码105，并给出识别该法案的开头文字。
- 107：专项税收调整按其实体政策领域编码；跨多个领域的通用税改才归107；随后列出医疗、儿童照护、交通等大量交叉引用例外。
- 108：针对特定产业领域的产业政策应归相应实质政策领域。
- 301/300：整套医疗体系改革与若干非统一改革政策组合的边界。

这些是可检索的实际编码决策规则，比Fashionpedia只有names/hierarchy更适合测试经验是否能补充规则应用。

但本次链接只提供**Part2主题编码规则**，没有核实Part1全流程/变量手册。因此可以称“完整下载的73页主题规则手册”，不能称“已拿到该项目所有原始标注操作说明”。也没有找到证明2019手册逐条适用于1979–2016每条gold的版本对照；这项需要明确保留为审计门槛。

## gold字段、信息边界与可执行投影

实际字段包括`id,bill_id,chamber,year,bill_no,...,nuc,...,pa_code,subtopic,...,majortopic`。所有`bill_id`唯一，`nuc`没有空字符串。

**建议目标为字符串`pa_code`，不是`subtopic`。** Part2是PA体系，包含24地方政府等本地内容；数据中26,411行`pa_code != subtopic`，例如PA 2401→CAP 2001、PA1609→CAP1608。用PA手册预测CAP映射后的字段会把不同规范混在一起。这里的字段对应由代码内容与数据实查支持，但尚缺Part1对`pa_code`的正式字段定义；实施时需保留此限定并审查抽样映射。

输入首版仅投影`nuc`摘要；`source/bill_id/year/chamber`仅供controller分组与溯源。预测端删除`pa_code/subtopic/majortopic`以及税收、老年等人工派生filters，不允许通过其他gold层偷答案。将所有代码作为字符串保存。

**摘要充分性未被证明。** 官网说给records分配代码，Part2未给出“只读nuc即可”的保证。相同摘要有冲突gold，可能是信息缺失、变更、噪声或不同全文。因此任务应称“从公开摘要复现PA主题代码”，不称完整立法文件理解。若对错误作规范学习解释，必须人工审查摘要是否含足够信息，必要时另设允许读取官方原bill全文的条件，且对所有方法一致。

目前人工作业来源得到项目介绍支持；未核实逐条人工/机器标记、双标意见和IAA。保守称**项目发布的编码标签**，不声称全部逐条双标gold或无噪声人类真值。

## 规范覆盖与过滤

数据出现238种PA代码。用手册显式heading正则检查，七种代码未匹配，共17行：`162`(1)、`1029`(1)、`1298`(9)、`12100`(2)、`809`(1)、`1021`(2)、`1012`(1)。它们可能是错误、历史码或PDF解析问题；**不能推测修正**。

最低方案：先人工核查这七种在PDF中的存在性，确定固定的完整库存；未核实前将这些17行隔离并发布数量/原因。过滤仅依据预先冻结库存与缺失状态，不依据方法难度或预测错例。不要把有争议多主题摘要悄悄删掉来美化分数。所有其余类别保留，即使在某个训练预算没有出现。

## split与重复：不能随机按row分

实际规范化方式为`lowercase + whitespace collapse`：

- 102,727个记录，66,528个唯一摘要；重复额外行36,199。
- 15,452个摘要簇跨year重复。
- 550个相同摘要簇含不同`pa_code`，共2,107行。

`bill_id`开头包含session年份，结合同一字母编号在另一session复用，因此仅bill_no不能定义独立样本；按完整bill_id又不足以防跨届重提同一法案。数据没有官方机器学习split。

建议由controller先建立文档家族：完整bill_id、规范化相同摘要及高相似近重复摘要的连通簇。所有簇只能落入一个split；近重复阈值在开发区审计后冻结。baseline正式split可按簇随机划分并固定seed，保留类别分布；时间外推另做，跨时间边界重复簇必须整体分配或从时间测试中隔离，并报告损失。**自建group split不能称官方split。**

对550冲突摘要簇，不进行majority relabel。主自然噪声轨可保留同簇同侧并报告冲突分层；干净诊断轨可预先隔离全部冲突簇，但应明确不代表全体语料。不能只隔离测试中的冲突。按group bootstrap计算不确定性，不能把重复法案当独立观察。

## 最小实验协议

1. 冻结手册/CSV hash，完成上述7码和若干多主题摘要的人工审计。
2. 暴露可搜索73页规范、有限已购例子；从适应池按group抽样构造嵌套预算，先测试0/4/16/64例。一次示例定义为一条摘要及其单一PA主题代码；相同摘要/家族不得重复计独立例。
3. 固定测试group，至少覆盖多个不同政策类别；政策长尾成绩另报，不将每类只有一例当稳健差异。必须保留rule-only、原例工具、笔记与程序组之间的相同信息权限。
4. 主要指标：PA完整代码accuracy与固定库存macro-F1，另报major级诊断（PA major映射从手册取得，不从CAP`majortopic`偷映射）。这是自建research metric，没有发现统一官方ML scorer。
5. 主claim限定为**政策主题规范应用**。政治背景、时代语义、摘要信息丢失、gold冲突与规则学习分别诊断。原manual的例子属于既有监督，并计量与语料的重叠。

## 可检验的信息边界：摘要相同但gold不同

预先固定的防泄漏规范化函数为Python `re.sub(r"\s+", " ", text.lower()).strip()`。不删除标点/数字，不词干化，不按gold决定哪些文字保留，也不做Unicode兼容折叠。split簇键为完整规范化文本（归档可另存其SHA-256）。**主模型输入保留原始`nuc`，规范化只用于防泄漏分组；不人为改变输入制造歧义。** 全文数据和跨行gold只由host/controller持有；agent接收原始`nuc`及预算内已购例子，无bill ID、row ID文本提示、year、party或隐含gold字段。预测结果可由controller外侧关联opaque ID，但若模型能利用实例ID作区分，则只按文本相同计算的信息上界不再适用。

对固定经验分布，任何只看该规范化摘要、并且对同一摘要输出相同标签的确定性分类器，最多正确：

`sum_over_clusters(max_over_labels(count(cluster, label)))`。

除以行数得到该经验分布上的最高可实现accuracy。该计算使用全体gold仅作可信host离线数据诊断，**不是可部署分类器，不是未见样本/新分布理论界，不是human ceiling，也不代表这些冲突都是标注错误**。

| 固定数据范围 | 行数 | 规范化摘要簇 | 冲突簇 | 冲突行 | 最多正确 | 经验accuracy界 | 至少无法同时匹配的行 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 全部发布行 | 102,727 | 66,528 | 550 | 2,107 | 102,067 | 99.3575204% | 660 |
| 隔离7种未覆盖码的17行后 | 102,710 | 66,521 | 545 | 2,084 | 102,055 | 99.3622822% | 655 |

仅看冲突行，规范化同文分类器最多分别正确1,447/2,107与1,429/2,084。该分层信息上限比总体接近99%的数字更能揭示重复摘要的局部问题，但仍然不是新样本性能保证。

**输入条件必须一致**：若agent看到保留大小写/空白差异的原始摘要，不能把规范化簇的界硬套给它，因为这些差异原则上可用来区分行。若给year、全文或其他上下文，也可能解除同输入不同gold。实做规范化输入轨与有上下文轨时，应分别称“受限信息一致性”与“增加信息后的变化”，不能把后者超过上述界解读为违反信息限制。

数据分层不得按预测表现挑选：固定支持码规则后，在host建立一致簇与冲突簇；所有方法用同一group split，整个摘要簇只能落在train/dev/test的一侧，near-duplicate家族再把相关簇合并。两层都保留并报告准确率、支持数及失败；不静默清掉冲突样本，也不把majority label当裁决gold。标签仅用于预先分层/固定split平衡，最终test gold不向agent暴露。

正式实验建议同时报告row-weighted与group-macro结果：前者重现发布分布，后者避免同文大量复制支配总体分数。适应预算区分“唯一摘要数”与“揭示的标注行数”；一个冲突簇若展示多条不同gold，必须计多次标注曝光并显式告知不一致，不能假装它提供多条独立自然语言例证。首轮可每适应簇随机揭示一条行，并把该选择随seed固定，各方法共享；这种有限反馈下，模型未知冲突是预期而非作弊。

数字已保存至`data/raw/cap-pa/summary_ambiguity_bound.json`，可直接离线重算。新增账目文件应加入后续材料manifest更新。

### 原始exact-string输入的主分析（优先于规范化界）

进一步以CSV解析后的**原始`nuc`字符串完全相同**建立信息簇，不lower、不改空白，得到：

| 数据范围 | 行数 | 原始摘要簇 | 冲突簇 | 冲突行 | 全体最多正确 | 全体经验accuracy界 | 冲突行最多正确/总数 | 冲突子集经验界 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 全部发布行 | 102,727 | 66,722 | 545 | 2,089 | 102,072 | 99.3623877% | 1,434/2,089 | 68.6452848% |
| 隔离17行后 | 102,710 | 66,715 | 540 | 2,066 | 102,060 | 99.3671502% | 1,416/2,066 | 68.5382381% |

因此即便完整保留摘要大小写与空白，只看相同文本且输出一致的分类器，也无法同时匹配全部发布标签：全体至少655行、隔离后至少650行无法同时匹配。没有通过规范化创造这一冲突。正式主输入轨使用这个raw-exact经验界，normalized统计只用于split保护与补充数据分析。

“任何确定性分类器”还需固定同一资产/示例/算法状态：如果不同重复实例给不同训练例或可变外部信息，就不是相同输入。该经验界不是一个模型在随机测试抽样上绝不能超过的常数；测试行构成变化后界也变化，必须按相应固定集合重新计算。随机化预测也可能在一次有限抽样中偶然更多正确，但在同输入标签分布上的期望不能超过多数标签的经验上限。不能用理论措辞夸大到未知分布或法律真实含义。

### 人工gold与版本的最终证据等级

人工来源只确证到官方项目说明的“faculty-supervised students”建设，以及数据目录的项目对records赋主题码；没有取得逐行标注员/双标/人工机器标记，因而不能宣布这批102,727条全部逐条人工核验。旧官方页面链接的Temple项目地址目前返回404，未因此补猜历史流程。

PDF metadata：CreationDate 2019-06-17 15:25:29 UTC，ModDate同日15:25:50 UTC，73页。这与文件名061719吻合，但gold记录为1979–2016。官网将该PDF直接配给CSV，说明它是**官方配套现行主题规范**；不能进一步证明历史gold已全面按2019条款重编码。正式论文应把“与发布规范的一致性”作为任务定义，并通过人工抽样把明显政策修订/历史码与摘要歧义分开。未做这一审计前，agent学习到的可能是历史数据习惯，不纯是2019规范。

## ContractNLI否决证据

[官网](https://stanfordnlp.github.io/contract-nli/)与[官方仓库](https://github.com/stanfordnlp/contract-nli)给CC BY4.0及真实607份NDA；实际检查官方ZIP（65,362,913 bytes），包含train/dev/test=423/61/123文档、17固定hypotheses、span候选及NLI/evidence gold，文档IDs跨split唯一。证据span需包括冗余证据，NotMentioned没有证据；这是一项良好的法律文档标注任务。

但[论文A.1.1](https://aclanthology.org/2021.findings-emnlp.164.pdf)明确说采用**每个hypothesis的example-oriented annotation guideline**。实际发行包只有README、数据、许可、原始合同，没有这套逐hypothesis指南；仓库亦未发现它。论文附录列17假设、界面和标注流程，不能替代未发布的所有例证规则。

另外，论文说明train只复核所选span，most test进一步阅读全文确保覆盖，dev及部分test由primary annotator独立完成；需考虑跨split gold覆盖与标注流程差异。固定17hypotheses测试不能被称为未见schema学习。

因此ContractNLI可以用于“公开任务定义+示例”的次级对照，却**暂不用于本研究完整原始guideline主任务**。没有将CAP或ContractNLI的短标签描述伪装成完整指南。Manifesto保持有前途，现有账户语料门槛仍未由这些替代任务解决。
