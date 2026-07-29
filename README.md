# MCP Server for 爱思文档 (iSpace Wiki)

让 AI 助手（Claude Code、Claude Desktop 等）能够直接操作 [爱思文档](https://github.com/ispace-top/ispace_doc) 系统。

## 功能概览

| 分类 | 能力 |
|------|------|
| 📖 文档读写 | 获取内容、列出子文档、递归文档树、创建、更新、删除、恢复 |
| 📦 移动排序 | 移动文档到新父级、拖拽调整同级排序 |
| 🔐 权限管理 | 查看/授予/撤销文档权限（view / edit / admin） |
| 💬 评论系统 | 普通评论（含 @提及）、划词评论（行内标注） |
| 📥 导出 | 导出文档为 Markdown / PDF / HTML |
| 📜 版本历史 | 查看修改历史、获取历史版本内容 |
| 🔔 通知 | 通知列表、未读计数、标记已读 |
| 📋 模板标签 | 文档模板管理、标签列表 |
| 🔍 搜索 | 全文搜索、用户搜索 |
| 🔗 共享 | 生成分享链接、查看用户信息 |
| 📦 批量操作 | 批量创建、批量删除 |

> **共 32 个工具**，覆盖文档管理的完整生命周期。

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

### 1. 环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
ISPACE_WIKI_BASE_URL=https://your-wiki-server.com
ISPACE_WIKI_USERNAME=your_username
ISPACE_WIKI_PASSWORD=your_password
ISPACE_WIKI_VERIFY_SSL=false   # 自签名证书时设为 false
```

> ⚠️ `.env` 已在 `.gitignore` 中排除，不会被提交到 Git。

### 2. Claude Code 配置

在 `settings.json` 中添加：

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

### 3. Claude Desktop 配置

编辑 `claude_desktop_config.json`，同上格式。

## 使用方式

配置完成后，在对话中用自然语言即可操作 Wiki。AI 会自动选择合适的工具。

### 结合 Skill 使用（推荐）

本项目附带 [SKILL.md](./SKILL.md) 文件，定义了 AI 操作 Wiki 的最佳实践和完整工作流程（共 12 个流程）。将 SKILL.md 导入到你的 AI 助手中，可获得更稳定、更规范的操作体验。

在 Claude Code 中，将 SKILL.md 放置在项目目录下即可自动识别。

### 典型对话示例

**创建文档**
> "在 /pages/645/ 下创建一个名为 '设计模式详解' 的文档"

**批量上传**
> "把 D:\docs\ 下所有 .md 文件批量创建到 /pages/500/ 下"

**知识库问答**
> "阅读 /pages/645/ 下的所有文档，基于这些内容回答我的问题"

**搜索**
> "在 Wiki 中搜索关于 Handler 的文档"

**移动排序**
> "把 /pages/700/ 移到 /pages/645/ 下面，放第三个位置"

**权限管理**
> "给 Kerwin 授予 /pages/645/ 的编辑权限"

**评论**
> "在 /pages/645/ 下评论：'这篇写得很好，@张三 来看看'"

**划词评论**
> "在 /pages/645/ 的 'AMS是Android核心服务' 这句话上加个注释"

**导出**
> "把 /pages/645/ 导出为 PDF"

**查看历史**
> "看看 /pages/645/ 的修改历史，谁改的"

**检查通知**
> "看看我有没有未读消息"

**恢复文档**
> "恢复刚才误删的文档 /pages/700/"

## 项目结构

```
mcp-server-ispace-wiki/
├── pyproject.toml              # 项目元数据和依赖
├── README.md                   # 本文档
├── SKILL.md                    # AI 工作流程指南（12 个流程，32 个工具详解）
├── .env.example                # 环境变量模板
├── .gitignore
└── src/
    └── ispace_wiki_mcp/
        ├── __init__.py
        ├── server.py           # MCP Server 入口
        ├── wiki_client.py      # HTTP 客户端
        └── models.py           # 数据模型
```

## 常见问题

### Q: 自签名 SSL 证书报错？

设置 `ISPACE_WIKI_VERIFY_SSL=false`。

### Q: 登录失败？

检查用户名密码是否正确，确认 Wiki 服务器可正常访问。

### Q: 密码会不会泄露给 AI？

不会。密码仅在 MCP Server 启动时从环境变量读取，用于建立 HTTP Session。AI 模型只能看到工具函数的输入输出，看不到环境变量。

### Q: 如何在多台机器上使用？

每台机器安装 `mcp-server-ispace-wiki` 并配置相同的环境变量即可，不需要共享 session。

## 开发

```bash
pip install -e ".[dev]"
pytest
python -m ispace_wiki_mcp.server   # 本地调试
```

## 发布

```bash
pip install build && python -m build    # 构建
pip install twine && twine upload dist/* # 发布到 PyPI
git tag v1.1.0 && git push origin v1.1.0  # 发布到 GitHub
```

## License

MIT
