from __future__ import annotations

import base64
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from PIL import Image

from app.models.notes import normalize_drill_notes, normalize_practice_notes


SLIDE_W = 12192000
SLIDE_H = 6858000
MARGIN = 520000
TITLE_Y = 330000
LINE_Y = 1120000
IMAGE_X = 560000
IMAGE_Y = 1320000
IMAGE_W = 6810000
IMAGE_H = 5080000
NOTES_X = 7640000
NOTES_Y = 1320000
NOTES_W = 3900000
NOTES_H = 5080000
FIGURE_ROLES = ("setter", "outside", "opposite", "middle", "libero", "coach")


@dataclass
class TextBox:
    text: str
    x: int
    y: int
    w: int
    h: int
    size: int = 1800
    bold: bool = False
    color: str = "16211F"
    align: str = "l"


@dataclass
class ImageBox:
    data: bytes
    x: int
    y: int
    w: int
    h: int


@dataclass
class SlideSpec:
    texts: list[TextBox]
    images: list[ImageBox]


def _safe_filename(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value or "export").strip("-").lower()
    return slug[:80] or "export"


def export_filename(name: str, prefix: str = "") -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    base = _safe_filename(name)
    stem = f"{_safe_filename(prefix)}-{base}" if prefix else base
    return f"{stem}-{date}.pptx"


def _decode_image(data_url: str) -> bytes:
    if not isinstance(data_url, str) or not data_url.startswith("data:image/png;base64,"):
        raise ValueError("Frame image must be a PNG data URL")
    return base64.b64decode(data_url.split(",", 1)[1], validate=True)


def _note_lines(title: str, value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(item.get("text", "")).strip() for item in value if isinstance(item, dict) and str(item.get("text", "")).strip()]
        return [title, *[f"- {item}" for item in items]] if items else []
    text = str(value or "").strip()
    return [title, text] if text else []


def _drill_note_text(drill: dict[str, Any]) -> str:
    metadata = drill.get("metadata", {})
    notes = normalize_drill_notes(drill.get("notes"), metadata)
    sections = [
        _note_lines("Description", notes["description"]),
        _note_lines("Coaching Points", notes["coachingPoints"]),
        _note_lines("General Comments", notes["generalComments"]),
        _note_lines("Equipment Notes", notes["equipmentNotes"]),
    ]
    return "\n\n".join("\n".join(lines) for lines in sections if lines)


def _practice_note_text(practice: dict[str, Any]) -> str:
    notes = normalize_practice_notes(practice.get("practiceNotes"), practice)
    fields = [
        ("Main Objective", notes["mainObjective"] or practice.get("main_objective", "")),
        ("Technical Objective", notes["technicalObjective"]),
        ("Tactical Objective", notes["tacticalObjective"]),
        ("Physical Objective", notes["physicalObjective"]),
        ("Intensity", notes["intensity"]),
        ("Important Notes", notes["importantNotes"]),
        ("General Comments", notes["generalComments"]),
    ]
    return "\n\n".join(f"{title}\n{value}" for title, value in fields if str(value or "").strip())


def _title_slide(title: str, subtitle: str = "") -> SlideSpec:
    texts = [
        TextBox(title, 720000, 1570000, 9900000, 860000, 4000, True),
        TextBox(subtitle or "Volleyball practice", 760000, 2500000, 7200000, 420000, 1800, False, "5B6965"),
        TextBox("", 760000, 3190000, 2800000, 90000, 900, False, "176B62"),
    ]
    return SlideSpec(texts, [])


