"""PDF and structured report generation (deterministic, no AI)."""

from __future__ import annotations

import io
import logging
import os
import textwrap
import unicodedata
from typing import Any

from django.conf import settings
from django.utils import timezone

try:
    from fpdf import FPDF as _FPDF
except Exception:  # pragma: no cover - optional dependency fallback
    _FPDF = None

from apps.cases.models import MOTagOption

logger = logging.getLogger(__name__)


class _ManualPDF:
    """Small PDF writer used when fpdf is unavailable.

    It supports the narrow subset of drawing operations used by the case export
    builder so exports remain functional in lean environments and test runs.
    """

    PAGE_WIDTH = 595.28
    PAGE_HEIGHT = 841.89

    def __init__(self):
        self.w = self.PAGE_WIDTH
        self.h = self.PAGE_HEIGHT
        self.l_margin = 14
        self.r_margin = 14
        self.t_margin = 14
        self.b_margin = 15
        self.auto_page_break = True
        self.page_break_margin = 15
        self._font_family = "Helvetica"
        self._font_style = ""
        self._font_size = 12
        self._text_color = (0, 0, 0)
        self._fill_color = (255, 255, 255)
        self._draw_color = (0, 0, 0)
        self._line_width = 0.5
        self._x = self.l_margin
        self._y = self.t_margin
        self._pages: list[str] = []
        self._current: list[str] | None = None

    def set_auto_page_break(self, auto=True, margin=15):
        self.auto_page_break = auto
        self.page_break_margin = margin
        self.b_margin = margin

    def set_margins(self, left, top, right=None):
        self.l_margin = left
        self.t_margin = top
        self.r_margin = right if right is not None else left
        self._x = self.l_margin
        self._y = self.t_margin

    def add_page(self):
        if self._current is not None:
            self._pages.append("".join(self._current))
        self._current = []
        self._x = self.l_margin
        self._y = self.t_margin

    def _emit(self, command: str):
        if self._current is None:
            self.add_page()
        self._current.append(command + "\n")

    def _escape(self, text: Any) -> str:
        return (
            "" if text is None else str(text)
        ).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("\r", "").replace("\n", " ")

    def _pdf_y(self, top_y: float) -> float:
        return self.h - top_y

    def _font_resource(self) -> str:
        return "/F2" if "B" in self._font_style.upper() else "/F1"

    def _line_height(self) -> float:
        return max(1.0, self._font_size * 1.35)

    def _estimate_wrap_chars(self, width: float) -> int:
        average_char_width = max(2.5, self._font_size * 0.5)
        return max(8, int(width / average_char_width))

    def _wrap_lines(self, text: Any, width: float) -> list[str]:
        paragraphs = _safe_text(text).splitlines() or [""]
        lines: list[str] = []
        for paragraph in paragraphs:
            wrapped = textwrap.wrap(
                paragraph or " ",
                width=self._estimate_wrap_chars(width),
                break_long_words=True,
                break_on_hyphens=True,
            )
            lines.extend(wrapped or [""])
        return lines or [""]

    def set_font(self, family, style="", size=12):
        self._font_family = family
        self._font_style = style or ""
        self._font_size = size

    def set_text_color(self, r, g=None, b=None):
        if g is None:
            g = r
        if b is None:
            b = g
        self._text_color = (r, g, b)
        self._emit(f"{r/255:.3f} {g/255:.3f} {b/255:.3f} rg")

    def set_fill_color(self, r, g=None, b=None):
        if g is None:
            g = r
        if b is None:
            b = g
        self._fill_color = (r, g, b)

    def set_draw_color(self, r, g=None, b=None):
        if g is None:
            g = r
        if b is None:
            b = g
        self._draw_color = (r, g, b)
        self._emit(f"{r/255:.3f} {g/255:.3f} {b/255:.3f} RG")

    def set_line_width(self, width):
        self._line_width = width
        self._emit(f"{width:.3f} w")

    def get_string_width(self, text):
        return len(_safe_text(text)) * max(1.0, self._font_size * 0.5)

    def set_x(self, x):
        self._x = x

    def set_y(self, y):
        self._y = y

    def set_xy(self, x, y):
        self._x = x
        self._y = y

    def get_y(self):
        return self._y

    def _maybe_page_break(self, height):
        if self.auto_page_break and self._y + height > self.h - self.page_break_margin:
            self.add_page()

    def rect(self, x, y, w, h, style="S"):
        pdf_y = self._pdf_y(y) - h
        op = "S"
        if "F" in style and "D" in style:
            op = "B"
        elif "F" in style:
            op = "f"
        self._emit(
            f"{self._draw_color[0]/255:.3f} {self._draw_color[1]/255:.3f} {self._draw_color[2]/255:.3f} RG "
            f"{self._fill_color[0]/255:.3f} {self._fill_color[1]/255:.3f} {self._fill_color[2]/255:.3f} rg "
            f"{x:.2f} {pdf_y:.2f} {w:.2f} {h:.2f} re {op}"
        )

    def line(self, x1, y1, x2, y2):
        self._emit(
            f"{self._draw_color[0]/255:.3f} {self._draw_color[1]/255:.3f} {self._draw_color[2]/255:.3f} RG "
            f"{x1:.2f} {self._pdf_y(y1):.2f} m {x2:.2f} {self._pdf_y(y2):.2f} l S"
        )

    def text(self, x, y, txt):
        self._emit(
            f"BT {self._font_resource()} {self._font_size:.2f} Tf "
            f"{self._text_color[0]/255:.3f} {self._text_color[1]/255:.3f} {self._text_color[2]/255:.3f} rg "
            f"{x:.2f} {self._pdf_y(y):.2f} Td ({self._escape(txt)}) Tj ET"
        )

    def image(self, *args, **kwargs):  # pragma: no cover - no image embedding in fallback
        return None

    def cell(self, w, h=0, txt="", border=0, ln=0, align="", fill=False):
        height = h or self._line_height()
        self._maybe_page_break(height)
        if fill:
            self.rect(self._x, self._y, w, height, style="DF")
        if txt != "":
            text_width = self.get_string_width(txt)
            if align == "C":
                text_x = self._x + max(1, (w - text_width) / 2)
            elif align == "R":
                text_x = self._x + max(1, w - text_width - 1.5)
            else:
                text_x = self._x + 1.5
            baseline = self._y + max(2, height * 0.72)
            self.text(text_x, baseline, txt)
        if ln:
            self._x = self.l_margin
            self._y += height
        else:
            self._x += w

    def multi_cell(self, w, h, txt, border=0, align="L", fill=False):
        for line in self._wrap_lines(txt, w):
            self.cell(w, h, line, border=border, ln=1, align=align, fill=fill)

    def ln(self, h=None):
        self._x = self.l_margin
        self._y += h if h is not None else self._line_height()

    def output(self, dest="S"):
        if self._current is not None:
            self._pages.append("".join(self._current))
            self._current = None

        page_count = max(1, len(self._pages))
        total_objects = 4 + (page_count * 2)
        objects = [None] * (total_objects + 1)

        def make_stream(stream_text):
            data = stream_text.encode("latin-1", "replace")
            return f"<< /Length {len(data)} >>\nstream\n{stream_text}endstream"

        page_objects = []
        for index, page_stream in enumerate(self._pages or [""]):
            content_obj = 5 + (index * 2)
            page_obj = 6 + (index * 2)
            page_objects.append(page_obj)
            objects[content_obj] = make_stream(page_stream)
            objects[page_obj] = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.PAGE_WIDTH:.2f} {self.PAGE_HEIGHT:.2f}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_obj} 0 R >>"
            )

        objects[1] = "<< /Type /Catalog /Pages 2 0 R >>"
        kids = " ".join(f"{obj} 0 R" for obj in page_objects)
        objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>"
        objects[3] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        objects[4] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"

        pdf = io.BytesIO()
        pdf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for obj_num in range(1, total_objects + 1):
            offsets.append(pdf.tell())
            pdf.write(f"{obj_num} 0 obj\n{objects[obj_num]}\nendobj\n".encode("latin-1", "replace"))
        xref_pos = pdf.tell()
        pdf.write(f"xref\n0 {total_objects + 1}\n".encode("latin-1"))
        pdf.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.write(
            (
                f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF"
            ).encode("latin-1")
        )
        data = pdf.getvalue()
        return data if dest == "S" else None


