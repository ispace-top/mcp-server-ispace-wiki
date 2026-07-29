# MCP Server for 爱思文档 (iSpace Wiki)

一个 MCP (Model Context Protocol) Server，让 AI 助手（如 Claude Code、Claude Desktop）能够直接操作 [爱思文档](https://github.com/ispace-top/ispace_doc) 系统，进行文档的增删改查、批量操作、搜索、权限管理、评论、导出、历史版本等全套操作。

## 功能

### 文档读写（8 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_get_document` | 📖 获取文档 | 获取 Markdown 格式的完整内容 + 元数据 |
| `wiki_list_children` | 📂 列出子文档 | 获取指定文档的所有直接子文档 |
| `wiki_get_document_tree` | 🌳 获取文档树 | 递归获取多层级文档结构 |
| `wiki_create_document` | ✏️ 创建文档 | 在指定父文档下创建新子文档 |
| `wiki_update_document` | 🔄 更新文档 | 修改标题、内容、状态、标签 |
| `wiki_delete_document` | 🗑️ 删除文档 | 删除指定文档（含所有子文档） |
| `wiki_restore_document` | ♻️ 恢复文档 | 从回收站恢复已删除的文档 |
| `wiki_move_document` | 📦 移动/排序 | 移动文档到新父级，或拖拽调整排序 |

### 搜索与用户（2 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_search` | 🔍 全文搜索 | 按关键词搜索文档 |
| `wiki_search_users` | 🔎 搜索用户 | 搜索用户用于 @提及 |

### 权限管理（4 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_get_permissions` | 🔐 查看权限 | 获取文档的权限列表 |
| `wiki_grant_permission` | 🔓 授予权限 | 授予用户 view/edit/admin 权限 |
| `wiki_revoke_permission` | 🔒 撤销权限 | 撤销用户对文档的访问权限 |
| `wiki_get_my_permission` | 👤 我的权限 | 查看当前用户对文档的权限 |

### 评论系统（6 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_get_comments` | 💬 查看评论 | 获取文档评论列表（含回复） |
| `wiki_add_comment` | ✍️ 添加评论 | 在文档下添加评论，支持 @提及 |
| `wiki_delete_comment` | ❌ 删除评论 | 删除指定评论 |
| `wiki_get_inline_comments` | 📝 划词评论列表 | 获取文档的划词评论（行内评论） |
| `wiki_add_inline_comment` | 🖊️ 添加划词评论 | 在选中文本上添加行内评论 |
| `wiki_delete_inline_comment` | ❌ 删除划词评论 | 删除指定划词评论 |

### 导出与历史（3 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_export_document` | 📥 导出文档 | 导出为 md / pdf / html 格式 |
| `wiki_get_history` | 📜 版本历史 | 获取文档的历史版本列表 |
| `wiki_get_history_diff` | 🔍 历史对比 | 获取历史版本的具体内容 |

### 通知（3 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_get_notifications` | 🔔 通知列表 | 获取当前用户的通知列表 |
| `wiki_get_unread_count` | 🔴 未读计数 | 获取未读通知数量 |
| `wiki_mark_notifications_read` | ✅ 标记已读 | 标记指定通知或全部为已读 |

### 模板与标签（2 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_list_templates` | 📋 模板列表 | 获取文档模板列表 |
| `wiki_list_tags` | 🏷️ 标签列表 | 获取文档标签列表 |

### 批量与共享（4 个）

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_batch_create` | 📦 批量创建 | 一次性创建多个文档 |
| `wiki_batch_delete` | 📦 批量删除 | 一次性删除多个文档 |
| `wiki_create_share_link` | 🔗 分享链接 | 生成文档分享链接 |
| `wiki_get_user_info` | 👤 用户信息 | 查看当前登录用户 |

> **共 32 个工具**，覆盖爱思文档系统的全部开放 API。

## 安装

### 前置要求

- Python >= 3.10
- pip

### 从 PyPI 安装（推荐）

```bash
pip install mcp-server-ispace-wiki
```

### 从源码安装

```bash
git clone https://github.com/KerwinJ/mcp-server-ispace-wiki.git
cd mcp-server-ispace-wiki
pip install -e .
```

## 配置

### 1. 创建环境变量文件

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Wiki 服务器的 URL
ISPACE_WIKI_BASE_URL=https://your-wiki-server.com

# 登录账号
ISPACE_WIKI_USERNAME=your_username
ISPACE_WIKI_PASSWORD=your_password

# 自签名 SSL 证书时设为 false
ISPACE_WIKI_VERIFY_SSL=false
```

> ⚠️ **安全提醒**：`.env` 文件包含密码，已在 `.gitignore` 中排除，不会被提交到 Git。

### 2. 在 Claude Code 中配置

在 Claude Code 的 `settings.json` 中添加：

```json
{
  "mcpServers": {
    "ispace-wiki": {
      "command": "python",
      "args": ["-m", "ispace_wiki_mcp.server"],
      "env": {
        "ISPACE_WIKI_BASE_URL": "https://your-wiki-server.com",
        "ISPACE_WIKI_USERNAME": "your_username",
        "ISPACE_WIKI_PASSWORD": "your_password",
        "ISPACE_WIKI_VERIFY_SSL": "false"
      }
    }
  }
}
```

### 3. 在 Claude Desktop 中配置

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "ispace-wiki": {
      "command": "python",
      "args": ["-m", "ispace_wiki_mcp.server"],
      "env": {
        "ISPACE_WIKI_BASE_URL": "https://your-wiki-server.com",
        "ISPACE_WIKI_USERNAME": "your_username",
        "ISPACE_WIKI_PASSWORD": "your_password",
        "ISPACE_WIKI_VERIFY_SSL": "false"
      }
    }
  }
}
```

## 使用示例

配置好后，AI 助手可以直接调用这些能力。以下是一些典型对话示例：

### 创建文档

> "在 /pages/645/ 下创建一个名为 '设计模式详解' 的 Markdown 文档"

AI 会自动调用 `wiki_create_document(parent_id=645, name="设计模式详解", content="...")`

### 批量创建

> "把 D:\docs\ 下所有 .md 文件作为子文档批量创建到 /pages/500/ 下"

AI 会先读取文件，然后调用 `wiki_batch_create(parent_id=500, documents=[...])`

### 获取文档内容作为知识库

> "阅读 /pages/645/ 下的所有文档，帮我基于这些内容回答问题"

AI 会先调用 `wiki_get_document_tree(parent_id=645)` 获取结构，再调用 `wiki_get_document(id=...)` 逐篇读取。

### 搜索

> "在 Wiki 中搜索关于 Handler 的所有文档"

AI 会调用 `wiki_search(query="Handler")`

### 移动文档 / 调整排序

> "把 /pages/700/ 移动到 /pages/645/ 下面，放在第三个位置"

AI 会调用 `wiki_move_document(doc_id=700, parent_id=645, position=3)`

### 权限管理

> "给用户 Kerwin 授予 /pages/645/ 的编辑权限"

AI 会先搜索用户获取 user_id，再调用 `wiki_grant_permission(doc_id=645, user_id=..., permission="edit")`

### 添加评论

> "在 /pages/645/ 下添加一条评论：'这篇写得太好了，@张三 你也来看看'"

AI 会调用 `wiki_add_comment(doc_id=645, content="这篇写得太好了，@张三 你也来看看")`

### 划词评论

> "在 /pages/645/ 的第三段 'AMS是Android系统核心服务' 这句上添加划词评论：'这里需要补充说明'"

AI 会先获取文档内容，定位选中文本的字符偏移，再调用 `wiki_add_inline_comment(...)`

### 导出文档

> "把 /pages/645/ 导出为 PDF"

AI 会调用 `wiki_export_document(doc_id=645, format="pdf")`

### 查看历史

> "查看 /pages/645/ 的修改历史"

AI 会调用 `wiki_get_history(doc_id=645)`，如需对比可调用 `wiki_get_history_diff(...)`

### 检查通知

> "看看我有没有未读消息"

AI 会调用 `wiki_get_unread_count()`，如有未读则调用 `wiki_get_notifications()`

## 技术架构

```
┌──────────────┐     MCP Protocol      ┌──────────────┐
│  AI 助手      │ ←──────────────────→ │  MCP Server  │
│ (Claude等)    │    stdio/JSON-RPC     │  (本服务)     │
└──────────────┘                       └──────┬───────┘
                                              │
                                    HTTP (requests)
                                              │
                                     ┌────────▼───────┐
                                     │  爱思文档 Wiki  │
                                     │  (Django 后端)  │
                                     └────────────────┘
