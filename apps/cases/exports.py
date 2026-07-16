"""PDF and structured report generation (deterministic, no AI)."""

import logging
import os
import unicodedata

from django.conf import settings
from django.utils import timezone
from fpdf import FPDF

from apps.cases.models import MOTagOption

logger = logging.getLogger(__name__)


class LexGuardPDF(FPDF):
    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(110, 116, 125)
        self.cell(0, 5, _safe_text(f"Page {self.page_no()}"), align="R")


def _safe_text(value):
    text = "" if value is None else str(value)
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2022", "-")
    text = unicodedata.normalize("NFKD", text)
    return text.encode("latin-1", "replace").decode("latin-1")


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


def _section_header(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, _safe_text(title), ln=True)
    pdf.set_draw_color(214, 220, 227)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def _content_width(pdf: FPDF) -> float:
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


def _append_line(pdf: FPDF, text: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_content_width(pdf), 6, _safe_text(text))


def _overview_block(pdf: FPDF, label: str, value: str, *, pill: bool = False, fill=None, text=None) -> None:
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
        pdf.multi_cell(_content_width(pdf) - 8, 5.8, _safe_text(value))
    pdf.ln(1.5)


def _build_simple_case_pdf(case) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

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
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(14, 14, 14)
        pdf.add_page()

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

        badge_w = 50
        badge_x = pdf.w - pdf.r_margin - badge_w
        badge_y = header_y + 7
        pdf.set_fill_color(25, 43, 69)
        pdf.set_text_color(255, 255, 255)
        pdf.set_draw_color(25, 43, 69)
        pdf.rect(badge_x, badge_y, badge_w, 19, style="DF")
        pdf.set_xy(badge_x + 2, badge_y + 2.5)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(badge_w - 4, 4, _safe_text("CASE NO."), align="C", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(badge_w - 4, 6, _safe_text(case.case_number), align="C", ln=True)

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
