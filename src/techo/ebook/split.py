"""Split an omnibus EPUB at top-level NCX table-of-contents sections."""

from __future__ import annotations

import copy
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
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


@dataclass(frozen=True)
class EpubPackage:
    """The package structures needed while producing split EPUB files."""

    opf_name: str
    opf_dir: str
    ncx_name: str
    ncx_id: str
    opf_root: ET.Element
    ncx_root: ET.Element
    items: dict[str, ET.Element]
    spine_order: list[str]


def _read_package(archive: zipfile.ZipFile) -> EpubPackage:
    opf_name = _rootfile(archive)
    opf_dir = posixpath.dirname(opf_name)
    opf_root = ET.fromstring(archive.read(opf_name))
    spine = opf_root.find(f"{{{OPF}}}spine")
    manifest = opf_root.find(f"{{{OPF}}}manifest")
    if spine is None or manifest is None:
        raise ValueError("EPUB package is missing its manifest or spine")
    items = {item.get("id", ""): item for item in manifest.findall(f"{{{OPF}}}item")}
    ncx_id = spine.get("toc", "ncx")
    ncx_item = items.get(ncx_id)
    if ncx_item is None or not (ncx_href := ncx_item.get("href")):
        raise ValueError("Only EPUBs with an NCX table of contents can be split")
    ncx_name = posixpath.join(opf_dir, ncx_href)
    return EpubPackage(
        opf_name=opf_name,
        opf_dir=opf_dir,
        ncx_name=ncx_name,
        ncx_id=ncx_id,
        opf_root=opf_root,
        ncx_root=ET.fromstring(archive.read(ncx_name)),
        items=items,
        spine_order=[
            ref.get("idref", "") for ref in spine.findall(f"{{{OPF}}}itemref")
        ],
    )


def _title(nav_point: ET.Element) -> str:
    label = nav_point.find(f"{{{NCX}}}navLabel/{{{NCX}}}text")
    return label.text.strip() if label is not None and label.text else "untitled"


def _kept_ids(
    package: EpubPackage, nav_point: ET.Element
) -> tuple[set[str], set[str]] | None:
    href_to_id = {
        item.get("href", ""): item_id for item_id, item in package.items.items()
    }
    content_ids = {
        href_to_id[href] for href in _sources(nav_point) if href in href_to_id
    }
    positions = [
        index
        for index, item_id in enumerate(package.spine_order)
        if item_id in content_ids
    ]
    if not positions:
        return None
    spine_ids = set(package.spine_order[positions[0] : positions[-1] + 1])
    keep_ids = spine_ids | content_ids | {package.ncx_id}
    for item_id, item in package.items.items():
        media_type = item.get("media-type", "")
        if (
            media_type.startswith(("image/", "font/", "audio/", "video/"))
            or media_type == "text/css"
        ):
            keep_ids.add(item_id)
    return keep_ids, spine_ids


def _filtered_xml(
    package: EpubPackage,
    nav_point: ET.Element,
    title: str,
    keep_ids: set[str],
    spine_ids: set[str],
) -> tuple[ET.Element, ET.Element]:
    opf = copy.deepcopy(package.opf_root)
    manifest = opf.find(f"{{{OPF}}}manifest")
    spine = opf.find(f"{{{OPF}}}spine")
    if manifest is None or spine is None:
        raise ValueError("EPUB package changed while splitting")
    manifest[:] = [item for item in manifest if item.get("id") in keep_ids]
    spine[:] = [ref for ref in spine if ref.get("idref") in spine_ids]
    if (title_element := opf.find(f"{{{OPF}}}metadata/{{{DC}}}title")) is not None:
        title_element.text = title

    ncx = copy.deepcopy(package.ncx_root)
    nav_map = ncx.find(f"{{{NCX}}}navMap")
    if nav_map is None:
        raise ValueError("NCX has no navigation map")
    nav_map[:] = [copy.deepcopy(nav_point)]
    if (ncx_title := ncx.find(f"{{{NCX}}}docTitle/{{{NCX}}}text")) is not None:
        ncx_title.text = title
    return opf, ncx


def _write_epub(
    archive: zipfile.ZipFile,
    output: Path,
    package: EpubPackage,
    keep_ids: set[str],
    opf: ET.Element,
    ncx: ET.Element,
) -> None:
    kept_names = {
        posixpath.join(package.opf_dir, package.items[item_id].get("href", ""))
        for item_id in keep_ids
        if item_id in package.items
    }
    replacements = {package.opf_name: opf, package.ncx_name: ncx}
    with zipfile.ZipFile(output, "w") as target:
        target.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )
        for name in archive.namelist():
            if name == "mimetype":
                continue
            if name in replacements:
                target.writestr(
                    name,
                    ET.tostring(
                        replacements[name], encoding="utf-8", xml_declaration=True
                    ),
                )
            elif (
                package.opf_dir and not name.startswith(f"{package.opf_dir}/")
            ) or name in kept_names:
                target.writestr(name, archive.read(name))


def split_omnibus(epub_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Create one EPUB for every non-leaf top-level NCX entry."""
    source = Path(epub_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as archive:
        package = _read_package(archive)
        nav_map = package.ncx_root.find(f"{{{NCX}}}navMap")
        if nav_map is None:
            raise ValueError("NCX has no navigation map")
        written: list[Path] = []
        for nav_point in nav_map.findall(f"{{{NCX}}}navPoint"):
            if not nav_point.findall(f"{{{NCX}}}navPoint"):
                continue
            ids = _kept_ids(package, nav_point)
            if ids is None:
                continue
            keep_ids, spine_ids = ids
            title = _title(nav_point)
            opf, ncx = _filtered_xml(package, nav_point, title, keep_ids, spine_ids)
            output = destination / f"{_safe(title)}.epub"
            _write_epub(archive, output, package, keep_ids, opf, ncx)
            written.append(output)
    return written
