from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import re

try:
    import pdfplumber
except ImportError as exc:
    raise ImportError(
        "Missing dependency 'pdfplumber'. Install it with: pip install pdfplumber"
    ) from exc

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None  # Optional fallback

# OCR is optional on purpose
try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pytesseract = None
    convert_from_path = None


class PDFUtilsError(Exception):
    """Base exception for PDF utility errors."""


class PDFTextNotFoundError(PDFUtilsError):
    """Raised when expected text is not found in the PDF."""


class PDFLabelNotFoundError(PDFUtilsError):
    """Raised when a label is not found in the PDF."""


class PDFTableNotFoundError(PDFUtilsError):
    """Raised when no table is found in the PDF."""


@dataclass(frozen=True)
class PDFWord:
    """Represents one word extracted from a PDF page."""

    text: str
    page_number: int
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass(frozen=True)
class MatchResult:
    """Represents a text match found inside the PDF."""

    text: str
    page_number: int
    context: str


@dataclass(frozen=True)
class LabelValueResult:
    """Represents a label/value pair found in a PDF."""

    label: str
    value: str
    page_number: int


def _ensure_file_exists(pdf_path: str | Path) -> Path:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if not path.is_file():
        raise PDFUtilsError(f"Path is not a file: {path}")
    return path


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_for_search(text: str, case_sensitive: bool = False) -> str:
    normalized = _normalize_spaces(text)
    return normalized if case_sensitive else normalized.lower()


def _safe_extract_text_pdfplumber(pdf_path: Path) -> list[str]:
    pages_text: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

    return pages_text


def _safe_extract_text_pypdf2(pdf_path: Path) -> list[str]:
    if PdfReader is None:
        raise ImportError("PyPDF2 is not installed. Install it with: pip install PyPDF2")

    reader = PdfReader(str(pdf_path))
    pages_text: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    return pages_text


def extract_text_by_page(
    pdf_path: str | Path,
    *,
    use_fallback_pypdf2: bool = True,
) -> list[str]:
    """
    Extract text from each page of a PDF.

    Returns:
        A list where each item contains the text of one page.
    """
    path = _ensure_file_exists(pdf_path)

    pages_text = _safe_extract_text_pdfplumber(path)

    if use_fallback_pypdf2 and all(not page.strip() for page in pages_text):
        try:
            pages_text = _safe_extract_text_pypdf2(path)
        except Exception:
            pass

    return pages_text


def extract_full_text(
    pdf_path: str | Path,
    *,
    separator: str = "\n",
    use_fallback_pypdf2: bool = True,
) -> str:
    """
    Extract the full text of the PDF as a single string.
    """
    pages_text = extract_text_by_page(
        pdf_path,
        use_fallback_pypdf2=use_fallback_pypdf2,
    )
    return separator.join(pages_text)


def get_page_count(pdf_path: str | Path) -> int:
    """
    Return the number of pages in the PDF.
    """
    path = _ensure_file_exists(pdf_path)

    with pdfplumber.open(path) as pdf:
        return len(pdf.pages)


def contains_text(
    pdf_path: str | Path,
    expected_text: str,
    *,
    case_sensitive: bool = False,
    normalize_spaces: bool = True,
) -> bool:
    """
    Check whether the PDF contains a given text.
    """
    full_text = extract_full_text(pdf_path)

    if normalize_spaces:
        full_text = _normalize_spaces(full_text)
        expected_text = _normalize_spaces(expected_text)

    haystack = full_text if case_sensitive else full_text.lower()
    needle = expected_text if case_sensitive else expected_text.lower()

    return needle in haystack


def assert_contains_text(
    pdf_path: str | Path,
    expected_text: str,
    *,
    case_sensitive: bool = False,
    normalize_spaces: bool = True,
) -> None:
    """
    Assert that the PDF contains the expected text.
    """
    if not contains_text(
        pdf_path,
        expected_text,
        case_sensitive=case_sensitive,
        normalize_spaces=normalize_spaces,
    ):
        raise PDFTextNotFoundError(
            f"Expected text not found in PDF: {expected_text!r}"
        )


