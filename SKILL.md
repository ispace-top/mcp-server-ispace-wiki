# Skill: 爱思文档 Wiki 操作

此 Skill 定义了使用 AI 操作 爱思文档 Wiki 的最佳实践和工作流程。

## 触发条件

当用户要求以下操作时自动应用本 Skill：
- 在 Wiki 上创建、更新、删除、恢复文档
- 批量上传内容到 Wiki
- 从 Wiki 读取文档作为知识库
- 搜索 Wiki 内容
- 管理 Wiki 文档结构（移动、排序）
- 管理文档权限
- 管理评论和划词评论
- 导出文档、查看版本历史
- 查看通知
- 使用模板和标签

## 工具清单

使用 MCP Server `ispace-wiki` 提供的工具（共 32 个）：

### 文档读写

| 工具 | 用途 |
|------|------|
| `wiki_get_document` | 获取单个文档的完整内容 + 元数据 |
| `wiki_list_children` | 列出子文档 |
| `wiki_get_document_tree` | 递归获取文档树，适合构建知识库索引 |
| `wiki_create_document` | 创建新文档 |
| `wiki_update_document` | 修改现有文档（只传要改的字段） |
| `wiki_delete_document` | 删除文档（不可逆，含子文档） |
| `wiki_restore_document` | 从回收站恢复已删除文档 |
| `wiki_move_document` | 移动文档或调整同级排序 |

### 搜索

| 工具 | 用途 |
|------|------|
| `wiki_search` | 全文搜索文档 |
| `wiki_search_users` | 搜索用户（用于 @提及） |

### 权限

| 工具 | 用途 |
|------|------|
| `wiki_get_permissions` | 获取文档的权限列表 |
| `wiki_grant_permission` | 授予用户 view / edit / admin 权限 |
| `wiki_revoke_permission` | 撤销用户权限 |
| `wiki_get_my_permission` | 查看当前用户对文档的权限 |

### 评论

| 工具 | 用途 |
|------|------|
| `wiki_get_comments` | 获取文档评论列表（含回复） |
| `wiki_add_comment` | 添加评论，支持 @提及 |
| `wiki_delete_comment` | 删除评论 |
| `wiki_get_inline_comments` | 获取划词评论列表 |
| `wiki_add_inline_comment` | 在选中文本上添加划词评论 |
| `wiki_delete_inline_comment` | 删除划词评论 |

### 导出与历史

| 工具 | 用途 |
|------|------|
| `wiki_export_document` | 导出为 md / pdf / html |
| `wiki_get_history` | 获取版本历史列表 |
| `wiki_get_history_diff` | 获取历史版本内容（用于对比） |

### 通知

| 工具 | 用途 |
|------|------|
| `wiki_get_notifications` | 获取通知列表 |
| `wiki_get_unread_count` | 获取未读通知数量 |
| `wiki_mark_notifications_read` | 标记通知为已读 |

### 模板与标签

| 工具 | 用途 |
|------|------|
| `wiki_list_templates` | 获取文档模板列表 |
| `wiki_list_tags` | 获取标签列表 |

### 批量与共享

| 工具 | 用途 |
|------|------|
| `wiki_batch_create` | 批量创建多个文档 |
| `wiki_batch_delete` | 批量删除多个文档 |
| `wiki_create_share_link` | 生成文档分享链接 |
| `wiki_get_user_info` | 获取当前登录用户信息 |

## 工作流程

### 流程 1：批量创建子文档

**场景**：用户有一个大文档要拆分成多个子文档上传。

**步骤**：
1. 确认父文档 ID（从用户提供的 URL 中提取，如 `/pages/645/` → `645`）
2. 将内容拆分为独立的文档（每篇 1 个主题）
3. 文档命名规范：`{序号}. {主题名}`，如 `01. Zygote进程详解`
4. 使用 `wiki_batch_create` 一次性上传，比逐个调用 `wiki_create_document` 更高效
5. 上传完成后，使用 `wiki_list_children` 验证
6. 向用户报告创建结果和每个文档的 URL

