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


def cover_paragraph(text: str, size: int = 22, color: str = "203542", bold: bool = False, align: str = "center", italic: bool = False) -> str:
    bold_xml = '<w:b/>' if bold else ''
    italic_xml = '<w:i/>' if italic else ''
    return f'<w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:after="140"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="{size}"/><w:color w:val="{color}"/>{bold_xml}{italic_xml}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def cover_table(rows: list[tuple[str, str]]) -> str:
    rendered = []
    for left, right in rows:
        rendered.append(
            f'<w:tr><w:tc><w:tcPr><w:tcW w:w="4700" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{esc(left)}</w:t></w:r></w:p></w:tc>'
            f'<w:tc><w:tcPr><w:tcW w:w="4700" w:type="dxa"/></w:tcPr><w:p><w:r><w:t>{esc(right)}</w:t></w:r></w:p></w:tc></w:tr>'
        )
    borders = '<w:tblBorders><w:top w:val="single" w:sz="8" w:color="203542"/><w:left w:val="single" w:sz="8" w:color="203542"/><w:bottom w:val="single" w:sz="8" w:color="203542"/><w:right w:val="single" w:sz="8" w:color="203542"/><w:insideH w:val="single" w:sz="8" w:color="203542"/><w:insideV w:val="single" w:sz="8" w:color="203542"/></w:tblBorders>'
    return f'<w:tbl><w:tblPr><w:tblW w:w="9400" w:type="dxa"/>{borders}</w:tblPr>{"".join(rendered)}</w:tbl>'


def report_cover() -> str:
    return "".join([
        cover_paragraph("B. M. S. COLLEGE OF ENGINEERING", 30, "6B3E25", True),
        cover_paragraph("Autonomous Institute, Affiliated to VTU, Belagavi", 20, "6B3E25", False, italic=True),
        cover_paragraph("DEPARTMENT OF MACHINE LEARNING", 27, "6B3E25", True),
        cover_paragraph("Program: B.E. In Artificial Intelligence and Machine Learning", 21, "203542", False),
        cover_paragraph("Academic Year: 2026 - 27, Session: July 2026 - Dec 2026", 18, "203542", True),
        cover_paragraph("NATURAL LANGUAGE PROCESSING FOR LLM", 25, "0000CC", True),
        cover_paragraph("(24AM7PCLLM)", 22, "0000CC", True),
        cover_paragraph("Alternative Assessment Tool (AAT) Report", 21, "203542", True),
        cover_paragraph("Topic:", 21, "A52A74", True),
        cover_paragraph("Privacy-Preserving Named Entity Recognition for Automated PCI/PII Detection in Financial Text", 20, "0000CC", True),
        cover_paragraph("Submitted by", 22, "203542", True),
        cover_table([
            ("Student Name / Team Member 1", "____________________________"),
            ("Team Member 2", "____________________________"),
            ("USN – Team Member 1", "____________________________"),
            ("USN – Team Member 2", "____________________________"),
            ("Semester & Section", "7C"),
        ]),
        cover_paragraph("Valuation Report", 21, "0000CC", True),
        cover_paragraph("(to be filled by faculty)", 16, "203542", False, italic=True),
        cover_table([
            ("Score", "____________________________"),
            ("Comments", "____________________________"),
            ("Faculty In-charge", "Upeksha Prasad G"),
            ("Faculty Signature with date", "____________________________"),
        ]),
    ])


def report_toc() -> str:
    entries = [
        ("1. Introduction", True),
        ("1.1 Background of Natural Language Processing", False),
        ("1.2 Importance of the Selected NLP Topic", False),
        ("1.3 Objective of the Study", False),
        ("1.4 Scope of the Report", False),
        ("2. Selected NLP Topic Overview", True),
        ("2.1 Description of the NLP Task", False),
        ("2.2 Real-World Use Cases", False),
        ("2.3 Relevance to the Syllabus and Industry", False),
        ("2.4 Key Challenges in This NLP Task", False),
        ("3. Real-Time Application / API Identified", True),
        ("3.1 Application or API Name", False),
        ("3.2 Purpose and Functionality", False),
        ("3.3 Architecture or Platform", False),
        ("3.4 Input/Output Behavior", False),
        ("3.5 Limitations and Practical Considerations", False),
        ("4. NLP Model / Architecture Study", True),
        ("4.1 Theoretical Foundations", False),
        ("4.2 Algorithms Used", False),
        ("4.3 Architecture Diagram / Layer-Wise Design", False),
        ("4.4 Data Flow in the Model", False),
        ("4.5 Mathematical Formulation", False),
        ("4.6 Why This Model Suits the Task", False),
        ("5. Dataset and Preprocessing", True),
        ("6. Implementation Methodology", True),
        ("7. Results and Evaluation", True),
        ("8. Discussion", True),
        ("9. Conclusion", True),
        ("10. References", True),
    ]
    output = [cover_paragraph("Table of Contents", 30, "203542", True)]
    for text, major in entries:
        output.append(cover_paragraph(text, 18 if major else 15, "203542", major, "left"))
    return "".join(output)


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
    body = report_cover() + page_break() + report_toc() + page_break() + "".join(markdown_to_docx_blocks(report_path.read_text(encoding="utf-8")))
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