def _overview_slide(practice: dict[str, Any], drill_exports: list[dict[str, Any]]) -> SlideSpec:
    total = 0
    for section in practice.get("sections") or []:
        for item in section.get("drills") or []:
            try:
                total += int(item.get("duration") or 0)
            except (TypeError, ValueError):
                pass
    summary = [f"Total planned time: {total} min" if total else "Total planned time: not set", f"Drills: {len(drill_exports)}"]
    if practice.get("main_objective"):
        summary.append(f"Main objective: {practice['main_objective']}")
    return SlideSpec(
        [
            TextBox("Practice Overview", MARGIN, TITLE_Y, 7700000, 570000, 2500, True),
            TextBox(str(practice.get("name") or "Practice Plan"), MARGIN, 820000, 7600000, 310000, 1100, False, "5B6965"),
            TextBox("\n\n".join(summary), 700000, 1450000, 4850000, 4480000, 2200),
            TextBox(_practice_note_text(practice) or "No practice notes added.", 6040000, 1450000, 5200000, 4480000, 1600),
        ],
        [],
    )


def _section_slide(name: str, index: int) -> SlideSpec:
    return SlideSpec(
        [
            TextBox(f"Section {index}", 720000, 2240000, 2200000, 420000, 1600, True, "176B62"),
            TextBox(name or f"Section {index}", 720000, 2760000, 9900000, 760000, 3600, True),
        ],
        [],
    )


def _drill_frame_slide(drill: dict[str, Any], frame: dict[str, Any], frame_no: int) -> SlideSpec:
    metadata = drill.get("metadata", {})
    name = str(metadata.get("name") or drill.get("name") or "Untitled drill")
    frame_name = str(frame.get("name") or f"Frame {frame_no}")
    return SlideSpec(
        [
            TextBox(name, MARGIN, TITLE_Y, 7900000, 560000, 2500, True),
            TextBox(frame_name, MARGIN, 820000, 7600000, 300000, 1100, False, "5B6965"),
            TextBox(_drill_note_text(drill) or "No notes added.", NOTES_X, NOTES_Y, NOTES_W, NOTES_H, 1500),
            TextBox(f"Frame {frame_no}", MARGIN, 6420000, 11000000, 250000, 1000, False, "5B6965", "r"),
        ],
        [ImageBox(_decode_image(frame["image"]), IMAGE_X, IMAGE_Y, IMAGE_W, IMAGE_H)],
    )


def _paragraphs(text: str, size: int, bold: bool, color: str, align: str) -> str:
    lines = str(text or "").splitlines() or [""]
    paragraphs = []
    for line in lines:
        paragraphs.append(
            f'<a:p><a:pPr algn="{align}"/><a:r><a:rPr lang="en-US" sz="{size}" b="{1 if bold else 0}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{escape(line)}</a:t></a:r></a:p>'
        )
    return "".join(paragraphs)


def _shape_xml(idx: int, box: TextBox) -> str:
    fill = ""
    if not box.text:
        fill = '<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'.format(
            x=box.x, y=box.y, w=box.w, h=box.h, color=box.color
        )
        body = "<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>"
    else:
        fill = f'<p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.w}" cy="{box.h}"/></a:xfrm><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        body = f'<p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>{_paragraphs(box.text, box.size, box.bold, box.color, box.align)}</p:txBody>'
    return f'<p:sp><p:nvSpPr><p:cNvPr id="{idx}" name="Text {idx}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>{fill}{body}</p:sp>'


def _picture_xml(idx: int, rel_id: str, image: ImageBox) -> str:
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{idx}" name="Export image"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{image.x}" y="{image.y}"/><a:ext cx="{image.w}" cy="{image.h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
    """


def _slide_xml(spec: SlideSpec) -> str:
    shapes = []
    next_id = 2
    for box in spec.texts:
        shapes.append(_shape_xml(next_id, box))
        next_id += 1
    for index, image in enumerate(spec.images, start=1):
        shapes.append(_picture_xml(next_id, f"rId{index}", image))
        next_id += 1
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFEFA"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {''.join(shapes)}
  </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def _slide_rels_xml(spec: SlideSpec, image_offset: int) -> str:
    rels = []
    for index, _image in enumerate(spec.images, start=1):
        rels.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{image_offset + index - 1}.png"/>'
        )
    rels.append(
        f'<Relationship Id="rId{len(spec.images) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def _content_types_xml(slide_count: int) -> str:
    slides = "".join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(1, slide_count + 1))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
{slides}</Types>"""