**示例**：
```
用户: "把这份 Android Framework 笔记拆成 7 个篇章，放到 /pages/645/ 下"
AI:
  1. 拆分为 7 个 .md 文件
  2. wiki_batch_create(parent_id=645, documents=[
       {name: "01. Zygote进程详解", content: "..."},
       {name: "02. AMS活动管理服务详解", content: "..."},
       ...
     ])
  3. 报告: "7/7 创建成功，链接：/pages/646/, /pages/647/, ..."
```

### 流程 2：读取 Wiki 文档作为本地知识库

**场景**：用户需要基于 Wiki 中已有内容回答问题。

**步骤**：
1. 先用 `wiki_get_document_tree` 了解文档结构
2. 确定相关的文档 ID
3. 用 `wiki_get_document` 批量读取内容
4. 基于读取的内容回答问题

### 流程 3：更新已有文档

**场景**：用户要修改某个已有文档的内容。

**步骤**：
1. 用 `wiki_get_document` 先获取当前内容
2. 根据用户要求修改
3. 用 `wiki_update_document` 更新
4. 只传需要修改的字段（name/content/status/tags），未传字段保持不变

### 流程 4：搜索和查找

**场景**：用户要在 Wiki 中搜索内容。

**步骤**：
1. 使用 `wiki_search` 搜索
2. 如需详细内容，用 `wiki_get_document` 获取搜索结果中的文档
3. 综合分析回复用户

### 流程 5：移动文档 / 调整排序

**场景**：用户要重新组织文档结构，移动文档到另一个父节点或调整同级顺序。

**步骤**：
1. 确认要移动的文档 ID 和目标父文档 ID
2. 如果要调整顺序，先用 `wiki_list_children` 了解当前排序
3. 使用 `wiki_move_document(doc_id=..., parent_id=..., position=...)` 执行移动
4. 用 `wiki_list_children` 验证结果
5. 告知用户新位置

**示例**：
```
用户: "把 /pages/700/ 移动到 /pages/645/ 下，放第一个"
AI:
  1. wiki_move_document(doc_id=700, parent_id=645, position=0)
  2. wiki_list_children(parent_id=645) → 确认 700 已排在最前
  3. 报告: "已将 /pages/700/ 移动到 /pages/645/ 下，排在第 1 位"
```

### 流程 6：权限管理

**场景**：用户要授予或撤销某人访问文档的权限。

**步骤**：
1. 如需按用户名查找，先用 `wiki_search_users` 获取 user_id
2. 用 `wiki_get_permissions` 了解当前权限状态
3. 使用 `wiki_grant_permission(doc_id=..., user_id=..., permission="view|edit|admin")` 授权
4. 或使用 `wiki_revoke_permission(doc_id=..., user_id=...)` 撤销权限
5. 验证结果

**示例**：
```
用户: "给张三授予 /pages/645/ 的编辑权限"
AI:
  1. wiki_search_users(query="张三") → 获取 user_id=10
  2. wiki_get_my_permission(doc_id=645) → 确认自己有管理权限
  3. wiki_grant_permission(doc_id=645, user_id=10, permission="edit")
  4. 报告: "已将 /pages/645/ 的编辑权限授予 张三"

用户: "撤销李四对 /pages/645/ 的访问权限"
AI:
  1. wiki_search_users(query="李四") → user_id=12
  2. wiki_revoke_permission(doc_id=645, user_id=12)
  3. 报告: "已撤销李四对 /pages/645/ 的访问权限"
```

### 流程 7：查看和回复评论

**场景**：用户要查看文档评论或在文档上添加评论。

**步骤**：
1. 用 `wiki_get_comments` 获取文档评论列表
2. 如需添加评论，用 `wiki_add_comment(doc_id=..., content="...", parent_id=0)`
3. 如需回复某评论，设置 `parent_id` 为该评论的 ID
4. `content` 中可直接写 `@用户名` 来 @提及用户

