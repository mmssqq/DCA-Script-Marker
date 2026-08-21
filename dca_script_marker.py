# Copyright © 2026 马斯琪 Siqi Ma
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import fitz  # PyMuPDF
import re
import unicodedata
import argparse
import html
import json
import platform
import sys
import tempfile
import warnings
import openpyxl
from openpyxl import load_workbook
from datetime import date

TEMPLATE_FILE = "dca_template.xlsx"
PDF_FILE = "chinese_sample_script v3.pdf"
OUTPUT_FILE = "marked_script.pdf"
REPORT_FILE = "review_report.txt"

STATE_COLOUR = (0.0, 0.35, 0.75)
NUMBER_COLOUR = (0.85, 0.0, 0.35)
CHINESE_FONT_FILE = "/System/Library/Fonts/STHeiti Medium.ttc"
NUMBER_SCALE = 1.25

# Some PDFs expose simplified CJK radicals instead of the ordinary character
# stored in the workbook. Keep this deliberately narrow so speaker matching is
# tolerant without making unrelated Chinese names compare as equal.
SPEAKER_CHARACTER_TRANSLATION = str.maketrans({
    "⻓": "长",
})

STAGE_DIRECTION_PREFIXES = ("(", "[", "{", "【", "〔")


def normalise(text):
    text = unicodedata.normalize("NFKC", str(text))
    return " ".join(text.strip().lower().split())


def cue_match_key(text):
    """Normalise a DCA State cue while allowing Chinese spacing variations."""
    cleaned = normalise(text)

    if any("\u4e00" <= character <= "\u9fff" for character in cleaned):
        return re.sub(r"\s+", "", cleaned)

    return cleaned


def cue_identifier(text):
    """Return a leading music/playback cue code such as M0 or PB3."""
    cleaned = unicodedata.normalize("NFKC", str(text)).strip().lower()
    match = re.match(r"^(pb|m)\s*(\d+)(?=$|[^0-9a-z_])", cleaned)

    if not match:
        return ""

    return f"{match.group(1)}{match.group(2)}"


def speaker_match_key(text):
    """Compare names while ignoring punctuation and European accents.

    This lets an Excel name such as ``HELENE`` match a script cue printed as
    ``HÉLÈNE``.  The original text remains unchanged in the marked PDF.
    """
    cleaned = normalise(text).translate(SPEAKER_CHARACTER_TRANSLATION)
    accent_free = "".join(
        character
        for character in unicodedata.normalize("NFD", cleaned)
        if unicodedata.category(character) != "Mn"
    )
    # The template may contain a label copied directly from a script, such as
    # ``马克桑斯：`` or ``MR. Z.``. Colons are label punctuation, not part of
    # the character name, so ignore them during every speaker comparison.
    return re.sub(r"[\s·・.．。:：]", "", accent_free)


def speaker_base_key(text):
    """Match a speaker name while ignoring a cast-count note in brackets."""
    base_name = re.split(r"[（(]", str(text), maxsplit=1)[0]
    return speaker_match_key(base_name)


def contains_cjk(text):
    return any("\u4e00" <= character <= "\u9fff" for character in str(text))


def css_colour(colour):
    """Convert a PyMuPDF RGB tuple into a CSS hexadecimal colour."""
    channels = (
        round(max(0.0, min(1.0, channel)) * 255)
        for channel in colour
    )
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def rich_text_font_family(font_name, font_file):
    """Return a safe CSS family for a rich FreeText annotation."""
    if font_file:
        return "sans-serif"

    return {
        "helv": "Helvetica",
        "hebo": "Helvetica",
        "tiro": "Times New Roman",
        "tibo": "Times New Roman",
        "cour": "Courier New",
        "cobo": "Courier New",
    }.get(font_name, "Helvetica")


def starts_with_stage_direction(text):
    cleaned = unicodedata.normalize("NFKC", str(text)).strip()
    return cleaned.startswith(STAGE_DIRECTION_PREFIXES)


def looks_like_speaker_label(text, speaker_name):
    """Avoid marking a character name used inside dialogue or narration."""
    text = unicodedata.normalize("NFKC", text).strip()

    # A name inside a bracketed action is not a dialogue label. Check this
    # before accepting explicit colons so title-case cues such as ``Mary:`` can
    # be supported without turning ``[Mary: enters]`` into spoken dialogue.
    if starts_with_stage_direction(text):
        return False

    english_name = not contains_cjk(speaker_name)

    def has_english_cue_case(value):
        """English speaker labels are conventionally printed in capitals."""
        letters = "".join(letter for letter in value if letter.isalpha())
        return bool(letters) and letters.isupper()

    # A colon is a speaker separator only when the text *before* it is the
    # speaker name.  Dialogue can contain a later colon ("Now:",
    # "[MUSIC: ...]"), so it must not prevent the ordinary full-stop label
    # checks below from recognising ADAM., HENRI., and similar cues.
    if "：" in text or ":" in text:
        label = re.split(r"[：:]", text, maxsplit=1)[0].strip()
        if speaker_match_key(label) == speaker_match_key(speaker_name):
            # An exact name followed by a colon is unambiguous enough to allow
            # title-case English labels such as Mary: and Fanny：. Less explicit
            # English layouts below retain the uppercase safety requirement.
            return True

    if speaker_match_key(text) == speaker_match_key(speaker_name):
        return not english_name or has_english_cue_case(text)

    # Preserve abbreviations inside a name, such as ``MR. Z.``, while using
    # the final full stop / colon as the speaker-label boundary. This avoids
    # confusing an action such as ``MR. Z appears`` with spoken dialogue.
    escaped_speaker = re.escape(str(speaker_name))
    punctuated_label = re.match(
        rf"^\s*{escaped_speaker}(?=$|[.:：])",
        text,
        flags=re.IGNORECASE,
    )
    if punctuated_label:
        return (
            not english_name
            or has_english_cue_case(punctuated_label.group(0))
        )

    # English scripts commonly use a full stop after a multi-word speaker
    # label: ``AMERICAN SOLDIER. Jerry, there you are.``  The old check below
    # considered only the first word (``AMERICAN``), which meant these valid
    # labels were skipped while one-word labels such as ``JERRY.`` worked.
    speaker_prefix = re.split(r"[.:：]", text, maxsplit=1)[0].strip()
    if speaker_match_key(speaker_prefix) == speaker_match_key(speaker_name):
        return (
            not english_name
            or has_english_cue_case(speaker_prefix)
        )

    # A script may write a name with a different middle dot, then a single
    # space before the dialogue: 本丢.彼拉多 你是怎么看出来的？
    # Compare only that first word using the punctuation-insensitive key.
    first_word = text.split(maxsplit=1)[0] if text else ""
    # A shared English label often begins ``HENRI, ADAM, JERRY...``.
    # Treat the comma after the first name as a label separator, not as part
    # of that name.
    first_word = first_word.rstrip(",;；")
    if speaker_match_key(first_word) == speaker_match_key(speaker_name):
        return not english_name or has_english_cue_case(first_word)

    # Slash-separated and ampersand-separated group labels keep all names in
    # one visual word, for example ``MILO/JERRY/HENRI/LISE.``.  The first
    # component still establishes that this row is a speaker label.
    leading_component = re.split(
        r"[,/&＋+、/／;；]",
        first_word,
        maxsplit=1,
    )[0].rstrip(".")
    if speaker_match_key(leading_component) == speaker_match_key(speaker_name):
        return (
            not english_name
            or has_english_cue_case(leading_component)
        )

    # The first name in a shared label can itself contain spaces, such as
    # ``ALL THREE MEN & ENSEMBLE.``. In that layout `first_word` is only
    # ALL, so also inspect the complete text before the first group
    # separator. This remains safe for dialogue because an ordinary cue like
    # ``HENRI. (to JERRY & ADAM)`` was already recognised by its full stop.
    leading_group_name = re.split(
        r"[,/&＋+、/／;；]",
        text,
        maxsplit=1,
    )[0].strip().rstrip(".")
    if speaker_match_key(leading_group_name) == speaker_match_key(speaker_name):
        return (
            not english_name
            or has_english_cue_case(leading_group_name)
        )

    # Group labels are often printed as, for example, 歌队（8位）.
    # The cast-count note is not part of the character name in the template.
    if speaker_base_key(first_word) == speaker_match_key(speaker_name):
        return not english_name or has_english_cue_case(first_word)

    # A lead speaker can be followed by a group count, for example
    # 李晨暘+5群众. The count describes the group; it is not part of the name.
    group_label = re.match(r"^(.*?)\s*\+\s*\d+", first_word)
    if (
        group_label
        and speaker_match_key(group_label.group(1))
        == speaker_match_key(speaker_name)
    ):
        return not english_name or has_english_cue_case(first_word)

    # Chinese theatre scripts normally have a wide gap after a speaker label.
    label = re.split(r"\s{2,}", text, maxsplit=1)[0]
    if speaker_match_key(label) == speaker_match_key(speaker_name):
        return not english_name or has_english_cue_case(label)

    # Some English-style layouts use one ordinary space after the name.
    return (
        not english_name
        and normalise(text).startswith(normalise(speaker_name) + " ")
    )


