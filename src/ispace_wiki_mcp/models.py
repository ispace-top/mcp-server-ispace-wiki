"""Data models for iSpace Wiki MCP Server."""

from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class DocumentInfo:
    """A wiki document's metadata."""
    id: int
    name: str
    parent_id: Optional[int] = None
    content: Optional[str] = None
    pre_content: Optional[str] = None
    tags: Optional[str] = None


@dataclass
class DocumentChildren:
    """Children listing result."""
    total_children: int
    direct_children: list[dict]


@dataclass
class SearchResult:
    """Search result."""
    hits: list[dict]
    total: int
    took_ms: float
    page: int = 1
    page_size: int = 10
    total_pages: int = 1


@dataclass
class WikiResponse:
    """Generic wiki API response."""
    success: bool
    data: Any = None
    message: str = ""


@dataclass
class UserInfo:
    """Current user information."""
    username: str
    user_id: int
    is_authenticated: bool
