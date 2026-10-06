# Fashionpedia真实视觉pilot终审

审查日期：2026-10-06。只读核查 `scripts/prepare_fashion_pilot.py`、`scripts/run_fashion_pilot.py`、`src/guideline_harness/protocol.py`、实际prepared gold、predictions、episodes、assets、results与`paper/main.tex`；未运行任何付费API，未修改实验代码。本文件记录审查时状态，父agent后续修复可能使代码/稿件更新。

## 必须修复的评测实现缺陷

原`score()`把294个属性当成连续ID `0 <= a < 294`。实际官方inventory有294项，ID范围却是0–340且不连续；真实gold包含295、304、317、337等。因此合法性必须依据实际inventory ID集合，不能依据类别数量推断ID范围。

另外，原分类accuracy使用`ok and category==goldcat`，其中`ok`同时要求属性合法。给定区域的类别准确率不应被另一个输出字段的非法属性抹掉；类别正确性与联合输出有效率应分开。属性计数目前又独立于`ok`，导致两个指标对非法输出采用不一致的策略。请定义并验证各字段处理，不要仅修改显示名。

实际离线gold自评分证据：原scorer在16例上返回category accuracy = 0.6875、valid output rate = 0.6875，而attribute F1 = 1.0。这直接证明原合法性逻辑错误，不涉及模型行为。

**当前Mini数值不受这一错误影响**：我逐一核验了五格已保存预测，所有实际输出属性ID恰好都属于官方inventory且低于294；分类独立重算与存储分数一致。可以不调用API，修复scorer并重评分，同时保留原始实现hash与修正说明。不能因当前恰未触发就保留错误scorer。

## 独立重算的实际结果

| 条件 | B | 分类正确/16 | 分类accuracy | TP | FP | FN | completed | HTTP failed | tool-limit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| frozen | 0 | 5/16 | 31.25% | 0 | 10 | 49 | 16 | 0 | 0 |
| frozen | 4 | 6/16 | 37.50% | 0 | 2 | 49 | 15 | 1 | 0 |
| frozen | 16 | 2/16 | 12.50% | 0 | 1 | 49 | 8 | 8 | 0 |
| notes | 4 | 3/16 | 18.75% | 0 | 1 | 49 | 13 | 3 | 0 |
| notes | 16 | 2/16 | 12.50% | 0 | 3 | 49 | 13 | 0 | 3 |

16个region共有49个录入gold属性，3个gold属性集为空，独立核验吻合。五格published-attribute micro-F1均为0，没有预测ID与对应实例gold相交。空/空不产生TP。失败实例保留在分类分母，空预测产生全部gold属性的FN。FP仅是相对已发布标注的不匹配计数，不证明该属性在图像语义上不存在。

稿件对given-region分类、属性annotation agreement及非official AP的限定正确。不能把“five configuration loops completed”写成80个有效模型预测全部完成；实际65/80 prediction episodes completed，12 HTTP failures，3 tool-limit。最好在正文或表中给上述逐格完成数，而不只写笼统存在HTTP失败。

## 必须披露的notes操纵事实

Mini `notes-s11-b4.json` 与 `notes-s11-b16.json` 的资产hash完全相同：

`108e8a8cf04cdcb69d976b73c7bda6e51869144cb514f0e52081a8f70d263b88`。

B4适应完成并调用一次`write_asset`。B16适应虽然status completed，进行了15次`read_example`（14个唯一ID）和3次`read_material`，但**没有任何`write_asset`调用**。所以B16验证使用的是B4笔记外加16个可访问原例，而不是依据16例完成更新后的新笔记。不要把B16称为“16例规范精炼结果”；至少在Fashionpedia段落明确笔记未更新。

两个预算间的notes是顺序持续适应，不是从零独立拟合，这与嵌套轨迹一致，但需如实描述。预算是可访问gold集合大小；如论文另报实际曝光，应从`read_example`及返回带gold的`search_examples`合并去重，不能只数图片观看次数。

## 检索强度与字段审计

- prepared image输入的`text`全部是相同通用提示，target text也全为`marked region`。`search_examples`仅根据这些文字词重叠排名，不读取图像，也不使用视觉embedding。因此它是有图像读取工具的原例访问基线，**不是按视觉相似性检索的强RAG基线**。按ID读取例子仍然有效；稿件应避免暗示视觉相关检索已经实现。
- 选区随机种子为`20261006 + image_id`，候选按annotation ID排序，未按类别/属性筛选。当前代码只排除w/h非正的bbox；审查时实际selection没有额外语义筛选。
- context pad实际是`0.1 * max(w,h)`，并非横纵各自10%；稿件“relative to the longer box side”准确。保持纵横比缩至≤512、红色边框、gold bbox均披露。
- 46类别ID为0–45，294属性ID则不连续。类别名称inventory始终直接给模型，属性名称/父类需要读工具材料；这不等于完整标注manual。
- 同一官方val JSON被controller用于inventory和gold是允许的实现方式，因为agent只收到投影后的inventory与所购train实例，未直接暴露val JSON。应继续保持该权限边界。
- 训练prefix偏差、oracle localization、单seed16例、未标属性不是可靠负例均已在稿件正确限定。无证据支持完整视觉annotation learning、自演化或样本充分性结论。

## 强模型中断

审查时strong `results.json`仍显示running并含B0全失败的0分，父agent已说明将修正为interrupted。B0为16个failed、没有有效完成预测；B4也是失败/预算中止。**这些0是流程占位/失败计分，不是模型分类能力。** 稿件已经将strong视觉run明确列为interrupted并不作模型比较，方向正确。正式归档需同步结果状态，保留episode证据且从能力比较汇总中排除，不删除失败历史。

## 结论

论文已正确称其为真实视觉工程pilot，并没有把分类准确率冒充官方分割AP。当前表述最需补齐：修复稀疏属性ID校验与分类/属性有效性的耦合；披露B16没有更新notes；给逐格65/80总完成及失败数；明确原例搜索没有视觉检索能力。离线修复不会改变本次五格主数值，但能避免发布一个连gold自评分也失败的评测器。

## 审查后修复
主agent已修复稀疏ID membership与分类/属性validity耦合，真实gold自评分三项均1.0；重新计分证明已报告五格数值不变，见results/fashion-scorer-verification.json。正文已说明B16笔记未更新。
