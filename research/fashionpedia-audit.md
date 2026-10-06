# Fashionpedia 审计：视觉标注是否能检验规范学习

核查日期：2026-10-06。结论：**纳入跨模态 pilot，但先运行给定区域的类别/属性标注；现有公开证据尚不能证明它具有可从少量例子归纳的真实 guideline 缺口。** 不应直接把标准实例分割 AP 的提升解释为规范学习。本文只记录文献/数据结构审计及实验协议，不声称已经运行模型实验。

## 1. 已核实的一手资源

| 项目 | 官方证据与结论 |
|---|---|
| 数据规模 | [官方网站源文件](https://github.com/fashionpedia/home/blob/master/index.html)：48,825 张服装图像，覆盖日常、街拍、名人活动、走秀与网购场景；类别 mask 由 crowd workers 标注，局部属性由 fashion experts 标注。 |
| Ontology | [CVDF 官方数据仓库](https://github.com/cvdfoundation/fashionpedia)：27 个主要服装类别、19 个服装部件、294 个细粒度属性及其关系；网站称属性跨 9 个 super categories。 |
| 任务 | 实例分割与局部属性联合预测；另外提供图像级属性预测。图像级属性合并会消除“属性属于哪个实例”的问题，不宜作为本研究唯一 Fashionpedia 任务。 |
| 实例格式 | COCO 风格 JSON，每个 annotation 包含 image_id、category_id、attribute_ids、segmentation、bbox、area、iscrowd。segmentation 为 polygon 或 RLE，属性为每个 mask 的多标签集合。 |
| 标签结构 | category/attribute 含 id、name、supercategory、level、taxonomy_id。**这些字段是名称与层级，不等于详细判定准则。** |
| 样例与评测 | [官方 API](https://github.com/KMnP/fashionpedia-api)，已读取 README、数据样例和 fp_eval.py；审计 checkout commit 为 `1ef732050e15d446c38d58ef945ccadc28c59328`。 |
| 论文 | Jia et al., ECCV 2020, [Fashionpedia: Ontology, Segmentation, and an Attribute Localization Dataset](https://arxiv.org/abs/2004.12276)。官方项目确认为 ECCV 2020 oral。本次 PDF 下载被 HTTP 403 阻断，**未据此声称读过全文或完整标注手册**。 |

### 数据版本陷阱：已经实查，必须处理

API 仓库的 [data/demo/category_attributes_descriptions.json](https://github.com/KMnP/fashionpedia-api/blob/1ef732050e15d446c38d58ef945ccadc28c59328/data/demo/category_attributes_descriptions.json) 含 **46 类、294 属性**。该文件实际提供名称和层级，没有自然语言定义字段。例如类别含 `shirt, blouse`、`top, t-shirt, sweatshirt`；属性含 `classic (t-shirt)`、`polo (shirt)`。

但 [data/sample.json](https://github.com/KMnP/fashionpedia-api/blob/1ef732050e15d446c38d58ef945ccadc28c59328/data/sample.json) 含 **48 类、320 属性、2 张图、12 个 annotation**，且 info 明确写明：`sample dataset for test purpose. Please refer to the whole dataset for the final version of categories and attributes.`

因此 API sample 只可用于接口 smoke test，不能作为正式 taxonomy、few-shot benchmark 或正式划分。正式数据下载后必须固定文件哈希，核对所有 ID 与 taxonomy，不得将 demo schema 直接套到 sample annotations；也不得把这个样例/正式版差异当作真实政策演化数据。

## 2. 许可与下载状态

[官方 Terms of Use](https://fashionpedia.github.io/home/data_license.html) 的[同源 GitHub 文件](https://github.com/fashionpedia/home/blob/master/data_license.html)已成功读取：

- annotations、ontology 和网站内容：Creative Commons Attribution 4.0。
- software：官方条款列出保留版权声明和免责声明的两条再分发条件；API 仓库还提供 `license.txt`。代码许可不能替代数据或图像许可。
- images：Fashionpedia **不拥有图像版权**，要求遵守 Flickr、Unsplash、Burst by Shopify、Freestocks、Kaboompics 和 Pexels 各来源的条款。不能把整个图像集称为 CC BY 4.0。发布研究产物宜优先发布 split IDs、派生预测、规范审计与下载脚本；如发布图像或 crop，需要保留对应来源及适用许可信息。

官方 README 的直接下载地址：

- [train2020.zip](https://s3.amazonaws.com/ifashionist-dataset/images/train2020.zip)
- [val_test2020.zip](https://s3.amazonaws.com/ifashionist-dataset/images/val_test2020.zip)
- [instances_attributes_train2020.json](https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_train2020.json)
- [instances_attributes_val2020.json](https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_val2020.json)
- [info_test2020.json](https://s3.amazonaws.com/ifashionist-dataset/annotations/info_test2020.json)

本次 Git HTTPS 及 raw.githubusercontent.com 可用；项目网页直连、arXiv PDF、Cornell 技术报告和 S3 validation JSON 请求返回 HTTP 403。项目网页内容通过官方 GitHub 源文件核实，S3 完整标注与图像**尚未下载**。403 只描述本次访问结果，不代表数据集已下架或一定需要新增凭证。正式 test 的上述公开链接是 image info，不能当作公开 test gold；可从公开 train/val 建立预先冻结的研究评测划分，并清楚区分于官方隐藏测试。

完整标注获取进一步核查：官方 `s3.amazonaws.com` 地址的 GET 也返回 403；一次同 bucket 的 virtual-host 地址检查同样返回 403，未获取数据。现已停止替代入口尝试，等待主任务中官方 `s3.amazonaws.com` 网络设置生效后再重试原始链接。

下载恢复后的验收顺序：先获取 validation JSON，保存 SHA-256、字节数、info/version、images/annotations/categories/attributes 数量、非法引用与空属性分布，再获取 train JSON 并核查 image overlap。图像先依据真实 image metadata 下载与 audit/pilot 对应的小批次；README 只列出完整 ZIP，未核实逐图 S3 endpoint，因此不能臆造逐图地址。若必须取得 ZIP，先检查 Content-Length、可用磁盘与压缩包目录，再提取所选 image IDs；如用 `original_url`，保留来源许可并记录失效图像。当前无完整数据统计可报告。

## 3. 原生指标与研究指标必须分开

[API README](https://github.com/KMnP/fashionpedia-api/blob/1ef732050e15d446c38d58ef945ccadc28c59328/README.md) 定义主指标为：

`AP@[IoU=0.50:0.95 | F1=0.50:0.95 | area=all | maxDets=100]`。

它是对象检测/实例分割 AP 的扩展，匹配需满足定位 IoU 和属性 F1 条件；还报告仅 IoU、仅 F1 阈值等诊断结果。官方 [fp_eval.py](https://github.com/KMnP/fashionpedia-api/blob/1ef732050e15d446c38d58ef945ccadc28c59328/fashionpedia/fp_eval.py) 默认 `f1Type = "binary_macro"`，并对无属性类别特殊处理。不可使用自写普通多标签 macro-F1 后仍称其为官方联合 AP；复现时固定官方 evaluator commit、依赖和参数，并处理旧实现与现代依赖兼容性。

给定区域协议可使用类别 accuracy/macro-F1、属性 micro-F1、属性 macro-F1、instance exact-set accuracy 和支持数分层结果，但这些是**本研究新协议的诊断指标，不是官方 leaderboard 分数**。预先定义空属性集合、无属性类别、忽略实例和未标注属性的处理。annotation 中缺少属性不自动证明视觉上不存在该属性，需审计 gold 的完整性后解释 false positive。

## 4. 是否存在可学的规范缺口？目前答案是待验证

Fashionpedia 有专家 ontology、局部属性、多标签关系和视觉例子，确实比再增加一个语义解析数据集更能检验跨模态范围。但“294 个属性很难”不等于“guideline 缺少约定”，模型混淆领型也可能只是看不清或缺少服装知识。

已读官方 README、网站源文件及 JSON 不足以核实完整的 annotator-facing handbook、边界决策表、专家仲裁记录或规则更新日志。不得用模型自行生成的一页说明冒充官方 guideline，也不得宣称找到了未经核实的“官方遗漏规则”。

应先建立小规模人工审计：从训练侧按高混淆类别/属性选取样本，由熟悉服装分类的标注者判断 (a) 图像特征是否可见；(b) 官方可获得文本是否明确给出决策；(c) gold 是否一致；(d) 多个例子是否支持可复用的约定。例子与候选规则来自训练侧，确认规则后的迁移集必须独立保留。每条候选缺口保存来源、适用范围、正反例、争议与可识别性判定。

可以审计类别合并边界、类别与 nickname 属性的分工、属性是否应赋给衣物整体或局部等，但这些只是**候选审计维度，不是已发现的缺口**。遮挡、低分辨率、材料无法从图片辨识等应标为感知/不可识别问题，不强行归入规范不足。

若无法确认真实规范缺口，保留 Fashionpedia 为“视觉 taxonomy/约定执行”的跨模态控制任务，不能用它证明“补全缺失 guideline”。受控另订政策的版本必须明确标为实验构造，并由专家确认可执行，与原生缺口结论分开。

## 5. 三层协议：从规则决策到完整视觉标注

### A. Given-region：建议主 pilot

输入为原图、目标实例编号、gold mask 的轮廓叠加或 bbox，以及可选上下文 crop；不给 gold category 或 attribute。输出 category_id 与 attribute_ids。所有组使用同一图像编码、分辨率、目标区域呈现、可用工具及预算。它隔离检测/分割负担，**仍包含细粒度视觉识别能力**，不能完全隔离规范推理。

再设置 `given-region + given-category` 的属性诊断子条件，明确 category 是 oracle 信息，不能将其结果与完整类别/属性条件直接比较。保留原图上下文，避免 crop 使部件归属、整体/局部关系无法判断。

### B. Given-candidates：区分感知与约定的诊断

固定一个前端模型或预先产生的区域与候选标签列表，全部实验组共享同样 candidates；报告候选 recall 和 oracle ceiling。候选包含错误或漏召回时，结果只是候选选择任务，不能解释成端到端标注。不得根据当前 test gold 为每个实例挑选“刚好含真标签”的候选，除非明确标为 oracle 条件。

可以再加入由独立人员确认的视觉特征描述/证据（不直接透露 gold label）的诊断条件；它改变了输入任务，只用于判断剩余错误是否来自政策执行。感知特征本身无法观测的样本应允许弃权。

### C. End-to-end：外部效度实验

输入原图，agent 输出全部实例、类别、mask 和属性，用官方 evaluator。必须报告分割/定位 AP、类别错误、区域已正确匹配时的属性性能及联合 AP，并固定同样的候选生成与分割工具。若允许 agent 选用、调整或训练视觉模型，需要另算数据、预训练和计算成本；不能把得到更强分割器的收益归到规范记忆。

主研究可以先做 A、用 B 诊断，再对有限配置运行 C；不必在未确认规范学习信号前展开整个分割训练矩阵。

## 6. 固定权重适应的公平实验

比较同一视觉语言模型上的：冻结 guideline + 原始例库检索；迭代自然语言规范精炼（包括最近邻 moderation 方法的适配）；规范精炼 + 可执行程序。已获取的 gold 图片/属性例子对所有组同样可访问，按图像、实例、正属性数及调用成本分别计数。不能把一个包含很多实例/属性的图片与一个简单文本标签都称为“一个样本”后直接比较效率。

代码条件最可能编写 label mapping、结构检查、候选过滤或图像处理工具。格式合法率与类别/属性语义质量必须分开；手工专家提供的映射不可只送给代码组。测试时冻结持久状态，保护 gold 文件和 evaluator，避免模型从官方验证 JSON 读取答案。

按 image 分组划分，所有 crop/part/garment 必须跟随原图；进一步检查同一服装、人物、拍摄系列、近重复图片与公开 tutorial/example 泄漏。多标签长尾需报告每类支持数、常见/稀有属性和可见性分层，不能凭总体 micro-F1 掩盖例外学习失败。given-region 至少使用视觉能力可比的模型配对；模型强弱差异可能来自视觉编码器，不能直接归因于 agent 推理。

## 7. 执行门槛与目前状态

已完成：官方来源核查、官方 API checkout 与数据结构检查、许可区分、指标实现检查、样例版本冲突识别，以及三层实验协议。

下一步必要工作：恢复官方完整数据下载；取得/核实论文及实际标注定义；固定正式 schema、license metadata 和 split；完成小规模专家缺口审计；随后运行 A 的冻结检索与规范精炼小预算比较。若审计不能确认真实缺口，仍可运行跨模态约定执行 pilot，但须收窄结论。

尚未完成：正式数据下载、官方论文全文阅读、真实缺口确认、模型推理及学习曲线。API 的两图测试样例不构成任何样本效率证据。
