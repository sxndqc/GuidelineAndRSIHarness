# Manifesto / MARPOR benchmark 审查

核验日期：2026-10-06。结论：**研究适配准备 GO；当前真实数据实验 NO-GO（可解除的资源门槛），作为主 benchmark 暂不承诺。** Manifesto 能提供“按复杂规范给政治文本编码”的不同任务，但不能仅凭其跨国规模就认定它测量的是少样本规范学习。当前尚未取得并逐条读完完整 handbook，未下载真实 corpus，未运行模型实验。

## 1. 实际核验的来源与证据边界

| 来源 | 本次实际读到的证据 |
|---|---|
| [项目维护方 manifestoR README](https://github.com/ManifestoProject/manifestoR/blob/master/README.md) | 客户端访问 Manifesto Corpus 的 coded election programmes；要求通过官网账户获取 API key；提供 `mp_corpus`、`codes` 工作流 |
| [CRAN 发布包 DESCRIPTION 镜像](https://github.com/cran/manifestoR/blob/master/DESCRIPTION) | 当前读到版本为 1.6.3，2026-05-15；软件许可 GPL >= 3；官方项目网址与维护者 |
| [CRAN 发布包 workflow](https://github.com/cran/manifestoR/blob/master/vignettes/manifestoRworkflow.Rmd) | quasi-sentence 编码、文档/选举/语言元数据、`handbook` 版本字段、availability、原文与英语翻译、corpus 与 MPDS 分别锁版本 |
| [codebook.R](https://github.com/cran/manifestoR/blob/master/R/codebook.R) | codebook 仅为类别的 condensed descriptions；完整 coding instructions 需另看 handbook；codebook 部分接口不需要 key |
| [codes.R](https://github.com/cran/manifestoR/blob/master/R/codes.R) | Handbook v5 到 v4 的映射有特殊处理，不能统一取前三位；CEE 子类别也有专门映射 |
| [db_api.R](https://github.com/cran/manifestoR/blob/master/R/db_api.R) | corpus 请求需要配置 API key；通过 Authorization header 发送；部分版本/codebook 请求除外 |
| [corpus.R](https://github.com/cran/manifestoR/blob/master/R/corpus.R) | 文本与 `cmp_code`、可选 `eu_code` 是不同数据列；同一文档可以有多个编码层 |

以上 CRAN 发布包文件已保存至 [sources/manifesto](sources/manifesto/)，下载来源、时间及 SHA-256 见 [manifest.json](sources/manifesto/manifest.json)。这是官方发行包的 CRAN 镜像，不应把 GitHub `ManifestoProject/manifestoR` 的较旧 1.3.0 分支误当最新客户端。

尝试访问官方 [handbook 列表](https://manifesto-project.wzb.eu/information/documents/handbooks)、[corpus 说明](https://manifesto-project.wzb.eu/information/documents/corpus) 时，连接代理返回 `Tunnel connection failed: 403 Forbidden`。因此没有读到官网页面内容，也没有绕过网络限制。客户端给出的 handbook 官方入口已核实；handbook 正文、其完整版本列表、数据当前使用条款**未核实**。另尝试的 terms URL 也被代理拦截，其路径是否有效未能确认。

## 2. 数据：必须选择 Corpus，不是只下载 MPDS

MPDS/Main Dataset 的政党—选举级类别比例与左右立场指标不能替代逐 quasi-sentence 的监督标签。标注研究需要 **Manifesto Corpus 中确实有 `annotations == TRUE` 的原文及逐条 `cmp_code`**。官方 workflow 明确：不是每个党—选举都有机器可读文本，也不是每个有文本的文档都有数字编码。可用 `mp_availability` 先筛选，不能按 MPDS 总规模宣称训练标签量。

已确认有用字段：

- `manifesto_id`：文档标识，通常包含党代码与选举时间；同一党—选举可能有多个文档。
- `party`、`date`、`language`：用于分组与域外测试。
- `handbook`：使用的规范版本（例如 4 或 5，自 corpus 2016-6 起提供）。
- `is_primary_doc`：是否是该党—选举用于项目编码的主要文档。
- `may_contradict_core_dataset`：文本编码和 MPDS 汇总可能不一致，例如重编码或历史纸质编码转录。
- `has_eu_code`：可能还有欧洲联盟层面的额外编码；本研究初版只用主 `cmp_code`，不能让 `eu_code` 暗中成为输入。
- `translation_en`：自 corpus 2024-1 起许多文档可取英语翻译；原本为英语则返回英语原文。

**没有在本次核验的官方资源中找到现成的统一 train/dev/test benchmark 划分或文本分类 leaderboard scorer。** 这意味着本项目需要定义并发布自己的划分与指标，不意味着全世界不存在派生 benchmark。也没有核实覆盖全部 corpus 的多标注员逐项标签，不得把单一现有标签当作专家一致意见。

## 3. Handbook 与规范变化：适配潜力真实，覆盖缺口尚未证明

存在文档级 `handbook` 字段，是很有价值的自然版本控制线索。正式主实验先固定一个 handbook 版本；不能将不同版本混合后的错误直接归因于 agent 不会规范。

当前已核实的 v5→v4 官方映射：`202.2`、`605.2`、`703.2` 映射为 `0`；其他满足官方规则的三级小数子类才折叠到对应三位类别。因此：

1. 代码必须保存为字符串，不应先转浮点，也不应简单截断。
2. 若定义 v4 聚合任务，要使用经过核验的显式映射并说明信息损失。
3. 该映射说明规范库存发生变化，**并不证明同一句文本在新旧版本下拥有经专家独立产生的两套 gold**。不能仅靠映射代码就宣称已具备自然 policy-switch benchmark。
4. `0`、`000`、`uncod`、缺失值、标题标记等表示需要在选定 release 的真实导出中审计；不能把缺失监督当正常类别，也不能悄悄去掉难标项来提高分数。

下载到完整 handbook 后，应建立条款/例证索引并记录原生示例曝光量；仅给类别短描述再声称“guideline 不完整”会人为构造弱 baseline。尚未核实的候选现象包括多议题表述、隐式政策主张、否定/评价、类别边界与上下文依赖，需政治文本标注专家先看数据及指南再确认。

## 4. ACL reviewer 的核心质疑

**政治知识与规范学习混在一起。** 模型可能识别政党、政治人物和典型口号，然后预测其常见议题类别。主实验限制元数据为切分/审计使用，不给党派历史立场、MPDS 类别分布、RILE 等派生 gold。原文不可避免仍有党名和国家背景，因此需要报告相同文本输入下的 guideline-only 与少样本增量，另做谨慎的党名遮蔽诊断；遮蔽可能破坏语义，不能用它取代自然任务。

**切分与标签决策不是同一个任务。** quasi-sentence 是标注单元，未必等同标点分句。初版给定官方单位，只预测类别，明确这是 gold segmentation 条件；若以后让 agent 自行切分，需单独评估边界及标签联合质量。不能把长句切错导致的下降解释为不会规范。完整 handbook 到手前，不应擅自写出“官方切分规则”。

**上下文是必需的受控变量。** 单个 quasi-sentence 可能依赖前后语境。初版统一给前后固定窗口的原始文本并突出目标单位，邻接单位不显示 gold。所有方法获得同样上下文。单实例、邻接实例、整文档的证据预算要区分；如果整篇带 gold 的 manifesto 被 agent 读过，不能只把其中检索出来的 8 条计为 8-shot。

**随机逐句划分会造成严重泄漏。** 同 manifesto 的模板、标题、邻接内容以及同党跨届重复承诺，使 quasi-sentence IID 假设很弱。适应/开发/测试按整篇文档分组；原文与译文、同党—选举多个版本必须同组。跨届近重复段落须检测并把重复簇放在同侧，保留去重前后统计。最终误差区间至少按文档聚类；只有少数文档时不能靠大量句子制造“高统计显著性”。

**跨国/跨时间包含许多变化。** 不同语言、不同政治制度、议题分布、时代词汇、handbook 更新可能同时改变。先同语言同 handbook，再分别构造 held-out party、later election、held-out country；无法满足这些条件时，结论只能是组合域偏移。英语翻译跨国实验测量翻译后的输入分布，不能冒充原文多语言泛化，也不能把原文放在train、译文放在test。

**人类 gold 可能不唯一。** 本次未核实逐项 coder disagreement 数据或可引用的一致率。初版应请至少两名适当训练的政治文本标注员盲标独立样本，记录可接受替代标签、指南支持与裁决。分别报告对原始 corpus gold 和专家裁决样本的一致性；不能把不同意见全称为 guideline 缺口。若分歧主要来自信息不足或体系设计，更多例子也不一定能解决。

## 5. 最小可执行任务

### 任务定义

输入：一种语言（默认优先英语原文）、同一 handbook 版本、给定目标 quasi-sentence 及固定原始上下文；输出：该版本的 `cmp_code` 字符串。标签库存从锁定 handbook/机器可读表得到；不根据测试集中出现的类别临时裁剪标签集。类别清单本身可公开，逐实例 gold 只通过预算工具显示。

主指标：本研究定义的 macro-F1（固定标签集合、明确零支持类别处理）及 accuracy；另报每类支持数、无效代码率、文档级汇总误差。它们是我们公开实现的指标，**不是经核实的官方 benchmark scorer**。不要以 RILE 误差取代细粒度标注质量，左右分类的抵消可能掩盖大量类别错误。

### 落地步骤

1. 在可访问官网的环境核查完整 handbook 和文本/标注使用条款；锁定 handbook 文件、corpus snapshot 与 MPDS 查询版本。当前官网域名需要加入环境网络设置。
2. 使用用户账户已经拥有或新建的 Manifesto API key 读取 availability 和 metadata；key 仅由环境 secret 注入，不进仓库、日志或聊天。先选 `annotations == TRUE`、英语原文、同 handbook、primary documents。
3. 只下载有资格的适应/开发文档，先审计真实字段、无效码与版本映射。最终测试另由 controller 保存，不挂载完整 corpus 给 agent。
4. 在适应/开发区内按文档分组建立 pilot，预算先试 0/8/32 个新增 gold 单元；三种状态条件为冻结原例检索、规则记忆、规则记忆+代码。所有方法共享随机嵌套例序。单元数是工程起点，不是足够标注量或统计功效保证。
5. 采用 gold 自评分、错位 ID 拒绝、无效标签检测、doc/translation overlap audit、版本映射边界测试验证适配器。开发数据不足以支撑独立文档数量时缩减研究问题，不用随机句子拆分填满实验。
6. 两名相关专家审计小规模类别边界与上下文依赖样本；再决定该任务能否提供“例子补足规范操作知识”的证据。只有看见与规范有关的可定位差异，才将它升为主任务。

### GO / NO-GO 门槛

| 决策 | 目前状态 |
|---|---|
| 编写本审查、定义数据投影/预算/分组协议 | GO，已完成审查并保存官方客户端证据 |
| 声称已完整核实 handbook 或 corpus 许可 | NO-GO，官网代理403，正文/条款未取得 |
| 拉取真实编码语料并运行有效模型实验 | 当前 NO-GO：网络阻断 + 未配置可用 API key + 数据使用条款待核查 |
| 使用代码GPL宣称政治宣言可自由再分发 | NO-GO；软件、编码数据库、原始文本权利必须区分 |
| 只拿类别短描述充当完整 guideline | NO-GO；官方明确 codebook 不等同 handbook |
| 以英语同版本固定切分做 pilot | 有条件 GO：访问/条款就绪，metadata 确认有足够独立文档后执行 |
| 直接主张跨国少样本规范学习边界 | NO-GO，须先分离语言、制度、时间、近重复和规范版本 |

## 6. 当前环境事实与下一次解阻所需信息

实际检查环境配置：`observations_current = true`；配置的 secrets、runtime variables、outbound identities 均为空。仅检查进程变量名，未发现包含 `MANIFESTO` / `MARPOR` / `CMP_API` 的变量；没有读取或打印凭据内容。官方客户端已证实取 corpus 需要账户 API key；这不是根据某个工具没有登录就推断认证缺失。

准备真实数据实验至少需要：网络设置允许 `manifesto-project.wzb.eu`；环境安全注入 Manifesto API key，或用户提供其合法取得的官方 corpus 导出和对应 handbook/条款。现阶段不能通过其他镜像规避被禁止的官网网络访问，也不能凭一个网络403断言账号没有权限。API实时访问、返回schema和许可最终确认仍是待完成验证。

**最终判断：Manifesto 是有说服力的候选“跨领域规范编码”任务，优于只继续添加与 UMR 相近的语义图任务；但在当前证据下，它是有条件候选而非已ready benchmark。** 真正有价值的是同 handbook 的类别边界学习及受控规范/域迁移，而不是随意挑一批公开政治文本做 few-shot 分类。

## 7. 无 API key 备选与官方 fixtures 的追加核验

为检查是否存在可以直接支持真实实验的官方开放文件，本次实际浅克隆了两个公开仓库，未执行仓库程序：

- CRAN 最新发行包镜像，commit `e89f85537334c9576ec31856cfac9b2f8ae10a8e`：没有 bundled `tests/data` corpus；`inst/extdata/fk_issue_structure_2015.csv` 和 `fk_issue_structure_2019.csv` 是国家/选举/类别结构数据，没有逐 quasi-sentence 的 text+cmp_code。
- ManifestoProject 维护方旧仓库，commit `51f7a59d76134eb17e50a612fd61b1d0759261b6`：`tests/data/` 中四个 CSV 分别为 `clarity_replication.csv`、`iad_replication.csv`、`lrfranz.csv`、`niche_bischof_replication.csv`，列名显示为党/国家/日期以及类别比例、左右立场、议题多样性等汇总值。它们不是可用来训练文本编码器的标注句子。

[官方 testcorpus.R](https://github.com/ManifestoProject/manifestoR/blob/51f7a59d76134eb17e50a612fd61b1d0759261b6/tests/testthat/testcorpus.R) 第一行调用 `mp_setapikey("../manifesto_apikey.txt")`，测试通过在线 `mp_corpus` 拉取 Sweden 等语料。所谓 corpus tests 不是离线附带的真实语料 fixture。用户提供的合法导出仍可作为入口，但本次核查范围内没有找到官方公开无需 key 的完整句级标注下载路径。

不能将这几个汇总 CSV 当作小型 benchmark，更不能以它们训练/测试后声称完成了 guideline-driven annotation 实验。公开文档中的少量展示样例最多用于格式核查，不能形成有意义的独立训练测试集；其展示许可也不自动扩张为 corpus 再分发许可。

建议安全配置 secret 名称为 **`MANIFESTO_API_KEY`**。这是本项目建议的环境变量名，不是 manifestoR 官方自动读取的约定。获取数据脚本显式使用 `mp_setapikey(key = Sys.getenv("MANIFESTO_API_KEY"))`；缺失时停止，日志只记录“已配置/未配置”。不得打印key、提交key文件、把完整认证请求头写日志。

当前完成真实实验仍缺：官网网络策略变更生效；可用 API key 或合法官方导出；选定版本的完整 handbook；corpus 文本与编码的具体使用/再分发条款；实际 availability 清单与真实导出 schema；足够独立文档和专家审计。网络设置保存后应重试官方入口，不能把本次403当作永久不可访问。给 corpus 解锁仅解决数据访问，并不能自动证明版本对齐、标注一致性或数据许可。
