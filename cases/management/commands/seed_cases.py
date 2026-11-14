from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from cases.models import Case, CaseNote

CASES = [
    {
        "reference": "CM-DEMO-0001",
        "address": "12 Oak Court, Waltham Abbey",
        "resident_name": "A. Rahman",
        "repair_type": Case.REPAIR_WATER,
        "priority": Case.PRIORITY_EMERGENCY,
        "status": Case.STATUS_IN_PROGRESS,
        "trade": "plumber_electrician",
        "summary": "Active leak into the kitchen, water on a socket. Raised as Emergency Plumber / Electrician.",
        "notes": [
            ("status", "Case opened as Open / Emergency."),
            ("note", "Resident advised not to use the wet socket. Stopcock found under the sink."),
            ("status", "Status changed from Open to In progress. Electrician attending with plumber."),
        ],
    },
    {
        "reference": "CM-DEMO-0002",
        "address": "4b Highbridge Street, Waltham Abbey",
        "resident_name": "M. Cole",
        "repair_type": Case.REPAIR_HEATING,
        "priority": Case.PRIORITY_EMERGENCY,
        "status": Case.STATUS_AWAITING_CONTRACTOR,
        "trade": "heating_engineer",
        "summary": "No heating. Child under 5 in the household. Emergency heating engineer.",
        "notes": [
            ("status", "Case opened as Open / Emergency."),
            ("status", "Status changed from Open to Awaiting contractor. Job sent to heating contractor."),
        ],
    },
    {
        "reference": "CM-DEMO-0003",
        "address": "19 Sewardstone Road",
        "resident_name": "J. Patel",
        "repair_type": Case.REPAIR_DAMP,
        "priority": Case.PRIORITY_URGENT,
        "status": Case.STATUS_OPEN,
        "trade": "damp_specialist",
        "summary": "Visible mould in the bedroom for more than 28 days. Resident reports asthma. Urgent damp specialist.",
        "notes": [
            ("status", "Case opened as Open / Urgent."),
            ("note", "Photo requested. Do not delay the works order if none arrives."),
        ],
    },
    {
        "reference": "CM-DEMO-0004",
        "address": "2 The Green, Upshire",
        "resident_name": "S. Hughes",
        "repair_type": Case.REPAIR_DOORS,
        "priority": Case.PRIORITY_URGENT,
        "status": Case.STATUS_AWAITING_RESIDENT,
        "trade": "locksmith",
        "summary": "Front door will not lock. Resident is staying in tonight. Urgent locksmith.",
        "notes": [
            ("status", "Case opened as Open / Urgent."),
            ("status", "Status changed from Open to Awaiting resident. No access on first attendance."),
        ],
    },
    {
        "reference": "CM-DEMO-0005",
        "address": "Flat 6, 40 Sun Street",
        "resident_name": "L. Okeke",
        "repair_type": Case.REPAIR_ROOFING,
        "priority": Case.PRIORITY_URGENT,
        "status": Case.STATUS_CLOSED,
        "trade": "roofer",
        "summary": "Water entering through the bedroom ceiling after heavy rain. Electrics dry. Urgent roofer.",
        "notes": [
            ("status", "Case opened as Open / Urgent."),
            ("note", "Temporary bowl in place. Resident stayed off the loft."),
            ("status", "Status changed from Open to Closed. Roof tile replaced; stain to dry."),
        ],
    },
    {
        "reference": "CM-DEMO-0006",
        "address": "8 Abbeyview",
        "resident_name": "P. Singh",
        "repair_type": Case.REPAIR_ELECTRICAL,
        "priority": Case.PRIORITY_ROUTINE,
        "status": Case.STATUS_OPEN,
        "trade": "electrician",
        "summary": "Hall light flicker. No burning smell or sparking. Routine electrician.",
        "notes": [
            ("status", "Case opened as Open / Routine."),
        ],
    },
]


class Command(BaseCommand):
    help = "Load demo advisor user and sample housing cases."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="advisor", defaults={"is_staff": False}
        )
        user.set_password("changeme")
        user.save()
        self.stdout.write("Demo user advisor / changeme " + ("created" if created else "updated"))

        admin, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True},
        )
        admin.set_password("changeme")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write("Admin user admin / changeme " + ("created" if admin_created else "updated"))

        for data in CASES:
            notes = data["notes"]
            payload = {k: v for k, v in data.items() if k not in ("notes", "reference")}
            payload["created_by"] = user
            case, _ = Case.objects.update_or_create(
                reference=data["reference"],
                defaults=payload,
            )
            if case.status == Case.STATUS_CLOSED and not case.closed_at:
                case.closed_at = timezone.now()
                case.save(update_fields=["closed_at"])
            if not case.notes.exists():
                for kind, body in notes:
                    CaseNote.objects.create(case=case, author=user, kind=kind, body=body)
        self.stdout.write(f"{len(CASES)} demo cases loaded")