def find_text_matches(
    pdf_path: str | Path,
    pattern: str,
    *,
    regex: bool = False,
    case_sensitive: bool = False,
    context_chars: int = 50,
) -> list[MatchResult]:
    """
    Search text matches across PDF pages.

    Args:
        pattern: Exact text or regex pattern.
        regex: If True, treat pattern as regex.
        case_sensitive: Whether search is case-sensitive.
        context_chars: Number of chars before/after the match.

    Returns:
        List of MatchResult.
    """
    results: list[MatchResult] = []
    pages_text = extract_text_by_page(pdf_path)

    flags = 0 if case_sensitive else re.IGNORECASE

    for page_index, page_text in enumerate(pages_text, start=1):
        if not page_text:
            continue

        if regex:
            for match in re.finditer(pattern, page_text, flags):
                start, end = match.span()
                context_start = max(0, start - context_chars)
                context_end = min(len(page_text), end + context_chars)
                results.append(
                    MatchResult(
                        text=match.group(0),
                        page_number=page_index,
                        context=page_text[context_start:context_end],
                    )
                )
        else:
            haystack = page_text if case_sensitive else page_text.lower()
            needle = pattern if case_sensitive else pattern.lower()

            start = 0
            while True:
                idx = haystack.find(needle, start)
                if idx == -1:
                    break
                end = idx + len(needle)
                context_start = max(0, idx - context_chars)
                context_end = min(len(page_text), end + context_chars)
                results.append(
                    MatchResult(
                        text=page_text[idx:end],
                        page_number=page_index,
                        context=page_text[context_start:context_end],
                    )
                )
                start = end

    return results


def extract_words(
    pdf_path: str | Path,
    *,
    keep_blank_chars: bool = False,
    use_text_flow: bool = True,
) -> list[PDFWord]:
    """
    Extract all words with coordinates from the PDF.

    This is useful when you need position-based validation.
    """
    path = _ensure_file_exists(pdf_path)
    words: list[PDFWord] = []

    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            raw_words = page.extract_words(
                keep_blank_chars=keep_blank_chars,
                use_text_flow=use_text_flow,
            )
            for word in raw_words:
                words.append(
                    PDFWord(
                        text=word.get("text", ""),
                        page_number=page_index,
                        x0=float(word.get("x0", 0)),
                        x1=float(word.get("x1", 0)),
                        top=float(word.get("top", 0)),
                        bottom=float(word.get("bottom", 0)),
                    )
                )

    return words


def get_words_by_page(
    pdf_path: str | Path,
    *,
    keep_blank_chars: bool = False,
    use_text_flow: bool = True,
) -> dict[int, list[PDFWord]]:
    """
    Return words grouped by page number.
    """
    result: dict[int, list[PDFWord]] = {}
    for word in extract_words(
        pdf_path,
        keep_blank_chars=keep_blank_chars,
        use_text_flow=use_text_flow,
    ):
        result.setdefault(word.page_number, []).append(word)
    return result


def find_word(
    pdf_path: str | Path,
    target_text: str,
    *,
    case_sensitive: bool = False,
    exact_match: bool = True,
) -> list[PDFWord]:
    """
    Find words matching a target text.
    """
    target = target_text if case_sensitive else target_text.lower()
    matches: list[PDFWord] = []

    for word in extract_words(pdf_path):
        candidate = word.text if case_sensitive else word.text.lower()

        if exact_match and candidate == target:
            matches.append(word)
        elif not exact_match and target in candidate:
            matches.append(word)

    return matches