```

- **传输协议**：MCP over stdio
- **HTTP 客户端**：Python `requests` 库，自动管理 Session 和 CSRF Token
- **认证**：Cookie-based session（通过 `/login/` 接口登录）
- **内容提取**：从页面 HTML 中提取 `window._docContent` 等内嵌数据

## API 覆盖情况

| 模块 | API | 方法 | 路径 | 状态 |
|------|-----|------|------|------|
| 认证 | 登录 | POST | `/login/` | ✅ |
| 文档 | 获取文档 | GET+解析 | `/pages/{id}/` | ✅ |
| 文档 | 创建文档 | POST | `/documents/create/` | ✅ |
| 文档 | 更新文档 | POST | `/documents/{id}/edit/` | ✅ |
| 文档 | 删除文档 | POST | `/documents/delete/` | ✅ |
| 文档 | 恢复文档 | POST | `/documents/restore/` | ✅ |
| 文档 | 子文档列表 | GET | `/documents/{id}/children/` | ✅ |
| 文档 | 文档树 | GET (递归) | `/documents/{id}/children/` | ✅ |
| 移动排序 | 移动/排序 | POST | `/documents/move/` | ✅ |
| 移动排序 | REST 移动 | POST | `/api/docs/{id}/move/` | ✅ |
| 搜索 | 全文搜索 | GET | `/api/search/` | ✅ |
| 搜索 | 用户搜索 | GET | `/api/users/search/` | ✅ |
| 权限 | 权限列表 | GET | `/api/docs/{id}/permissions/` | ✅ |
| 权限 | 授予权限 | POST | `/api/docs/{id}/permissions/grant/` | ✅ |
| 权限 | 撤销权限 | POST | `/api/docs/{id}/permissions/revoke/` | ✅ |
| 权限 | 我的权限 | GET | `/api/docs/{id}/permissions/mine/` | ✅ |
| 评论 | 评论列表 | GET | `/pages/{id}/comments/` | ✅ |
| 评论 | 添加评论 | POST | `/pages/{id}/comments/` | ✅ |
| 评论 | 删除评论 | POST | `/comments/{id}/delete/` | ✅ |
| 评论 | 划词评论列表 | GET | `/pages/{id}/inline-comments/` | ✅ |
| 评论 | 添加划词评论 | POST | `/pages/{id}/inline-comments/` | ✅ |
| 评论 | 删除划词评论 | POST | `/comments/inline/{id}/delete/` | ✅ |
| 导出 | 导出文档 | GET | `/documents/{id}/export/{fmt}/` | ✅ |
| 历史 | 版本历史 | GET | `/documents/{id}/history/` | ✅ |
| 历史 | 历史对比 | POST | `/documents/{id}/diff/{history_id}/` | ✅ |
| 通知 | 通知列表 | GET | `/api/notifications/` | ✅ |
| 通知 | 未读计数 | GET | `/api/notifications/unread-count/` | ✅ |
| 通知 | 标记已读 | POST | `/api/notifications/read/` | ✅ |
| 模板 | 模板列表 | GET | `/content-templates/manage/` | ✅ |
| 标签 | 标签列表 | GET | `/content-tags/manage/` | ✅ |
| 分享 | 分享链接 | POST | `/shared-links/create/` | ✅ |
| 用户 | 用户信息 | GET | `/my/` | ✅ |

> **共 32 个 API 端点，全部标记为 ✅**。所有 API 路径均来源于 [爱思文档源码](https://github.com/ispace-top/ispace_doc) 的 `urls.py` / `router.py` / `views.py` 分析。

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 本地调试

```bash
# 启动 MCP Server（stdio 模式）
python -m ispace_wiki_mcp.server
```

### 项目结构

```
mcp-server-ispace-wiki/
├── pyproject.toml              # 项目元数据和依赖
├── README.md                   # 本文档
├── SKILL.md                    # AI 工作流程指南
├── .env.example                # 环境变量模板
├── .gitignore
└── src/
    └── ispace_wiki_mcp/
        ├── __init__.py         # 包入口
        ├── server.py           # MCP Server（32 个工具定义 + 处理逻辑）
        ├── wiki_client.py      # HTTP 客户端（Session、CSRF、32 个 API 封装）
        └── models.py           # 数据模型
```

## 发布

### 构建分发包

```bash
pip install build
python -m build
```

### 发布到 PyPI

```bash
pip install twine
twine upload dist/*
```

### 发布到 GitHub

```bash
git tag v1.1.0
git push origin v1.1.0
```

## 常见问题

### Q: 自签名 SSL 证书报错？

在 `.env` 中设置 `ISPACE_WIKI_VERIFY_SSL=false`。

### Q: 登录失败？

检查用户名密码是否正确，确认 Wiki 服务器的 `/login/` 接口可正常访问。

### Q: 如何在多台机器上使用？

每台机器安装 `mcp-server-ispace-wiki` 并在 Claude Code / Claude Desktop 中配置相同的环境变量即可。不需要共享 session。

### Q: 密码会不会泄露给 AI？

不会。密码仅在 MCP Server 启动时从环境变量读取，用于建立与 Wiki 的 HTTP Session。AI 模型只能看到工具函数的输入输出（文档内容等），看不到环境变量和密码。

## License

MIT
