from django.urls import path

from . import views

app_name = "cases"

urlpatterns = [
    path("", views.case_list, name="list"),
    path("new/", views.case_create, name="create"),
    path("audit/", views.audit_log, name="audit"),
    path("<int:pk>/", views.case_detail, name="detail"),
    path("<int:pk>/export/pdf/", views.case_export_pdf, name="export_pdf"),
    path("<int:pk>/investigate/", views.case_set_investigating, name="investigate"),
    path("<int:pk>/link-suspect/", views.case_link_suspect, name="link_suspect"),
    path("<int:pk>/add-witness/", views.case_add_witness, name="add_witness"),
    path("<int:pk>/add-evidence/", views.case_add_evidence, name="add_evidence"),
    path("<int:pk>/close/", views.case_close, name="close"),
]
