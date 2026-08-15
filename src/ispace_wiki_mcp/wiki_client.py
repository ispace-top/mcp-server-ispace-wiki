"""HTTP client for iSpace Wiki (爱思文档).

Handles session management, CSRF tokens, and all wiki API interactions.
Covers the complete API surface discovered from the open-source backend.
"""

import re
import json
import logging
from typing import Optional, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _extract_js_string(text: str, var: str) -> Optional[str]:
    """Extract a ``window.<var> = '...'`` value and decode JS/escapejs escapes.

    The wiki template embeds document data as single-quoted JS string literals
    (``window._docName = '...'``) using Django's ``escapejs`` filter, which
    encodes special characters as ``\\uXXXX``.  This helper matches either quote
    style and decodes those escapes back to plain text.
    """
    for quote in ("'", '"'):
        m = re.search(
            r"window\." + re.escape(var) + r"\s*=\s*"
            + quote + r"((?:[^" + quote + r"\\]|\\.)*)" + quote,
            text, re.S,
        )
        if m:
            raw = m.group(1)
            break
    else:
        return None

    # Django escapejs encodes these as \uXXXX; decode those first.
    raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda mm: chr(int(mm.group(1), 16)), raw)
    # Then decode common JS string escapes.
    raw = raw.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
    raw = raw.replace("\\/", "/").replace('\\"', '"').replace("\\'", "'").replace("\\\\", "\\")
    return raw