def _presentation_xml(slide_count: int) -> str:
    slide_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, slide_count + 1))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>"""


def _presentation_rels_xml(slide_count: int) -> str:
    rels = "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>' for i in range(1, slide_count + 1))
    rels += f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    rels += f'<Relationship Id="rId{slide_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>'


def _write_pptx(path: Path, slides: list[SlideSpec]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", _content_types_xml(len(slides)))
        pptx.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>""")
        pptx.writestr("ppt/presentation.xml", _presentation_xml(len(slides)))
        pptx.writestr("ppt/_rels/presentation.xml.rels", _presentation_rels_xml(len(slides)))
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>""")
        pptx.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
        pptx.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>""")
        pptx.writestr("ppt/theme/theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="VPD"><a:themeElements><a:clrScheme name="VPD"><a:dk1><a:srgbClr val="16211F"/></a:dk1><a:lt1><a:srgbClr val="FFFEFA"/></a:lt1><a:dk2><a:srgbClr val="5B6965"/></a:dk2><a:lt2><a:srgbClr val="FFFFFF"/></a:lt2><a:accent1><a:srgbClr val="176B62"/></a:accent1><a:accent2><a:srgbClr val="EF7D4D"/></a:accent2><a:accent3><a:srgbClr val="F2C85B"/></a:accent3><a:accent4><a:srgbClr val="2668A5"/></a:accent4><a:accent5><a:srgbClr val="4B685F"/></a:accent5><a:accent6><a:srgbClr val="DCDDD8"/></a:accent6><a:hlink><a:srgbClr val="176B62"/></a:hlink><a:folHlink><a:srgbClr val="176B62"/></a:folHlink></a:clrScheme><a:fontScheme name="VPD"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="VPD"><a:fillStyleLst><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="accent6"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""")
        pptx.writestr("docProps/core.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Volleyball Practice Designer Export</dc:title><dc:creator>Volleyball Practice Designer</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{datetime.now(UTC).isoformat()}</dcterms:created></cp:coreProperties>""")
        pptx.writestr("docProps/app.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Volleyball Practice Designer</Application><Slides>{len(slides)}</Slides></Properties>""")
        image_index = 1
        for slide_index, spec in enumerate(slides, start=1):
            pptx.writestr(f"ppt/slides/slide{slide_index}.xml", _slide_xml(spec))
            pptx.writestr(f"ppt/slides/_rels/slide{slide_index}.xml.rels", _slide_rels_xml(spec, image_index))
            for image in spec.images:
                pptx.writestr(f"ppt/media/image{image_index}.png", image.data)
                image_index += 1


def _asset_local_path(asset: dict[str, Any], static_root: Path, field: str = "master") -> Path:
    source = str(asset.get(field) or asset.get("asset") or "")
    return static_root / source.removeprefix("/static/")


def _png_name(asset: dict[str, Any]) -> str:
    team = f"team_{str(asset.get('team') or '').lower()}"
    view = str(asset.get("view") or asset.get("characterView") or "").replace("3/4", "three quarter")
    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        "_".join(str(part or "") for part in [asset.get("role"), asset.get("pose"), view, team]),
    ).strip("_").lower()
    return f"{slug[:80] or 'player_figure'}.png"


def _pptx_name(label: str) -> str:
    if label == "all":
        return "all_player_figures.pptx"
    if label == "selected_figures":
        return "selected_figures.pptx"
    return f"{_safe_filename(label)}.pptx"


def _role_label(role: str) -> str:
    return {
        "setter": "Setter",
        "outside": "Outside",
        "opposite": "Opposite",
        "middle": "Middle",
        "libero": "Libero",
        "coach": "Coach",
    }.get(role, role.replace("_", " ").title())


