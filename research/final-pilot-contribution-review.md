# 诊断样稿最终贡献审阅

审阅日期：2026-10-06。对象：当前 `paper/main.tex` 的真实结果诊断稿。本次是 AI 审稿角色的文本与科学主张审查，不是新实验或对全部日志的独立复算；未改论文源文件。

## 总评

**可以作为用户先行检查的诊断样稿交付；不应标为完成研究或 ACL submission-ready。** 当前标题、摘要、提示框、结果讨论与 Limitations 对这一界限基本一致。与此前版本相比，稿件已明确纳入真实 API 和真图实验，也正确撤掉了“尚无模型运行”这一过时陈述。

全文没有将 controller 完成循环等同于所有 prediction/adaptation 成功，也没有把表中模型档位差异解释为能力排名。大模型静态对照中断后不进入完整 cell 比较，处理说明清楚。API 信用耗尽是当前可执行实验阻塞；它不能被写成模型学习失败，稿件已作区分。

若作为 ACL 实证稿审阅，我目前仍不建议接收：核心干预的一个分支没有真正执行程序，提供商失败与条件/运行顺序混淆，最近邻方法比较未完成，且主要结果只覆盖小规模抽样。诚实的诊断有工程和研究规划价值，但目前不足以识别原始研究问题中的学习机制与边界。

## 是否仍暗示研究完成或因果效果？

总体没有。以下表述尤其正确，应保留：

- `planned prediction episodes` 而非全部成功样本；各模型 completed/HTTP/tool-limit 分别报告。
- 表格明确为 pipeline accuracy，失败保留分母，并说明这不是模型能力估计。
- `Program use is a failed manipulation`：零程序执行只能说明该 controller 下没有发生预期干预，不能用来判断程序自演化有效或无效。
- notes 实际被读取与 notes 的因果收益明确分开；Mini 完整上下文控制与 notes 接近，不能独占归因于持久适应。
- 非单调曲线没有被解释为过拟合，视觉零属性命中没有被解释为已找到学习边界。
- 最近邻已经阅读全文/代码，但忠实模型复现仍未完成，且自由笔记没有冒充 moderation。
- 401/429 诊断重放没有被追溯套到原始所有 HTTP failures；没有伪造错误原因的逐例分类。

**没有发现把不存在的有效科学对比写成已完成结果的陈述。** 这不等于验证所有数字：本轮没有重新计算全部新表格、bootstrap 或视觉指标。最终交付时仍需保证表格与封存结果 manifest 一致，并将当前失败/成本明细一并提供。

## 建议立即收紧的少数措辞

1. **摘要末句 `a concrete design for the next adequately powered study` 过强。** 当前提供三个必要方向，没有给出功效/精度依据和样本量设计。建议改为 `a concrete plan for the next controlled study`，或者 `requirements for a larger, controlled study`。不要把尚无论证的后续研究预先叫 adequately powered。

2. **方法范围需指明 SNACS。** `The official guideline remains accessible in every condition` 若被读成同时描述 Fashionpedia，会与后文 taxonomy-only 冲突。建议改成 `In the SNACS pilot, the official guideline remains accessible in every condition; the visual pilot instead uses the explicitly documented taxonomy inventory.` 同理，完整上下文对照只在一个 seed/B16 的有限配置运行，不能从通用协议句读成全矩阵均已计算。

3. **“registered”不要暗示外部预注册。** 当前 `Materials and Registered Settings` 和 `as registered` 应注明是本地冻结配置；推荐标题 `Materials and Fixed Pilot Settings`。保留实际冻结时间、配置哈希与后续修订记录即可，不必添加未经实现的 preregistration 身份。

4. **静态对照结论可再精确一点。** `This prevents attributing the raw notes advantage to persistent adaptation alone` 大体合适，但该对照仅一个轨迹且本身存在有效输出缺失，不能视为证实“全部差异由检索造成”。可改为 `This supplies a competing explanation based on evidence presentation, although the single-trajectory control is itself insufficient to identify the source of the difference.`

这些属于措辞和覆盖范围修正，不需要新增 API 请求，也不改变结果。

## 如何向用户交付这份样稿

建议明确说明：这是已经有真实结果、可检查方法与失败记录的诊断稿；当前未完成用户要求的完整 agent 研究。一次精确诊断重放确认了 `429 credit_balance_exhausted`，因此停止新增调用。不能写成“整个 API 不可用”或“所有历史错误都由信用不足导致”，也不能只说泛泛网络问题。

应该同时交付 PDF/源码及结果状态摘要；科学阻塞和账户阻塞分别说明：恢复可用余额只解除运行障碍，不会自动解决差异化失败、零程序执行和缺乏最近邻对照。重跑前先冻结新的运行/重试计划并校验程序干预能够真正发生，再继续耗费预算。

## 后续决定性的三个补项

1. **恢复有效干预与可比运行。** 补足推理账户条件，先验证程序确实被调用且能作用于预测，再采用均衡运行顺序、统一重试与冻结失败策略重跑配对 cell；保留旧 pilot 为诊断记录，不拼接成功子样本来制造完整比较。
2. **完成最近邻和强信息对照。** 加入真正的 structured moderation，保持原例检索与完整上下文基线，分别计算反馈与实际调用成本；这是区别已发表规范精炼工作的必要证据。
3. **扩展到能回答问题的评测。** 增加独立适应轨迹和评测文档，并用专家确认的约定/政策案例及保留迁移集识别学习机制。否则继续增加相同小样本上的运行次数，也无法回答“举一反三的边界”或“多少例子足够”。

最终判定：**真实、透明、可供用户审阅的诊断样稿；科学研究未完成，当前不建议投稿。**