PDFBase = _FPDF or _ManualPDF


class LexGuardPDF(PDFBase):
    def footer(self):
        if _FPDF is None:
            return
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(110, 116, 125)
        self.cell(0, 5, _safe_text(f"Page {self.page_no()}"), align="R")


def _safe_text(value):
    text = "" if value is None else str(value)
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2022", "-")
    text = unicodedata.normalize("NFKD", text)
    return text.encode("latin-1", "replace").decode("latin-1")


def _wrap_pdf_text(pdf, text: Any, width: float | None = None) -> list[str]:
    width = width if width is not None else _content_width(pdf)
    width = max(20, width)
    try:
        sample_width = float(pdf.get_string_width("M"))
    except Exception:
        sample_width = 0.0
    if sample_width <= 0:
        sample_width = 4.0
    chars = max(12, int(width / sample_width))
    wrapped: list[str] = []
    for paragraph in _safe_text(text).splitlines() or [""]:
        wrapped.extend(
            textwrap.wrap(
                paragraph or " ",
                width=chars,
                break_long_words=True,
                break_on_hyphens=True,
            )
            or [""]
        )
    return wrapped or [""]


def _mo_display(mo_tags: dict) -> list[str]:
    lines = []
    for category, value in ((mo_tags if isinstance(mo_tags, dict) else {}) or {}).items():
        option = MOTagOption.objects.filter(category=category, value=value).first()
        label = option.label if option else value
        lines.append(f"{category.replace('_', ' ').title()}: {_safe_text(label)}")
    return lines or ["None recorded"]


