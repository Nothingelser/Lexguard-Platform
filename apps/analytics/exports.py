"""Excel report generation for regional command."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.drawing.image import Image as XLImage
import os
from django.conf import settings

from apps.analytics.pattern_matcher import precinct_performance, subcounty_hotspots


def build_precinct_workbook() -> bytes:
    wb = Workbook()
    # Precinct performance sheet
    ws1 = wb.active
    ws1.title = "Precinct Performance"

    # If a supplied logo exists, add it to the sheet and push headers down.
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "Logo.jpg")
    start_row = 1
    if os.path.exists(logo_path):
        try:
            img = XLImage(logo_path)
            img.width = 160
            img.height = 60
            ws1.add_image(img, 'A1')
            start_row = 6
        except Exception:
            start_row = 1

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    headers = ["Code", "Station", "County", "Open", "Closed", "Closure %", "Avg Days"]
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=start_row, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill

    for row_idx, row in enumerate(precinct_performance(), start_row + 1):
        ws1.cell(row=row_idx, column=1, value=row["station"].code)
        ws1.cell(row=row_idx, column=2, value=row["station"].name)
        ws1.cell(row=row_idx, column=3, value=row["station"].county)
        ws1.cell(row=row_idx, column=4, value=row["open"])
        ws1.cell(row=row_idx, column=5, value=row["closed"])
        ws1.cell(row=row_idx, column=6, value=row["closure_rate"])
        ws1.cell(row=row_idx, column=7, value=row["avg_resolution_days"] or "")

    # Hotspot sheet
    ws2 = wb.create_sheet("Sub-County Hotspots")
    headers2 = ["Sub-County", "County", "Category", "Case Count"]
    for col, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill

    for row_idx, row in enumerate(subcounty_hotspots()[:50], 2):
        ws2.cell(row=row_idx, column=1, value=row["station__sub_county"] or "Unspecified")
        ws2.cell(row=row_idx, column=2, value=row["station__county"])
        ws2.cell(row=row_idx, column=3, value=row["crime_category"])
        ws2.cell(row=row_idx, column=4, value=row["count"])

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
