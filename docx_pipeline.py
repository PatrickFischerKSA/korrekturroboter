from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"

NSMAP = {"w": W_NS, "r": R_NS}

etree.register_namespace("w", W_NS)
etree.register_namespace("r", R_NS)
etree.register_namespace("", PKG_REL_NS)
etree.register_namespace("ct", CONTENT_TYPES_NS)
etree.register_namespace("cp", CORE_NS)
etree.register_namespace("dc", DC_NS)
etree.register_namespace("dcterms", DCTERMS_NS)
etree.register_namespace("xsi", XSI_NS)
etree.register_namespace("ep", APP_NS)
etree.register_namespace("vt", VT_NS)


def qn(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def read_docx_paragraphs(document_bytes: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(document_bytes)) as archive:
        try:
            xml_bytes = archive.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("Die hochgeladene Datei ist kein gültiges DOCX-Dokument.") from exc

    root = etree.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespaces=NSMAP):
        fragments = []
        for text_node in paragraph.findall(".//w:t", namespaces=NSMAP):
            fragments.append(text_node.text or "")
        paragraph_text = "".join(fragments).strip()
        if paragraph_text:
            paragraphs.append(paragraph_text)

    if not paragraphs:
        raise ValueError("Das DOCX-Dokument enthält keinen auswertbaren Fließtext.")
    return paragraphs


def read_reference_paragraphs(file_name: str, document_bytes: bytes) -> list[str]:
    extension = Path(file_name or "").suffix.lower()
    if extension == ".docx":
        return read_docx_paragraphs(document_bytes)
    if extension in {".txt", ".md"}:
        return _read_plain_text_paragraphs(document_bytes)
    if extension == ".pdf":
        return _read_pdf_paragraphs(document_bytes)
    raise ValueError("Das Prüfungsdossier muss als DOCX, TXT oder PDF vorliegen.")


def _read_plain_text_paragraphs(document_bytes: bytes) -> list[str]:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            text = document_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Die Textdatei konnte nicht gelesen werden.")

    paragraphs = [line.strip() for line in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if line.strip()]
    if not paragraphs:
        raise ValueError("Das Prüfungsdossier enthält keinen auswertbaren Text.")
    return paragraphs


def _read_pdf_paragraphs(document_bytes: bytes) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
        handle.write(document_bytes)
        pdf_path = handle.name

    try:
        extracted = _extract_pdf_text_via_mdls(pdf_path) or _extract_pdf_text_via_strings(pdf_path)
    finally:
        try:
            os.unlink(pdf_path)
        except OSError:
            pass

    paragraphs = [line.strip() for line in re.split(r"\n\s*\n|\r\n\s*\r\n", extracted or "") if line.strip()]
    if not paragraphs:
        raise ValueError(
            "Das PDF-Prüfungsdossier konnte nicht ausgelesen werden. Verwende bitte DOCX oder TXT."
        )
    return paragraphs