**示例**：
```
用户: "在 /pages/645/ 下评论'写得很好，@张三 来看看'"
AI:
  wiki_add_comment(doc_id=645, content="写得很好，@张三 来看看")
```

### 流程 8：划词评论（行内评论）

**场景**：用户要对文档中某段特定文本添加标注式评论。

**步骤**：
1. 用 `wiki_get_document` 获取文档完整内容
2. 在文档内容中定位选中文本 `selected_text` 的字符位置（`start_offset`, `end_offset`）
3. 使用 `wiki_add_inline_comment(doc_id=..., content="...", selected_text="...", start_offset=..., end_offset=...)` 添加
4. 如需查看已有的划词评论，用 `wiki_get_inline_comments(doc_id=...)`

**示例**：
```
用户: "在 /pages/645/ 的 'AMS是Android系统核心服务' 这句话上加个注释：需要补充源码引用"
AI:
  1. wiki_get_document(doc_id=645)
  2. 在 content 中找到 "AMS是Android系统核心服务" 起始偏移 420，结束偏移 442
  3. wiki_add_inline_comment(doc_id=645, content="需要补充源码引用",
       selected_text="AMS是Android系统核心服务", start_offset=420, end_offset=442)
  4. 报告: "已在选中文本上添加划词评论"
```

### 流程 9：导出文档

**场景**：用户要将 Wiki 文档导出为本地文件。

**步骤**：
1. 确认导出格式（`md` / `pdf` / `html`）
2. 使用 `wiki_export_document(doc_id=..., format="pdf")` 导出
3. 如果是 md/html 格式，内容会直接返回文本
4. 如果是 pdf 格式，返回的是二进制数据（显示大小，供后续保存）

**示例**：
```
用户: "把 /pages/645/ 导出为 PDF"
AI:
  wiki_export_document(doc_id=645, format="pdf")
  → 返回 size_bytes=245000, note="Binary content (PDF)"
  报告: "已导出 /pages/645/ 为 PDF，文件大小约 245KB"
```

### 流程 10：查看版本历史和对比

**场景**：用户要查看文档的修改历史或对比某个历史版本。

**步骤**：
1. 用 `wiki_get_history(doc_id=...)` 获取版本列表
2. 找到感兴趣的 history_id
3. 用 `wiki_get_history_diff(doc_id=..., history_id=...)` 获取该版本具体内容
4. 对比分析变更内容

**示例**：
```
用户: "看看 /pages/645/ 最近谁改过"
AI:
  1. wiki_get_history(doc_id=645)
  2. 报告: "共有 5 个版本，最近由 Kerwin 在 2024-07-15 编辑"
```

### 流程 11：检查通知

**场景**：用户要查看系统通知和未读消息。

**步骤**：
1. 用 `wiki_get_unread_count()` 快速检查是否有未读
2. 如有未读，用 `wiki_get_notifications(page=1)` 查看详情
3. 如用户要求，用 `wiki_mark_notifications_read(ids="1,2,3")` 标记指定通知已读
4. 或 `wiki_mark_notifications_read(mark_all=True)` 全部标记已读

### 流程 12：从回收站恢复文档

**场景**：用户误删了文档想要恢复。

**步骤**：
1. 确认要恢复的文档 ID
2. 使用 `wiki_restore_document(doc_id=...)` 从回收站恢复
3. 验证文档是否恢复成功

## 文档命名规范

- 使用 `01.`, `02.` 等序号前缀保证排序
- 标题清晰表达文档主题
- 同一系列文档保持命名风格一致

## 安全注意事项

- ⚠️ **删除前必须确认**：`wiki_delete_document` 是不可逆操作（含所有子文档），执行前务必向用户确认
- ⚠️ **权限操作需谨慎**：`wiki_grant_permission` 和 `wiki_revoke_permission` 会直接影响文档访问控制
- 使用 `wiki_get_document` 验证目标文档存在再操作
- 批量操作时分批处理，避免一次性请求过大（建议每次不超过 50 个文档）
- 单次上传内容建议不超过 100KB
- 文档树递归深度不宜过深（建议 max_depth ≤ 5）