def _status_colors(status: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    status = (status or "").lower()
    if status == "closed":
        return (22, 163, 74), (240, 253, 244)
    if status == "investigating":
        return (217, 119, 6), (255, 251, 235)
    return (37, 99, 235), (239, 246, 255)


def _section_header(pdf: Any, title: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _safe_text(title), ln=True)
    pdf.set_draw_color(214, 220, 227)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def _content_width(pdf: Any) -> float:
    return max(40, pdf.w - pdf.l_margin - pdf.r_margin)


def _display_or_value(obj, method_name: str, fallback: str) -> str:
    method = getattr(obj, method_name, None)
    if callable(method):
        try:
            value = method()
            if value:
                return str(value)
        except Exception:
            pass
    return fallback


def _timestamp(value) -> str:
    if not value:
        return "N/A"
    try:
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def _append_line(pdf: Any, text: Any) -> None:
    pdf.set_x(pdf.l_margin)
    for line in _wrap_pdf_text(pdf, text):
        pdf.multi_cell(_content_width(pdf), 6, line)


def _overview_block(pdf: Any, label: str, value: str, *, pill: bool = False, fill=None, text=None) -> None:
    pdf.set_x(pdf.l_margin + 4)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(56, 63, 74)
    pdf.cell(0, 5, _safe_text(label), ln=True)

    pdf.set_x(pdf.l_margin + 4)
    if pill and fill and text:
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*text)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(30, 6.5, _safe_text(value), fill=True, ln=True)
    else:
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(30, 41, 59)
        wrapped = _wrap_pdf_text(pdf, value, _content_width(pdf) - 8)
        for index, line in enumerate(wrapped):
            pdf.multi_cell(_content_width(pdf) - 8, 5.8, line)
            if index < len(wrapped) - 1:
                pdf.set_x(pdf.l_margin + 4)
    pdf.ln(1.5)


def _base_pdf() -> LexGuardPDF:
    pdf = LexGuardPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()
    return pdf


