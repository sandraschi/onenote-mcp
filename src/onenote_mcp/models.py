"""Pydantic models for OneNote MCP Server."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Notebook(BaseModel):
    """OneNote notebook model."""

    id: str
    displayName: str
    self: str
    sectionsUrl: str
    sectionGroupsUrl: str
    links: dict[str, Any] | None = None


class Section(BaseModel):
    """OneNote section model."""

    id: str
    displayName: str
    pagesUrl: str
    self: str
    parentNotebook: dict[str, Any] | None = None


class Page(BaseModel):
    """OneNote page model."""

    id: str
    title: str
    createdDateTime: str
    lastModifiedDateTime: str
    self: str
    contentUrl: str
    content: str | None = None


class TOCPage(BaseModel):
    """Page entry in table of contents."""

    title: str
    id: str
    created: str
    modified: str


class TOCSection(BaseModel):
    """Section entry in table of contents."""

    name: str
    pageCount: int
    pages: list[TOCPage]


class TOCData(BaseModel):
    """Table of contents data structure."""

    notebook: str
    stats: dict[str, int] = Field(default_factory=lambda: {"sections": 0, "pages": 0})
    sections: list[TOCSection] = Field(default_factory=list)



























