from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "outputs"


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def run_text(text: str, bold: bool = False, size: int = 22, color: str = "1D303C") -> str:
    bold_xml = '<a:b/>' if bold else ''
    return f'<a:r><a:rPr lang="en-US" sz="{size}">{bold_xml}<a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{esc(text)}</a:t></a:r>'


def paragraph(text: str, style: str | None = None, bold: bool = False) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    run_props = '<w:rPr><w:b/></w:rPr>' if bold else ''
    return f'<w:p>{style_xml}<w:r>{run_props}<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'


def table(rows: list[list[str]]) -> str:
    cells = []
    for row_index, row in enumerate(rows):
        row_cells = []
        for value in row:
            shading = '<w:shd w:fill="102C3A"/>' if row_index == 0 else ''
            color = '<w:color w:val="FFFFFF"/>' if row_index == 0 else ''
            row_cells.append(f'<w:tc><w:tcPr>{shading}</w:tcPr><w:p><w:r><w:rPr>{color}</w:rPr><w:t>{esc(value)}</w:t></w:r></w:p></w:tc>')
        cells.append(f'<w:tr>{"".join(row_cells)}</w:tr>')
    borders = '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="D8E3E5"/><w:left w:val="single" w:sz="4" w:color="D8E3E5"/><w:bottom w:val="single" w:sz="4" w:color="D8E3E5"/><w:right w:val="single" w:sz="4" w:color="D8E3E5"/><w:insideH w:val="single" w:sz="4" w:color="D8E3E5"/><w:insideV w:val="single" w:sz="4" w:color="D8E3E5"/></w:tblBorders>'
    return f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>{borders}</w:tblPr>{"".join(cells)}</w:tbl>'