class WikiClient:
    """Low-level HTTP client for iSpace Wiki."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._csrf_token: Optional[str] = None
        self._is_authenticated = False

    # ─── Auth ─────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    def login(self) -> bool:
        if not self.username or not self.password:
            raise ValueError("username and password required")

        resp = self._session.get(f"{self.base_url}/login/", timeout=30)
        resp.raise_for_status()
        self._extract_csrf(resp.text)
        if not self._csrf_token:
            raise RuntimeError("Could not extract CSRF token")

        login_data = {
            "csrfmiddlewaretoken": self._csrf_token,
            "next": "/",
            "username": self.username,
            "password": self.password,
        }
        resp = self._session.post(
            f"{self.base_url}/login/?next=/",
            data=login_data,
            headers={"Referer": f"{self.base_url}/login/"},
            timeout=30,
            allow_redirects=True,
        )
        if resp.status_code == 200 and (self.username in resp.text or "退出" in resp.text):
            self._is_authenticated = True
            self._extract_csrf(resp.text)
            return True
        return False

    def ensure_authenticated(self):
        if not self._is_authenticated:
            self.login()
        if not self._is_authenticated:
            raise RuntimeError("Authentication failed")

    def _extract_csrf(self, html: str):
        m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
        if m:
            self._csrf_token = m.group(1)

    def _post_form(self, url: str, data: dict, *, timeout: int = 30) -> dict:
        """POST with FormData + CSRF, returning parsed JSON."""
        self.ensure_authenticated()
        data["csrfmiddlewaretoken"] = self._csrf_token or ""
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "Referer": self.base_url + "/",
        }
        resp = self._session.post(url, data=data, headers=headers, timeout=timeout)
        self._extract_csrf(resp.text)
        try:
            return resp.json()
        except Exception:
            return {"status": False, "data": resp.text[:500]}

    def _post_json(self, url: str, data: dict, *, timeout: int = 30) -> dict:
        """POST with JSON body + CSRF, returning parsed JSON."""
        self.ensure_authenticated()
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": self._csrf_token or "",
            "Accept": "application/json",
        }
        # Django also needs the CSRF cookie set
        self._session.headers.update({"X-CSRFToken": self._csrf_token or ""})
        resp = self._session.post(url, json=data, headers=headers, timeout=timeout)
        self._extract_csrf(resp.text)
        try:
            return resp.json()
        except Exception:
            return {"status": False, "data": resp.text[:500]}

    def _get_json(self, url: str, params: dict = None, *, timeout: int = 30) -> dict:
        """GET with JSON accept header."""
        self.ensure_authenticated()
        headers = {"Accept": "application/json"}
        resp = self._session.get(url, params=params, headers=headers, timeout=timeout)
        try:
            return resp.json()
        except Exception:
            return {"status": False, "data": resp.text[:500]}

    # ─── Page Data ────────────────────────────────────────────

    def get_page_data(self, doc_id: int) -> dict:
        """Get page HTML and extract embedded document data."""
        self.ensure_authenticated()
        url = f"{self.base_url}/pages/{doc_id}/"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return self._parse_page_data(resp.text, doc_id)

    def _parse_page_data(self, html: str, doc_id: int) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        data: dict = {"id": doc_id}

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            data["meta_description"] = meta_desc["content"]

        scripts = soup.find_all("script", src=False)
        extractors = {
            "_docContent": "content",
            "_docPreContent": "pre_content",
            "_docName": "name",
            "_docTags": "tags",
        }
        for script in scripts:
            text = script.string or ""
            for var, key in extractors.items():
                val = _extract_js_string(text, var)
                if val is not None:
                    data[key] = val

            for var in ("_docParentDoc", "_inlineParentDoc"):
                m = re.search(r"window\." + re.escape(var) + r"\s*=\s*(\d+)", text)
                if m:
                    data["parent_id"] = int(m.group(1))
                    break

        csrf_input = soup.find("input", attrs={"name": "csrfmiddlewaretoken"})
        if csrf_input:
            self._csrf_token = csrf_input.get("value")
            data["csrf_token"] = self._csrf_token

        return data

    # ═══════════════════════════════════════════════════════════
    #  Document CRUD
    # ═══════════════════════════════════════════════════════════

    def create_document(self, parent_id: int, name: str, content: str,
                        status: int = 1, editor_mode: int = 2) -> dict:
        return self._post_form(f"{self.base_url}/documents/create/", {
            "parent_doc": str(parent_id),
            "doc_name": name,
            "editor_mode": str(editor_mode),
            "content": content,
            "pre_content": content,
            "status": str(status),
            "open_children": "off",
            "show_children": "off",
        })

    def update_document(self, doc_id: int, name: str = None, content: str = None,
                        pre_content: str = None, status: int = None,
                        tags: str = None, parent_id: Optional[int] = None,
                        editor_mode: int = 2) -> dict:
        """Update document fields, preserving anything not explicitly provided.

        The edit endpoint overwrites content/pre_content with whatever is POSTed
        (empty string if omitted), so we must supply the current values when the
        caller only wants to change one field.  Markdown source (pre_content) is
        read back reliably via the export endpoint rather than scraping the page.
        """
        current = self.get_page_data(doc_id)
        final_name = name if name is not None else (current.get("name") or "")
        final_tags = tags if tags is not None else (current.get("tags") or "")

        if content is None or pre_content is None:
            try:
                md = self.export_document(doc_id, "md").decode("utf-8")
            except Exception:
                md = (current.get("pre_content") or current.get("content") or "")
        final_content = content if content is not None else md
        final_pre_content = pre_content if pre_content is not None else md

        # Empty parent_doc leaves the document in its current parent (the backend
        # keeps the existing value when the field is absent).  Sending 0 here would
        # silently move the document to the root level.
        parent_doc = str(parent_id) if parent_id is not None else ""

        payload = (
            f"doc_id={doc_id}"
            f"&doc_name={requests.utils.quote(final_name or '', safe='')}"
            f"&content={requests.utils.quote(final_content or '', safe='')}"
            f"&pre_content={requests.utils.quote(final_pre_content or '', safe='')}"
            f"&parent_doc={parent_doc}"
            f"&doc_tag={requests.utils.quote(final_tags or '', safe='')}"
            f"&status={status if status is not None else 1}"
            f"&editor_mode={editor_mode}"
            f"&csrfmiddlewaretoken={requests.utils.quote(self._csrf_token or '', safe='')}"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/pages/{doc_id}/",
        }
        resp = self._session.post(f"{self.base_url}/documents/{doc_id}/edit/",
                                  data=payload, headers=headers, timeout=30)
        self._extract_csrf(resp.text)
        try:
            return resp.json()
        except Exception:
            return {"status": False, "data": resp.text[:500]}

    def delete_document(self, doc_id: int) -> dict:
        return self._post_form(f"{self.base_url}/documents/delete/", {"doc_id": str(doc_id)})

    def restore_document(self, doc_id: int) -> dict:
        return self._post_form(f"{self.base_url}/documents/restore/", {"doc_id": str(doc_id)})

    def get_children(self, parent_id: int) -> dict:
        return self._get_json(f"{self.base_url}/documents/{parent_id}/children/")

    # ═══════════════════════════════════════════════════════════
    #  Move & Sort
    # ═══════════════════════════════════════════════════════════

    def move_document(self, doc_id: int, parent_id: int = 0,
                      position: int = 0, move_type: str = "1") -> dict:
        """Move/reorder a document.

        Args:
            doc_id: Document ID to move.
            parent_id: Target parent doc ID (0 = root level).
            position: Position index among siblings.
            move_type: '1' = move, '3' = drag reorder.

        Uses legacy form API (/documents/move/).
        """
        return self._post_form(f"{self.base_url}/documents/move/", {
            "doc_id": str(doc_id),
            "parent_id": str(parent_id),
            "move_type": move_type,
            "new_index": str(position),
            "new_parent_id": str(parent_id),
            "pro_id": "0",
        })

    def move_document_v2(self, doc_id: int, parent_id: int = 0,
                          position: int = 0) -> dict:
        """Move/reorder using the REST JSON API (/api/docs/{id}/move/)."""
        return self._post_json(f"{self.base_url}/api/docs/{doc_id}/move/", {
            "parent_id": parent_id,
            "position": position,
        })

    # ═══════════════════════════════════════════════════════════
    #  Permissions
    # ═══════════════════════════════════════════════════════════

    def get_permissions(self, doc_id: int) -> dict:
        return self._get_json(f"{self.base_url}/api/docs/{doc_id}/permissions/")

    def grant_permission(self, doc_id: int, user_id: int,
                         permission: str = "view") -> dict:
        """Grant document permission to a user.

        Args:
            doc_id: Document ID.
            user_id: Target user ID.
            permission: 'view', 'edit', or 'admin'.
        """
        return self._post_json(f"{self.base_url}/api/docs/{doc_id}/permissions/grant/", {
            "user_id": user_id,
            "permission": permission,
        })

    def revoke_permission(self, doc_id: int, user_id: int) -> dict:
        return self._post_json(f"{self.base_url}/api/docs/{doc_id}/permissions/revoke/", {
            "user_id": user_id,
        })

    def get_my_permission(self, doc_id: int) -> dict:
        return self._get_json(f"{self.base_url}/api/docs/{doc_id}/permissions/mine/")

    def get_batch_permissions(self, doc_ids: list[int]) -> dict:
        return self._get_json(f"{self.base_url}/api/docs/permissions/summary/",
                              {"doc_ids": ",".join(str(i) for i in doc_ids)})

    def set_doc_access_mode(self, doc_id: int, is_public: bool = True) -> dict:
        return self._post_json(f"{self.base_url}/api/docs/{doc_id}/access/", {
            "is_public": is_public,
        })

    # ═══════════════════════════════════════════════════════════
    #  Comments
    # ═══════════════════════════════════════════════════════════

    def get_comments(self, doc_id: int) -> dict:
        """GET /pages/{doc_id}/comments/ — list comments."""
        return self._get_json(f"{self.base_url}/pages/{doc_id}/comments/")

    def add_comment(self, doc_id: int, content: str,
                    parent_id: int = 0) -> dict:
        """POST /pages/{doc_id}/comments/ — add comment.

        @mentions are parsed from comment text by the backend."""
        return self._post_form(f"{self.base_url}/pages/{doc_id}/comments/", {
            "content": content,
            "parent_id": str(parent_id),
        })

    def delete_comment(self, comment_id: int) -> dict:
        return self._post_form(f"{self.base_url}/comments/{comment_id}/delete/", {})

    # Inline (word-level) comments

    def get_inline_comments(self, doc_id: int) -> dict:
        return self._get_json(f"{self.base_url}/pages/{doc_id}/inline-comments/")

    def add_inline_comment(self, doc_id: int, content: str,
                           selected_text: str, start_offset: int,
                           end_offset: int, anchor_hash: str = "") -> dict:
        return self._post_form(f"{self.base_url}/pages/{doc_id}/inline-comments/", {
            "content": content,
            "selected_text": selected_text,
            "start_offset": str(start_offset),
            "end_offset": str(end_offset),
            "anchor_hash": anchor_hash,
        })

    def delete_inline_comment(self, comment_id: int) -> dict:
        return self._post_form(f"{self.base_url}/comments/inline/{comment_id}/delete/", {})

    # ═══════════════════════════════════════════════════════════
    #  Export
    # ═══════════════════════════════════════════════════════════

    def export_document(self, doc_id: int, fmt: str = "md") -> bytes:
        """Export document in given format.

        Args:
            doc_id: Document ID.
            fmt: 'md', 'pdf', or 'html'.
        Returns:
            Raw bytes of the exported file.
        """
        self.ensure_authenticated()
        url = f"{self.base_url}/documents/{doc_id}/export/{fmt}/"
        resp = self._session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content

    # ═══════════════════════════════════════════════════════════
    #  Document History
    # ═══════════════════════════════════════════════════════════

    def get_history(self, doc_id: int) -> dict:
        """Get document version history list (HTML page, parsed)."""
        self.ensure_authenticated()
        url = f"{self.base_url}/documents/{doc_id}/history/"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        # Parse history from page
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for row in soup.select("tr[id^=history-]"):
            cells = row.find_all("td")
            if len(cells) >= 3:
                items.append({
                    "id": row.get("id", "").replace("history-", ""),
                    "time": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                    "action": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                    "user": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                })
        return {"status": True, "doc_id": doc_id, "history": items}

    def get_history_diff(self, doc_id: int, history_id: int) -> dict:
        """Get content of a specific historical version (JSON)."""
        self.ensure_authenticated()
        url = f"{self.base_url}/documents/{doc_id}/diff/{history_id}/"
        resp = self._session.post(url, data={
            "csrfmiddlewaretoken": self._csrf_token or "",
        }, headers={
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "Referer": f"{self.base_url}/pages/{doc_id}/",
        }, timeout=30)
        try:
            return resp.json()
        except Exception:
            return {"status": False, "data": resp.text[:500]}

    # ═══════════════════════════════════════════════════════════
    #  Notifications
    # ═══════════════════════════════════════════════════════════

    def get_notifications(self, page: int = 1, page_size: int = 20) -> dict:
        return self._get_json(f"{self.base_url}/api/notifications/",
                              {"page": page, "page_size": page_size})

    def get_unread_count(self) -> dict:
        return self._get_json(f"{self.base_url}/api/notifications/unread-count/")

    def mark_notifications_read(self, ids: list[int] = None,
                                 mark_all: bool = False) -> dict:
        """Mark notifications as read."""
        return self._post_form(f"{self.base_url}/api/notifications/read/", {
            "ids": ",".join(str(i) for i in ids) if ids else "",
            "mark_all": "1" if mark_all else "0",
        })

    def clear_all_notifications(self) -> dict:
        return self._post_form(f"{self.base_url}/api/notifications/clear-all/", {})

    # ═══════════════════════════════════════════════════════════
    #  Templates
    # ═══════════════════════════════════════════════════════════

    def list_templates(self) -> dict:
        return self._get_json(f"{self.base_url}/content-templates/manage/")

    def get_template(self, template_id: int) -> dict:
        return self._post_form(f"{self.base_url}/content-templates/get/", {
            "template_id": str(template_id),
        })

    def create_template(self, name: str, content: str) -> dict:
        return self._post_form(f"{self.base_url}/content-templates/create/", {
            "name": name,
            "content": content,
        })

    def delete_template(self, template_id: int) -> dict:
        return self._post_form(f"{self.base_url}/content-templates/delete/", {
            "template_id": str(template_id),
        })

    # ═══════════════════════════════════════════════════════════
    #  Search & Users
    # ═══════════════════════════════════════════════════════════

    def search(self, query: str, page: int = 1, page_size: int = 10) -> dict:
        return self._get_json(f"{self.base_url}/api/search/",
                              {"q": query, "page": page, "page_size": page_size})

    def search_users(self, query: str) -> dict:
        return self._get_json(f"{self.base_url}/api/users/search/", {"q": query})

    # ═══════════════════════════════════════════════════════════
    #  Tags
    # ═══════════════════════════════════════════════════════════

    def list_tags(self) -> dict:
        return self._get_json(f"{self.base_url}/content-tags/manage/")

    def get_docs_by_tag(self, tag_id: int, page: int = 1) -> dict:
        return self._get_json(f"{self.base_url}/content-tags/{tag_id}/documents/",
                              {"page": page})

    # ═══════════════════════════════════════════════════════════
    #  Share & Social
    # ═══════════════════════════════════════════════════════════

    def create_share_link(self, doc_id: int) -> dict:
        return self._post_form(f"{self.base_url}/shared-links/create/",
                               {"doc_id": str(doc_id)})

    def toggle_like(self, doc_id: int) -> dict:
        return self._post_form(f"{self.base_url}/documents/{doc_id}/like/", {})

    def toggle_bookmark(self, doc_id: int) -> dict:
        return self._post_form(f"{self.base_url}/my/bookmarks/toggle/",
                               {"doc_id": str(doc_id)})

    # ═══════════════════════════════════════════════════════════
    #  Tree & Batch
    # ═══════════════════════════════════════════════════════════

    def get_document_tree(self, parent_id: int, max_depth: int = 5) -> dict:
        def _fetch(pid: int, depth: int) -> list[dict]:
            if depth > max_depth:
                return []
            try:
                result = self.get_children(pid)
            except Exception:
                return []
            if not result.get("status", False):
                return []
            children = []
            for child in result.get("direct_children", []):
                children.append({
                    "id": child["id"], "name": child["name"],
                    "children": _fetch(child["id"], depth + 1),
                })
            return children
        children = _fetch(parent_id, 1)
        return {"parent_id": parent_id, "total_direct": len(children), "children": children}

    def create_batch(self, parent_id: int, documents: list[dict],
                     status: int = 1) -> list[dict]:
        results = []
        for doc in documents:
            r = self.create_document(parent_id, doc["name"], doc["content"], status=status)
            results.append({
                "name": doc["name"],
                "success": r.get("status", False),
                "doc_id": r.get("data", {}).get("doc") if isinstance(r.get("data"), dict) else None,
                "message": r.get("data", "") if not isinstance(r.get("data"), dict) else "",
            })
        return results

    # ═══════════════════════════════════════════════════════════
    #  User Info
    # ═══════════════════════════════════════════════════════════

    def get_user_info(self) -> dict:
        self.ensure_authenticated()
        resp = self._session.get(f"{self.base_url}/my/", timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        username_el = soup.find(attrs={"class": re.compile(r"ispace-user.*name")})
        return {
            "username": username_el.text.strip() if username_el else (self.username or "unknown"),
            "is_authenticated": True,
            "base_url": self.base_url,
        }

    def logout(self):
        self._session.get(f"{self.base_url}/logout/", timeout=10)
        self._is_authenticated = False
        self._csrf_token = None
