# MCP Server for 爱思文档 (iSpace Wiki)

一个 MCP (Model Context Protocol) Server，让 AI 助手（如 Claude Code、Claude Desktop）能够直接操作 [爱思文档](https://your-wiki-server.com) 系统，进行文档的增删改查、批量操作、搜索等。

## 功能

| 工具 | 功能 | 说明 |
|------|------|------|
| `wiki_get_document` | 📖 获取文档 | 获取 Markdown 格式的完整内容 + 元数据 |
| `wiki_list_children` | 📂 列出子文档 | 获取指定文档的所有直接子文档 |
| `wiki_get_document_tree` | 🌳 获取文档树 | 递归获取多层级文档结构 |
| `wiki_create_document` | ✏️ 创建文档 | 在指定父文档下创建新子文档 |
| `wiki_update_document` | 🔄 更新文档 | 修改标题、内容、状态、标签 |
| `wiki_delete_document` | 🗑️ 删除文档 | 删除指定文档（含所有子文档） |
| `wiki_search` | 🔍 全文搜索 | 按关键词搜索文档 |
| `wiki_batch_create` | 📦 批量创建 | 一次性创建多个文档 |
| `wiki_add_comment` | 💬 添加评论 | 在文档下添加评论，支持 @提及 |
| `wiki_add_inline_comment` | 📝 划词评论 | 在选中文本上添加行内评论 |
| `wiki_delete_comment` | 🗑️ 删除评论 | 删除指定评论 |
| `wiki_search_users` | 🔎 搜索用户 | 搜索用户用于 @提及 |
| `wiki_batch_delete` | 📦 批量删除 | 一次性删除多个文档 |
| `wiki_create_share_link` | 🔗 分享链接 | 生成文档分享链接 |
| `wiki_get_user_info` | 👤 用户信息 | 查看当前登录用户 |

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

| API | 方法 | 路径 | 状态 |
|-----|------|------|------|
| 登录 | POST | `/login/` | ✅ |
| 获取文档 | GET+解析 | `/pages/{id}/` | ✅ |
| 创建文档 | POST | `/documents/create/` | ✅ |
| 更新文档 | POST | `/documents/{id}/edit/` | ✅ |
| 删除文档 | POST | `/documents/delete/` | ✅ |
| 子文档列表 | GET | `/documents/{id}/children/` | ✅ |
| 搜索 | GET | `/api/search/` | ✅ |
| 分享链接 | POST | `/shared-links/create/` | ✅ |
| 点赞 | POST | `/documents/{id}/like/` | ✅ |
| 添加评论 | POST | `/pages/0/{id}/comments/` | ✅ |
| 删除评论 | POST | `/comments/{id}/delete/` | ✅ |
| 搜索用户 | GET | `/api/users/search/` | ✅ |
| 通知列表 | GET | `/api/notifications/` | ✅ |
| 移动文档 | — | 待发现 | ❓ |
| 排序 | — | 待发现 | ❓ |
| 权限管理 | — | 待发现 | ❓ |

> **注**：移动、排序、权限等功能取决于 Wiki 系统本身是否提供对应的 API。如后续 Wiki 扩展这些接口，MCP Server 可同步更新。

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
├── .env.example                # 环境变量模板
├── .gitignore
└── src/
    └── ispace_wiki_mcp/
        ├── __init__.py         # 包入口
        ├── server.py           # MCP Server（工具定义 + 处理逻辑）
        ├── wiki_client.py      # HTTP 客户端（Session、CSRF、API 封装）
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
git tag v1.0.0
git push origin v1.0.0
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
