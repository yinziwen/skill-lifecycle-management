# v0.2.0 技术设计
Meta Skill 负责路由、授权、LLM 归一化、自然语言推荐及真实用户确认；Python 3.9+ CLI 负责 SQLite 持久化、保守聚类、推荐状态、审批、版本及反馈。现有 slm.sqlite3 schema 保留，新增 recommendation_state；WAL、busy_timeout 与唯一键防止并发重复写入。旧记录没有可选字段时视作项目级普通价值。没有后台服务，宿主必须实际加载 Skill。通用/TeleAgent 入口大小写分包。依赖检测使用 find_spec/shutil.which，不加载第三方模块、不安装。Embedding 留为未来提供者接口，当前由宿主完成语义分析。发布前真实平台验证。

# v0.2.1 技术设计
保留 tasks 主键及历史 JSON。新增 task_sessions(task_ref, session_id) 复合主键与外键，事务内回填原会话；record 比较去掉 session_id 的完整规范化数据，事务内追加会话关联，保留原始记录。新增 task-sessions PROJECT TASK_ID 查询。数据库新增表不破坏旧数据；备份后单版本使用。统一 validate_draft(require_dependencies=True) 用于新建/优化提案及应用；明确列表和声明标志；历史版本不重写。审批、应用在写事务内重新计算 hash 并验证；失败回滚。依赖缺失可保留为未验证草稿，不能发布。此修复不增加宿主自动触发机制。
