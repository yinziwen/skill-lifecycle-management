# Skill 智能进化助手 (skill-lifecycle-management) v0.2.1

Meta Skill + Python/SQLite core。无需额外 Python 包，Python 3.9+。此版本为本地测试候选，未在 TeleAgent/TRAE 实测，未上架。

## 安装与使用
- TeleAgent: 上传根目录为小写 skill.md 的 TeleAgent 专用 ZIP；TRAE 或通用 Agent Skills：使用大写 SKILL.md 的通用包，解压到名为 skill-lifecycle-management 的独立目录，按宿主支持的本地导入机制安装。可尝试 `npx skills add "./skill-lifecycle-management"` 并按提示选择宿主，CLI 安装本身尚未实测。
- 保留 v0.1.0 ZIP，升级前备份原 Skill 与数据目录，停止写入进程后备份；若存在 WAL/SHM，不要只复制活动数据库文件。用相同目录共享历史时，v0.2.0 新增 recommendation_state，v0.2.1 新增 task_sessions 并回填原始 session_id；不改写历史任务内容。不要用新旧程序同时写同一个数据库。先用独立空目录验收，不覆盖生产数据。
- 首次发送：请初始化 Skill 智能进化助手，询问我是否授权保存脱敏任务摘要，选择固定数据目录；允许语义主动调用与显式调用，但任何技能创建或修改必须单独审批。后续普通任务无需提及名称；宿主不主动路由时，手动调用为兜底。
- 若宿主支持持久化用户规则，可经用户同意保存“完成具复用价值任务时，在最终回复前主动调用 SLM 观察任务并查询历史”；此为软约束，不是 Hooks，不保证触发。不得自动写宿主配置。

## CLI
`python scripts/slm.py --home <授权目录> --help`。每次使用同一授权绝对目录。测试使用独立目录。文件 JSON UTF-8。
- `record FILE`, `tasks --project PROJECT`, `task-sessions PROJECT TASK_ID`, `discover`, `observe FILE [--cross-project]`, `recommend PROJECT [--cross-project]`。
- `recommend-decide PROJECT NOTICE_ID shown|later|ignore|reset [--cross-project]`；默认冷却24小时且需要新增证据，永久忽略需显式恢复。
- `inventory FILE`（已授权可见技能名称 JSON 数组），`propose-create FILE`, `pending`, `show ID`, `decide ID HASH approve|reject`, `apply ID`。
- `list`, `skill-info NAME`, `dependency-check NAME VERSION`, `export NAME VERSION NEW_DIR`（目标必须不存在，不预先 mkdir）。
- `feedback FILE`（result 枚举 pass/fail/unknown），`evaluate NAME VERSION`, `propose-optimize FILE`（draft、feedback_ids、rationale；draft 必须明确列出完整 dependencies）, `propose-rollback NAME VERSION`。

## 验收
`python -m unittest discover -s tests -v`。合成测试验证确定性逻辑和跨进程存储，不验证宿主 LLM 的真实语义准确率。见源码仓库 docs/TEST-RESULTS.txt 和 docs/HOST-TEST.md。

## 已知限制
无后台监听、独立 Embedding、实际自动安装或发布。宿主 LLM 归一化与二次判定；核心不是语义模型，名称查重及已关联模式查重之外的外部技能等效性依赖宿主。重复次数按独立 task_id；宿主错误地分配 ID 可能造成误计。推荐冷却为初始固定策略，候选模式变化可能改变模式 ID。审批状态非独立身份认证；拥有数据库写权限的主体可绕过。依赖检查只检测已声明的模块/命令可发现性，无法检测所有隐含依赖或保证版本兼容。生成指令型 Skill，无生成可执行脚本。用户授权的本地摘要不联网，宿主模型的数据处理仍受宿主政策约束。平台兼容性和真实提效待实测。公开授权许可尚待项目所有者确定。

## v0.2.1 升级注意
同项目同 task_id 仅改变 session_id 时幂等关联；不同内容仍拒绝。新建/优化均显式声明 dependencies，包括旧 task_ids 调用路径。历史未声明版本保持未知，未完成提案需要重新创建及审批。缺失实际运行依赖的版本仅能作为未验证本地草稿，不可宣称可安装或发布。