def ppt_text_box(shape_id: int, x: int, y: int, width: int, height: int, text: str, size: int = 22, color: str = "1A1A1A", bold: bool = False, fill: str | None = "FFFFFF") -> str:
    paragraphs = []
    for line in text.split("\n"):
        paragraphs.append(f'<a:p><a:pPr marL="0" algn="l"/><a:r>{run_text(line, bold=bold, size=size, color=color)}</a:r><a:endParaRPr lang="en-US" sz="{size}"/></a:p>')
    fill_xml = '<a:noFill/>' if fill is None else f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
    return f'''<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{"".join(paragraphs)}</p:txBody></p:sp>'''


def slide_xml(title: str, subtitle: str, bullets: list[str], slide_number: int) -> str:
    body = "\n".join(f"• {bullet}" for bullet in bullets)
    shapes = [
        ppt_text_box(2, 720000, 420000, 11200000, 850000, title, 3000, "0000CC", True),
        ppt_text_box(3, 720000, 1250000, 11200000, 600000, subtitle, 1450, "6B3E25", False),
        ppt_text_box(4, 950000, 2200000, 10500000, 4300000, body, 2100, "1A1A1A"),
        ppt_text_box(5, 720000, 6900000, 11200000, 250000, f"Natural Language Processing for LLM · 24AM7PCLLM · {slide_number}", 900, "6B3E25"),
    ]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def cover_slide_xml() -> str:
    shapes = [
        ppt_text_box(2, 500000, 350000, 11600000, 420000, "B.M.S. COLLEGE OF ENGINEERING", 2850, "1A1A1A", True),
        ppt_text_box(3, 500000, 780000, 11600000, 300000, "(Autonomous Institute, Affiliated to VTU, Belagavi)", 1250, "1A1A1A", False),
        ppt_text_box(4, 500000, 1180000, 11600000, 500000, "DEPARTMENT OF MACHINE LEARNING", 2650, "0000CC", True),
        ppt_text_box(5, 500000, 1740000, 11600000, 370000, "(UG Program: B.E. in Artificial Intelligence and Machine Learning)", 1350, "0000CC"),
        ppt_text_box(6, 500000, 2450000, 11600000, 450000, "Course: Natural Language Processing for LLM\nCourse Code: 24AM7PCLLM", 2050, "6B3E25", True),
        ppt_text_box(7, 500000, 3300000, 11600000, 500000, "PRIVACY-PRESERVING NAMED ENTITY RECOGNITION\nFOR AUTOMATED PCI/PII DETECTION IN FINANCIAL TEXT", 2200, "0000CC", True),
        ppt_text_box(8, 500000, 4050000, 11600000, 370000, "Alternative Assessment Tool (AAT)", 1550, "A52A74", True),
        ppt_text_box(9, 500000, 5050000, 5300000, 900000, "Presented By,\nStudent Name & USN: __________________\nStudent Name & USN: __________________\nSemester & Section: 7C\nDate: __________________", 1250, "1A1A1A"),
        ppt_text_box(10, 6700000, 5050000, 5100000, 900000, "Faculty In-Charge:\nUpeksha Prasad G\nAssistant Professor\nDepartment of Machine Learning\nBMS College of Engineering", 1250, "1A1A1A"),
    ]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def agenda_slide_xml() -> str:
    return slide_xml("Agenda", "Alternative Assessment Tool (AAT)", [
        "Introduction",
        "Selected NLP Topic Overview",
        "Real-Time Application / API Identified",
        "NLP Model / Architecture Study",
        "Dataset and Preprocessing",
        "Implementation Methodology",
        "Results and Evaluation",
        "Discussion",
        "Conclusion",
        "References",
    ], 2)


