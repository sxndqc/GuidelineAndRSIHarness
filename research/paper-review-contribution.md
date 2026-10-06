# 论文终审：贡献、真实性与下一实验

审阅日期：2026-10-06。审阅对象：`paper/main.tex`、`paper/references.bib`、控制实验表、`results/snacs-controls/baseline-results.json` 及预测文件、`results/control-analysis.json`、`results/verification.json` 和实验状态记录。本意见来自 AI 审稿角色，不代表真实 ACL 审稿或领域专家裁决。

后续状态更新：最近邻 Kim et al. (2026) 现已完成全文与公开实现阅读，详见 [closest-work-fulltext-review.md](closest-work-fulltext-review.md)。本文下面“尚未读全方法”的判断记录的是本次终审当时状态，不再适用于该篇；其真正的模型复现仍未运行。全文明确已有 10 train 文档适应、100 official-dev 文档独立评测，不能把独立评测当作我们的新贡献。最新父任务诊断还显示网络已恢复，Codex 推理当前为 401 登录失效，不能再沿用 403 作为当前阻塞说明。

## 结论

**当前版本是诚实的研究协议与初步控制实验工作稿，不是完成的 ACL 实证研究，也尚不能作为用户要求的完整研究交付。** 建议当前不投稿，以核心 agent 对照为下一实验优先级。不可投稿的主要原因是证据不覆盖核心科学问题，而不是必须取得正结果：即使持久记忆与程序都没有收益，经过充分控制的真实负结果仍可能形成论文。

## 1. 是否超出结果或虚构数据？

本次审查未发现正文将不存在的 agent、视觉、政治文本或人工实验写成已完成结果。标题中的 `Protocol and Preliminary Controls`、摘要和独立提示框均明确范围。正文没有把 UMR 职业同位语观察当成已证实的官方 guideline 遗漏，也未把 Fashionpedia API 两图样例当正式实验数据。这些限定应保留到真实实验替换它们为止。

我独立从保存的 60 个 run records 重算了 128 句预算下的均值与样本标准差：majority 15.0515% / 0；lexical majority 32.6598% / 3.6466；TF–IDF nearest 25.0309% / 1.7226，与论文四舍五入值一致。存在 60 个预测文件；按仓库 `digest` 的 canonical JSON 规则重新计算，全部与记录的预测 SHA-256 一致。这里的 hash 是 JSON 内容摘要，不是文件原始字节摘要，未来 artifact 文档宜明确区别。

本文未独立重跑全部模型/控制流程、重算 bootstrap 或验证完整隔离实现。因此上述检查支持“保存结果内部一致”，不构成对所有实验执行历史的独立认证。原始日志、代码、数据哈希仍需随 artifact 保留。工作区中的 registration JSON 是本地事前设定记录，不等于外部注册平台的可验证 preregistration；正文目前仅说设置在预测前记录，不宜升级为正式预注册研究。

`7.63` 个百分点的差异与保存的分析记录一致，95% 区间被明确称为 descriptive，且承认五条轨迹的限制。当前没有用这一区间支持 agent 假设，也没有从 128 句外推“多少例子足够”，表述合适。60 个 run 是 3 方法 × 4 预算 × 5 共享轨迹，不是 60 次独立随机研究；正文应继续保持这一解释。

## 2. 当前不可投稿的明确原因

1. **研究对象缺席。** 核心问题是固定权重 agent 的持久状态适应，现有三种算法既不读 guideline、也不调用 LLM、不生成记忆或程序。控制实验可验证数据与预算管线，但无法支持主贡献。
2. **最近邻没有实证对照。** `Refining and Reusing Annotation Guidelines for LLM Annotation` 已覆盖迭代 guideline 精炼、少量监督和模型差异。尚未读全方法、复现或迁移该 moderation 流程，不能证明拟议比较增加了新的科学认识。
3. **外部效度仍是资源清单。** Manifesto 与 Fashionpedia 的协议设计扩大了研究范围，但没有实际模型结果。现有证据仅是一个英语 given-target SNACS 任务，不能宣称跨领域或跨模态学习结论。
4. **缺失规则机制没有观测。** 未经专家确认的 guideline 缺口、没有构式保留测试、没有诊断性证据供应，无法区分规则归纳、检索失败、先验知识、感知失败与格式改善。
5. **“样本足够”和“强弱差异”尚未测量。** 没有零例子 agent 基线、模型配对、目标质量阈值、完整曲线或人工参照。现有 4/16/64/128 句控制曲线仅说明三种控制的表现。
6. **文献与引用不完整。** CER、Gödel Agent、工具增强标注、2024 concept-guideline 研究等与机制定位直接相关，但当前 references 只有少数条目。摘要核实不能替代全文的新颖性分析，作者占位符也尚未清除。

