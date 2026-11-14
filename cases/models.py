import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Case(models.Model):
    REPAIR_WATER = "water_leak"
    REPAIR_ELECTRICAL = "electrical"
    REPAIR_HEATING = "heating"
    REPAIR_DAMP = "damp_mould"
    REPAIR_ROOFING = "roofing"
    REPAIR_DOORS = "doors_windows"
    REPAIR_CHOICES = [
        (REPAIR_WATER, "Water leak"),
        (REPAIR_ELECTRICAL, "Electrical"),
        (REPAIR_HEATING, "Heating"),
        (REPAIR_DAMP, "Damp and mould"),
        (REPAIR_ROOFING, "Roofing"),
        (REPAIR_DOORS, "Doors and windows"),
    ]

    PRIORITY_EMERGENCY = "emergency"
    PRIORITY_URGENT = "urgent"
    PRIORITY_ROUTINE = "routine"
    PRIORITY_CHOICES = [
        (PRIORITY_EMERGENCY, "Emergency"),
        (PRIORITY_URGENT, "Urgent"),
        (PRIORITY_ROUTINE, "Routine"),
    ]

    STATUS_OPEN = "open"
    STATUS_AWAITING_CONTRACTOR = "awaiting_contractor"
    STATUS_AWAITING_RESIDENT = "awaiting_resident"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_AWAITING_CONTRACTOR, "Awaiting contractor"),
        (STATUS_AWAITING_RESIDENT, "Awaiting resident"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_CLOSED, "Closed"),
    ]

    TRADE_CHOICES = [
        ("plumber", "Plumber"),
        ("electrician", "Electrician"),
        ("plumber_electrician", "Plumber / Electrician"),
        ("heating_engineer", "Heating Engineer"),
        ("damp_specialist", "Damp Specialist"),
        ("roofer", "Roofer"),
        ("locksmith", "Locksmith"),
        ("joiner", "Joiner"),
    ]

    reference = models.CharField(max_length=24, unique=True, editable=False)
    address = models.CharField(max_length=160)
    resident_name = models.CharField(max_length=120, blank=True)
    repair_type = models.CharField(max_length=30, choices=REPAIR_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN
    )
    trade = models.CharField(max_length=30, choices=TRADE_CHOICES)
    summary = models.TextField(help_text="What was reported and why this priority.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cases_raised",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

    def get_absolute_url(self):
        return reverse("case_detail", kwargs={"reference": self.reference})

    def save(self, *args, **kwargs):
        if not self.reference:
            stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
            self.reference = f"CM-{stamp}-{secrets.token_hex(2)}"
            while Case.objects.filter(reference=self.reference).exists():
                self.reference = f"CM-{stamp}-{secrets.token_hex(2)}"
        if self.status == self.STATUS_CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        if self.status != self.STATUS_CLOSED:
            self.closed_at = None
        super().save(*args, **kwargs)


class CaseNote(models.Model):
    NOTE = "note"
    STATUS = "status"
    KIND_CHOICES = [
        (NOTE, "Case note"),
        (STATUS, "Status change"),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="case_notes"
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=NOTE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case.reference} {self.kind} {self.created_at:%Y-%m-%d %H:%M}"
