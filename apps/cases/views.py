from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import enforce_write_access, require_commander, require_station_officer
from apps.cases.forms import CaseForm, EvidenceForm, MOTagForm, SuspectLinkForm, WitnessForm
from apps.cases.models import AuditLog, Case, CaseSuspect, CaseStatus, CrimeCategory, EvidenceItem
from apps.cases.services import log_audit
from apps.cases.storage import upload_evidence_file


def _officer_cases(request):
    qs = Case.objects.select_related("station", "created_by")
    if request.user.is_commander:
        return qs.all()
    if request.user.station_id:
        return qs.filter(station=request.user.station)
    return qs.none()


def _apply_case_filters(qs, request):
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    query = request.GET.get("q", "").strip()
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(crime_category=category)
    if query:
        qs = qs.filter(
            Q(case_number__icontains=query)
            | Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(narrative__icontains=query)
        )
    return qs.order_by("-opened_at")


@login_required
def case_list(request):
    cases = _apply_case_filters(_officer_cases(request), request)
    context = {
        "cases": cases,
        "active_status": request.GET.get("status", ""),
        "active_category": request.GET.get("category", ""),
        "search_query": request.GET.get("q", ""),
        "status_choices": CaseStatus.choices,
        "category_choices": CrimeCategory.choices,
    }
    template = "cases/partials/case_table.html" if request.htmx else "cases/case_list.html"
    return render(request, template, context)


@login_required
@require_http_methods(["GET", "POST"])
def case_create(request):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")

    form = CaseForm(request.POST or None)
    mo_form = MOTagForm(request.POST or None)

    if request.method == "POST" and form.is_valid() and mo_form.is_valid():
        case = form.save(commit=False)
        case.station = request.user.station
        case.created_by = request.user
        case.modus_operandi = mo_form.cleaned_mo_tags()
        case.save()
        log_audit(request.user, "create", "case", case.pk, f"Registered case {case.case_number}")
        return redirect("cases:detail", pk=case.pk)

    return render(request, "cases/case_form.html", {"form": form, "mo_form": mo_form})


@login_required
def case_detail(request, pk):
    case = get_object_or_404(
        _officer_cases(request).prefetch_related("case_suspects__suspect", "witnesses", "evidence_items"),
        pk=pk,
    )
    timeline = (
        AuditLog.objects.filter(station=case.station)
        .filter(Q(entity="case", entity_id=str(case.pk)) | Q(detail__icontains=case.case_number))
        .select_related("user")[:20]
    )
    return render(
        request,
        "cases/case_detail.html",
        {
            "case": case,
            "witness_form": WitnessForm(),
            "evidence_form": EvidenceForm(),
            "timeline": timeline,
        },
    )


@login_required
@require_http_methods(["POST"])
def case_link_suspect(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=pk)
    form = SuspectLinkForm(request.POST)
    if form.is_valid():
        suspect = form.resolve_suspect()
        CaseSuspect.objects.get_or_create(
            case=case,
            suspect=suspect,
            defaults={"role": form.cleaned_data["role"]},
        )
        log_audit(request.user, "link", "suspect", suspect.pk, f"Linked to case {case.case_number}")

    if request.htmx:
        case = get_object_or_404(
            Case.objects.prefetch_related("case_suspects__suspect"),
            pk=case.pk,
        )
        return render(request, "cases/partials/suspect_list.html", {"case": case})
    return redirect("cases:detail", pk=case.pk)


@login_required
@require_http_methods(["POST"])
def case_add_witness(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=pk)
    form = WitnessForm(request.POST)
    if form.is_valid():
        witness = form.save(commit=False)
        witness.case = case
        witness.save()
        log_audit(request.user, "add", "witness", witness.pk, f"Added witness to {case.case_number}")

    if request.htmx:
        case = get_object_or_404(
            Case.objects.prefetch_related("witnesses"),
            pk=case.pk,
        )
        return render(request, "cases/partials/witness_list.html", {"case": case})
    return redirect("cases:detail", pk=case.pk)


