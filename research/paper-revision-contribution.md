# 小规模真实 pilot 阶段的论文贡献修订

审阅日期：2026-10-06。已重新读取 `paper/main.tex`、SNACS 两个正式 pilot config，并抽查 SNACS/Fashionpedia episode 文件。本次仅写建议，不改论文源码。现有 episode 同时包含 completed 和 failed 状态；没有据不完整运行结果作任何效果判断。

## 1. 可直接替换的 Related Work / novelty

以下 LaTeX 只使用当前 bibliography 已存在的 citation keys，可以直接替换 `Related Work and Novelty Boundary` 的正文。对最近邻的描述来自已经读完的正文、附录和公开实现；不再写“只核实摘要”。

```latex
Guideline-conditioned annotation predates this study. GoLLIE uses
annotation guidelines for information extraction \citep{gollie}, while
GuideBench evaluates domain-oriented rule following and responses to
rule updates \citep{guidebench}. These studies motivate distinguishing
access to a policy from the ability to apply it. Our question concerns
how newly revealed annotations are retained and used by a fixed-weight
system, rather than whether language models can read guidelines.

The closest work is \citet{kim2026refining}. Their moderation procedure
annotates a small adaptation set, groups prediction--gold discrepancies,
contrasts errors with verified correct cases, generates a general
principle with negative constraints, and integrates it into the complete
guideline. Updates are retained only when adaptation-set strict-match F1
improves, with an additional stopping threshold of 0.9. For each of three
biomedical NER datasets, refinement uses ten documents sampled from the
original training split, followed by independent evaluation on 100
documents from the original development split. The study also compares
reasoning configurations and analyzes both corrected errors and newly
introduced false positives. Thus, persistent guideline refinement,
low-supervision adaptation, held-out evaluation, and refinement-induced
regressions are established precedents for our study.

We examine a narrower empirical question: under matched access to labeled
examples, what additional benefit is provided by natural-language notes
and executable programs over retaining the original examples? The
ten-document setting of \citet{kim2026refining} does not establish a
sample-efficiency curve; its discussion explicitly identifies varying
the amount of refinement data as future work. Our intended extension
combines budget-dependent comparisons with analysis of retrieval,
state construction, and state execution. The current small pilots do
not establish a general advantage of persistent adaptation, a sufficient
number of examples, or state-of-the-art performance. Our free-form notes
condition is not a reproduction of their structured moderation method;
that comparison remains necessary before attributing gains to a new
adaptation mechanism.
```

这里有意写 `matched access to labeled examples`，没有写已经做到 matched total computation：调用上限相同不等于实际 token、工具使用和适应计算相同。待完整 ledger 汇总后再报告实际资源差异。也没有把随机未见句子叫 unseen-construction transfer。

通用 agent memory 与 self-modifying program 文献仍应在最终稿补齐，尤其 CER、Gödel Agent 与工具增强标注工作；本次可编译替换片段不虚构缺失的 bib keys，也不把这些机制声称为新发明。

## 2. 主问题段落应与实际运行一致

当前 `Our proposed comparison isolates persistent external state...` 语气略强。pilot 还没有排除成本、retrieval、notes内容与程序调用差异，建议替换为：

```latex
We compare systems that retain purchased examples, additionally maintain
free-form notes, or additionally permit executable annotation programs.
Our goal is to distinguish the effects of these persistent assets from
access to examples and additional computation. We begin with small
supplied-target SNACS and supplied-region Fashionpedia pilots. These
settings support feasibility checks and within-pilot comparisons; broader
claims about construction transfer, policy changes, or annotation sample
requirements require further experiments.
```

`Conditions and Identification` 中把当前三条件称为 persistent guideline refinement 也应修改为 free-form notes；实际是附加笔记，不能等同于最近邻完整 guideline rewrite。需按最终实现准确说明 notes_program 是否允许重写 guideline、是否执行程序、是否存在回滚机制。

## 3. 删除过时阻塞，不提前宣布运行成功

以下说法已经过时，应从摘要、提示框、Implementation 与 Limitations 同步删除或改成历史诊断记录：

- `Model experiments ... prerequisites remain unresolved`、`Model experiments have not run` 和 `no model API binding ... found`。
- `All numerical results come from completed non-LLM controls`：只有当正文仍未纳入任何新数字时才在字面上成立，不能用它描述整个项目当前状态。
- `Full annotations and actual images have not yet been acquired`：Fashionpedia 真图 pilot 已在运行。
- 最近邻仅核实摘要、全文仍未读取。
- 当前因为 403 网络或 401 登录无法推理：新的 API 已成功执行真实调用，旧错误不再是当前实验状态。

在正式完整汇总前，可用以下实施状态段落：

```latex
A working API backend is now available, and real SNACS and Fashionpedia
pilot episodes have been executed. Earlier network and login failures
describe the setup history rather than a current inference blocker.
We report a pilot configuration only after reconciling its planned
evaluation instances, completed predictions, failures, and usage records.
Partial execution is not treated as a completed benchmark result.
The closest-work workflow has been inspected in full text and public
code, but its model-based reproduction remains incomplete.
```

新结果表进入稿件时，摘要必须明确“non-LLM controls + small real-agent pilots”，并使用实际分母。运行途中不应填写预期 improvement、不应把失败 episode 从分母静默移除。若模型拒答/格式错误按错误评分，说明；若 API 故障需重试，保留原失败与重试费用，说明哪些配置未完整完成。

## 4. 当前 pilot 的准确范围

当前 SNACS config 指定 `gpt-5.4-mini-2026-03-17` 与 `gpt-5.4-2026-03-05`，reasoning_effort 为 `none`，预算 0/4/16，seeds 11/23，test 最多 24 句，统一 evaluation_seed=20261006。这与较早的 GPT-4.1 API 连通性探测及三条 seed 计划不同。论文模型名称、轨迹数必须从最终运行 manifest/实际响应确认，不能引用早期计划。

这些条件支持同家族两档 pilot，不能称“reasoning vs non-reasoning 对照”，也不能仅根据命名断言具体参数规模原因。24 句子内的多个 target 不等于大量独立评测样本；两条适应序列更不足以准确估计总体样本效率。B=0 的重复必须按推理随机性处理，不能说具有两个不同适应样本。

Fashionpedia 给定区域减少定位负担，保留视觉感知与服装知识混淆；它扩大 pilot 模态，不证明已确认 guideline gap，也不是完整 segmentation benchmark。Manifesto 尚无结果时应继续放在资源/未来扩展部分，不能计入“已完成跨领域实验”数量。

## 5. 投稿前最重要的三个补项

1. **补足关键比较。** 完成一个 biomedical 数据集的最近邻 moderation 校准，主任务加入其迁移基线，并验证冻结检索/完整例子提示足够强；只有这样才能将状态更新收益与已发表规范精炼和信息获取收益区分开。
2. **获得足够稳定的真实学习曲线。** 完成并核对当前全部配置，保留失败和成本；随后扩大冻结评测集、适应轨迹及有意义的预算范围，预先规定质量目标和不确定性分析。小 pilot 不能回答“多少例子足够”，也不能因几次正差异宣称普遍优越。
3. **证明所解释的机制。** 在训练侧专家确认至少一组可学习的约定/缺口或政策变化，独立保留对应迁移测试，并通过证据供应与结构/感知诊断区分规则归纳、检索、执行和格式收益。没有这一步，论文最多是在已知标签任务上比较提示与工具配置，尚未回答原始研究问题。

当前可诚实报告“已经启动并执行真实小规模 agent 实验”，不能报告“完整研究已经完成”或“已达到 ACL 投稿标准”。
