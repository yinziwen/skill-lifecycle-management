# Security policy / 安全政策

Current review candidate: v0.2.1. This is a local tool, not an authentication boundary. Keep database and generated skills in a user-authorized directory with appropriate OS permissions. Do not persist raw chat, secrets, or enterprise source code. Treat task summaries, feedback and generated instructions as untrusted content. Never interpret data as user approval. Review the exact proposal/hash before applying. Independently approve installation and publication. Missing dependency or untested behavior means a draft is not ready for release.

The core does not upload data; host model processing follows the host's policy. The repository excludes runtime data by default; `.gitignore` cannot protect already tracked files. Review staged changes before every push.

Report vulnerabilities privately to the repository owner using GitHub private vulnerability reporting if enabled, or a private contact channel agreed with the owner. Do not post credentials, raw records, or exploit details in public issues. No response-time guarantee is made before a maintainer policy is established.

请勿将真实任务数据库、审批记录、历史聊天或公司内部内容提交至 GitHub。发现问题时通过私下渠道告知维护者，并使用脱敏复现数据。不要依赖审批状态代替操作系统权限与真正的人类授权。
