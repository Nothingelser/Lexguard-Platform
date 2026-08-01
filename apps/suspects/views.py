from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import require_station_officer
from apps.cases.models import CaseSuspect
from apps.suspects.forms import SuspectForm
from apps.suspects.models import Suspect


@login_required
def suspect_search(request):
    query = request.GET.get("q", "").strip()

    if query:
        suspects = Suspect.objects.filter(
            Q(national_id__icontains=query)
            | Q(full_name__icontains=query)
            | Q(aliases__icontains=query)
        )[:20]
    elif request.user.is_commander:
        suspects = Suspect.objects.all().order_by("full_name")
    elif request.user.is_station_officer and request.user.station_id:
        # Show suspects already linked to this station's cases on page load
        suspects = Suspect.objects.filter(
            case_links__case__station=request.user.station
        ).distinct().order_by("full_name")
    else:
        suspects = Suspect.objects.none()

    template = "suspects/partials/search_results.html" if request.htmx else "suspects/search.html"
    return render(request, template, {"suspects": suspects, "query": query})


@login_required
@require_http_methods(["GET", "POST"])
def suspect_create(request):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")

    initial = {}
    national_id = request.GET.get("national_id", "").strip()
    if national_id:
        initial["national_id"] = national_id

    form = SuspectForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        suspect = form.save()
        return redirect("suspects:profile", pk=suspect.pk)

    return render(request, "suspects/suspect_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def suspect_edit(request, pk):
    if not require_station_officer(request.user):
        return HttpResponseForbidden("Station officers only.")

    suspect = get_object_or_404(Suspect, pk=pk)
    form = SuspectForm(request.POST or None, request.FILES or None, instance=suspect)
    if request.method == "POST" and form.is_valid():
        suspect = form.save()
        return redirect("suspects:profile", pk=suspect.pk)

    return render(request, "suspects/suspect_form.html", {"form": form, "suspect": suspect, "editing": True})


@login_required
def suspect_profile(request, pk):
    suspect = get_object_or_404(Suspect, pk=pk)
    links = CaseSuspect.objects.filter(suspect=suspect).select_related("case", "case__station")

    if request.user.is_station_officer and request.user.station_id:
        links = links.filter(case__station=request.user.station)

    return render(
        request,
        "suspects/profile.html",
        {"suspect": suspect, "case_links": links},
    )

