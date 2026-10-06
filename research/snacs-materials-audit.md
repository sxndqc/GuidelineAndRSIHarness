# SNACS 2.6 运行材料审计

日期：2026-10-06。用途：允许使用完整公开手册开展内部 Agent pilot；不是规范缺口的专家认证，也不是完整手册的再分发许可确认。

## 版本与完整性

本地 PDF 与 `data/raw/papers/snacs-guidelines.txt` 的首页明确标注 **Adposition and Case Supersenses v2.6: Guidelines for English**、arXiv:1704.02134v8（2022-07-07）、正文日期 June 18, 2022。文本保留目录、52 标签定义、construal 说明、编号示例、修订历史、参考文献和索引；提取文本包含 114 个 PDF 页界。

完整文本作为单个可分页读取/search 的材料提供，而非用人工生成的短指南替代。其 SHA-256 为 `2399afd629aa682a5f74d66499ec7a3f6079df2186fead27bc9b57cdd7bbbbce`；PDF 独立哈希见 `configs/snacs-materials.json`。PDF 提取的 small caps 标签有空格、数学/排版符号可能近似，使用者不得把原排版层级损失当成原指南没有说明。

手册摘要将 STREUSLE 4.5 与 guideline 2.6 对齐。固定数据 commit 的 README 同样记录 4.5 对 SNACS 2.6 的标签更新，后续版本主要为 UD 更新与小修正；这足以支持 ontology 版本对齐，不证明之后每个 corpus correction 均可由手册逐条推导。

## 原生例子不能视为零监督

对提取全文应用 Python 正则 `(?m)^[ \t\f]*\((\d+)\)[ \t]+`，得到 543 次行首编号匹配、**541 个不同编号例组**，范围 (1)–(541) 连续无缺号；456、484 各有重复匹配，按唯一编号去重。

这是可复算的**编号例组数量**，不是已核实的 541 个带标签实例，更不是 541 个预测 target。例组可以包含 a/b/c 子例、多种替换、反例、多个目标；正文和表格还包含未编号例子。部分编号行是对已有例子的重新列出，文本抽取也可能改变换行。因此 manifest 的 `embedded_labeled_examples` 保留 null，另以结构化字段明确记录 541 个编号组及计数方法，不伪造精确 gold decision 数。

论文与运行报告应表述为：**完整指南（含 541 个编号例组及其他原生示例）+ B 个新增带标签句子**。预算 B=0 不等于没有示例。所有比较条件共享完整材料，读取时间/成本另外计量。

## 数据重叠初筛

以 NFKD、lowercase、删除非 ASCII 字母数字的确定性标准化，将每个 projected 完整句子在完整标准化手册中检索。只检查标准化后长度至少 25 的句子：train 1827、dev 233、test 228；三个集合均无完整句子命中。

这个筛查使用 trusted controller 侧的公开输入文本，不向 Agent 提供 test gold。它不是独立性证明：短句、手册中的局部带标签片段、改写、PDF 提取噪声以及语义近例尚未逐项排查。当前可运行冻结 pilot；不得仅凭零命中声称 unseen-construction 泛化或完全无测试相关例子。

## 许可审查范围

全文未发现明确 copyright/Creative Commons 授权声明。尝试请求固定 arXiv v8 摘要页的许可元数据，被执行环境网络阻止；因此不能确定其具体再分发许可。STREUSLE 标注的 CC BY-SA 4.0 **不能转移为这份论文/手册的许可**。

当前用途限于用户请求的本地研究参考和模型 pilot。manifest 记录来源和哈希，不将完整手册作为仓库再分发资产；任何面向外部发布完整 PDF/提取文本的操作仍需先确认相应权利。`status: audited` 表示这些检查和局限已记录，不表示获得作者授权或完成法律认证。这个限定不妨碍进行当前内部参考材料实验。

## 运行结论

已将 `configs/snacs-materials.json` 从占位状态更新为有范围限定的 `audited` 状态，记录固定版本、全文/PDF 哈希、原生例组统计、版本对齐证据、重叠初筛和未决许可项。可以启动真实 SNACS pilot；正式外部分发或未见构式结论仍须分别满足上面的条件。
