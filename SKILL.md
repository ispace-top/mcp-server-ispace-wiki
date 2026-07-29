# Skill: 爱思文档 Wiki 操作

此 Skill 定义了使用 AI 操作 爱思文档 Wiki 的最佳实践和工作流程。

## 触发条件

当用户要求以下操作时自动应用本 Skill：
- 在 Wiki 上创建、更新、删除文档
- 批量上传内容到 Wiki
- 从 Wiki 读取文档作为知识库
- 搜索 Wiki 内容
- 管理 Wiki 文档结构

## 工具清单

使用 MCP Server `ispace-wiki` 提供的工具：

| 工具 | 用途 |
|------|------|
| `wiki_get_document` | 获取单个文档的完整内容 |
| `wiki_list_children` | 列出子文档 |
| `wiki_get_document_tree` | 递归获取文档树 |
| `wiki_create_document` | 创建新文档 |
| `wiki_update_document` | 修改现有文档 |
| `wiki_delete_document` | 删除文档 |
| `wiki_search` | 全文搜索 |
| `wiki_batch_create` | 批量创建文档 |
| `wiki_create_share_link` | 生成分享链接 |
| `wiki_get_user_info` | 获取用户信息 |

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

## 文档命名规范

- 使用 `01.`, `02.` 等序号前缀保证排序
- 标题清晰表达文档主题
- 同一系列文档保持命名风格一致

## 安全注意事项

- 删除前必须确认，不可逆操作
- 使用 `wiki_get_document` 验证目标文档存在再操作
- 批量操作时分批处理，避免一次性请求过大

## 已知限制

- 移动/排序/权限管理功能暂不支持（Wiki 侧无对应 API）
- 单次上传内容建议不超过 100KB（避免 Binder 类似的内存限制）
- 文档树递归深度不宜过深（建议 max_depth ≤ 5）