def get_speaker_name(text, possible_characters):
    clean_text = normalise(text)

    for separator in ("：", ":"):
        if separator in text:
            possible_name = text.split(
                separator, 1
            )[0].strip()

            full_name = normalise(possible_name)
            if full_name in possible_characters:
                return full_name

            compact_name = speaker_match_key(possible_name)
            for character in possible_characters:
                if speaker_match_key(character) == compact_name:
                    return character

            base_name = normalise(
                re.split(r"[（(]", possible_name, maxsplit=1)[0]
            )
            base_key = speaker_match_key(base_name)
            for character in possible_characters:
                if speaker_match_key(character) == base_key:
                    return character
            # This colon belongs to the dialogue, not to a speaker label.
            # Fall through to the normal beginning-of-line name matching.
            break

    compact_text = speaker_match_key(clean_text)
    for character in sorted(possible_characters, key=len, reverse=True):
        if compact_text.startswith(speaker_match_key(character)):
            return character

    for character in sorted(possible_characters, key=len, reverse=True):
        if clean_text.startswith(character):
            return character

    for character in possible_characters:
        if clean_text.startswith(character + "("):
            return character

    for character in sorted(
        possible_characters, key=len, reverse=True
    ):
        if clean_text == character:
            return character

        if (
            any("\u4e00" <= letter <= "\u9fff" for letter in character)
            and clean_text.startswith(character + " ")
        ):
            return character

    spaced_name = re.match(r"^(\S+)\s{2,}", text)

    if spaced_name:
        return normalise(spaced_name.group(1))

    return clean_text


def get_speaker_names(text, possible_characters):
    """Return every character named in one shared dialogue cue.

    English scripts often use labels such as ``MARY & BOLKONSKY``. Both
    people are speaking, so both DCA assignments must appear together.
    """
    # Read names only from the start of a printed cue label.  Searching the
    # whole dialogue line causes false combinations such as
    # ``HENRI. ... (to JERRY & ADAM ...)`` and makes ENSEMBLE MEN also match
    # the shorter template name ENSEMBLE.  A real shared label is a compact
    # prefix: ``MILO/JERRY/HENRI/LISE.``, ``JERRY AND GUESTS.``, or
    # ``HENRI, ADAM, JERRY, & DUTOIS.``.
    clean_text = normalise(text)
    candidates = sorted(possible_characters, key=len, reverse=True)
    combined_names = []
    cursor = 0

    while cursor < len(clean_text):
        while cursor < len(clean_text) and clean_text[cursor].isspace():
            cursor += 1

        matched_name = next(
            (
                character
                for character in candidates
                if clean_text.startswith(character, cursor)
                and (
                    cursor + len(character) == len(clean_text)
                    or not clean_text[cursor + len(character)].isalnum()
                )
            ),
            None,
        )
        if not matched_name:
            break

        combined_names.append(matched_name)
        cursor += len(matched_name)

        # A dot, colon, or Chinese sentence stop ends the speaker label.
        # The punctuation may be part of abbreviations in a name (MR. Z),
        # so test longer template names first before reaching this point.
        while cursor < len(clean_text) and clean_text[cursor].isspace():
            cursor += 1
        if cursor >= len(clean_text) or clean_text[cursor] in ".:：。":
            return combined_names

        # One name can be joined to the next by punctuation, by the word
        # AND, or by a combination such as ``, & DUTOIS``.
        if clean_text[cursor] in ",/&＋+、/／;；":
            cursor += 1
            while cursor < len(clean_text) and clean_text[cursor].isspace():
                cursor += 1
            if clean_text.startswith("and ", cursor):
                cursor += 4
            elif cursor < len(clean_text) and clean_text[cursor] in "&＋+":
                cursor += 1
        elif (
            clean_text.startswith("and", cursor)
            and (cursor + 3 == len(clean_text)
                 or clean_text[cursor + 3].isspace())
        ):
            cursor += 3
        else:
            break

    if len(combined_names) >= 2:
        return combined_names

    speaker_name = get_speaker_name(text, possible_characters)
    return [speaker_name] if speaker_name else []

def read_sheet_rows(worksheet):
    header_row = None
    headers = []

    for cells in worksheet.iter_rows():
        possible_headers = [
            normalise(cell.value) if cell.value is not None else ""
            for cell in cells
        ]

        if "dca state" in possible_headers:
            header_row = cells[0].row
            headers = possible_headers
            break

    if header_row is None:
        return []

    rows = []

    for row in worksheet.iter_rows(
        min_row=header_row + 1,
        values_only=True,
    ):
        row_data = {}

        for index, value in enumerate(row):
            if index < len(headers) and headers[index]:
                row_data[headers[index]] = value

        if any(value is not None for value in row):
            rows.append(row_data)

    return rows


def split_aliases(value):
    if value is None:
        return []

    return [
        normalise(alias)
        for alias in re.split(r"[,，;；|]", str(value))
        if alias.strip()
    ]


def split_character_cell(value):
    """Read one horizontal DCA cell, including names and [aliases]."""
    if value is None:
        return []

    names = []

    for line in str(value).splitlines():
        line = line.strip()

        if not line:
            continue

        alias_match = re.match(r"^(.*?)\s*\[([^\]]+)\]\s*$", line)

        if alias_match:
            character = alias_match.group(1).strip()
            aliases = alias_match.group(2)
        else:
            character = line
            aliases = ""

        if character:
            names.append(normalise(character))

        names.extend(split_aliases(aliases))

    return names


