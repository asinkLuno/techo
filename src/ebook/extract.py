"""Extract EPUB table-of-contents entries as Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from ebooklib import epub
from markdownify import markdownify


@dataclass(frozen=True)
class TocEntry:
    title: str
    href: str
    parent: str | None = None


def _flatten(items: list, parent: str | None = None) -> list[TocEntry]:
    entries: list[TocEntry] = []
    for item in items:
        if isinstance(item, tuple):
            section, children = item
            entries.extend(_flatten(children, section.title))
        elif isinstance(item, epub.Link):
            entries.append(TocEntry(item.title, item.href, parent))
    return entries


_UNSAFE = re.compile(r"[^\w一-鿿\- .()（）]+")


def _safe_name(value: str) -> str:
    return re.sub(r"_{2,}", "_", _UNSAFE.sub("_", value).strip()).strip() or "untitled"


def _section_html(body: Tag, anchor: str | None, next_anchors: set[str]) -> str:
    if not anchor or (start := body.find(id=anchor)) is None:
        return str(body)

    root = start
    while isinstance(root.parent, Tag) and root.parent.name not in {
        "body",
        "[document]",
    }:
        candidate = root.parent
        if any(
            candidate.find(id=other) is not None for other in next_anchors - {anchor}
        ):
            break
        root = candidate

    parts: list[str] = []
    node = root
    while node is not None:
        if isinstance(node, Tag):
            if node is not root and any(
                node.find(id=other) is not None for other in next_anchors
            ):
                break
            parts.append(str(node))
        node = node.next_sibling
    return "\n".join(parts)


def epub_to_markdown(
    epub_path: str | Path,
    output_dir: str | Path,
    *,
    flat: bool = False,
) -> list[Path]:
    """Write one Markdown file per leaf entry in the EPUB TOC."""
    book = epub.read_epub(str(epub_path))
    entries = _flatten(book.toc)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    by_file: dict[str, list[TocEntry]] = {}
    for entry in entries:
        by_file.setdefault(entry.href.partition("#")[0], []).append(entry)

    markdown: dict[str, str] = {}
    for href, file_entries in by_file.items():
        item = book.get_item_with_href(href)
        if item is None:
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        body = soup.find("body")
        if not isinstance(body, Tag):
            continue
        anchors = {
            entry.href.partition("#")[2] for entry in file_entries if "#" in entry.href
        }
        for entry in file_entries:
            anchor = entry.href.partition("#")[2] or None
            html = _section_html(body, anchor, anchors)
            text = markdownify(html, heading_style="ATX", strip=["img"])
            markdown[entry.href] = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

    written: list[Path] = []
    counters: dict[str, int] = {}
    index = ["# Table of Contents", ""]
    for position, entry in enumerate(entries, 1):
        parent = _safe_name(entry.parent) if entry.parent else None
        if parent and not flat:
            folder = destination / parent
            folder.mkdir(exist_ok=True)
            counters[parent] = counters.get(parent, 0) + 1
            filename = f"{counters[parent]:02d}_{_safe_name(entry.title)}.md"
            path = folder / filename
        else:
            filename = f"{position:02d}_{_safe_name(entry.title)}.md"
            path = destination / filename
        path.write_text(
            markdown.get(entry.href, f"> Missing EPUB section: {entry.href}\n"),
            encoding="utf-8",
        )
        written.append(path)
        relative = path.relative_to(destination).as_posix()
        index.append(f"- [{entry.title}]({relative})")

    (destination / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return written
