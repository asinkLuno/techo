import xml.etree.ElementTree as ET

from techo.ebook.split import NCX, EpubPackage, _kept_ids


def _nav_point(source: str, *children: ET.Element) -> ET.Element:
    point = ET.Element(f"{{{NCX}}}navPoint")
    ET.SubElement(point, f"{{{NCX}}}content", src=source)
    point.extend(children)
    return point


def _package() -> EpubPackage:
    items = {}
    for index in range(7):
        item_id = f"part{index}"
        items[item_id] = ET.Element("item", id=item_id, href=f"Text/part{index}.xhtml")
    items["ncx"] = ET.Element("item", id="ncx", href="toc.ncx")
    items["css"] = ET.Element(
        "item", id="css", href="Styles/book.css", attrib={"media-type": "text/css"}
    )
    return EpubPackage(
        opf_name="content.opf",
        opf_dir="",
        ncx_name="toc.ncx",
        ncx_id="ncx",
        opf_root=ET.Element("package"),
        ncx_root=ET.Element("ncx"),
        items=items,
        spine_order=[f"part{index}" for index in range(7)],
    )


def test_leaf_entry_uses_next_top_level_entry_as_spine_boundary() -> None:
    package = _package()
    current = _nav_point("Text/part1.xhtml")
    following = _nav_point("Text/part4.xhtml")

    keep_ids, spine_ids = _kept_ids(package, current, following) or (set(), set())

    assert spine_ids == {"part1", "part2", "part3"}
    assert {"part1", "part2", "part3", "ncx", "css"} <= keep_ids


def test_last_leaf_entry_keeps_rest_of_spine() -> None:
    package = _package()

    _, spine_ids = _kept_ids(package, _nav_point("Text/part4.xhtml")) or (set(), set())

    assert spine_ids == {"part4", "part5", "part6"}


def test_nested_entry_still_ends_at_last_descendant() -> None:
    package = _package()
    current = _nav_point(
        "Text/part1.xhtml",
        _nav_point("Text/part2.xhtml"),
        _nav_point("Text/part3.xhtml"),
    )

    _, spine_ids = _kept_ids(package, current, _nav_point("Text/part6.xhtml")) or (
        set(),
        set(),
    )

    assert spine_ids == {"part1", "part2", "part3"}
