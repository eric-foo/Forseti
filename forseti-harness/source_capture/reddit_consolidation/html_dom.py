from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable


_TEXT_BREAK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header",
    "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table", "td", "th",
    "tr", "ul",
}


@dataclass
class HtmlNode:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    # One ordered stream: separate text/child lists lose every inline boundary.
    content: list["HtmlNode | str"] = field(default_factory=list)
    parent: "HtmlNode | None" = None

    @property
    def children(self) -> list["HtmlNode"]:
        return [part for part in self.content if isinstance(part, HtmlNode)]

    @property
    def text_parts(self) -> list[str]:
        return [part for part in self.content if isinstance(part, str)]

    def classes(self) -> set[str]:
        return {item for item in self.attrs.get("class", "").split() if item}

    def has_class(self, class_name: str) -> bool:
        return class_name in self.classes()

    def text_content(self, *, preserve_blockquotes: bool = False) -> str:
        parts: list[str] = []
        self._collect_text(parts, preserve_blockquotes=preserve_blockquotes)
        return " ".join("".join(parts).split())

    def descendants(self) -> Iterable["HtmlNode"]:
        for child in self.children:
            yield child
            yield from child.descendants()

    def first_descendant(self, *, tag: str | None = None, class_name: str | None = None) -> "HtmlNode | None":
        for node in self.descendants():
            if tag is not None and node.tag != tag:
                continue
            if class_name is not None and not node.has_class(class_name):
                continue
            return node
        return None

    def _collect_text(self, parts: list[str], *, preserve_blockquotes: bool) -> bool:
        start = len(parts)
        quoted = preserve_blockquotes and self.tag == "blockquote"
        if quoted:
            parts.append(" <blockquote> ")
        elif self.tag in _TEXT_BREAK_TAGS:
            parts.append(" ")
        has_text = False
        for part in self.content:
            if isinstance(part, str):
                parts.append(part)
                has_text = bool(part.strip()) or has_text
            else:
                has_text = part._collect_text(
                    parts, preserve_blockquotes=preserve_blockquotes
                ) or has_text
        if quoted:
            if has_text:
                parts.append(" </blockquote> ")
            else:
                del parts[start:]  # Empty markup must not become customer text.
        elif self.tag in _TEXT_BREAK_TAGS:
            parts.append(" ")
        return has_text


class _DomBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = HtmlNode(tag="document")
        self._stack: list[HtmlNode] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = HtmlNode(
            tag=tag.lower(),
            attrs={key.lower(): value or "" for key, value in attrs},
            parent=self._stack[-1],
        )
        self._stack[-1].content.append(node)
        if tag.lower() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param"}:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == normalized:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self._stack[-1].content.append(data)


def parse_html_document(html: str) -> HtmlNode:
    builder = _DomBuilder()
    builder.feed(html)
    builder.close()
    return builder.root