def _copy_asset_png(asset: dict[str, Any], static_root: Path, output_dir: Path, used_names: set[str]) -> Path:
    source = _asset_local_path(asset, static_root)
    if not source.is_file():
        raise ValueError(f"Missing player figure asset: {source}")
    name = _png_name(asset)
    if name in used_names:
        stem = Path(name).stem
        name = f"{stem}_{_safe_filename(str(asset.get('characterId') or asset.get('id')))}.png"
    counter = 2
    while name in used_names:
        name = f"{Path(name).stem}_{counter}.png"
        counter += 1
    used_names.add(name)
    output = output_dir / name
    with Image.open(source) as image:
        image.convert("RGBA").save(output, "PNG")
    return output


def _asset_png_bytes(asset: dict[str, Any], static_root: Path) -> bytes:
    source = _asset_local_path(asset, static_root)
    if not source.is_file():
        raise ValueError(f"Missing player figure asset: {source}")
    stream = BytesIO()
    with Image.open(source) as image:
        image.convert("RGBA").save(stream, "PNG")
    return stream.getvalue()


def _player_figure_slide(asset: dict[str, Any], png_data: bytes) -> SlideSpec:
    role = _role_label(str(asset.get("role") or "player"))
    pose = str(asset.get("pose") or "")
    view = str(asset.get("view") or asset.get("characterView") or "")
    character_id = str(asset.get("characterId") or "")
    team = str(asset.get("team") or "")
    uniform = str(asset.get("uniform") or team)
    filename = Path(str(asset.get("asset") or "")).name
    details = "\n".join(
        [
            f"Role: {role}",
            f"Pose: {pose}",
            f"View: {view}",
            f"Character ID: {character_id}",
            f"Team/uniform: {team} / {uniform}",
            f"Asset filename: {filename}",
        ]
    )
    return SlideSpec(
        [
            TextBox(f"{role} - {pose}", MARGIN, TITLE_Y, 7600000, 560000, 2500, True),
            TextBox(str(asset.get("id") or ""), MARGIN, 820000, 7600000, 300000, 1100, False, "5B6965"),
            TextBox(details, 1200000, 6100000, 9800000, 520000, 1300, False, "16211F", "ctr"),
        ],
        [ImageBox(png_data, 3300000, 1250000, 5600000, 4650000)],
    )


def _professional_player_assets(asset_registry, *, role: str | None = None, asset_ids: list[str] | None = None) -> list[dict[str, Any]]:
    selected_ids = set(asset_ids or [])
    source_assets = getattr(asset_registry, "library_assets", asset_registry.assets)
    assets = [
        item for item in source_assets
        if item.get("category") == "player"
        and item.get("visualStyle") == "professional"
        and item.get("role") in FIGURE_ROLES
    ]
    if role:
        role_key = role.lower().strip()
        if role_key not in FIGURE_ROLES:
            raise ValueError(f"Unsupported player figure role: {role}")
        assets = [item for item in assets if item.get("role") == role_key]
    if selected_ids:
        missing = selected_ids - {item["id"] for item in assets}
        if missing:
            raise ValueError(f"Invalid player figure asset id: {sorted(missing)[0]}")
        assets = [item for item in assets if item["id"] in selected_ids]
    assets.sort(key=lambda item: (FIGURE_ROLES.index(item["role"]), item.get("team", ""), item.get("characterId", ""), item.get("poseId", item.get("pose", "")), item["id"]))
    return assets


def _export_player_pngs(assets: list[dict[str, Any]], static_root: Path, png_dir: Path) -> list[str]:
    if not assets:
        raise ValueError("No player figures matched the export request")
    png_dir.mkdir(parents=True, exist_ok=True)
    png_paths: list[str] = []
    used_names: set[str] = set()
    for asset in assets:
        png_path = _copy_asset_png(asset, static_root, png_dir, used_names)
        png_paths.append(str(png_path))
    return png_paths