def markdown_to_docx_blocks(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("```"):
            index += 1
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            level = min(len(heading.group(1)), 3)
            blocks.append(paragraph(heading.group(2), f"Heading{level}"))
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and "---" in lines[index + 1]:
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                values = [value.strip() for value in lines[index].strip().strip("|").split("|")]
                if not all(set(value) <= {"-", ":", " "} for value in values):
                    rows.append(values)
                index += 1
            blocks.append(table(rows))
            continue
        if line.startswith("- "):
            blocks.append(paragraph(line[2:], "ListBullet"))
            index += 1
            continue
        if re.match(r"^\d+\.\s+", line):
            blocks.append(paragraph(re.sub(r"^\d+\.\s+", "", line), "ListNumber"))
            index += 1
            continue
        blocks.append(paragraph(line))
        index += 1
    return blocks


def build_docx(report_path: Path, destination: Path) -> None:
    body = "".join(markdown_to_docx_blocks(report_path.read_text(encoding="utf-8")))
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900"/></w:sectPr></w:body></w:document>'''
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="20"/><w:color w:val="203542"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="0B6E69"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="102C3A"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="Heading 3"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="21"/><w:color w:val="40565F"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr></w:style><w:style w:type="paragraph" w:styleId="ListNumber"><w:name w:val="List Number"/><w:basedOn w:val="Normal"/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr></w:pPr></w:style></w:styles>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    document_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/_rels/document.xml.rels", document_rels)


def ppt_text_box(shape_id: int, x: int, y: int, width: int, height: int, text: str, size: int = 22, color: str = "EAF4F4", bold: bool = False) -> str:
    paragraphs = []
    for line in text.split("\n"):
        paragraphs.append(f'<a:p><a:pPr marL="0" algn="l"/><a:r>{run_text(line, bold=bold, size=size, color=color)}</a:r><a:endParaRPr lang="en-US" sz="{size}"/></a:p>')
    return f'''<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="07131D"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{"".join(paragraphs)}</p:txBody></p:sp>'''


def slide_xml(title: str, subtitle: str, bullets: list[str], slide_number: int) -> str:
    body = "\n".join(f"• {bullet}" for bullet in bullets)
    shapes = [
        ppt_text_box(2, 720000, 480000, 11200000, 850000, title, 3000, "41D7C3", True),
        ppt_text_box(3, 720000, 1300000, 11200000, 600000, subtitle, 1450, "8CA7B1"),
        ppt_text_box(4, 950000, 2300000, 10500000, 4300000, body, 2100, "EAF4F4"),
        ppt_text_box(5, 720000, 6900000, 11200000, 250000, f"SentinelOS NLP activity  ·  {slide_number}", 900, "5C7A85"),
    ]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def build_pptx(metrics: dict, destination: Path) -> None:
    result_lines = []
    for result in metrics["results"]:
        micro = result["entity"]["micro"]
        result_lines.append(f'{result["name"]}: Precision {micro["precision"]:.4f} · Recall {micro["recall"]:.4f} · F1 {micro["f1"]:.4f}')
    slides = [
        ("Privacy-Preserving Financial NER", "Named Entity Recognition for automated PCI/PII detection", ["NLP activity: concept, implementation, validation and presentation", "A separate project in the llm-aat repository", "Synthetic data only; raw sensitive values stay behind the scanner"]),
        ("The problem", "Financial text carries high-impact sensitive entities", ["Customer emails, support transcripts and payment logs may contain PII or cardholder data", "Blindly sending raw text to analytics or LLM systems creates a privacy boundary failure", "Goal: detect, classify, validate and redact before downstream processing"]),
        ("Why NER is the right topic", "A domain-specific application of a core syllabus technique", ["BIO tagging labels the beginning and continuation of each entity span", "Labels: PERSON, EMAIL, PHONE, CARD_NUMBER, ACCOUNT_NUMBER, TAX_ID, ADDRESS, TRANSACTION_ID and ORGANIZATION", "The output is useful for both redaction and audit evidence"]),
        ("System architecture", "A transparent hybrid pipeline", ["Tokenizer preserves character offsets and produces BIO labels", "Rules layer validates structured identifiers and applies a Luhn checksum to card-like values", "Averaged perceptron uses word shape, context, prefixes, suffixes and previous BIO labels", "Overlap resolver returns masked spans and a privacy note"]),
        ("Dataset and experiment", "Reproducible synthetic financial corpus", ["600 examples generated from payment, KYC, refund, billing and support templates", "70% train · 15% development · 15% test", "Seed: 42 · eight training epochs · exact character-span evaluation", "No real personal or payment data is used"]),
        ("Approach comparison", "Rules are precise; context-aware learning recovers language entities", result_lines),
        ("Example output", "The service protects downstream systems", ["Input: Maya Rao emailed maya.rao@example.com about card 4111 1111 1111 1111", "Output: [PERSON] emailed [EMAIL] about card [CARD_NUMBER]", "API: GET /health, GET /demo, POST /redact", "The response contains masked metadata, not raw values for an LLM"]),
        ("Conclusion", "A practical, privacy-first NER contribution", ["The hybrid architecture combines explicit validation with contextual language understanding", "The synthetic benchmark is a controlled classroom experiment, not a production guarantee", "Next: held-out templates, human annotation, transformer comparison, calibration and SentinelOS integration"]),
    ]
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>']
    content_types.extend(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(1, len(slides) + 1))
    content_types.append('</Types>')
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>'
    presentation_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    presentation_rels.extend(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>' for i in range(1, len(slides) + 1))
    presentation_rels.append('</Relationships>')
    slide_master = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles/></p:sldMaster>'
    slide_layout = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
    theme = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="SentinelOS"><a:themeElements><a:clrScheme name="Sentinel"><a:dk1><a:srgbClr val="07131D"/></a:dk1><a:lt1><a:srgbClr val="EAF4F4"/></a:lt1><a:dk2><a:srgbClr val="102C3A"/></a:dk2><a:lt2><a:srgbClr val="8CA7B1"/></a:lt2><a:accent1><a:srgbClr val="41D7C3"/></a:accent1><a:accent2><a:srgbClr val="A992FF"/></a:accent2><a:accent3><a:srgbClr val="FF7F78"/></a:accent3><a:accent4><a:srgbClr val="F3B56D"/></a:accent4><a:accent5><a:srgbClr val="75DF9C"/></a:accent5><a:accent6><a:srgbClr val="FFFFFF"/></a:accent6><a:hlink><a:srgbClr val="41D7C3"/></a:hlink><a:folHlink><a:srgbClr val="A992FF"/></a:folHlink></a:clrScheme><a:fontScheme name="Sentinel"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="Sentinel"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("ppt/presentation.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>{"".join(f"<p:sldId id=\"{256 + i}\" r:id=\"rId{i + 1}\"/>" for i in range(1, len(slides) + 1))}</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
        archive.writestr("ppt/_rels/presentation.xml.rels", "".join(presentation_rels))
        archive.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
        archive.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>')
        archive.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
        archive.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>')
        archive.writestr("ppt/theme/theme1.xml", theme)
        for index, (title, subtitle, bullets) in enumerate(slides, start=1):
            archive.writestr(f"ppt/slides/slide{index}.xml", slide_xml(title, subtitle, bullets, index))
            archive.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>')


def main() -> None:
    metrics_path = OUTPUT_DIR / "metrics.json"
    if not metrics_path.exists():
        raise SystemExit("Run `python -m src.cli pipeline --seed 42 --size 600` first.")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    report_path = REPORT_DIR / "technical_report.md"
    build_docx(report_path, REPORT_DIR / "Privacy_Preserving_Financial_NER_Report.docx")
    build_pptx(metrics, REPORT_DIR / "Privacy_Preserving_Financial_NER_Presentation.pptx")
    print("Generated DOCX report and PPTX presentation in reports/")


if __name__ == "__main__":
    main()
