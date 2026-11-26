# Skill 创建助手（SLM）

**主动发现重复工作，将经过验证的经验沉淀为可复用 Skill。**

[English](README.md) · [宿主验收](docs/HOST-TEST.md) · [发布审查](docs/RELEASE-REVIEW.md)

版本：**v0.2.1 GitHub 发布候选版**。采用 Meta Skill + Python/SQLite 独立核心引擎，结合宿主模型语义理解与 SDD（规范驱动开发）。发现相似任务后提出创建、复用或优化建议，最终由用户决定。

## 核心功能

| 功能 | 说明 |
| --- | --- |
| 双入口 | 宿主语义自动选择与显式调用相结合 |
| 语义识别 | 将不同表达归一化为目标、操作、产物和约束 |
| 跨会话经验 | 授权固定目录内的脱敏摘要共享，默认项目隔离 |
| 主动推荐 | 默认三个独立成功任务；两个有证据的高价值成功任务可提前推荐 |
| 推荐管理 | 调整、暂缓、不再提醒；默认冷却24小时且需新增证据 |
| SDD 创建 | 审批后生成规格、计划、任务、指令型 Skill 和测试用例 |
| 持续优化 | 依据反馈提出优化，依赖声明、版本记录与审批回滚 |

## 安装条件及方法

需要 Python 3.9+（含 sqlite3）、授权的本地读写和执行能力，以及支持 Skill 加载与语义分析的宿主。核心不依赖额外 pip 包。使用外部 Skills CLI 时才需要 Node.js/npm。

仓库正式发布后，将 `OWNER` 替换为实际 GitHub 用户名：

```bash
npx skills add OWNER/skill-lifecycle-management --skill skill-lifecycle-management
```

本地测试：在解压后的仓库根目录运行：

```bash
npx skills add ./skills/skill-lifecycle-management
```

也可执行 `python tools/package.py` 生成 ZIP，按宿主支持的导入方式安装。TeleAgent 使用小写 `skill.md` 的专用包，TRAE/Codex 等使用标准 `SKILL.md` 包。以上为安装路径设计，尚未完成本发布候选的宿主实测。升级前备份旧 Skill 和完整数据目录，停止写入后处理 SQLite/WAL，不同时运行新旧版本。

## 使用示例

首次使用：请初始化 Skill 创建助手，询问授权固定本地数据目录，仅记录脱敏任务摘要；创建、优化、安装及公开发布分别审批。

随后正常执行三个独立任务，例如：修复数值计算错误、字符串处理错误、参数校验错误，均保持无关逻辑不变并执行验证。宿主加载技能后，可以查询历史；若有充分证据，推荐「最小范围代码修改」Skill。用户可选择创建、调整、暂缓或不再提醒。确认具体规格及哈希后，才可执行创建/优化。

如果宿主未自动触发，可直接提出“分析最近有哪些重复任务值得封装”。不需要为触发而伪造任务次数。

## 核心命令与测试

在仓库根目录运行：

```bash
python skills/skill-lifecycle-management/scripts/slm.py --version
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data --help
python -m unittest discover -s skills/skill-lifecycle-management/tests -v
python tools/package.py
```

合成数据体验（独立测试库，不写正式数据）：

```bash
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data observe skills/skill-lifecycle-management/assets/task.example.json
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data tasks --project demo
```

示例任务未验证，不计为真实成功经验。详细参数见 [CLI 指南](docs/CLI-CN.md)，测试结束后可删除 local-test-data。

## 已验证与平台限制

核心自动化测试仅验证确定性逻辑（任务去重、跨进程、审批、生成、依赖检查、回滚等），不等同于真实语义准确率及自动触发率。语义提取依赖宿主 LLM，没有独立 Embedding。宿主未加载技能时无法观测对话；没有后台监听、自动安装及公开发布 API。跨会话同一任务必须复用稳定 task_id。生成指令型 Skill 草稿，不生成可执行代码。依赖可发现性不保证实际运行。审批状态不是独立人类身份认证；本地数据库写权限必须受到保护。

真实测试证据：[原核心报告](docs/TEST-RESULTS.txt) · [发布包复测](docs/DISTRIBUTION-TEST.txt)。TeleAgent/TRAE 等宿主的本版本实际导入、触发、真实语义识别及生成技能效果待验证。

## 目录与发布

`skills/skill-lifecycle-management/` 是完整可安装技能目录，包含核心脚本、执行协议、SDD 规格、示例及测试。`tools/package.py` 构建通用及 TeleAgent 安装包与 SHA-256 清单。GitHub Actions 提供三平台测试、版本标签或手动触发自动打包，不自动公开发布。发布前请审阅 [安全政策](SECURITY.md) 和 [发布审查](docs/RELEASE-REVIEW.md)。

## 开源许可

**目前尚未授予公开分发许可。** 源码未自带许可证；MIT 仅为待所有者确认的模板。请确认代码及职务成果归属、公司政策及第三方权利，再正式采用许可证并公开。见 [许可审查](docs/LICENSE-REVIEW.md)。
