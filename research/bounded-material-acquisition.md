# 有界真实材料获取：Fashionpedia 与 Manifesto

2026-10-06；用于工程pilot，不能冒充完整实验或代表性benchmark结果。

## Fashionpedia：官方train/val配对材料

已核验官方 [CVDF下载说明](https://github.com/cvdfoundation/fashionpedia) 及S3对象HEAD：

| 文件 | 官方URL | bytes |
|---|---|---:|
| train images ZIP | https://s3.amazonaws.com/ifashionist-dataset/images/train2020.zip | 3,344,364,592 |
| val/test images ZIP | https://s3.amazonaws.com/ifashionist-dataset/images/val_test2020.zip | 236,499,034 |
| instance train JSON | https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_train2020.json | 542,193,045 |
| global attribute train JSON | https://s3.amazonaws.com/ifashionist-dataset/annotations/attributes_train2020.json | 27,496,742 |

HTTP范围请求实测返回206。为避免整包下载，先读取global train JSON获得图像ID到filename映射，再读取instance train JSON前4MB并解析完整JSON对象，选择前16个完整图像组；按ZIP中央目录、成员头和成员内容的字节偏移分别请求指定JPEG。Python `zipfile`检查成员CRC；未关闭TLS或校验。

本地ignored数据：

- `data/raw/fashionpedia/train_prefix_pilot.json`：16张官方train图、138个实例；所有这些图像的完整实例均位于读取前缀中。
- `data/raw/fashionpedia/val_pilot.json`：seed 20261006，从官方val图像ID排序列表抽16张，114个实例。
- `data/raw/fashionpedia/images/train/`、`images/val/`：上述JPEG。
- `data/raw/fashionpedia/bounded_acquisition.json`：每张图像官方ZIP URL、member路径、文件大小与SHA-256；总传输计数。

标签库存为46类、294属性。官方global train文件只用于图像metadata/ontology映射，预测目标仍取instance annotation。训练材料未取自val；验证标签不能进入agent适应文件系统。原始`original_url`也可指向Flickr等源站，但本次实际使用官方ZIP图像，避免源站图像缺失或尺寸不同。

**选择偏差**：训练前缀不构成官方train随机样本，因此只能称工程pilot。这16图可用于验证图像API、格式、分类标签与工具流程；不能据此给出完整数据的样本效率、强弱模型边界或ACL最终结论。训练一个实例意味着暴露该实例gold；若读取整图全部138实例gold则必须计138决策，不可笼统报16-shot。

最小真实图像任务可以固定官方bbox/实例位置、预测category或属性，分离检测与规范决策。即使输入用了gold定位，也必须明确是oracle localization任务；不能把分类准确率称为Fashionpedia官方实例分割AP。若只有ontology名称而缺少实际标注决策手册，只能先测ontology-conditioned识别，不能据此证明guideline gap。

## Manifesto：手册就绪，语料仍需账户

官网网络已200，已下载2026与2021版v5手册，各约187KB，并实际阅读训练、切分、歧义、上下文及背景知识章节。完整结果见 [manifesto-audit.md](manifesto-audit.md) §8。

官网明确CSV需登录、API需Manifesto key；模型API key不能替代数据key。官方Terms允许科学研究，但未经书面授权禁止再分发原始材料，因此本地原始手册、条款与未来语料保持ignored，仓库仅提交来源和研究代码。

正文还明确六层context hierarchy与受限使用政治背景知识。忠实任务应允许按需读取未标注全文，固定邻句窗口只能算ablation。现有handbook字段只区分4/5，不区分2021/2026同为v5的正文修订；必须再锁正文日期。