def _extract_pdf_text_via_mdls(pdf_path: str) -> str:
    try:
        result = subprocess.run(
            ["mdls", "-raw", "-name", "kMDItemTextContent", pdf_path],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""

    output = (result.stdout or "").strip()
    if result.returncode != 0 or not output or "could not find" in output.lower() or output == "(null)":
        return ""
    return output.strip('"')


def _extract_pdf_text_via_strings(pdf_path: str) -> str:
    try:
        result = subprocess.run(
            ["strings", "-n", "6", pdf_path],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""

    output = result.stdout or ""
    lines = []
    for line in output.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if len(cleaned) < 20:
            continue
        if sum(character.isalpha() for character in cleaned) < 12:
            continue
        lines.append(cleaned)
    return "\n".join(lines)


def calculate_overall_grade(review: dict) -> float:
    inhalt = float(review["criteria_comments"]["inhalt"]["score"])
    aufbau = float(review["criteria_comments"]["aufbau"]["score"])
    ausdruck = float(review["criteria_comments"]["ausdruck"]["score"])
    orthografie = float(review["orthography"]["grade"])
    return round(inhalt * 0.4 + aufbau * 0.2 + ausdruck * 0.2 + orthografie * 0.2, 2)


def build_reviewed_docx(source_name: str, paragraphs: list[str], review: dict) -> bytes:
    prepared = _prepare_annotations(paragraphs, review)
    package = io.BytesIO()

    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _build_content_types())
        archive.writestr("_rels/.rels", _build_root_relationships())
        archive.writestr("docProps/core.xml", _build_core_properties())
        archive.writestr("docProps/app.xml", _build_app_properties())
        archive.writestr("word/document.xml", _build_document_xml(source_name, paragraphs, review, prepared))
        archive.writestr("word/comments.xml", _build_comments_xml(prepared["comments"]))
        archive.writestr("word/styles.xml", _build_styles_xml())
        archive.writestr("word/_rels/document.xml.rels", _build_document_relationships())

    package.seek(0)
    return package.read()


def _prepare_annotations(paragraphs: list[str], review: dict) -> dict:
    by_paragraph: dict[int, list[dict]] = {index: [] for index in range(len(paragraphs))}
    comments: list[dict] = []
    next_id = 0

    for item in review.get("annotations", []):
        paragraph_index = int(item["paragraph_index"])
        prepared = {
            **item,
            "comment_id": next_id,
            "comment_text": _build_anchor_comment(item),
            "kind": "annotation",
        }
        by_paragraph.setdefault(paragraph_index, []).append(prepared)
        comments.append({"id": next_id, "text": prepared["comment_text"]})
        next_id += 1

    for item in review.get("language_errors", []):
        paragraph_index = int(item["paragraph_index"])
        prepared = {
            **item,
            "comment_id": next_id,
            "comment_text": _build_language_comment(item),
            "kind": "language_error",
            "action": "ueberarbeiten",
        }
        by_paragraph.setdefault(paragraph_index, []).append(prepared)
        comments.append({"id": next_id, "text": prepared["comment_text"]})
        next_id += 1

    spans_by_paragraph = {}
    for index, paragraph in enumerate(paragraphs):
        spans_by_paragraph[index] = _locate_spans(paragraph, by_paragraph.get(index, []))

    return {"spans_by_paragraph": spans_by_paragraph, "comments": comments}


def _build_anchor_comment(item: dict) -> str:
    category_labels = {
        "inhalt": "Inhalt",
        "aufbau": "Aufbau",
        "ausdruck": "Ausdruck",
        "rhetorik": "Rhetorik",
    }
    action_label = "Überarbeiten" if item.get("action") == "ueberarbeiten" else "Kommentieren"
    category_label = category_labels.get(item.get("category"), "Kommentar")
    comment = item.get("comment", "").strip()
    suggestion = item.get("suggestion", "").strip()
    return (
        f"{action_label} ({category_label}): {comment} "
        f"Vorschlag: {suggestion}"
    ).strip()


def _build_language_comment(item: dict) -> str:
    label = "Grammatikfehler" if item.get("category") == "grammatik" else "Rechtschreibfehler"
    comment = item.get("comment", "").strip()
    suggestion = item.get("suggestion", "").strip()
    return f"{label}: {comment} Korrekturvorschlag: {suggestion}".strip()


def _locate_spans(paragraph: str, items: list[dict]) -> list[dict]:
    spans: list[dict] = []
    reserved: list[tuple[int, int]] = []

    ordered = sorted(items, key=lambda item: (-len(item.get("snippet", "")), item.get("comment_id", 0)))
    for item in ordered:
        snippet = item.get("snippet", "")
        if not snippet:
            continue
        start = _find_non_overlapping(paragraph, snippet, reserved)
        if start < 0:
            continue
        end = start + len(snippet)
        reserved.append((start, end))
        spans.append({"start": start, "end": end, "item": item})

    spans.sort(key=lambda span: span["start"])
    return spans


def _find_non_overlapping(paragraph: str, snippet: str, reserved: list[tuple[int, int]]) -> int:
    start = paragraph.find(snippet)
    while start != -1:
        end = start + len(snippet)
        if not any(start < reserved_end and end > reserved_start for reserved_start, reserved_end in reserved):
            return start
        start = paragraph.find(snippet, start + 1)
    return -1


def _build_document_xml(source_name: str, paragraphs: list[str], review: dict, prepared: dict) -> bytes:
    document = etree.Element(qn(W_NS, "document"))
    body = etree.SubElement(document, qn(W_NS, "body"))

    _append_heading(body, f"Korrekturroboter: {Path(source_name).stem}")
    _append_plain_paragraph(
        body,
        "Die Textstellenkommentare stammen aus einem lokalen LM-Studio-Workflow. "
        "Grammatik- und Rechtschreibfehler sind rot markiert und werden für Kriterium 4 gezählt.",
    )
    if review.get("privacy_notice"):
        _append_plain_paragraph(body, review["privacy_notice"])
    if review.get("document_type_label"):
        _append_plain_paragraph(body, f"Gewählte Form: {review['document_type_label']}.")
    if review.get("topic"):
        _append_plain_paragraph(body, f"Thema: {review['topic']}.")
    if review.get("thesis"):
        _append_plain_paragraph(body, f"Leitfrage / These: {review['thesis']}.")
    if review.get("assignment_text"):
        _append_subheading(body, "Aufgabenstellung")
        _append_plain_paragraph(body, review["assignment_text"])
    _append_plain_paragraph(body, "")

    for index, paragraph in enumerate(paragraphs):
        body.append(_build_annotated_paragraph(paragraph, prepared["spans_by_paragraph"].get(index, [])))

    _append_plain_paragraph(body, "")
    _append_heading(body, "Gesamtfeedback")
    _append_plain_paragraph(body, review.get("summary", ""))
    _append_plain_paragraph(body, "")

    criteria_labels = {
        "inhalt": "Kriterium 1 - Inhalt",
        "aufbau": "Kriterium 2 - Aufbau",
        "ausdruck": "Kriterium 3 - Ausdruck",
    }
    for key in ("inhalt", "aufbau", "ausdruck"):
        entry = review["criteria_comments"][key]
        _append_subheading(body, f"{criteria_labels[key]} ({entry['score']:.2f})")
        _append_plain_paragraph(body, entry["comment"])

    orthography = review["orthography"]
    _append_subheading(body, f"Kriterium 4 - Sprachliche Korrektheit ({orthography['grade']:.2f})")
    _append_plain_paragraph(body, orthography["comment"])
    _append_plain_paragraph(
        body,
        f"Gezählt wurden {orthography['error_count']} Grammatik- und Rechtschreibfehler in "
        f"{orthography['word_count']} Wörtern. Das entspricht {orthography['errors_per_200']:.2f} "
        f"Fehlern pro 200 Wörter.",
    )

    _append_subheading(body, f"Gesamtnote ({calculate_overall_grade(review):.2f})")
    _append_plain_paragraph(
        body,
        "Die Gesamtnote folgt der Gewichtung 40 Prozent Inhalt sowie je 20 Prozent für Aufbau, Ausdruck "
        "und sprachliche Korrektheit.",
    )
    if review.get("privacy_notice"):
        _append_plain_paragraph(body, review["privacy_notice"])
    _append_plain_paragraph(body, f"Dokumenttyp: {review.get('document_type_label', review.get('document_type', 'essay'))}.")
    _append_plain_paragraph(body, f"LM-Studio-Modell: {review.get('model', 'unbekannt')}.")

    body.append(_build_section_properties())
    return etree.tostring(document, xml_declaration=True, encoding="UTF-8")


def _build_annotated_paragraph(text: str, spans: list[dict]) -> etree.Element:
    paragraph = etree.Element(qn(W_NS, "p"))
    cursor = 0
    for span in spans:
        if span["start"] > cursor:
            paragraph.append(_create_run(text[cursor : span["start"]]))

        item = span["item"]
        comment_id = str(item["comment_id"])
        paragraph.append(etree.Element(qn(W_NS, "commentRangeStart"), {qn(W_NS, "id"): comment_id}))
        paragraph.append(_create_run(text[span["start"] : span["end"]], item=item))
        paragraph.append(etree.Element(qn(W_NS, "commentRangeEnd"), {qn(W_NS, "id"): comment_id}))
        paragraph.append(_create_comment_reference_run(comment_id))
        cursor = span["end"]

    if cursor < len(text):
        paragraph.append(_create_run(text[cursor:]))

    if not len(paragraph):
        paragraph.append(_create_run(""))
    return paragraph


def _create_run(text: str, item: dict | None = None, bold: bool = False, size: int | None = None) -> etree.Element:
    run = etree.Element(qn(W_NS, "r"))
    properties = etree.SubElement(run, qn(W_NS, "rPr"))

    if bold:
        etree.SubElement(properties, qn(W_NS, "b"))
    if size is not None:
        etree.SubElement(properties, qn(W_NS, "sz"), {qn(W_NS, "val"): str(size)})

    if item:
        if item.get("kind") == "language_error":
            etree.SubElement(properties, qn(W_NS, "color"), {qn(W_NS, "val"): "C00000"})
            etree.SubElement(properties, qn(W_NS, "u"), {qn(W_NS, "val"): "single"})
        elif item.get("action") == "ueberarbeiten":
            etree.SubElement(properties, qn(W_NS, "highlight"), {qn(W_NS, "val"): "yellow"})

    text_node = etree.SubElement(run, qn(W_NS, "t"))
    if text != text.strip() or "  " in text:
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_node.text = text
    return run


def _create_comment_reference_run(comment_id: str) -> etree.Element:
    run = etree.Element(qn(W_NS, "r"))
    properties = etree.SubElement(run, qn(W_NS, "rPr"))
    etree.SubElement(properties, qn(W_NS, "rStyle"), {qn(W_NS, "val"): "CommentReference"})
    etree.SubElement(run, qn(W_NS, "commentReference"), {qn(W_NS, "id"): comment_id})
    return run


def _append_heading(body: etree.Element, text: str) -> None:
    paragraph = etree.SubElement(body, qn(W_NS, "p"))
    properties = etree.SubElement(paragraph, qn(W_NS, "pPr"))
    etree.SubElement(properties, qn(W_NS, "pStyle"), {qn(W_NS, "val"): "Heading1"})
    paragraph.append(_create_run(text, bold=True, size=32))


def _append_subheading(body: etree.Element, text: str) -> None:
    paragraph = etree.SubElement(body, qn(W_NS, "p"))
    properties = etree.SubElement(paragraph, qn(W_NS, "pPr"))
    etree.SubElement(properties, qn(W_NS, "pStyle"), {qn(W_NS, "val"): "Heading2"})
    paragraph.append(_create_run(text, bold=True, size=26))


def _append_plain_paragraph(body: etree.Element, text: str) -> None:
    paragraph = etree.SubElement(body, qn(W_NS, "p"))
    paragraph.append(_create_run(text))


def _build_section_properties() -> etree.Element:
    section = etree.Element(qn(W_NS, "sectPr"))
    etree.SubElement(section, qn(W_NS, "pgSz"), {qn(W_NS, "w"): "11906", qn(W_NS, "h"): "16838"})
    etree.SubElement(
        section,
        qn(W_NS, "pgMar"),
        {
            qn(W_NS, "top"): "1440",
            qn(W_NS, "right"): "1440",
            qn(W_NS, "bottom"): "1440",
            qn(W_NS, "left"): "1440",
            qn(W_NS, "header"): "720",
            qn(W_NS, "footer"): "720",
            qn(W_NS, "gutter"): "0",
        },
    )
    return section


def _build_comments_xml(comments: list[dict]) -> bytes:
    root = etree.Element(qn(W_NS, "comments"))
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for entry in comments:
        comment = etree.SubElement(
            root,
            qn(W_NS, "comment"),
            {
                qn(W_NS, "id"): str(entry["id"]),
                qn(W_NS, "author"): "Korrekturroboter",
                qn(W_NS, "initials"): "KR",
                qn(W_NS, "date"): timestamp,
            },
        )
        paragraph = etree.SubElement(comment, qn(W_NS, "p"))
        paragraph.append(_create_run(entry["text"]))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def _build_styles_xml() -> bytes:
    styles = etree.Element(qn(W_NS, "styles"))

    doc_defaults = etree.SubElement(styles, qn(W_NS, "docDefaults"))
    run_defaults = etree.SubElement(doc_defaults, qn(W_NS, "rPrDefault"))
    run_props = etree.SubElement(run_defaults, qn(W_NS, "rPr"))
    etree.SubElement(run_props, qn(W_NS, "rFonts"), {qn(W_NS, "ascii"): "Georgia", qn(W_NS, "hAnsi"): "Georgia"})
    etree.SubElement(run_props, qn(W_NS, "sz"), {qn(W_NS, "val"): "24"})
    etree.SubElement(run_props, qn(W_NS, "lang"), {qn(W_NS, "val"): "de-CH"})

    default_paragraph = etree.SubElement(
        styles,
        qn(W_NS, "style"),
        {qn(W_NS, "type"): "paragraph", qn(W_NS, "default"): "1", qn(W_NS, "styleId"): "Normal"},
    )
    etree.SubElement(default_paragraph, qn(W_NS, "name"), {qn(W_NS, "val"): "Normal"})

    heading1 = etree.SubElement(styles, qn(W_NS, "style"), {qn(W_NS, "type"): "paragraph", qn(W_NS, "styleId"): "Heading1"})
    etree.SubElement(heading1, qn(W_NS, "name"), {qn(W_NS, "val"): "Heading 1"})
    etree.SubElement(heading1, qn(W_NS, "basedOn"), {qn(W_NS, "val"): "Normal"})
    etree.SubElement(heading1, qn(W_NS, "qFormat"))
    heading1_props = etree.SubElement(heading1, qn(W_NS, "rPr"))
    etree.SubElement(heading1_props, qn(W_NS, "b"))
    etree.SubElement(heading1_props, qn(W_NS, "sz"), {qn(W_NS, "val"): "32"})

    heading2 = etree.SubElement(styles, qn(W_NS, "style"), {qn(W_NS, "type"): "paragraph", qn(W_NS, "styleId"): "Heading2"})
    etree.SubElement(heading2, qn(W_NS, "name"), {qn(W_NS, "val"): "Heading 2"})
    etree.SubElement(heading2, qn(W_NS, "basedOn"), {qn(W_NS, "val"): "Normal"})
    etree.SubElement(heading2, qn(W_NS, "qFormat"))
    heading2_props = etree.SubElement(heading2, qn(W_NS, "rPr"))
    etree.SubElement(heading2_props, qn(W_NS, "b"))
    etree.SubElement(heading2_props, qn(W_NS, "sz"), {qn(W_NS, "val"): "26"})

    default_character = etree.SubElement(
        styles,
        qn(W_NS, "style"),
        {qn(W_NS, "type"): "character", qn(W_NS, "default"): "1", qn(W_NS, "styleId"): "DefaultParagraphFont"},
    )
    etree.SubElement(default_character, qn(W_NS, "name"), {qn(W_NS, "val"): "Default Paragraph Font"})
    etree.SubElement(default_character, qn(W_NS, "semiHidden"))

    comment_reference = etree.SubElement(
        styles,
        qn(W_NS, "style"),
        {qn(W_NS, "type"): "character", qn(W_NS, "styleId"): "CommentReference"},
    )
    etree.SubElement(comment_reference, qn(W_NS, "name"), {qn(W_NS, "val"): "Comment Reference"})
    comment_reference_props = etree.SubElement(comment_reference, qn(W_NS, "rPr"))
    etree.SubElement(comment_reference_props, qn(W_NS, "b"))
    etree.SubElement(comment_reference_props, qn(W_NS, "color"), {qn(W_NS, "val"): "7F6000"})
    etree.SubElement(comment_reference_props, qn(W_NS, "sz"), {qn(W_NS, "val"): "16"})

    return etree.tostring(styles, xml_declaration=True, encoding="UTF-8")


def _build_document_relationships() -> bytes:
    relationships = etree.Element(qn(PKG_REL_NS, "Relationships"))
    etree.SubElement(
        relationships,
        qn(PKG_REL_NS, "Relationship"),
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            "Target": "styles.xml",
        },
    )
    etree.SubElement(
        relationships,
        qn(PKG_REL_NS, "Relationship"),
        {
            "Id": "rId2",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
            "Target": "comments.xml",
        },
    )
    return etree.tostring(relationships, xml_declaration=True, encoding="UTF-8")