def _create_player_figure_deck(label: str, assets: list[dict[str, Any]], pack_dir: Path, static_root: Path, png_paths: list[str] | None = None) -> dict[str, Any]:
    if not assets:
        raise ValueError("No player figures matched the export request")
    slides = []
    if png_paths is None:
        for asset in assets:
            slides.append(_player_figure_slide(asset, _asset_png_bytes(asset, static_root)))
    else:
        for asset, png_path in zip(assets, png_paths):
            slides.append(_player_figure_slide(asset, Path(png_path).read_bytes()))
    pptx_path = pack_dir / _pptx_name(label)
    _write_pptx(pptx_path, slides)
    return {
        "path": str(pptx_path),
        "filename": pptx_path.name,
        "slideCount": len(slides),
        "pngPaths": png_paths,
    }


def create_player_figure_exports(asset_registry, export_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    pack_dir = export_dir / "player_figures"
    pack_dir.mkdir(parents=True, exist_ok=True)
    png_dir = pack_dir / "png"
    static_root = asset_registry.manifest_path.parents[1]
    mode = str(payload.get("mode") or "all")
    requested_format = str(payload.get("format") or "pptx")
    if requested_format not in {"pptx", "png", "both"}:
        raise ValueError(f"Unsupported player figure export format: {requested_format}")

    def build_response(label: str, assets: list[dict[str, Any]]) -> dict[str, Any]:
        png_paths = _export_player_pngs(assets, static_root, png_dir) if requested_format in {"png", "both"} else []
        decks = []
        if requested_format in {"pptx", "both"}:
            decks.append(_create_player_figure_deck(label, assets, pack_dir, static_root, png_paths or None))
        return {"mode": mode, "format": requested_format, "folder": str(pack_dir), "decks": decks, "pngPaths": png_paths}

    if mode == "all":
        assets = _professional_player_assets(asset_registry)
        return build_response("all", assets)
    if mode == "role":
        role = payload.get("role")
        assets = _professional_player_assets(asset_registry, role=str(role or ""))
        return build_response(str(role), assets)
    if mode == "selected":
        if not payload.get("assetIds"):
            raise ValueError("Select at least one player figure to export")
        assets = _professional_player_assets(asset_registry, asset_ids=list(payload.get("assetIds") or []))
        return build_response("selected_figures", assets)
    raise ValueError(f"Unsupported player figure export mode: {mode}")


def create_drill_pptx(drill: dict[str, Any], frames: list[dict[str, Any]], export_dir: Path, *, filename_prefix: str = "drill") -> Path:
    if not frames:
        raise ValueError("At least one frame image is required")
    export_dir.mkdir(parents=True, exist_ok=True)
    slides = [_drill_frame_slide(drill, frame, index) for index, frame in enumerate(frames, start=1)]
    path = export_dir / export_filename(str(drill.get("metadata", {}).get("name") or "drill"), filename_prefix)
    _write_pptx(path, slides)
    return path


def create_practice_pptx(practice: dict[str, Any], drill_exports: list[dict[str, Any]], export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    slides = [_title_slide(str(practice.get("name") or "Practice Plan"), " / ".join(str(x) for x in [practice.get("date"), practice.get("team")] if x)), _overview_slide(practice, drill_exports)]
    sections = practice.get("sections") or []
    if sections:
        for index, section in enumerate(sections, start=1):
            slides.append(_section_slide(str(section.get("name") or f"Section {index}"), index))
            section_drill_ids = [item.get("drill_id") for item in section.get("drills") or []]
            for drill_export in drill_exports:
                drill_id = drill_export.get("drill", {}).get("id")
                if section_drill_ids and drill_id not in section_drill_ids:
                    continue
                slides.extend(_drill_frame_slide(drill_export["drill"], frame, frame_index) for frame_index, frame in enumerate(drill_export.get("frames") or [], start=1))
    else:
        for drill_export in drill_exports:
            slides.extend(_drill_frame_slide(drill_export["drill"], frame, frame_index) for frame_index, frame in enumerate(drill_export.get("frames") or [], start=1))
    path = export_dir / export_filename(str(practice.get("name") or "practice"), "practice")
    _write_pptx(path, slides)
    return path
