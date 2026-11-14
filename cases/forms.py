from django import forms

from .models import Case, CaseNote


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            "address",
            "resident_name",
            "repair_type",
            "priority",
            "trade",
            "summary",
        ]


class CaseNoteForm(forms.ModelForm):
    class Meta:
        model = CaseNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
        }


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=Case.STATUS_CHOICES)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Why the status is changing (access, contractor booked, complete).",
    )