def thank_you_slide_xml() -> str:
    shapes = [ppt_text_box(2, 500000, 2700000, 11600000, 1300000, "Thank you !", 4400, "1A1A1A", False)]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def build_pptx(metrics: dict, destination: Path) -> None:
    result_lines = []
    for result in metrics["results"]:
        micro = result["entity"]["micro"]
        result_lines.append(f'{result["name"]}: Precision {micro["precision"]:.4f} · Recall {micro["recall"]:.4f} · F1 {micro["f1"]:.4f}')
    slides = [
        ("__COVER__", "", []),
        ("__AGENDA__", "", []),
        ("Introduction", "Why sensitive financial text needs a privacy boundary", ["Financial institutions process emails, support cases, transactions and operational logs", "These texts may contain PII or payment-card information", "NER can identify sensitive spans before analytics or language-model processing", "This project demonstrates detection, validation and redaction with synthetic data"]),
        ("Selected NLP Topic Overview", "Named Entity Recognition (NER)", ["NER assigns semantic labels to text spans using BIO tagging", "Financial labels: PERSON, EMAIL, PHONE, CARD_NUMBER, ACCOUNT_NUMBER, TAX_ID, ADDRESS, TRANSACTION_ID and ORGANIZATION", "Application: local compliance data-loss prevention for financial text", "Challenge: protect against false negatives without creating excessive false positives"]),
        ("Real-Time Application / API Identified", "Privacy-preserving financial text redaction service", ["API endpoints: GET /health, GET /demo and POST /redact", "Input is raw text in the local scanner; output is masked text and entity metadata", "The service can sit before an LLM, ticketing system, data warehouse or monitoring tool", "Raw values should remain inside a controlled scanning boundary"]),
        ("NLP Model / Architecture Study", "Transparent hybrid architecture", ["Tokenizer preserves character offsets and converts spans to BIO labels", "Rules layer validates structured identifiers and applies Luhn verification to card-like values", "Averaged perceptron uses token shape, context, prefixes, suffixes and previous BIO labels", "Overlap resolution returns one auditable set of entities for redaction"]),
        ("Dataset and Preprocessing", "Reproducible synthetic financial corpus", ["600 examples from payment, KYC, refund, billing, support and privacy templates", "Split: 420 train · 90 development · 90 test", "Seed: 42; character-level spans; tokenization; BIO conversion", "No real personal or payment data is used"]),
        ("Implementation Methodology", "From corpus generation to API response", ["Generate synthetic examples and gold entity spans", "Train the averaged perceptron for eight epochs", "Run rules, model and hybrid approaches on the held-out test split", "Serialize metrics, sample predictions and dataset JSONL", "Expose the detector through a dependency-free local JSON API"]),
        ("Results and Evaluation", "Exact entity-level comparison", result_lines),
        ("Discussion", "What the comparison tells us", ["Rules achieved perfect precision but lower recall because they miss contextual PERSON and ORGANIZATION entities", "The perceptron recovered contextual entities with 0.9960 entity F1 on the templated corpus", "The hybrid design adds explicit validation and remains auditable", "The result is educational evidence, not a production generalization claim"]),
        ("Conclusion", "A practical privacy-first NER contribution", ["The project implements a complete NLP workflow from dataset construction to API delivery", "Contextual NER and deterministic financial validation complement each other", "Future work: held-out templates, human annotations, multilingual text and transformer comparison"]),
        ("References", "Selected literature and standards", ["Lample et al. (2016), Neural Architectures for Named Entity Recognition", "Devlin et al. (2019), BERT: Pre-training of Deep Bidirectional Transformers", "Nadeau and Sekine (2007), A survey of named entity recognition and classification", "Payment Card Industry Security Standards Council, PCI DSS v4.0.1", "Luhn (1960), Computer for verifying numbers"]),
        ("__THANK_YOU__", "", []),
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
            if title == "__COVER__":
                xml = cover_slide_xml()
            elif title == "__AGENDA__":
                xml = agenda_slide_xml()
            elif title == "__THANK_YOU__":
                xml = thank_you_slide_xml()
            else:
                xml = slide_xml(title, subtitle, bullets, index)
            archive.writestr(f"ppt/slides/slide{index}.xml", xml)
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