def add_assignment(assignments, state_key, character, dca):
    """Keep every DCA when the same cue intentionally uses more than one."""
    state_assignments = assignments.setdefault(state_key, {})
    existing = state_assignments.get(character, [])

    if not isinstance(existing, list):
        existing = [existing]

    if dca not in existing:
        existing.append(dca)

    state_assignments[character] = existing


def display_dca(dca):
    if not isinstance(dca, list):
        return str(dca)

    # A shared cue should read naturally as 3/4 rather than following the
    # order in which the two speaker names happen to appear on the PDF page.
    ordered = sorted(
        dict.fromkeys(str(value) for value in dca),
        key=lambda value: (
            0,
            int(value),
        ) if value.isdigit() else (1, value),
    )
    return "/".join(ordered)


def load_template(filename):
    workbook = load_workbook(filename, data_only=True, read_only=True)

    if "DCA States" not in workbook.sheetnames:
        workbook.close()
        raise ValueError(
            'The Excel file needs a sheet named "DCA States".'
        )

    states_sheet = workbook["DCA States"]
    state_rows = read_sheet_rows(states_sheet)
    states = []
    assignments = {}

    for row in state_rows:
        state_name = str(row.get("dca state", "") or "").strip()
        # New template names:
        # Start Line Character / Start Line Text / State Start Position.
        # Old names remain supported for existing templates.
        cue_speaker = str(
            row.get(
                "start line character",
                row.get(
                    "start cue character",
                    row.get("start cue speaker", ""),
                ),
            ) or ""
        ).strip()

        cue_text = str(
            row.get(
                "start line text",
                row.get("start cue text", ""),
            ) or ""
        ).strip()

        start_position = str(
            row.get(
                "state start position",
                row.get("start position", "after"),
            ) or "after"
        ).strip().lower()
        # "Script Page Hint" means the number printed on the script page,
        # not necessarily the PDF's internal page number. Keep "Page Hint"
        # as a fallback so existing templates continue to work.
        page_hint = row.get(
            "script page hint",
            row.get("page hint"),
        )

        if state_name and cue_text:
            states.append({
                "name": state_name,
                "key": normalise(state_name),
                "cue": cue_match_key(cue_text),
                # Optional. When provided, the cue must be spoken by this
                # character, which removes ambiguity when the same line is
                # sung or spoken by more than one person.
                "cue_speaker": normalise(cue_speaker),
                "position": start_position,
                "page_hint": str(page_hint).strip()
                if page_hint is not None else "",
            })

    if "Assignments" in workbook.sheetnames:
        # Keeps compatibility with the original vertical template.
        assignments_sheet = workbook["Assignments"]

        for row in read_sheet_rows(assignments_sheet):
            state_name = str(row.get("dca state", "") or "").strip()
            character = str(row.get("character", "") or "").strip()
            dca = str(row.get("dca", "") or "").strip()

            if state_name and character and dca:
                state_key = normalise(state_name)
                character_names = [normalise(character)]
                character_names.extend(
                    split_aliases(row.get("aliases", ""))
                )

                for name in character_names:
                    add_assignment(assignments, state_key, name, dca)
    else:
        # Reads the new horizontal template: DCA 1, DCA 2, etc.
        for row in state_rows:
            state_name = str(row.get("dca state", "") or "").strip()

            if not state_name:
                continue

            state_key = normalise(state_name)

            for header, cell_value in row.items():
                dca_match = re.fullmatch(r"dca\s*(\d+)", header)

                if not dca_match:
                    continue

                dca = dca_match.group(1)

                for character in split_character_cell(cell_value):
                    add_assignment(assignments, state_key, character, dca)

    workbook.close()
    return states, assignments



def is_italic(span):
    return bool(span["flags"] & 2)


def cue_speaker_matches(state, speaker_names):
    """Return true if a state has no speaker requirement, or it matches."""
    required_speaker = state.get("cue_speaker", "")

    if not required_speaker:
        return True

    if not speaker_names:
        return False

    required_key = speaker_match_key(required_speaker)
    required_base_key = speaker_base_key(required_speaker)

    return any(
        speaker_match_key(name) == required_key
        or speaker_base_key(name) == required_base_key
        for name in speaker_names
    )


def get_matching_state(states, text, page_hints, speaker_names=None):
    if isinstance(page_hints, (str, int)):
        page_hints = {str(page_hints)}
    else:
        page_hints = {str(hint) for hint in page_hints}

    text_key = cue_match_key(text)
    cue_matches = [
        state for state in states
        if state["cue"] in text_key
    ]

    # Embedded fonts can make a title unreadable to the PDF text layer while
    # preserving its leading cue code (for example M0 or M1). Use that code
    # only when the workbook also supplies a matching page hint. This recovers
    # the real in-script cue while reducing the risk from contents-page lists.
    if not cue_matches:
        text_identifier = cue_identifier(text)
        if text_identifier:
            cue_matches = [
                state for state in states
                if state.get("page_hint") in page_hints
                and cue_identifier(state.get("cue", "")) == text_identifier
            ]

    # If the template specifies who says the cue, keep only the state whose
    # speaker matches the script's current speaker label. States with a blank
    # Start Cue Speaker retain the original cue-text-only behaviour.
    cue_matches = [
        state for state in cue_matches
        if cue_speaker_matches(state, speaker_names)
    ]

    # A Script Page Hint is an explicit safety boundary. A cue listed in a contents
    # page, song list, or other reference material must not accidentally
    # activate its DCA State before the real script page.
    exact_page_matches = [
        state for state in cue_matches
        if state["page_hint"] in page_hints
    ]

    if exact_page_matches:
        cue_matches = exact_page_matches
    else:
        # States without a Page Hint remain flexible, which is useful for
        # templates where the source PDF has unpredictable pagination.
        cue_matches = [
            state for state in cue_matches
            if not state["page_hint"]
        ]

    if len(cue_matches) == 1:
        return cue_matches[0]

    return None