@login_required
@require_http_methods(["POST"])
def case_add_evidence(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=pk)
    form = EvidenceForm(request.POST, request.FILES)
    saved = False
    if form.is_valid():
        try:
            item = form.save(commit=False)
            upload = form.cleaned_data.get("upload_file")
            if upload:
                item.storage_path = upload_evidence_file(case, upload)
                item.file_size = getattr(upload, "size", None)
            elif not item.storage_path:
                item.storage_path = ""
            item.uploaded_at = timezone.now()
            item.case = case
            item.save()
            log_audit(request.user, "add", "evidence", item.pk, f"Logged evidence for {case.case_number}")
            saved = True
        except RuntimeError as exc:
            form.add_error(None, str(exc))

    if saved:
        if request.htmx:
            case = get_object_or_404(
                Case.objects.prefetch_related("evidence_items"),
                pk=case.pk,
            )
            return render(request, "cases/partials/evidence_list.html", {"case": case})
        return redirect("cases:detail", pk=case.pk)

    if request.htmx:
        case = get_object_or_404(
            Case.objects.prefetch_related("evidence_items"),
            pk=case.pk,
        )
        return render(request, "cases/partials/evidence_list.html", {"case": case, "form": form})
    return render(
        request,
        "cases/case_detail.html",
        {
            "case": get_object_or_404(
                _officer_cases(request).prefetch_related("case_suspects__suspect", "witnesses", "evidence_items"),
                pk=pk,
            ),
            "witness_form": WitnessForm(),
            "evidence_form": form,
            "timeline": AuditLog.objects.filter(station=case.station)
            .filter(Q(entity="case", entity_id=str(case.pk)) | Q(detail__icontains=case.case_number))
            .select_related("user")[:20],
        },
    )


@login_required
@require_http_methods(["POST"])
def case_delete_evidence(request, case_pk, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=case_pk)
    evidence = get_object_or_404(EvidenceItem.objects.filter(case=case), pk=pk)
    label = evidence.label
    evidence.delete()
    log_audit(request.user, "delete", "evidence", pk, f"Deleted evidence {label} from {case.case_number}")

    if request.htmx:
        case = get_object_or_404(
            Case.objects.prefetch_related("evidence_items"),
            pk=case.pk,
        )
        return render(request, "cases/partials/evidence_list.html", {"case": case})
    return redirect("cases:detail", pk=case.pk)


@login_required
@require_http_methods(["POST"])
def case_set_investigating(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=pk)
    if case.status == CaseStatus.OPEN:
        case.status = CaseStatus.INVESTIGATING
        case.save(update_fields=["status", "updated_at"])
        log_audit(request.user, "update", "case", case.pk, f"Case {case.case_number} marked under investigation")
    return redirect("cases:detail", pk=case.pk)


@login_required
def case_export_pdf(request, pk):
    from apps.cases.exports import build_case_pdf

    case = get_object_or_404(
        _officer_cases(request).prefetch_related(
            "case_suspects__suspect", "witnesses", "evidence_items", "station", "created_by"
        ),
        pk=pk,
    )
    pdf_bytes = build_case_pdf(case)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="lexguard-{case.case_number}.pdf"'
    return response


@login_required
@require_http_methods(["POST"])
def case_close(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")
    enforce_write_access(request)

    case = get_object_or_404(Case.objects.filter(station=request.user.station), pk=pk)
    case.status = CaseStatus.CLOSED
    case.closed_at = timezone.now()
    case.save(update_fields=["status", "closed_at", "updated_at"])
    log_audit(request.user, "close", "case", case.pk, f"Closed case {case.case_number}")
    return redirect("cases:detail", pk=case.pk)


@login_required
def audit_log(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")

    logs = AuditLog.objects.select_related("station", "user").all()[:50]

    return render(request, "cases/audit_log.html", {"logs": logs})
