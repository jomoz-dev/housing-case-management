from django.contrib import admin

from .models import Case, CaseNote


class CaseNoteInline(admin.TabularInline):
    model = CaseNote
    extra = 0
    readonly_fields = ("author", "kind", "created_at")


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "address",
        "repair_type",
        "priority",
        "status",
        "trade",
        "access",
        "vulnerable",
        "created_at",
    )
    list_filter = ("status", "priority", "repair_type", "trade", "access", "vulnerable")
    search_fields = ("reference", "address", "resident_name", "summary")
    inlines = [CaseNoteInline]


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ("case", "kind", "author", "created_at")
    list_filter = ("kind",)