def find_page_hints(page, pdf_page_number, page_text=None):
    """Return the PDF index plus printed script-page numbers, when available.

    Theatre scripts commonly include cover sheets or contents pages, meaning
    the visible page number can differ from the PDF page index. Both remain
    safe, strict Script Page Hint choices. The PDF index remains as a
    compatibility fallback for templates that do not use printed pages.
    """
    hints = {str(pdf_page_number)}
    lower_page_area = page.rect.height * 0.75

    page_text = page_text or page.get_text("dict")

    for block in page_text["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            for span in line["spans"]:
                value = str(span["text"]).strip()

                if (
                    value.isdigit()
                    and span["bbox"][1] >= lower_page_area
                ):
                    hints.add(value)

    return hints


def load_ocr_pages(ocr_json_file, document):
    """Load Vision OCR lines exported by the Mac app.

    The OCR file has one list item per PDF page. Each recognised line keeps
    its original PDF-coordinate bounding box, so the normal marker can still
    place DCA numbers beside the correct printed line.
    """
    with open(ocr_json_file, encoding="utf-8") as file:
        raw_pages = json.load(file)

    if not isinstance(raw_pages, list):
        raise ValueError("OCR data must contain a list of PDF pages.")
    if len(raw_pages) != len(document):
        raise ValueError(
            "OCR data does not match this PDF. Please choose the same PDF "
            "again and rerun OCR."
        )

    pages = []
    for raw_page in raw_pages:
        raw_lines = raw_page.get("lines", []) if isinstance(raw_page, dict) else []
        lines = []
        for raw_line in raw_lines:
            text = str(raw_line.get("text", "")).strip()
            bbox = raw_line.get("bbox", [])
            if not text or not isinstance(bbox, list) or len(bbox) != 4:
                continue
            try:
                x0, y0, width, height = (float(value) for value in bbox)
            except (TypeError, ValueError):
                continue
            if width <= 0 or height <= 0:
                continue
            line_bbox = (x0, y0, x0 + width, y0 + height)
            lines.append(
                {
                    "bbox": line_bbox,
                    "spans": [
                        {
                            "text": text,
                            "bbox": line_bbox,
                            "size": max(8, height * 0.82),
                            "flags": 0,
                        }
                    ],
                }
            )
        pages.append({"blocks": [{"lines": lines}]})
    return pages

def build_legend_text(state, assignments):
    state_assignments = assignments.get(state["key"], {})

    legend_items = sorted(
        state_assignments.items(),
        key=lambda item: (
            int(item[1][0])
            if isinstance(item[1], list) and item[1][0].isdigit()
            else int(item[1])
            if str(item[1]).isdigit()
            else 999
        ),
    )
    lines = [state["name"]]

    for character, dca in legend_items:
        lines.append(f"{display_dca(dca)}: {character}")

    return "\n".join(lines)


def save_document_atomically(document, output_file):
    """Save a complete PDF before replacing an existing marked output.

    Preview may still need an already-open PDF to be closed and reopened, but
    presenting the finished file in one replacement event avoids a transient
    missing or half-written output and preserves the previous PDF if saving
    or validation fails.
    """
    output_directory = os.path.dirname(os.path.abspath(output_file))
    output_name = os.path.basename(output_file)
    page_count = len(document)
    descriptor, temporary_output = tempfile.mkstemp(
        prefix=f".{output_name}.",
        suffix=".tmp.pdf",
        dir=output_directory,
    )
    os.close(descriptor)

    try:
        os.remove(temporary_output)
        document.save(
            temporary_output,
            garbage=4,
            clean=True,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
        )
        document.close()

        saved_document = fitz.open(temporary_output)
        try:
            if len(saved_document) != page_count:
                raise RuntimeError(
                    "The replacement PDF did not preserve every page."
                )
        finally:
            saved_document.close()

        os.replace(temporary_output, output_file)
    finally:
        if not document.is_closed:
            document.close()
        if os.path.exists(temporary_output):
            os.remove(temporary_output)


def mark_pdf(
    states,
    assignments,
    pdf_file,
    output_file,
    editable=False,
    first_appearance=False,
    legend_only=False,
    legend_overrides=None,
    legend_style=None,
    number_style=None,
    state_style=None,
    start_page=None,
    end_page=None,
    ocr_json_file=None,
):
    document = fitz.open(pdf_file)
    ocr_pages = load_ocr_pages(ocr_json_file, document) if ocr_json_file else None
    current_state = None
    marked_count = 0
    unmatched_names = []
    activated_states = set()
    marked_speakers = set()
    marked_cue_lines = set()
    number_style = number_style or {}
    state_style = state_style or {}

    number_colour = number_style.get(
        "colour",
        NUMBER_COLOUR,
    )
    number_scale = number_style.get(
        "scale",
        NUMBER_SCALE,
    )
    number_font = number_style.get(
        "font_name",
        "helv",
    )
    # The label ends a fixed distance before the speaker name. Long labels
    # therefore grow left into the gutter instead of across the script text.
    number_gap = number_style.get("gap", 16)
    number_vertical_offset = number_style.get("vertical_offset", 0)
    state_colour = state_style.get(
        "colour",
        STATE_COLOUR,
    )
    state_font_name = state_style.get(
        "font_name",
        "heiti",
    )
    state_font_file = state_style.get(
        "font_file",
        CHINESE_FONT_FILE,
    )
    state_names = {state["key"]: state["name"] for state in states}
    all_template_characters = {
        character
        for state_assignments in assignments.values()
        for character in state_assignments
    }
    # A speaker name and its dialogue can occupy separate PDF lines. Keep the
    # most recent real speaker label so Start Cue Speaker still works there.
    current_cue_speakers = []

    for page_number, page in enumerate(document, start=1):
        # The selected page range is a strict export boundary.  We still
        # inspect pages before a selected range so the active DCA State can
        # be established, but once the end page has been reached there is
        # nothing later to mark.  Breaking here guarantees every following
        # PDF page is copied without any DCA numbers, state labels, headers,
        # footers, or editable annotations.
        if end_page is not None and page_number > end_page:
            break

        page_is_selected = (
            (start_page is None or page_number >= start_page)
            and (end_page is None or page_number <= end_page)
        )
        page_text = (
            ocr_pages[page_number - 1]
            if ocr_pages is not None
            else page.get_text("dict")
        )
        page_hint_values = find_page_hints(
            page, page_number, page_text=page_text
        )
        # PDF extraction can split one printed line into separate fragments.
        # For example: ``MARY &`` and ``BOLKONSKY`` may share the same
        # baseline but arrive as two independent lines. Keep a combined view
        # solely for speaker recognition.
        physical_lines = [
            line
            for block in page_text["blocks"]
            if "lines" in block
            for line in block["lines"]
        ]
        visual_line_texts = {}
        visual_row_left_edges = {}

        for physical_line in physical_lines:
            row_y = physical_line["bbox"][1]
            same_row = [
                candidate
                for candidate in physical_lines
                if abs(candidate["bbox"][1] - row_y) < 0.75
            ]
            same_row.sort(key=lambda candidate: candidate["bbox"][0])

            # Most PDFs split one printed row into nearby fragments (speaker
            # name + dialogue), which should remain one visual cue. A duet
            # may instead place two independent speaker columns on the same
            # row: MILO. on the left and HENRI. on the right. A large empty
            # horizontal gap means those are separate cue groups and both
            # labels must be eligible for a DCA number.
            cue_groups = []
            current_group = []
            previous_right = None
            for candidate in same_row:
                candidate_left = candidate["bbox"][0]
                if (
                    current_group
                    and previous_right is not None
                    and candidate_left - previous_right > 60
                ):
                    cue_groups.append(current_group)
                    current_group = []
                current_group.append(candidate)
                previous_right = candidate["bbox"][2]
            if current_group:
                cue_groups.append(current_group)

            cue_group = next(
                group for group in cue_groups if physical_line in group
            )
            visual_line_texts[id(physical_line)] = "".join(
                "".join(span["text"] for span in candidate["spans"])
                for candidate in cue_group
            )
            # Only the leftmost fragment within its own cue group can receive
            # a number. With a two-column duet, each column has its own
            # group and therefore its own leftmost speaker label.
            visual_row_left_edges[id(physical_line)] = min(
                candidate["bbox"][0] for candidate in cue_group
            )
        # This is the state already active as the page begins. On the first
        # page it may be unknown until the first cue has been found.
        page_start_state = current_state

        for block in page_text["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = "".join(
                    span["text"] for span in line["spans"]
                )
                speaker_line_text = visual_line_texts.get(
                    id(line),
                    line_text,
                )
                is_visual_row_anchor = abs(
                    line["bbox"][0]
                    - visual_row_left_edges.get(
                        id(line), line["bbox"][0]
                    )
                ) < 0.75
                line_clean_text = normalise(line_text)
                line_speaker_names = get_speaker_names(
                    speaker_line_text,
                    all_template_characters,
                )

                if (
                    line_speaker_names
                    and all(
                        name in all_template_characters
                        for name in line_speaker_names
                    )
                    and looks_like_speaker_label(
                        speaker_line_text,
                        line_speaker_names[0],
                    )
                ):
                    current_cue_speakers = line_speaker_names

                line_next_state = get_matching_state(
                    states,
                    line_clean_text,
                    page_hint_values,
                    current_cue_speakers,
                )
                state_anchor_index = next(
                    (
                        index
                        for index, candidate in enumerate(line["spans"])
                        if normalise(candidate["text"])
                    ),
                    None,
                )

                for span_index, span in enumerate(line["spans"]):
                    text = span["text"].strip()
                    clean_text = normalise(text)
                    # A state cue may be split into several PDF text spans.
                    # Match the complete printed line, then act only once.
                    next_state = (
                        line_next_state
                        if span_index == state_anchor_index
                        else None
                    )

                    mapping_state = current_state
                    possible_characters = assignments.get(
                        mapping_state or "", {}
                    )
                    # Some PDFs split one speaker name across several spans
                    # (for example 本丢 / · / 彼拉多). Match the complete line.
                    speaker_names = get_speaker_names(
                        speaker_line_text, possible_characters
                    )
                    speaker_name = speaker_names[0] if speaker_names else ""

                    # An "After" cue can occur inside the first line spoken
                    # in the new DCA State. In that case mark the speaker from
                    # the new state, while still placing the state label after
                    # the cue line.
                    if (
                        line_next_state
                        and line_next_state["position"] == "after"
                    ):
                        candidate_state = line_next_state["key"]
                        candidate_characters = assignments.get(
                            candidate_state, {}
                        )
                        candidate_speakers = get_speaker_names(
                            speaker_line_text, candidate_characters
                        )

                        if (
                            candidate_speakers
                            and all(
                                name in candidate_characters
                                for name in candidate_speakers
                            )
                            and looks_like_speaker_label(
                                speaker_line_text,
                                candidate_speakers[0],
                            )
                        ):
                            mapping_state = candidate_state
                            possible_characters = candidate_characters
                            speaker_names = candidate_speakers
                            speaker_name = speaker_names[0]

                    if not clean_text:
                        continue

                    if next_state and page_is_selected:
                        cue_box = fitz.Rect(line["bbox"])

                        if legend_only:
                            if legend_style is None:
                                legend_style = {}

                            legend_position = legend_style.get(
                                "position", "Left Gutter"
                            )

                            # Legends always live on the left. "Near Script"
                            # keeps the list near the script boundary, while
                            # "Left Gutter" starts it at the page edge.
                            legend_right = max(95, cue_box.x0 - 8)
                            legend_left = 18
                            if legend_position == "Near Script":
                                legend_left = max(18, legend_right - 120)

                            legend_box = fitz.Rect(
                                legend_left,
                                cue_box.y1 + 4,
                                legend_right,
                                cue_box.y1 + 180,
                            )

                            legend_text = build_legend_text(
                                next_state, assignments
                            )

                            if legend_overrides:
                                legend_text = legend_overrides.get(
                                    next_state["key"],
                                    legend_text,
                                )

                            legend_colour = legend_style.get(
                                "colour",
                                STATE_COLOUR,
                            )
                            legend_size = legend_style.get(
                                "size",
                                8,
                            )
                            legend_font = legend_style.get(
                                "font_name",
                                "heiti",
                            )
                            legend_font_file = legend_style.get(
                                "font_file",
                                CHINESE_FONT_FILE,
                            )

                            # Built-in Times / Helvetica / Courier fonts do
                            # not contain Chinese glyphs. Keep the selected
                            # colour and size, but safely fall back for text.
                            if contains_cjk(legend_text):
                                legend_font = "heiti"
                                legend_font_file = CHINESE_FONT_FILE

                            legend_annotation = page.add_freetext_annot(
                                legend_box,
                                legend_text,
                                fontsize=legend_size,
                                fontname=legend_font,
                                text_color=legend_colour,
                                fill_color=None,
                                align=0,
                            )

                            legend_annotation.set_border(width=0)
                            legend_annotation.update()

                        else:
                            state_font_size = state_style.get(
                                "size",
                                max(
                                    10,
                                    span["size"] * number_scale,
                                ),
                            )

                            draw_state_font_name = state_font_name
                            draw_state_font_file = state_font_file

                            if contains_cjk(next_state["name"]):
                                draw_state_font_name = "heiti"
                                draw_state_font_file = CHINESE_FONT_FILE

                            if draw_state_font_file:
                                state_font = fitz.Font(
                                    fontfile=draw_state_font_file
                                )
                            else:
                                state_font = fitz.Font(
                                    fontname=draw_state_font_name
                                )

                            state_position = state_style.get(
                                "position", "Left Gutter"
                            )
                            # The placement follows the meaning of the
                            # template's Start position.  A Before state is
                            # shown beside the cue that starts it; an After
                            # state is shown below the cue that finishes the
                            # previous state.
                            state_placement = (
                                "Below Cue"
                                if next_state["position"] == "after"
                                else "Beside Cue"
                            )
                            # A DCA State can begin on the same printed line
                            # as a character cue.  In that situation the blue
                            # state label and pink DCA number would compete for
                            # the same gutter.  Move only the state label above
                            # the cue automatically, keeping both readable.
                            state_line_speakers = get_speaker_names(
                                speaker_line_text,
                                assignments.get(next_state["key"], {}),
                            )
                            state_shares_cue_line = bool(
                                state_line_speakers
                                and looks_like_speaker_label(
                                    speaker_line_text,
                                    state_line_speakers[0],
                                )
                            )
                            state_width = state_font.text_length(
                                next_state["name"], fontsize=state_font_size
                            )

                            if state_position == "Left Gutter":
                                # Keep the state in the left gutter, but
                                # right-align its *end* before the pink DCA
                                # number column.  This matters for longer
                                # labels such as "Scene 8": a fixed left
                                # starting point lets the label grow right
                                # into the number.  A fixed right edge keeps
                                # both markings readable on every script.
                                # Do not follow the cue's x-position here.
                                # A first cue is often a centred scene title,
                                # which would pull its state label into the
                                # middle of the page. The fixed right edge
                                # makes Left Gutter a real, stable column.
                                state_right = 82
                                state_x = max(8, state_right - state_width)
                            elif state_position == "Near Script":
                                # Retained for old templates that explicitly
                                # want the label to follow each cue's indent.
                                state_x = max(
                                    12,
                                    cue_box.x0 - number_gap - state_width,
                                )
                            else:
                                # Far from Script is a visibly separate,
                                # far-left gutter.
                                state_x = 12

                            if state_position == "Left Gutter":
                                # A label in the far-left gutter must not
                                # share a dialogue row. Long state names can
                                # otherwise run into a speaker name even when
                                # their x-position is safely in the gutter.
                                state_y = (
                                    cue_box.y1 + state_font_size + 4
                                    if next_state["position"] == "after"
                                    else cue_box.y0 - 4
                                )
                            elif (
                                state_placement == "Beside Cue"
                                and not state_shares_cue_line
                            ):
                                state_y = cue_box.y1 - 2
                            elif state_placement == "Below Cue":
                                state_y = cue_box.y1 + state_font_size + 4
                            else:
                                # The default keeps the DCA State label above
                                # the cue line, irrespective of whether its
                                # assignment begins Before or After that cue.
                                state_y = cue_box.y0 - 4

                            if editable:
                                # Use a FreeText annotation so the DCA State
                                # label can be changed, moved, or removed in a
                                # PDF editor after export.
                                state_box = fitz.Rect(
                                    state_x - 3,
                                    state_y - state_font_size - 4,
                                    state_x + state_width + 5,
                                    state_y + 4,
                                )
                                annotation = page.add_freetext_annot(
                                    state_box,
                                    next_state["name"],
                                    fontsize=state_font_size,
                                    fontname=draw_state_font_name,
                                    text_color=state_colour,
                                    fill_color=None,
                                    align=0,
                                )
                                annotation.set_border(width=0)
                                annotation.update()
                            else:
                                page.insert_text(
                                    (state_x, state_y),
                                    next_state["name"],
                                    fontsize=state_font_size,
                                    fontname=draw_state_font_name,
                                    fontfile=draw_state_font_file,
                                    color=state_colour,
                                )
                            
                    if next_state and next_state["position"] == "before":
                        current_state = next_state["key"]
                        if page_start_state is None:
                            page_start_state = current_state
                        activated_states.add(current_state)
                        marked_speakers.clear()

                    if (
                        mapping_state
                        and page_is_selected
                        and not legend_only
                        and not is_italic(span)
                        and speaker_names
                        and is_visual_row_anchor
                        and all(
                            name in assignments.get(mapping_state, {})
                            for name in speaker_names
                        )
                        and looks_like_speaker_label(
                            speaker_line_text, speaker_name
                        )
                        and (
                            page_number,
                            round(line["bbox"][1], 1),
                            round(line["bbox"][0], 1),
                        ) not in marked_cue_lines
                        and (
                            not first_appearance
                            or any(
                                name not in marked_speakers
                                for name in speaker_names
                            )
                        )
                    ):
                        dca_values = []
                        for name in speaker_names:
                            values = assignments[mapping_state][name]
                            if not isinstance(values, list):
                                values = [values]
                            for value in values:
                                if value not in dca_values:
                                    dca_values.append(value)
                        dca = display_dca(dca_values)
                        name_box = fitz.Rect(span["bbox"])

                        number_right = max(36, name_box.x0 - number_gap)
                        number_font_size = max(
                            12, span["size"] * number_scale
                        )
                        number_width = fitz.Font(
                            fontname=number_font
                        ).text_length(dca, fontsize=number_font_size)
                        number_left = max(8, number_right - number_width)

                        if editable:
                            annotation_width = max(56, number_width + 10)

                            number_box = fitz.Rect(
                                max(8, number_right - annotation_width),
                                name_box.y0 + number_vertical_offset,
                                number_right,
                                name_box.y1 + 4 + number_vertical_offset,
                            )

                            annotation = page.add_freetext_annot(
                                number_box,
                                dca,
                                fontsize=number_font_size,
                                fontname=number_font,
                                text_color=number_colour,
                                fill_color=None,
                                align=2,
                            )

                        else:
                            page.insert_text(
                                (number_left, name_box.y1 - 2 + number_vertical_offset),
                                dca,
                                fontsize=number_font_size,
                                fontname=number_font,
                                color=number_colour,
                            )

                        marked_count += 1
                        marked_speakers.update(speaker_names)
                        marked_cue_lines.add(
                            (
                                page_number,
                                round(line["bbox"][1], 1),
                                round(line["bbox"][0], 1),
                            )
                        )

                    elif (
                        page_is_selected
                        and current_state
                        and speaker_name != clean_text
                        and not starts_with_stage_direction(
                            speaker_line_text
                        )
                        and (
                            page_number,
                            round(line["bbox"][1], 1),
                            round(line["bbox"][0], 1),
                        ) not in marked_cue_lines
                    ):
                        unmatched_names.append(
                            (page_number, current_state, text)
                        )

                    if next_state and next_state["position"] != "before":
                        current_state = next_state["key"]
                        if page_start_state is None:
                            page_start_state = current_state
                        activated_states.add(current_state)
                        marked_speakers.clear()

        if (
            page_is_selected
            and state_style.get("page_header_footer", False)
        ):
            header_state = page_start_state or current_state
            footer_state = current_state or header_state

            page_state_text_colour = state_style.get(
                "page_header_footer_text_colour",
                state_colour,
            )
            page_state_border_colour = state_style.get(
                "page_header_footer_border_colour",
                page_state_text_colour,
            )
            draw_state_font_name = state_style.get(
                "page_header_footer_font_name",
                state_font_name,
            )
            draw_state_font_file = state_style.get(
                "page_header_footer_font_file",
                state_font_file,
            )
            state_font_size = state_style.get(
                "page_header_footer_size",
                state_style.get("size", 12),
            )

            # Use the Chinese-capable font whenever a state label contains
            # Chinese text, even if the user chose an English font.
            state_text = " ".join(
                name
                for name in (
                    state_names.get(header_state, ""),
                    state_names.get(footer_state, ""),
                )
                if name
            )
            if contains_cjk(state_text):
                draw_state_font_name = "heiti"
                draw_state_font_file = CHINESE_FONT_FILE

            # Page header/footer labels are deliberately more prominent than
            # an in-script state-change label: bold text plus a thin box.
            if not draw_state_font_file:
                bold_font_map = {
                    "helv": "hebo",
                    "tiro": "tibo",
                    "cour": "cobo",
                }
                draw_state_font_name = bold_font_map.get(
                    draw_state_font_name,
                    "hebo",
                )

            if draw_state_font_file:
                footer_font = fitz.Font(fontfile=draw_state_font_file)
            else:
                footer_font = fitz.Font(fontname=draw_state_font_name)

            footer_label = state_names.get(footer_state, "")
            footer_width = footer_font.text_length(
                footer_label,
                fontsize=state_font_size,
            )
            # Keep 90 points clear at the far right for the PDF's own page
            # number, while still placing the DCA State in the lower-right.
            footer_x = max(
                36,
                page.rect.width - 90 - footer_width,
            )

            for page_label, point in (
                (state_names.get(header_state, ""), (36, 24)),
                (
                    footer_label,
                    (footer_x, page.rect.height - 22),
                ),
            ):
                if page_label:
                    label_width = footer_font.text_length(
                        page_label,
                        fontsize=state_font_size,
                    )
                    label_box = fitz.Rect(
                        point[0] - 4,
                        point[1] - state_font_size - 4,
                        point[0] + label_width + 4,
                        point[1] + 4,
                    )
                    if editable:
                        # Keep the text and border in one FreeText annotation
                        # so they move, resize, and delete together in a PDF
                        # editor.
                        if (
                            page_state_border_colour
                            == page_state_text_colour
                        ):
                            # Keep the long-standing plain FreeText output
                            # when both colours match. This preserves today's
                            # default appearance and older CLI behaviour.
                            annotation = page.add_freetext_annot(
                                label_box,
                                page_label,
                                fontsize=state_font_size,
                                fontname=draw_state_font_name,
                                text_color=page_state_text_colour,
                                fill_color=None,
                                align=1,
                            )
                            annotation.set_border(width=0.8)
                            annotation.update()
                        else:
                            # A plain PDF FreeText annotation exposes only one
                            # colour for its text and border. Rich text keeps
                            # the selected text colour in CSS while /DA holds
                            # the border colour, still as one movable object.
                            text_style = (
                                "font-family: "
                                f"{rich_text_font_family(draw_state_font_name, draw_state_font_file)}; "
                                f"font-size: {state_font_size:g}pt; "
                                "font-weight: bold; "
                                f"color: {css_colour(page_state_text_colour)}; "
                                "text-align: center; "
                                "margin: 0; padding: 0; line-height: 1;"
                            )
                            escaped_label = html.escape(page_label)
                            annotation = page.add_freetext_annot(
                                label_box,
                                escaped_label,
                                richtext=True,
                                style=text_style,
                                border_width=0.8,
                                fill_color=None,
                                align=1,
                            )
                            rich_content = (
                                '<?xml version="1.0"?>'
                                '<body xmlns="http://www.w3.org/1999/xhtml" '
                                'xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" '
                                'xfa:contentType="text/html" '
                                'xfa:APIVersion="Acrobat:8.0.0" '
                                'xfa:spec="2.4">'
                                f"{escaped_label}</body>"
                            )
                            # PyMuPDF 1.28 omits the closing body tag in its
                            # generated /RC value. Replace it with valid XHTML
                            # so cleaning or regenerating the PDF cannot drop
                            # the font glyphs.
                            document.xref_set_key(
                                annotation.xref,
                                "RC",
                                fitz.get_pdf_str(rich_content),
                            )
                            annotation.update(
                                text_color=page_state_border_colour,
                            )
                            # Retain a normal searchable /Contents value for
                            # Preview and other PDF editors. Set it only after
                            # generating the appearance: set_info() removes
                            # rich /RC data, while setting Contents before the
                            # update makes some renderers lose the glyphs.
                            document.xref_set_key(
                                annotation.xref,
                                "Contents",
                                fitz.get_pdf_str(page_label),
                            )
                    else:
                        page.draw_rect(
                            label_box,
                            color=page_state_border_colour,
                            width=0.8,
                            overlay=True,
                        )
                        page.insert_text(
                            point,
                            page_label,
                            fontsize=state_font_size,
                            fontname=draw_state_font_name,
                            fontfile=draw_state_font_file,
                            color=page_state_text_colour,
                        )
                        # Some Chinese system fonts do not expose a separate
                        # bold face to PDF output. A subtle second pass gives
                        # the page header/footer a reliably stronger weight.
                        page.insert_text(
                            (point[0] + 0.35, point[1]),
                            page_label,
                            fontsize=state_font_size,
                            fontname=draw_state_font_name,
                            fontfile=draw_state_font_file,
                            color=page_state_text_colour,
                        )

    # Rebuild and compress the finished PDF, then atomically place the complete
    # file at its destination. This keeps the previous output intact if saving
    # fails and gives PDF viewers one replacement event instead of a delete
    # followed by a second file appearing at the same path.
    save_document_atomically(document, output_file)

    return marked_count, unmatched_names, activated_states


def write_review_report(
    states, marked_count, unmatched_names, activated_states, report_file
):
    with open(report_file, "w", encoding="utf-8") as file:
        file.write("DCA Script Marker - Review Report\n")
        file.write("=" * 40 + "\n\n")
        file.write(f"Marked character cues: {marked_count}\n\n")

        missing_states = [
            state["name"]
            for state in states
            if state["key"] not in activated_states
        ]

        if missing_states:
            file.write("DCA States whose start cue was not found:\n\n")

            for state_name in missing_states:
                file.write(f"- {state_name}\n")

            file.write("\n")

        if unmatched_names:
            file.write("Possible character names without a DCA assignment:\n\n")

            for page, state, name in unmatched_names:
                file.write(f"- Page {page} | {state} | {name}\n")
        else:
            file.write("No possible unmatched character names found.\n")


def run_marker(
    template_file,
    pdf_file,
    output_folder,
    editable=False,
    first_appearance=False,
    legend_only=False,
    legend_overrides=None,
    legend_style=None,
    number_style=None,
    state_style=None,
    start_page=None,
    end_page=None,
    ocr_json_file=None,
    output_mode="replace",
):
    original_name = os.path.splitext(
        os.path.basename(pdf_file)
    )[0]

    today = date.today().isoformat()

    output_file = os.path.join(
        output_folder,
        f"{original_name}_marked_{today}.pdf",
    )

    report_file = os.path.join(
        output_folder,
        f"{original_name}_review_{today}.txt",
    )

    if output_mode == "new":
        pdf_root, pdf_extension = os.path.splitext(output_file)
        report_root, report_extension = os.path.splitext(report_file)

        version = 2
        while os.path.exists(output_file):
            output_file = f"{pdf_root}_{version}{pdf_extension}"
            report_file = f"{report_root}_{version}{report_extension}"
            version += 1

    # Some Excel templates contain a data-validation extension that openpyxl
    # does not preserve when saving. This app only reads the workbook, so the
    # warning is harmless and should not obscure the user's completion message.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Data Validation extension is not supported.*",
            category=UserWarning,
        )
        states, assignments = load_template(template_file)
    marked_count, unmatched_names, activated_states = mark_pdf(
        states,
        assignments,
        pdf_file,
        output_file,
        editable,
        first_appearance,
        legend_only,
        legend_overrides,
        legend_style,
        number_style,
        state_style,
        start_page,
        end_page,
        ocr_json_file,
    )
    write_review_report(
        states, marked_count, unmatched_names, activated_states, report_file
    )

    return marked_count, output_file, report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a DCA-marked rehearsal script."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Report the bundled runtime versions and architecture, then exit",
    )
    parser.add_argument("--template", help="Path to the DCA Excel template")
    parser.add_argument("--script", help="Path to the script PDF")
    parser.add_argument("--output", help="Folder for the marked PDF")
    parser.add_argument(
        "--output-mode",
        choices=["replace", "new"],
        default="replace",
        help="Replace an existing marked PDF or create a new version",
    )
    parser.add_argument(
        "--ocr-json",
        help="Vision OCR data produced by the Mac app for a scanned PDF",
    )
    parser.add_argument(
        "--list-legends",
        action="store_true",
        help="Print DCA State legend text as JSON and exit",
    )
    parser.add_argument(
        "--legend-overrides-file",
        help="Path to a JSON file containing edited legend text",
    )
    parser.add_argument("--number-colour", help="DCA number colour: red, blue, black, or green")
    parser.add_argument("--number-scale", type=float, help="DCA number size scale")
    parser.add_argument("--number-font", help="DCA number font: Helvetica, Times, or Courier")
    parser.add_argument("--number-x", type=float, help="Legacy DCA number position")
    parser.add_argument(
        "--number-gap",
        type=float,
        help="Space between a DCA number and the speaker name",
    )
    parser.add_argument(
        "--number-y-offset",
        type=float,
        default=0,
        help="Move DCA numbers vertically in points; negative is up",
    )
    parser.add_argument("--state-colour", help="DCA state colour: red, blue, black, or green")
    parser.add_argument("--state-scale", type=float, help="DCA state size scale")
    parser.add_argument("--state-font", help="DCA state font: Helvetica, Times, or Courier")
    parser.add_argument(
        "--state-position",
        choices=["Left Gutter", "Far from Script", "Near Script"],
        default="Left Gutter",
        help="Position for the blue DCA State label",
    )
    parser.add_argument(
        "--state-placement",
        choices=["Above Cue", "Beside Cue", "Below Cue"],
        default="Beside Cue",
        help="Legacy setting; DCA State labels default beside their cue",
    )
    parser.add_argument(
        "--page-state-header-footer",
        action="store_true",
        help="Show the active DCA State at the top and bottom of each page",
    )
    parser.add_argument(
        "--page-state-text-colour",
        choices=["red", "blue", "black", "green"],
        help="Text colour for page header/footer DCA State labels",
    )
    parser.add_argument(
        "--page-state-scale",
        type=float,
        help="Text size scale for page header/footer DCA State labels",
    )
    parser.add_argument(
        "--page-state-font",
        choices=[
            "PingFang SC",
            "Chinese System",
            "Helvetica",
            "Times",
            "Courier",
        ],
        help="Text font for page header/footer DCA State labels",
    )
    parser.add_argument(
        "--page-state-border-colour",
        choices=["red", "blue", "black", "green"],
        help="Border colour for page header/footer DCA State labels",
    )
    parser.add_argument(
        "--legend-position",
        choices=["Left Gutter", "Near Script"],
        default="Left Gutter",
        help="Position for the DCA State Legend",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        help="First PDF page to mark (optional)",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        help="Last PDF page to mark (optional)",
    )
    parser.add_argument(
        "--style",
        default="Full Marking",
        choices=[
            "Full Marking",
            "Editable Full Marking",
            "First Appearance Only",
            "DCA State Legend",
        ],
        help="Marking style to use",
    )
    arguments = parser.parse_args()

    if arguments.self_test:
        print(json.dumps({
            "ok": True,
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "pymupdf": getattr(fitz, "VersionBind", "unknown"),
            "openpyxl": openpyxl.__version__,
            "frozen": bool(getattr(sys, "frozen", False)),
            "executable": os.path.realpath(sys.executable),
            "module_paths": {
                "pymupdf": os.path.realpath(fitz.__file__),
                "openpyxl": os.path.realpath(openpyxl.__file__),
            },
        }, ensure_ascii=False))
        raise SystemExit(0)

    if arguments.list_legends:
        if not arguments.template:
            parser.error("--template is required with --list-legends")
        # Excel may report an unsupported validation-extension warning. The
        # Mac app expects clean JSON here, so do not send that warning to it.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            states, assignments = load_template(arguments.template)
        legends = [
            {
                "key": state["key"],
                "name": state["name"],
                "text": build_legend_text(state, assignments),
            }
            for state in states
        ]
        print(json.dumps(legends, ensure_ascii=False))
        raise SystemExit(0)

    # With no command-line options, keep the original simple test behaviour.
    if not arguments.template:
        marked_count, output_file, report_file = run_marker(
            TEMPLATE_FILE, PDF_FILE, os.getcwd()
        )
    else:
        if not arguments.script or not arguments.output:
            parser.error("--template, --script, and --output must be used together")
        if arguments.start_page and arguments.start_page < 1:
            parser.error("--start-page must be 1 or greater")
        if arguments.end_page and arguments.end_page < 1:
            parser.error("--end-page must be 1 or greater")
        if (
            arguments.start_page
            and arguments.end_page
            and arguments.start_page > arguments.end_page
        ):
            parser.error("--start-page cannot be after --end-page")

        colour_map = {
            "red": (0.85, 0.0, 0.35),
            "blue": (0.0, 0.35, 0.75),
            "black": (0.0, 0.0, 0.0),
            "green": (0.0, 0.45, 0.25),
        }
        font_map = {
            "Helvetica": "helv",
            "Times": "tiro",
            "Courier": "cour",
        }
        number_style = {}
        state_style = {}

        if arguments.number_colour:
            number_style["colour"] = colour_map[arguments.number_colour]
        if arguments.number_scale:
            number_style["scale"] = arguments.number_scale
        if arguments.number_font:
            number_style["font_name"] = font_map[arguments.number_font]
        if arguments.number_gap is not None:
            number_style["gap"] = arguments.number_gap
        if arguments.number_y_offset is not None:
            number_style["vertical_offset"] = arguments.number_y_offset
        elif arguments.number_x is not None:
            # Older Mac UI versions send 72/60/36 for near/standard/far.
            number_style["gap"] = max(8, 76 - arguments.number_x)
        if arguments.state_colour:
            state_style["colour"] = colour_map[arguments.state_colour]
        if arguments.state_scale:
            state_style["size"] = 12 * arguments.state_scale
        # Keep the existing Chinese-capable font for DCA State labels. The
        # selected state font is used only when it can safely render the text.
        if arguments.state_font == "PingFang SC":
            state_style["font_name"] = "heiti"
            state_style["font_file"] = CHINESE_FONT_FILE
        elif arguments.state_font and arguments.state_font != "Chinese System":
            state_style["font_name"] = font_map[arguments.state_font]
            state_style["font_file"] = None
            state_style["font_name"] = font_map[arguments.state_font]
            state_style["font_file"] = None
        state_style["position"] = arguments.state_position
        state_style["placement"] = arguments.state_placement
        state_style["page_header_footer"] = (
            arguments.page_state_header_footer
        )
        if arguments.page_state_text_colour:
            state_style["page_header_footer_text_colour"] = colour_map[
                arguments.page_state_text_colour
            ]
        if arguments.page_state_scale:
            state_style["page_header_footer_size"] = (
                12 * arguments.page_state_scale
            )
        if arguments.page_state_font in {
            "PingFang SC",
            "Chinese System",
        }:
            state_style["page_header_footer_font_name"] = "heiti"
            state_style["page_header_footer_font_file"] = (
                CHINESE_FONT_FILE
            )
        elif arguments.page_state_font:
            state_style["page_header_footer_font_name"] = font_map[
                arguments.page_state_font
            ]
            state_style["page_header_footer_font_file"] = None
        if arguments.page_state_border_colour:
            state_style["page_header_footer_border_colour"] = colour_map[
                arguments.page_state_border_colour
            ]

        legend_overrides = None
        if arguments.legend_overrides_file:
            with open(arguments.legend_overrides_file, encoding="utf-8") as file:
                legend_overrides = json.load(file)

        legend_style = {
            "colour": state_style.get("colour", STATE_COLOUR),
            "size": 8 * (arguments.state_scale or 1.2),
            "font_name": state_style.get("font_name", "heiti"),
            "font_file": state_style.get("font_file", CHINESE_FONT_FILE),
            "position": arguments.legend_position,
        }

        marked_count, output_file, report_file = run_marker(
            arguments.template,
            arguments.script,
            arguments.output,
            editable=arguments.style == "Editable Full Marking",
            first_appearance=arguments.style == "First Appearance Only",
            legend_only=arguments.style == "DCA State Legend",
            legend_overrides=legend_overrides,
            legend_style=legend_style,
            number_style=number_style,
            state_style=state_style,
            start_page=arguments.start_page,
            end_page=arguments.end_page,
            ocr_json_file=arguments.ocr_json,
            output_mode=arguments.output_mode,
        )

    print(f"Finished! Marked {marked_count} cues.")
    print(f"PDF: {output_file}")
    print(f"Review report: {report_file}")