def _build_simple_case_pdf(case) -> bytes:
    pdf = _base_pdf()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, _safe_text("LexGuard Case File Report"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 6, _safe_text("Fallback export layout"), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    _append_line(pdf, f"Case {getattr(case, 'case_number', 'N/A')}")
    pdf.set_font("Helvetica", "", 10)
    _append_line(pdf, getattr(case, "title", ""))
    pdf.ln(2)

    station = getattr(case, "station", None)
    created_by = getattr(case, "created_by", None)
    info = [
        ("Station", f"{getattr(station, 'code', 'N/A')} - {getattr(station, 'name', 'N/A')}"),
        (
            "County / Sub-County",
            f"{getattr(station, 'county', 'N/A')} / {getattr(station, 'sub_county', 'N/A') or 'N/A'}",
        ),
        ("Location", getattr(case, "location", "")),
        ("Category", _display_or_value(case, "get_crime_category_display", getattr(case, "crime_category", "N/A"))),
        ("Status", _display_or_value(case, "get_status_display", getattr(case, "status", "N/A"))),
        ("Opened", _timestamp(getattr(case, "opened_at", None))),
        (
            "Lead Officer",
            f"{_display_or_value(created_by, 'get_full_name', 'N/A')} ({getattr(created_by, 'badge_number', 'N/A')})",
        ),
    ]

    pdf.set_font("Helvetica", "", 10)
    for label, value in info:
        _append_line(pdf, f"{label}: {value}")

    pdf.ln(4)
    _section_header(pdf, "Narrative")
    pdf.set_font("Helvetica", "", 10)
    _append_line(pdf, getattr(case, "narrative", ""))

    output = pdf.output(dest="S")
    return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode("latin-1", "replace")


def build_case_pdf(case) -> bytes:
    try:
        pdf = _base_pdf()

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "Logo.jpg")

        header_y = 14
        header_h = 34
        header_x = pdf.l_margin
        header_w = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.set_draw_color(214, 220, 227)
        pdf.set_fill_color(246, 248, 251)
        pdf.rect(header_x, header_y, header_w, header_h, style="DF")

        if os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=17, y=17, w=18)
            except Exception:
                pass

        pdf.set_xy(39, 18)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, _safe_text("LexGuard Case File Report"), ln=True)
        pdf.set_x(39)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 5.5, _safe_text("Coast Region Police - Multi-County Case File Export"), ln=True)

        badge_w = 56
        badge_x = pdf.w - pdf.r_margin - badge_w
        badge_y = header_y + 7
        pdf.set_fill_color(25, 43, 69)
        pdf.set_text_color(255, 255, 255)
        pdf.set_draw_color(25, 43, 69)
        pdf.rect(badge_x, badge_y, badge_w, 19, style="DF")
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.text(badge_x + 17, badge_y + 6, _safe_text("CASE NO."))
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_xy(badge_x, badge_y + 9.2)
        pdf.cell(badge_w, 6, _safe_text(case.case_number), align="C")

        pdf.set_y(header_y + header_h + 8)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, _safe_text(case.title), ln=True)

        opened_stamp = _timestamp(getattr(case, "opened_at", None))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, _safe_text(f"Opened {opened_stamp}"), ln=True)
        pdf.ln(2)

        card_x = pdf.l_margin
        card_y = pdf.get_y()
        card_w = pdf.w - pdf.l_margin - pdf.r_margin
        card_h = 88
        pdf.set_draw_color(225, 232, 240)
        pdf.set_fill_color(248, 250, 252)
        pdf.rect(card_x, card_y, card_w, card_h, style="DF")
        pdf.set_xy(card_x + 4, card_y + 4)

        status_fill, status_text = _status_colors(getattr(case, "status", ""))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5.5, _safe_text("Case Overview"), ln=True)
        pdf.set_draw_color(230, 236, 244)
        pdf.line(card_x + 4, pdf.get_y(), card_x + card_w - 4, pdf.get_y())
        pdf.ln(3)

        station = getattr(case, "station", None)
        created_by = getattr(case, "created_by", None)
        crime_category = _display_or_value(case, "get_crime_category_display", getattr(case, "crime_category", "N/A"))
        status_display = _display_or_value(case, "get_status_display", getattr(case, "status", "N/A"))
        lead_officer = f"{_display_or_value(created_by, 'get_full_name', 'N/A')} ({getattr(created_by, 'badge_number', 'N/A')})"
        _overview_block(pdf, "Station", f"{getattr(station, 'code', 'N/A')} - {getattr(station, 'name', 'N/A')}")
        _overview_block(pdf, "County / Sub-County", f"{getattr(station, 'county', 'N/A')} / {getattr(station, 'sub_county', 'N/A') or 'N/A'}")
        _overview_block(pdf, "Location", getattr(case, "location", ""))
        _overview_block(pdf, "Category", crime_category)
        _overview_block(pdf, "Status", status_display, pill=True, fill=status_fill, text=status_text)
        _overview_block(pdf, "Lead Officer", lead_officer)
        if getattr(case, "closed_at", None):
            _overview_block(pdf, "Closed", _timestamp(case.closed_at))

        pdf.set_y(card_y + card_h + 6)
        _section_header(pdf, "Narrative")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        _append_line(pdf, getattr(case, "narrative", "") or "No narrative recorded.")

        pdf.ln(1)
        _section_header(pdf, "Modus Operandi Tags")
        pdf.set_font("Helvetica", "", 10)
        for line in _mo_display(getattr(case, "safe_modus_operandi", getattr(case, "modus_operandi", {}))):
            _append_line(pdf, f"- {line}")

        suspects = getattr(case, "case_suspects", None)
        if suspects:
            suspects = suspects.select_related("suspect").all()
            if suspects:
                pdf.ln(1)
                _section_header(pdf, "Linked Suspects")
                pdf.set_font("Helvetica", "", 10)
                for link in suspects:
                    _append_line(pdf, f"- {link.suspect.full_name} (ID: {link.suspect.national_id}) - {link.role}")

        witnesses = getattr(case, "witnesses", None)
        if witnesses:
            witnesses = witnesses.all()
            if witnesses:
                pdf.ln(1)
                _section_header(pdf, "Witnesses")
                pdf.set_font("Helvetica", "", 10)
                for witness in witnesses:
                    contact = f" ({witness.contact})" if witness.contact else ""
                    _append_line(pdf, f"- {witness.full_name}{contact}")

        evidence = getattr(case, "evidence_items", None)
        if evidence:
            evidence = evidence.all()
            if evidence:
                pdf.ln(1)
                _section_header(pdf, "Evidence Chain")
                pdf.set_font("Helvetica", "", 10)
                for item in evidence:
                    _append_line(pdf, f"- {item.label}: {item.storage_path or 'on file'}")

        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(110, 116, 125)
        generated_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M")
        pdf.cell(
            0,
            5,
            _safe_text(f"Generated by LexGuard on {generated_at}. Deterministic export; no automated inference applied."),
            ln=True,
        )

        output = pdf.output(dest="S")
        return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode("latin-1", "replace")
    except Exception:
        logger.exception("Falling back to simplified case PDF for case %s", getattr(case, "case_number", "unknown"))
        return _build_simple_case_pdf(case)
