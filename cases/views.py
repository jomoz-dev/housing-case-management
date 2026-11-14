import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AccessForm, CaseForm, CaseNoteForm, CloseCaseForm, StatusForm
from .models import Case, CaseNote


def filtered_cases(request):
    cases = Case.objects.all()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    repair_type = request.GET.get("repair_type", "").strip()
    access = request.GET.get("access", "").strip()
    vulnerable_only = request.GET.get("vulnerable") == "1"

    if query:
        cases = cases.filter(
            Q(reference__icontains=query)
            | Q(address__icontains=query)
            | Q(resident_name__icontains=query)
            | Q(summary__icontains=query)
        )
    if status in dict(Case.STATUS_CHOICES):
        cases = cases.filter(status=status)
    else:
        status = ""
    if priority in dict(Case.PRIORITY_CHOICES):
        cases = cases.filter(priority=priority)
    else:
        priority = ""
    if repair_type in dict(Case.REPAIR_CHOICES):
        cases = cases.filter(repair_type=repair_type)
    else:
        repair_type = ""
    if access in dict(Case.ACCESS_CHOICES) and access != Case.ACCESS_AVAILABLE:
        cases = cases.filter(access=access)
    else:
        access = ""
    if vulnerable_only:
        cases = cases.filter(vulnerable=True)

    return cases, {
        "query": query,
        "status": status,
        "priority": priority,
        "repair_type": repair_type,
        "access": access,
        "vulnerable_only": vulnerable_only,
    }


@login_required
def case_list(request):
    cases, filters = filtered_cases(request)
    counts = {
        row["status"]: row["total"]
        for row in Case.objects.values("status").annotate(total=Count("id"))
    }
    status_cards = [
        (value, label, counts.get(value, 0)) for value, label in Case.STATUS_CHOICES
    ]

    return render(
        request,
        "cases/list.html",
        {
            "cases": cases,
            "status_choices": Case.STATUS_CHOICES,
            "priority_choices": Case.PRIORITY_CHOICES,
            "repair_choices": Case.REPAIR_CHOICES,
            "status_cards": status_cards,
            "open_total": Case.objects.exclude(status=Case.STATUS_CLOSED).count(),
            **filters,
        },
    )


@login_required
def case_export(request):
    cases, _filters = filtered_cases(request)
    stamp = timezone.localdate().isoformat()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="housing-cases-{stamp}.csv"'
    )
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(
        [
            "Reference",
            "Address",
            "Resident",
            "Repair type",
            "Priority",
            "Status",
            "Trade",
            "Access",
            "Vulnerable",
            "Summary",
            "Raised",
            "Closed",
            "Raised by",
        ]
    )
    for case in cases:
        writer.writerow(
            [
                case.reference,
                case.address,
                case.resident_name,
                case.get_repair_type_display(),
                case.get_priority_display(),
                case.get_status_display(),
                case.get_trade_display(),
                case.get_access_display(),
                "Yes" if case.vulnerable else "No",
                case.summary,
                timezone.localtime(case.created_at).strftime("%Y-%m-%d %H:%M"),
                timezone.localtime(case.closed_at).strftime("%Y-%m-%d %H:%M")
                if case.closed_at
                else "",
                case.created_by.username,
            ]
        )
    return response


@login_required
def case_create(request):
    if request.method == "POST":
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            opening = (
                f"Case opened as {case.get_status_display()} / {case.get_priority_display()}."
            )
            if case.vulnerable:
                opening += " Vulnerable household."
            if case.access != Case.ACCESS_AVAILABLE:
                opening += f" {case.get_access_display()}."
            CaseNote.objects.create(
                case=case,
                author=request.user,
                kind=CaseNote.STATUS,
                body=opening,
            )
            messages.success(request, f"Case {case.reference} raised.")
            return redirect(case)
    else:
        form = CaseForm()
    return render(request, "cases/create.html", {"form": form})


@login_required
def case_detail(request, reference):
    case = get_object_or_404(Case, reference=reference)
    note_form = CaseNoteForm()
    status_form = StatusForm(initial={"status": case.status})
    access_form = AccessForm(instance=case)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "note":
            note_form = CaseNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.case = case
                note.author = request.user
                note.kind = CaseNote.NOTE
                note.save()
                messages.success(request, "Note added to the case record.")
                return redirect(case)
        elif action == "status":
            if request.POST.get("status") == Case.STATUS_CLOSED:
                return redirect("case_close", reference=case.reference)
            status_form = StatusForm(request.POST)
            if status_form.is_valid():
                new_status = status_form.cleaned_data["status"]
                comment = status_form.cleaned_data["comment"].strip()
                old = case.get_status_display()
                case.status = new_status
                case.save()
                case.refresh_from_db()
                body = f"Status changed from {old} to {case.get_status_display()}."
                if comment:
                    body = f"{body} {comment}"
                CaseNote.objects.create(
                    case=case,
                    author=request.user,
                    kind=CaseNote.STATUS,
                    body=body,
                )
                messages.success(request, "Status updated.")
                return redirect(case)
        elif action == "access":
            access_form = AccessForm(request.POST, instance=case)
            if access_form.is_valid():
                previous_access = case.get_access_display()
                previous_vulnerable = case.vulnerable
                access_form.save()
                case.refresh_from_db()
                CaseNote.objects.create(
                    case=case,
                    author=request.user,
                    kind=CaseNote.NOTE,
                    body=(
                        "Access / vulnerability updated: "
                        f"{previous_access} → {case.get_access_display()}; "
                        f"vulnerable {previous_vulnerable} → {case.vulnerable}."
                    ),
                )
                messages.success(request, "Access and vulnerability updated.")
                return redirect(case)

    return render(
        request,
        "cases/detail.html",
        {
            "case": case,
            "note_form": note_form,
            "status_form": status_form,
            "access_form": access_form,
        },
    )


@login_required
def case_close(request, reference):
    case = get_object_or_404(Case, reference=reference)
    if case.status == Case.STATUS_CLOSED:
        messages.info(request, "This case is already closed.")
        return redirect(case)

    if request.method == "POST":
        form = CloseCaseForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data["reason"].strip()
            old = case.get_status_display()
            case.status = Case.STATUS_CLOSED
            case.save()
            CaseNote.objects.create(
                case=case,
                author=request.user,
                kind=CaseNote.STATUS,
                body=f"Closed from {old}. Reason: {reason}",
            )
            messages.success(request, f"Case {case.reference} closed.")
            return redirect(case)
    else:
        form = CloseCaseForm()

    return render(request, "cases/close.html", {"case": case, "form": form})
