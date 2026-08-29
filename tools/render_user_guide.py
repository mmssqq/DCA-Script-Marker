#!/usr/bin/env python3
"""Render USER_GUIDE.md as the bilingual PDF bundled with each release."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "USER_GUIDE.md"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "pdf"
    / "START HERE - User Guide - 使用手册.pdf"
)
PAGE_WIDTH, PAGE_HEIGHT = A4
CJK_FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def contains_cjk(value: str) -> bool:
    return any("\u3400" <= character <= "\u9fff" for character in value)


def inline_markup(value: str, *, cjk: bool | None = None) -> str:
    rendered = html.escape(value.strip())
    rendered = re.sub(
        r"`([^`]+)`",
        lambda match: (
            f'<font name="GuideCJK" color="#1f3550">{match.group(1)}</font>'
            if contains_cjk(match.group(1))
            else f'<font name="Courier" color="#1f3550">{match.group(1)}</font>'
        ),
        rendered,
    )
    rendered = re.sub(
        r"\[([^]]+)]\(([^)]+)\)",
        r'<link href="\2" color="#175d8f"><u>\1</u></link>',
        rendered,
    )
    if cjk is None:
        cjk = contains_cjk(value)
    if cjk:
        # Keep emphasis readable with colour because the embedded Unicode font
        # does not expose a separate bold face.
        rendered = re.sub(
            r"\*\*([^*]+)\*\*",
            r'<font color="#173f5f">\1</font>',
            rendered,
        )
        return f'<font name="GuideCJK">{rendered}</font>'
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", rendered)


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def is_block_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith(("#", ">", "```", "|")):
        return True
    if stripped == "---":
        return True
    return bool(re.match(r"^(?:[-*]|\d+[.])\s+", stripped))


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "GuideTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#163f5c"),
            alignment=TA_CENTER,
            spaceAfter=7 * mm,
        ),
        "h2": ParagraphStyle(
            "GuideH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#174d70"),
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "GuideH3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#235e7c"),
            spaceBefore=2.5 * mm,
            spaceAfter=1.2 * mm,
            keepWithNext=True,
        ),
        "h4": ParagraphStyle(
            "GuideH4",
            parent=base["Heading4"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#2e6077"),
            spaceBefore=2 * mm,
            spaceAfter=1 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "GuideBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=10.8,
            textColor=colors.HexColor("#18242d"),
            spaceAfter=1.2 * mm,
            splitLongWords=True,
            wordWrap="CJK",
        ),
        "version": ParagraphStyle(
            "GuideVersion",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#4a6475"),
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        "quote": ParagraphStyle(
            "GuideQuote",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.8,
            textColor=colors.HexColor("#5a2e1f"),
            leftIndent=5 * mm,
            rightIndent=3 * mm,
            borderColor=colors.HexColor("#d9895b"),
            borderWidth=0.8,
            borderPadding=5,
            backColor=colors.HexColor("#fff6ef"),
            spaceAfter=2 * mm,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "GuideBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.6,
            leftIndent=5 * mm,
            firstLineIndent=-3.5 * mm,
            bulletIndent=0,
            spaceAfter=0.5 * mm,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "GuideCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.1,
            leading=9.2,
            leftIndent=3 * mm,
            rightIndent=3 * mm,
            borderColor=colors.HexColor("#c7d3dc"),
            borderWidth=0.5,
            borderPadding=5,
            backColor=colors.HexColor("#f4f7f9"),
            spaceAfter=2 * mm,
        ),
        "table": ParagraphStyle(
            "GuideTable",
            parent=base["BodyText"],
            fontName="GuideCJK",
            fontSize=7.2,
            leading=9.2,
            textColor=colors.HexColor("#18242d"),
            wordWrap="CJK",
        ),
    }


def markdown_story(markdown_text: str, styles: dict[str, ParagraphStyle]):
    lines = markdown_text.splitlines()
    story = []
    index = 0
    title_seen = False

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        if stripped == "---":
            story.append(HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor("#b9c9d3"),
                spaceBefore=2 * mm,
                spaceAfter=2 * mm,
            ))
            index += 1
            continue

        if stripped.startswith("```"):
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            story.append(XPreformatted("\n".join(code_lines), styles["code"]))
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            if level == 1 and not title_seen:
                story.append(Paragraph(inline_markup(text), styles["title"]))
                title_seen = True
            else:
                style_name = "h2" if level <= 2 else "h3" if level == 3 else "h4"
                story.append(Paragraph(inline_markup(text), styles[style_name]))
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            story.append(
                Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"])
            )
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            raw_rows = [stripped]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                raw_rows.append(lines[index].strip())
                index += 1
            rows = []
            for raw_row in raw_rows:
                cells = [cell.strip() for cell in raw_row.strip("|").split("|")]
                rows.append([
                    Paragraph(inline_markup(cell, cjk=True), styles["table"])
                    for cell in cells
                ])
            first_width = 42 * mm if len(rows[0]) == 2 else 30 * mm
            remaining = PAGE_WIDTH - 38 * mm - first_width
            widths = [first_width] + [remaining / (len(rows[0]) - 1)] * (len(rows[0]) - 1)
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeaf3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173f5f")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#a9bbc7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([table, Spacer(1, 2 * mm)])
            continue

        list_match = re.match(r"^([-*]|\d+[.])\s+(.+)$", stripped)
        if list_match:
            marker, text = list_match.groups()
            index += 1
            continuation = []
            while index < len(lines) and lines[index].strip() and not is_block_start(lines, index):
                continuation.append(lines[index].strip())
                index += 1
            item_text = " ".join([text, *continuation])
            bullet = "•" if marker in {"-", "*"} else marker
            story.append(Paragraph(
                f'{inline_markup(bullet, cjk=contains_cjk(item_text))} '
                f'{inline_markup(item_text)}',
                styles["bullet"],
            ))
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not is_block_start(lines, index):
            paragraph_lines.append(lines[index].strip())
            index += 1
        paragraph_text = " ".join(paragraph_lines)
        style = styles["version"] if paragraph_text.startswith("Version ") else styles["body"]
        story.append(Paragraph(inline_markup(paragraph_text), style))

    return story


def draw_page_chrome(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#b9c9d3"))
    canvas.setLineWidth(0.45)
    canvas.line(18 * mm, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - 18 * mm, PAGE_HEIGHT - 13 * mm)
    canvas.setFont("GuideCJK", 7.2)
    canvas.setFillColor(colors.HexColor("#5a6d79"))
    canvas.drawString(18 * mm, 9 * mm, "DCA Script Marker User Guide / 使用手册")
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, 9 * mm, f"Version 1.0.0  |  {document.page}")
    canvas.restoreState()


def render(source: Path, output: Path) -> None:
    if not CJK_FONT_PATH.is_file():
        raise FileNotFoundError(
            f"Required macOS Unicode font was not found: {CJK_FONT_PATH}"
        )
    pdfmetrics.registerFont(TTFont("GuideCJK", str(CJK_FONT_PATH)))
    pdfmetrics.registerFontFamily(
        "GuideCJK",
        normal="GuideCJK",
        bold="GuideCJK",
        italic="GuideCJK",
        boldItalic="GuideCJK",
    )
    styles = build_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title="DCA Script Marker User Guide / 使用手册",
        author="马斯琪 Siqi Ma",
        subject="Bilingual user guide for DCA Script Marker 1.0.0",
    )
    story = markdown_story(source.read_text(encoding="utf-8"), styles)
    story.insert(2, HRFlowable(
        width="100%",
        thickness=0.8,
        color=colors.HexColor("#87a9bd"),
        spaceBefore=0,
        spaceAfter=4 * mm,
    ))
    document.build(story, onFirstPage=draw_page_chrome, onLaterPages=draw_page_chrome)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render(args.source.resolve(), args.output.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