def get_text_near_word(
    pdf_path: str | Path,
    target_text: str,
    *,
    direction: str = "right",
    max_distance: float = 120.0,
    same_line_tolerance: float = 8.0,
    case_sensitive: bool = False,
) -> list[LabelValueResult]:
    """
    Find text near a target word, based on coordinates.

    Typical usage:
        get_text_near_word(pdf, "Total", direction="right")

    Args:
        direction: 'right', 'left', 'below', 'above'
    """
    direction = direction.lower().strip()
    if direction not in {"right", "left", "below", "above"}:
        raise ValueError("direction must be one of: right, left, below, above")

    pages_words = get_words_by_page(pdf_path)
    target_matches = find_word(
        pdf_path,
        target_text,
        case_sensitive=case_sensitive,
        exact_match=True,
    )

    results: list[LabelValueResult] = []

    for target in target_matches:
        candidates = pages_words.get(target.page_number, [])
        nearby: list[PDFWord] = []

        for candidate in candidates:
            if candidate == target:
                continue

            if direction == "right":
                same_line = abs(candidate.top - target.top) <= same_line_tolerance
                close_enough = 0 <= (candidate.x0 - target.x1) <= max_distance
                if same_line and close_enough:
                    nearby.append(candidate)

            elif direction == "left":
                same_line = abs(candidate.top - target.top) <= same_line_tolerance
                close_enough = 0 <= (target.x0 - candidate.x1) <= max_distance
                if same_line and close_enough:
                    nearby.append(candidate)

            elif direction == "below":
                same_column = abs(candidate.x0 - target.x0) <= max_distance
                close_enough = 0 <= (candidate.top - target.bottom) <= max_distance
                if same_column and close_enough:
                    nearby.append(candidate)

            elif direction == "above":
                same_column = abs(candidate.x0 - target.x0) <= max_distance
                close_enough = 0 <= (target.top - candidate.bottom) <= max_distance
                if same_column and close_enough:
                    nearby.append(candidate)

        if direction == "right":
            nearby.sort(key=lambda w: (w.x0, w.top))
        elif direction == "left":
            nearby.sort(key=lambda w: (-w.x1, w.top))
        elif direction == "below":
            nearby.sort(key=lambda w: (w.top, w.x0))
        elif direction == "above":
            nearby.sort(key=lambda w: (-w.bottom, w.x0))

        if nearby:
            results.append(
                LabelValueResult(
                    label=target.text,
                    value=nearby[0].text,
                    page_number=target.page_number,
                )
            )

    return results


def get_value_by_label(
    pdf_path: str | Path,
    label: str,
    *,
    strategy: str = "same_line_regex",
    separator_pattern: str = r"[:\-]?\s*",
    value_pattern: str = r"(.+)",
    case_sensitive: bool = False,
    direction: str = "right",
    max_distance: float = 120.0,
    same_line_tolerance: float = 8.0,
) -> str:
    """
    Extract a value associated with a label.

    Strategies:
        - same_line_regex: finds patterns like 'Total: 123'
        - near_word: finds text spatially near the label
    """
    strategy = strategy.lower().strip()

    if strategy == "same_line_regex":
        pages_text = extract_text_by_page(pdf_path)
        escaped_label = re.escape(label)
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = rf"{escaped_label}{separator_pattern}{value_pattern}"

        for page_text in pages_text:
            for line in page_text.splitlines():
                match = re.search(regex, line, flags)
                if match:
                    return _normalize_spaces(match.group(1))

        raise PDFLabelNotFoundError(f"Label not found with same_line_regex: {label!r}")

    if strategy == "near_word":
        results = get_text_near_word(
            pdf_path,
            label,
            direction=direction,
            max_distance=max_distance,
            same_line_tolerance=same_line_tolerance,
            case_sensitive=case_sensitive,
        )
        if results:
            return _normalize_spaces(results[0].value)
        raise PDFLabelNotFoundError(f"Label not found with near_word: {label!r}")

    raise ValueError("strategy must be 'same_line_regex' or 'near_word'")


def assert_label_value(
    pdf_path: str | Path,
    label: str,
    expected_value: str,
    *,
    strategy: str = "same_line_regex",
    case_sensitive: bool = False,
    normalize_spaces: bool = True,
    **kwargs: Any,
) -> None:
    """
    Assert that a label has the expected value.
    """
    actual_value = get_value_by_label(
        pdf_path,
        label,
        strategy=strategy,
        case_sensitive=case_sensitive,
        **kwargs,
    )

    if normalize_spaces:
        actual_value = _normalize_spaces(actual_value)
        expected_value = _normalize_spaces(expected_value)

    left = actual_value if case_sensitive else actual_value.lower()
    right = expected_value if case_sensitive else expected_value.lower()

    if left != right:
        raise AssertionError(
            f"Unexpected value for label {label!r}. "
            f"Expected: {expected_value!r}, Actual: {actual_value!r}"
        )


def extract_tables(
    pdf_path: str | Path,
    *,
    page_number: Optional[int] = None,
) -> list[list[list[Optional[str]]]]:
    """
    Extract tables from the PDF.

    Returns:
        A list of tables, where each table is a list of rows,
        and each row is a list of cell values.
    """
    path = _ensure_file_exists(pdf_path)
    all_tables: list[list[list[Optional[str]]]] = []

    with pdfplumber.open(path) as pdf:
        pages = pdf.pages if page_number is None else [pdf.pages[page_number - 1]]

        for page in pages:
            tables = page.extract_tables()
            for table in tables:
                all_tables.append(table)

    return all_tables


