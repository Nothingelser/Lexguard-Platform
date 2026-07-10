"""Public entry and shared views."""

import mimetypes
from pathlib import Path

from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from apps.analytics.views import commander_dashboard, station_dashboard


def home(request):
    if not request.user.is_authenticated:
        return render(request, "public/landing.html")
    if request.user.is_super_admin:
        return redirect("admin:index")
    if request.user.is_commander:
        return commander_dashboard(request)
    return station_dashboard(request)


def static_asset(request, path):
    full_path = finders.find(path)
    if not full_path:
        raise Http404

    if isinstance(full_path, list):
        full_path = full_path[0]

    file_path = Path(full_path)
    if not file_path.is_file():
        raise Http404

    content_type, encoding = mimetypes.guess_type(str(file_path))
    response = FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")
    if encoding:
        response.headers["Content-Encoding"] = encoding
    return response
