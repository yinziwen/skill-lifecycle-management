# SLM v0.2.1 协议

## 任务记录
UTF-8 JSON。必填 task_id/project_id/source/summary/goal_key/operation_key/output_key/workflow/constraints/category/status/evidence/verified。task_id 在项目内稳定唯一，跨窗口续做同一个任务仍使用同一标识；session_id 可选，仅用于溯源，不作为独立任务判定。同一项目、task_id 的规范化内容除 session_id 外一致时追加关联并返回 duplicate，原记录保持不变。task-sessions PROJECT TASK_ID 查询全部关联。内容冲突仍拒绝。goal/operation/output/workflow 使用小写 ASCII 规范化语义键（点、连字符），由宿主 LLM 从授权上下文提取并复用历史键。category: skill/rule/hook/workflow/preference/tool/unknown。status: success/failed/unknown；verified=true 必须有成功证据及实际步骤。

可选 scope=project（默认）或 general（已授权、脱敏通用经验）；reuse_value=normal（默认）或 high（必须附 value_evidence）。同项目默认匹配；跨项目须显式 --cross-project 且两边均标记 general。候选依据规范键和约束一致、实际步骤集合 Jaccard >=0.75、组内两两匹配。默认三条独立成功任务；至少两条有依据的 high 任务允许提前推荐。上述阈值为产品策略，不是训练结果。

## 推荐
observe FILE [--cross-project] 写入并返回 recommendations；recommend PROJECT [--cross-project] 只查询。候选返回 pattern_id、notice_id、notice_count、action=create/reuse/optimize、choices、tasks、minimum、scope。宿主负责复核语义、实际价值和外部技能等效性。展示后 recommend-decide PROJECT NOTICE_ID shown；用户暂缓 later、忽略 ignore、明确恢复 reset。冷却24小时且独立证据增加才重新建议；ignore 持久有效。重复提案待处理时不再提醒。已注册的模式建议复用，当前版本有失败反馈时建议优化；需要宿主判断根因。通知为当前答复中的建议，不提供后台推送。

## 提案
propose-create JSON: draft、project_id、rationale、pattern_id、完整 task_refs [{project_id,task_id}]；同项目兼容旧 task_ids 字符串数组。跨项目明确 cross_project_authorized=true。draft.name/description/goal/trigger/non_triggers/inputs/steps/constraints/acceptance/dependencies；dependencies 元素 python:MODULE（顶层模块）或 command:EXECUTABLE；所有新建和优化提案必须显式提交完整 dependencies 列表；保持原依赖也须重列，确认无额外依赖才填 []。历史版本缺省依赖仍为未知；历史未完成提案缺声明须重新生成审批。依赖检测只检查可发现性，不验证版本或运行成功。提案先 pending 后经真实用户明确批准，再 decide ID HASH approve、apply ID；reject 记为暂缓。审批与应用前重新计算并比对 hash；版本基线变更拒绝执行。本地状态保护不是身份认证。

## 反馈和版本
feedback result: pass/fail/unknown，case_id 同技能同版本唯一，source/evidence 必填，duration_ms/tokens/interventions 未知填 null。evaluate 只汇总记录；propose-optimize 需完整 draft、当前版本 feedback_ids、rationale。skill-info 查询版本；dependency-check NAME VERSION 检查实际解释器；export NAME VERSION NEW_DIR 目录必须不存在；propose-rollback NAME VERSION 审批后切换活跃版本。无自动安装/发布。

## 扩展接口（设计，尚未实现）
未来 SemanticProvider 可定义 normalize(task_context, candidate_keys) -> TaskRecord 和 embed(redacted_fields) -> vector；嵌入仅用于召回，必须经过目标/约束硬门控及宿主语义复核。本版没有独立 Embedding 模型、网络请求或后台监听。当前接口是宿主 LLM 生成结构化 JSON + CLI；无需依赖特定模型供应商。