论文不应借投向 resource/protocol track 自动规避这些问题：若改成纯 benchmark/protocol 贡献，仍需经验证的数据划分、专家确认的现象/政策案例、真实系统结果和与已有协议的明确增量，而非单纯通用 harness。

## 3. 下一优先实验：最小可判定的 agent 对照

先恢复并核实可复现推理后端，同时取得版本对齐的 SNACS 完整材料。记录模型版本、运行日期、temperature、推理 token、模型调用/工具调用预算、重试与截断策略。登录成功或网络 draft 已保存不等于实验后端可用。

第一阶段用 **development split** 确认接口和成本，再固定配置，在 held-out test 上比较一个模型的三种条件：

- 冻结 guideline 检索 + 全部已购原始例子；拥有与其他条件相同的固定格式校验器。
- 最近邻 moderation/规范精炼条件；同样的训练例子、gold feedback 及预算，持续更新自然语言资产。
- 精炼 + 程序条件；只有可执行资产更新权限不同。记录程序是否真正改变预测，而非仅格式化结果。

预算必须包含 B=0 与至少一个小预算和一个较大预算，序列嵌套且条件配对。第一批作为可行性 pilot，不用少数轨迹直接发表强结论；通过后按先定精度/成本计划增加轨迹。现有经典控制已在 test 上查看过，不代表该 test 已失效，但今后的 agent 调试与方案选择应在 development 上进行并留下记录。

主报告应同时给出语义正确率、输出有效率、实际已读的标签决策数、token/调用成本、失败/重试率与资产摘要。不能给适应组额外监督或大量额外计算后把收益全部归因于状态表示；资源无法严格相等时，应报告质量—成本曲线与差异来源。

先回答“精炼比同证据冻结检索更好吗？程序在精炼基础上有增量吗？”再扩展强弱模型配对、oracle evidence、构式迁移与政策切换。若第一批无收益，优先查有效资产是否产生、检索是否公平、评价是否足够敏感，而非立即增加复杂 agent。

与此同时，应全文核实最近邻并在其一个可取得的 biomedical NER 数据集完成校准复现；它不必加入所有模型/预算的全矩阵。Manifesto/Fashionpedia 获取和许可核查可并行，但正式跨域实验应沿已稳定协议推进，避免三个任务各自使用不同的信息与反馈条件。

## 4. Fashionpedia 作者元数据替换建议

当前 `author={{Fashionpedia authors}}` 是明确占位符，不能保留到投稿。[官方 API README](https://github.com/KMnP/fashionpedia-api/blob/1ef732050e15d446c38d58ef945ccadc28c59328/README.md) 提供以下 BibTeX，可以作为有来源的替换：

```bibtex
@inproceedings{fashionpedia,
  title={Fashionpedia: Ontology, Segmentation, and an Attribute Localization Dataset},
  author={Jia, Menglin and Shi, Mengyun and Sirotenko, Mikhail and Cui, Yin and Cardie, Claire and Hariharan, Bharath and Adam, Hartwig and Belongie, Serge},
  booktitle={European Conference on Computer Vision (ECCV)},
  year={2020},
  url={https://arxiv.org/abs/2004.12276}
}
```

值得保留的来源差异：官方项目 `index.html` 的引用块将 Adam 与 Hariharan 的顺序对调，API README 如上。不能用网站 contributor 列表补作者（它还列出其他贡献者）。本次全文 PDF 仍未取得，最终应以论文首页/出版元数据确定作者顺序、书目和页码；以上建议明确采用 API 作者提供的引用，未声称完成论文首页核实。

STREUSLE、Manifesto 的当前软件/仓库引用可以帮助重现版本，但还需要正式数据集、SNACS 规范和 Corpus 的标准引文；GuideBench 等也应使用官方 venue/DOI 元数据。未发现凭空杜撰论文题名的证据，不过本次没有重新独立核对每个作者条目，不能把“未发现问题”升级为“全部文献已认证”。

## 最终决定

**工作稿可保留、可供团队评审；目前对 ACL 实证投稿的判断为不通过。** 下一关键里程碑是获得真实、可审计且预算匹配的 agent 对照，而不是继续打磨稿件措辞或增加经典控制次数。完整研究是否成立，最终取决于这些实验对最近邻方法给出的新机制证据，包括严谨的负结果。
