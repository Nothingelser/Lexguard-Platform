from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("alerts/", views.regional_alerts, name="alerts"),
    path("pattern-match/<int:pk>/", views.pattern_match, name="pattern_match"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
]
