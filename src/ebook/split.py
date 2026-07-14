"""Split an omnibus EPUB at top-level NCX table-of-contents sections."""

from __future__ import annotations

import copy
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NCX = "http://www.daisy.org/z3986/2005/ncx/"
OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"
CONTAINER = "urn:oasis:names:tc:opendocument:xmlns:container"


def _safe(value: str) -> str:
    value = re.sub(r"[^\w一-鿿\- .()（）]+", "_", value).strip()
    return re.sub(r"_{2,}", "_", value) or "untitled"


def _sources(node: ET.Element) -> set[str]:
    result: set[str] = set()
    content = node.find(f"{{{NCX}}}content")
    if content is not None and (source := content.get("src")):
        result.add(source.partition("#")[0])
    for child in node.findall(f"{{{NCX}}}navPoint"):
        result.update(_sources(child))
    return result


def _rootfile(archive: zipfile.ZipFile) -> str:
    container = ET.fromstring(archive.read("META-INF/container.xml"))
    rootfile = container.find(f".//{{{CONTAINER}}}rootfile")
    if rootfile is None or not rootfile.get("full-path"):
        raise ValueError("EPUB container has no package rootfile")
    return rootfile.get("full-path", "")


def split_omnibus(epub_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Create one EPUB for every non-leaf top-level NCX entry."""
    source = Path(epub_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as archive:
        opf_name = _rootfile(archive)
        opf_dir = posixpath.dirname(opf_name)
        opf_root = ET.fromstring(archive.read(opf_name))
        spine = opf_root.find(f"{{{OPF}}}spine")
        manifest = opf_root.find(f"{{{OPF}}}manifest")
        if spine is None or manifest is None:
            raise ValueError("EPUB package is missing its manifest or spine")
        ncx_id = spine.get("toc", "ncx")
        items = {
            item.get("id", ""): item for item in manifest.findall(f"{{{OPF}}}item")
        }
        ncx_item = items.get(ncx_id)
        if ncx_item is None or not ncx_item.get("href"):
            raise ValueError("Only EPUBs with an NCX table of contents can be split")
        ncx_name = posixpath.join(opf_dir, ncx_item.get("href", ""))
        ncx_root = ET.fromstring(archive.read(ncx_name))
        nav_map = ncx_root.find(f"{{{NCX}}}navMap")
        if nav_map is None:
            raise ValueError("NCX has no navigation map")

        href_to_id = {item.get("href", ""): item_id for item_id, item in items.items()}
        spine_order = [
            ref.get("idref", "") for ref in spine.findall(f"{{{OPF}}}itemref")
        ]
        written: list[Path] = []
        for nav_point in nav_map.findall(f"{{{NCX}}}navPoint"):
            children = nav_point.findall(f"{{{NCX}}}navPoint")
            if not children:
                continue
            label = nav_point.find(f"{{{NCX}}}navLabel/{{{NCX}}}text")
            title = (
                label.text.strip() if label is not None and label.text else "untitled"
            )
            content_hrefs = _sources(nav_point)
            content_ids = {
                href_to_id[href] for href in content_hrefs if href in href_to_id
            }
            positions = [
                index
                for index, item_id in enumerate(spine_order)
                if item_id in content_ids
            ]
            if not positions:
                continue
            spine_ids = set(spine_order[positions[0] : positions[-1] + 1])

            keep_ids = spine_ids | content_ids | {ncx_id}
            for item_id, item in items.items():
                media_type = item.get("media-type", "")
                if (
                    media_type.startswith(("image/", "font/", "audio/", "video/"))
                    or media_type == "text/css"
                ):
                    keep_ids.add(item_id)

            new_opf = copy.deepcopy(opf_root)
            new_manifest = new_opf.find(f"{{{OPF}}}manifest")
            new_spine = new_opf.find(f"{{{OPF}}}spine")
            assert new_manifest is not None and new_spine is not None
            for item in list(new_manifest):
                if item.get("id") not in keep_ids:
                    new_manifest.remove(item)
            for reference in list(new_spine):
                if reference.get("idref") not in spine_ids:
                    new_spine.remove(reference)
            title_element = new_opf.find(f"{{{OPF}}}metadata/{{{DC}}}title")
            if title_element is not None:
                title_element.text = title

            new_ncx = copy.deepcopy(ncx_root)
            new_nav = new_ncx.find(f"{{{NCX}}}navMap")
            assert new_nav is not None
            for child in list(new_nav):
                new_nav.remove(child)
            new_nav.append(copy.deepcopy(nav_point))
            ncx_title = new_ncx.find(f"{{{NCX}}}docTitle/{{{NCX}}}text")
            if ncx_title is not None:
                ncx_title.text = title

            output = destination / f"{_safe(title)}.epub"
            kept_names = {
                posixpath.join(opf_dir, items[item_id].get("href", ""))
                for item_id in keep_ids
                if item_id in items
            }
            with zipfile.ZipFile(output, "w") as target:
                target.writestr(
                    "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
                )
                for name in archive.namelist():
                    if name == "mimetype":
                        continue
                    if name == opf_name:
                        target.writestr(
                            name,
                            ET.tostring(
                                new_opf, encoding="utf-8", xml_declaration=True
                            ),
                        )
                    elif name == ncx_name:
                        target.writestr(
                            name,
                            ET.tostring(
                                new_ncx, encoding="utf-8", xml_declaration=True
                            ),
                        )
                    elif (
                        opf_dir and not name.startswith(f"{opf_dir}/")
                    ) or name in kept_names:
                        target.writestr(name, archive.read(name))
            written.append(output)
    return written