def extract_first_table(
    pdf_path: str | Path,
    *,
    page_number: Optional[int] = None,
) -> list[list[Optional[str]]]:
    """
    Extract the first table found in the PDF.
    """
    tables = extract_tables(pdf_path, page_number=page_number)
    if not tables:
        raise PDFTableNotFoundError("No tables found in the PDF.")
    return tables[0]


def find_row_in_table(
    table: Sequence[Sequence[Optional[str]]],
    expected_cells: Sequence[str],
    *,
    case_sensitive: bool = False,
    normalize_spaces: bool = True,
) -> Optional[list[Optional[str]]]:
    """
    Find a row containing all expected cell values.
    """
    prepared_expected = []
    for cell in expected_cells:
        value = cell if case_sensitive else cell.lower()
        if normalize_spaces:
            value = _normalize_spaces(value)
        prepared_expected.append(value)

    for row in table:
        prepared_row = []
        for cell in row:
            cell_value = cell or ""
            cell_value = cell_value if case_sensitive else cell_value.lower()
            if normalize_spaces:
                cell_value = _normalize_spaces(cell_value)
            prepared_row.append(cell_value)

        if all(expected in prepared_row for expected in prepared_expected):
            return list(row)

    return None


def assert_table_contains_row(
    pdf_path: str | Path,
    expected_cells: Sequence[str],
    *,
    page_number: Optional[int] = None,
    table_index: int = 0,
    case_sensitive: bool = False,
    normalize_spaces: bool = True,
) -> None:
    """
    Assert that a table contains a row with the expected cells.
    """
    tables = extract_tables(pdf_path, page_number=page_number)

    if not tables:
        raise PDFTableNotFoundError("No tables found in the PDF.")

    if table_index >= len(tables):
        raise PDFTableNotFoundError(
            f"Requested table index {table_index}, but only {len(tables)} table(s) found."
        )

    row = find_row_in_table(
        tables[table_index],
        expected_cells,
        case_sensitive=case_sensitive,
        normalize_spaces=normalize_spaces,
    )

    if row is None:
        raise AssertionError(
            f"Expected row not found in table {table_index}. Expected cells: {expected_cells!r}"
        )


def extract_text_with_ocr(
    pdf_path: str | Path,
    *,
    dpi: int = 200,
    lang: str = "eng",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> str:
    """
    OCR fallback for scanned PDFs.

    Requires:
        pip install pytesseract pdf2image
        and Tesseract installed in the OS.
    """
    if pytesseract is None or convert_from_path is None:
        raise ImportError(
            "OCR dependencies missing. Install with: pip install pytesseract pdf2image"
        )

    path = _ensure_file_exists(pdf_path)

    images = convert_from_path(
        str(path),
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
    )

    pages_text: list[str] = []
    for image in images:
        pages_text.append(pytesseract.image_to_string(image, lang=lang))

    return "\n".join(pages_text)


def extract_text_smart(
    pdf_path: str | Path,
    *,
    try_ocr_if_empty: bool = False,
    ocr_lang: str = "eng",
) -> str:
    """
    Smart extractor:
    1. tries structured text extraction
    2. optionally falls back to OCR
    """
    text = extract_full_text(pdf_path)

    if text.strip():
        return text

    if try_ocr_if_empty:
        return extract_text_with_ocr(pdf_path, lang=ocr_lang)

    return text


def is_probably_scanned_pdf(pdf_path: str | Path) -> bool:
    """
    Heuristic check:
    if structured extraction returns nearly no text, it may be scanned.
    """
    text = extract_full_text(pdf_path)
    return len(_normalize_spaces(text)) < 10


def debug_dump_words(
    pdf_path: str | Path,
    *,
    page_number: Optional[int] = None,
) -> list[dict[str, Any]]:
    """
    Helper for debugging coordinates during test development.
    """
    rows: list[dict[str, Any]] = []

    for word in extract_words(pdf_path):
        if page_number is not None and word.page_number != page_number:
            continue

        rows.append(
            {
                "text": word.text,
                "page_number": word.page_number,
                "x0": word.x0,
                "x1": word.x1,
                "top": word.top,
                "bottom": word.bottom,
            }
        )

    return rows