def _build_root_relationships() -> bytes:
    relationships = etree.Element(qn(PKG_REL_NS, "Relationships"))
    etree.SubElement(
        relationships,
        qn(PKG_REL_NS, "Relationship"),
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "word/document.xml",
        },
    )
    etree.SubElement(
        relationships,
        qn(PKG_REL_NS, "Relationship"),
        {
            "Id": "rId2",
            "Type": "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
            "Target": "docProps/core.xml",
        },
    )
    etree.SubElement(
        relationships,
        qn(PKG_REL_NS, "Relationship"),
        {
            "Id": "rId3",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
            "Target": "docProps/app.xml",
        },
    )
    return etree.tostring(relationships, xml_declaration=True, encoding="UTF-8")


def _build_content_types() -> bytes:
    types = etree.Element(qn(CONTENT_TYPES_NS, "Types"))
    etree.SubElement(types, qn(CONTENT_TYPES_NS, "Default"), {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    etree.SubElement(types, qn(CONTENT_TYPES_NS, "Default"), {"Extension": "xml", "ContentType": "application/xml"})
    etree.SubElement(
        types,
        qn(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/word/document.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        },
    )
    etree.SubElement(
        types,
        qn(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/word/styles.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
        },
    )
    etree.SubElement(
        types,
        qn(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/word/comments.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
        },
    )
    etree.SubElement(
        types,
        qn(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/docProps/core.xml",
            "ContentType": "application/vnd.openxmlformats-package.core-properties+xml",
        },
    )
    etree.SubElement(
        types,
        qn(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/docProps/app.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        },
    )
    return etree.tostring(types, xml_declaration=True, encoding="UTF-8")


def _build_core_properties() -> bytes:
    root = etree.Element(qn(CORE_NS, "coreProperties"))
    etree.SubElement(root, qn(DC_NS, "title")).text = "Korrigierter Aufsatz"
    etree.SubElement(root, qn(DC_NS, "creator")).text = "Korrekturroboter"
    etree.SubElement(root, qn(CORE_NS, "lastModifiedBy")).text = "Korrekturroboter"
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    created = etree.SubElement(root, qn(DCTERMS_NS, "created"), {qn(XSI_NS, "type"): "dcterms:W3CDTF"})
    created.text = timestamp
    modified = etree.SubElement(root, qn(DCTERMS_NS, "modified"), {qn(XSI_NS, "type"): "dcterms:W3CDTF"})
    modified.text = timestamp
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def _build_app_properties() -> bytes:
    root = etree.Element(qn(APP_NS, "Properties"))
    etree.SubElement(root, qn(APP_NS, "Application")).text = "Korrekturroboter"
    etree.SubElement(root, qn(APP_NS, "DocSecurity")).text = "0"
    etree.SubElement(root, qn(APP_NS, "ScaleCrop")).text = "false"
    etree.SubElement(root, qn(APP_NS, "Company")).text = "Lokal"
    etree.SubElement(root, qn(APP_NS, "LinksUpToDate")).text = "false"
    etree.SubElement(root, qn(APP_NS, "SharedDoc")).text = "false"
    etree.SubElement(root, qn(APP_NS, "HyperlinksChanged")).text = "false"
    etree.SubElement(root, qn(APP_NS, "AppVersion")).text = "1.0"
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
