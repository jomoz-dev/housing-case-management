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


OPEN_STATUS_CHOICES = [
    choice for choice in Case.STATUS_CHOICES if choice[0] != Case.STATUS_CLOSED
]


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=OPEN_STATUS_CHOICES)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Why the status is changing (access, contractor booked, complete).",
    )


class CloseCaseForm(forms.Form):
    reason = forms.CharField(
        min_length=12,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Why this job is closed: completed, cancelled, duplicate, or no access after follow-up.",
        error_messages={
            "min_length": "Give a real close reason (at least 12 characters) so the next user can see why.",
        },
    )
    confirm = forms.BooleanField(
        label="I confirm this case should be closed and will stay on the record",
    )
