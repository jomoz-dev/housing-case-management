from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CaseForm, CaseNoteForm, StatusForm
from .models import Case, CaseNote


@login_required
def case_list(request):
    cases = Case.objects.all()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    repair_type = request.GET.get("repair_type", "").strip()

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
            "query": query,
            "status": status,
            "priority": priority,
            "repair_type": repair_type,
            "status_choices": Case.STATUS_CHOICES,
            "priority_choices": Case.PRIORITY_CHOICES,
            "repair_choices": Case.REPAIR_CHOICES,
            "status_cards": status_cards,
            "open_total": Case.objects.exclude(status=Case.STATUS_CLOSED).count(),
        },
    )


@login_required
def case_create(request):
    if request.method == "POST":
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            CaseNote.objects.create(
                case=case,
                author=request.user,
                kind=CaseNote.STATUS,
                body=f"Case opened as {case.get_status_display()} / {case.get_priority_display()}.",
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

    return render(
        request,
        "cases/detail.html",
        {
            "case": case,
            "note_form": note_form,
            "status_form": status_form,
        },
    )
