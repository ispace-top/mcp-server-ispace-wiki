"""MCP Server for iSpace Wiki (爱思文档).

Full API coverage: document CRUD, move/sort, permissions, comments,
inline comments, @mentions, export, history, notifications, templates, tags.
"""

import os
import json
import logging
from typing import Optional

from dotenv import load_dotenv
from mcp.server import MCPServer

from .wiki_client import WikiClient

load_dotenv()

BASE_URL = os.getenv("ISPACE_WIKI_BASE_URL", "")
USERNAME = os.getenv("ISPACE_WIKI_USERNAME", "")
PASSWORD = os.getenv("ISPACE_WIKI_PASSWORD", "")
VERIFY_SSL = os.getenv("ISPACE_WIKI_VERIFY_SSL", "true").lower() != "false"

_logger = logging.getLogger("ispace-wiki-mcp")
_client: Optional[WikiClient] = None


def _wiki() -> WikiClient:
    global _client
    if _client is None:
        _client = WikiClient(base_url=BASE_URL, username=USERNAME,
                             password=PASSWORD, verify_ssl=VERIFY_SSL)
    return _client


app = MCPServer(
    name="ispace-wiki",
    title="iSpace Wiki (爱思文档)",
    description="MCP Server for iSpace Wiki — full document + comment + permission management.",
    version="1.1.0",
)


# ═══════════════════════════════════════════════════════════════
#  Document Read
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取指定文档的完整 Markdown 内容和元数据。")
async def wiki_get_document(doc_id: int) -> str:
    w = _wiki()
    d = w.get_page_data(doc_id)
    return json.dumps({
        "success": True, "id": d.get("id"), "name": d.get("name"),
        "content": d.get("content", d.get("meta_description", "")),
        "pre_content": d.get("pre_content", ""),
        "parent_id": d.get("parent_id"), "tags": d.get("tags", ""),
        "url": f"{w.base_url}/pages/{doc_id}/",
    }, ensure_ascii=False, indent=2)


@app.tool(description="列出指定文档的所有直接子文档。")
async def wiki_list_children(parent_id: int) -> str:
    r = _wiki().get_children(parent_id)
    return json.dumps({
        "success": r.get("status", False), "parent_id": parent_id,
        "total_children": r.get("total_children", 0),
        "children": r.get("direct_children", []),
    }, ensure_ascii=False, indent=2) if r.get("status") else json.dumps(
        {"success": False, "error": str(r.get("data", r))}, ensure_ascii=False)


@app.tool(description="递归获取文档树结构，适合构建知识库索引。")
async def wiki_get_document_tree(parent_id: int, max_depth: int = 5) -> str:
    r = _wiki().get_document_tree(parent_id, max_depth=max_depth)
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


@app.tool(description="全文搜索 Wiki 文档。")
async def wiki_search(query: str, page: int = 1, page_size: int = 10) -> str:
    r = _wiki().search(query, page=page, page_size=page_size)
    return json.dumps({
        "success": True, "query": query, "total": r.get("total", 0),
        "hits": r.get("hits", []), "page": r.get("page", 1),
        "took_ms": r.get("took_ms", 0),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Document Write
# ═══════════════════════════════════════════════════════════════

@app.tool(description="在指定父文档下创建新子文档。")
async def wiki_create_document(parent_id: int, name: str, content: str,
                                status: int = 1) -> str:
    r = _wiki().create_document(parent_id=parent_id, name=name,
                                 content=content, status=status)
    doc_id = r.get("data", {}).get("doc") if isinstance(r.get("data"), dict) else None
    return json.dumps({
        "success": r.get("status", False), "doc_id": doc_id,
        "message": r.get("data", ""),
        "url": f"{_wiki().base_url}/pages/{doc_id}/" if doc_id else None,
    }, ensure_ascii=False, indent=2)


@app.tool(description="更新文档标题、内容、状态或标签。只传要修改的字段。")
async def wiki_update_document(doc_id: int, name: str = None,
                                content: str = None, status: int = None,
                                tags: str = None) -> str:
    kwargs = {k: v for k, v in dict(name=name, content=content,
                                      status=status, tags=tags).items() if v is not None}
    r = _wiki().update_document(doc_id=doc_id, **kwargs)
    return json.dumps({
        "success": r.get("status", False), "message": r.get("data", ""),
        "doc_id": doc_id, "url": f"{_wiki().base_url}/pages/{doc_id}/",
    }, ensure_ascii=False, indent=2)


@app.tool(description="删除指定文档（不可逆，含子文档）。")
async def wiki_delete_document(doc_id: int) -> str:
    r = _wiki().delete_document(doc_id)
    return json.dumps({
        "success": r.get("status", False),
        "message": r.get("data", ""), "deleted_count": r.get("deleted", 0),
    }, ensure_ascii=False, indent=2)


@app.tool(description="从回收站恢复已删除的文档。")
async def wiki_restore_document(doc_id: int) -> str:
    r = _wiki().restore_document(doc_id)
    return json.dumps({
        "success": r.get("status", False), "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Move & Sort
# ═══════════════════════════════════════════════════════════════

@app.tool(description="移动文档到新的父文档下，或在同级中调整排序位置（拖拽排序）。")
async def wiki_move_document(doc_id: int, parent_id: int = 0,
                              position: int = 0) -> str:
    r = _wiki().move_document(doc_id=doc_id, parent_id=parent_id,
                               position=position)
    return json.dumps({
        "success": r.get("status", False), "doc_id": doc_id,
        "new_parent_id": parent_id, "new_position": position,
        "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Permissions
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取文档的权限列表。")
async def wiki_get_permissions(doc_id: int) -> str:
    r = _wiki().get_permissions(doc_id)
    return json.dumps({"success": True, "doc_id": doc_id, **r},
                      ensure_ascii=False, indent=2)


@app.tool(description="授予用户对文档的访问权限（view / edit / admin）。")
async def wiki_grant_permission(doc_id: int, user_id: int,
                                 permission: str = "view") -> str:
    r = _wiki().grant_permission(doc_id, user_id, permission)
    return json.dumps({
        "success": r.get("status", r.get("success", False)),
        "doc_id": doc_id, "user_id": user_id, "permission": permission,
        "message": r.get("data", r.get("message", "")),
    }, ensure_ascii=False, indent=2)


@app.tool(description="撤销用户对文档的访问权限。")
async def wiki_revoke_permission(doc_id: int, user_id: int) -> str:
    r = _wiki().revoke_permission(doc_id, user_id)
    return json.dumps({
        "success": r.get("status", r.get("success", False)),
        "doc_id": doc_id, "user_id": user_id,
        "message": r.get("data", r.get("message", "")),
    }, ensure_ascii=False, indent=2)


@app.tool(description="查看当前用户对某文档的权限。")
async def wiki_get_my_permission(doc_id: int) -> str:
    r = _wiki().get_my_permission(doc_id)
    return json.dumps({"success": True, "doc_id": doc_id, **r},
                      ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Comments
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取文档的评论列表（含回复）。")
async def wiki_get_comments(doc_id: int) -> str:
    r = _wiki().get_comments(doc_id)
    return json.dumps({"success": True, "doc_id": doc_id, **r},
                      ensure_ascii=False, indent=2)


@app.tool(description="在文档下添加评论，支持 @提及用户。parent_id > 0 表示回复某评论。")
async def wiki_add_comment(doc_id: int, content: str,
                            parent_id: int = 0) -> str:
    r = _wiki().add_comment(doc_id, content, parent_id)
    return json.dumps({
        "success": r.get("status", False), "doc_id": doc_id,
        "parent_id": parent_id, "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


@app.tool(description="删除某条评论。")
async def wiki_delete_comment(comment_id: int) -> str:
    r = _wiki().delete_comment(comment_id)
    return json.dumps({
        "success": r.get("status", False), "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Inline Comments (划词评论)
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取文档的划词评论（行内评论）列表。")
async def wiki_get_inline_comments(doc_id: int) -> str:
    r = _wiki().get_inline_comments(doc_id)
    return json.dumps({"success": True, "doc_id": doc_id, **r},
                      ensure_ascii=False, indent=2)


@app.tool(description="在文档选中文本上添加划词评论。需提供选中文本和字符偏移位置。")
async def wiki_add_inline_comment(doc_id: int, content: str,
                                   selected_text: str, start_offset: int,
                                   end_offset: int, anchor_hash: str = "") -> str:
    r = _wiki().add_inline_comment(doc_id, content, selected_text,
                                    start_offset, end_offset, anchor_hash)
    return json.dumps({
        "success": r.get("status", False), "doc_id": doc_id,
        "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


@app.tool(description="删除某条划词评论。")
async def wiki_delete_inline_comment(comment_id: int) -> str:
    r = _wiki().delete_inline_comment(comment_id)
    return json.dumps({
        "success": r.get("status", False), "message": r.get("data", ""),
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Export
# ═══════════════════════════════════════════════════════════════

@app.tool(description="导出文档为指定格式（md / pdf / html）。返回文件内容。")
async def wiki_export_document(doc_id: int, format: str = "md") -> str:
    w = _wiki()
    content = w.export_document(doc_id, fmt=format)
    # Return as text for md; for PDF, note it's binary
    try:
        text = content.decode("utf-8")
        return json.dumps({
            "success": True, "doc_id": doc_id, "format": format,
            "content": text,
        }, ensure_ascii=False, indent=2)
    except UnicodeDecodeError:
        return json.dumps({
            "success": True, "doc_id": doc_id, "format": format,
            "size_bytes": len(content),
            "note": "Binary content (PDF), cannot display as text. Saved to memory only.",
        }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  History
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取文档的历史版本列表。")
async def wiki_get_history(doc_id: int) -> str:
    r = _wiki().get_history(doc_id)
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


@app.tool(description="获取文档某个历史版本的内容（用于对比）。")
async def wiki_get_history_diff(doc_id: int, history_id: int) -> str:
    r = _wiki().get_history_diff(doc_id, history_id)
    return json.dumps({"success": r.get("status", False), "doc_id": doc_id,
                       "history_id": history_id, **r}, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Notifications
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取当前用户的通知列表。")
async def wiki_get_notifications(page: int = 1, page_size: int = 20) -> str:
    r = _wiki().get_notifications(page, page_size)
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


@app.tool(description="获取未读通知数量。")
async def wiki_get_unread_count() -> str:
    r = _wiki().get_unread_count()
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


@app.tool(description="标记通知为已读。传 ids 标记指定通知，传 mark_all=true 标记全部。")
async def wiki_mark_notifications_read(ids: str = "",
                                        mark_all: bool = False) -> str:
    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()] if ids else None
    r = _wiki().mark_notifications_read(id_list, mark_all)
    return json.dumps({"success": r.get("status", r.get("code") == 0),
                       "message": r.get("data", "")},
                      ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Templates & Tags
# ═══════════════════════════════════════════════════════════════

@app.tool(description="获取文档模板列表。")
async def wiki_list_templates() -> str:
    r = _wiki().list_templates()
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


@app.tool(description="获取文档标签列表，或按标签查看文档。")
async def wiki_list_tags() -> str:
    r = _wiki().list_tags()
    return json.dumps({"success": True, **r}, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Batch
# ═══════════════════════════════════════════════════════════════

@app.tool(description="批量创建多个子文档。每个元素需提供 name 和 content。")
async def wiki_batch_create(parent_id: int, documents: list[dict],
                             status: int = 1) -> str:
    results = _wiki().create_batch(parent_id, documents, status=status)
    ok = sum(1 for r in results if r["success"])
    return json.dumps({
        "success": True, "total": len(results),
        "success_count": ok, "failed_count": len(results) - ok,
        "results": results,
    }, ensure_ascii=False, indent=2)


@app.tool(description="批量删除多个文档。")
async def wiki_batch_delete(doc_ids: list[int]) -> str:
    w = _wiki(); results = []
    for did in doc_ids:
        r = w.delete_document(did)
        results.append({"doc_id": did, "success": r.get("status", False),
                        "message": r.get("data", "")})
    ok = sum(1 for r in results if r["success"])
    return json.dumps({
        "success": ok == len(doc_ids), "total": len(doc_ids),
        "deleted": ok, "failed": len(doc_ids) - ok, "results": results,
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  Misc
# ═══════════════════════════════════════════════════════════════

@app.tool(description="搜索 Wiki 用户，用于 @提及功能。")
async def wiki_search_users(query: str) -> str:
    r = _wiki().search_users(query)
    return json.dumps({"success": True, "query": query,
                       "users": r.get("results", [])},
                      ensure_ascii=False, indent=2)


@app.tool(description="创建文档分享链接。")
async def wiki_create_share_link(doc_id: int) -> str:
    r = _wiki().create_share_link(doc_id)
    return json.dumps({
        "success": r.get("status", False), "doc_id": doc_id,
        "share_hash": r.get("data", {}).get("doc") if isinstance(r.get("data"), dict) else None,
    }, ensure_ascii=False, indent=2)


@app.tool(description="获取当前登录用户信息。")
async def wiki_get_user_info() -> str:
    return json.dumps({"success": True, **_wiki().get_user_info()},
                      ensure_ascii=False, indent=2)


# ─── Entry Point ─────────────────────────────────────────────

def main():
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
