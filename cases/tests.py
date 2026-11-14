import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from cases.models import Case, CaseNote


@pytest.fixture
def advisor(db):
    return User.objects.create_user(username="advisor", password="changeme")


@pytest.fixture
def case(advisor):
    return Case.objects.create(
        address="12 Oak Court",
        resident_name="A. Rahman",
        repair_type=Case.REPAIR_WATER,
        priority=Case.PRIORITY_EMERGENCY,
        trade="plumber_electrician",
        summary="Water on a socket.",
        created_by=advisor,
    )


@pytest.mark.django_db
def test_list_requires_login(client):
    response = client.get(reverse("case_list"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_list_shows_case(client, advisor, case):
    client.login(username="advisor", password="changeme")
    response = client.get(reverse("case_list"))
    assert response.status_code == 200
    assert case.reference.encode() in response.content
    assert b"12 Oak Court" in response.content
    assert b"Raise a case" in response.content


@pytest.mark.django_db
def test_create_case_assigns_reference_and_opening_note(client, advisor):
    client.login(username="advisor", password="changeme")
    response = client.post(
        reverse("case_create"),
        {
            "address": "1 Test Street",
            "resident_name": "B. Smith",
            "repair_type": Case.REPAIR_HEATING,
            "priority": Case.PRIORITY_URGENT,
            "trade": "heating_engineer",
            "access": Case.ACCESS_AVAILABLE,
            "summary": "No heating overnight.",
        },
    )
    case = Case.objects.get(address="1 Test Street")
    assert case.reference.startswith("CM-")
    assert response.status_code == 302
    assert case.get_absolute_url() in response.url
    assert case.notes.filter(kind=CaseNote.STATUS).exists()


@pytest.mark.django_db
def test_status_change_writes_audit_note(client, advisor, case):
    client.login(username="advisor", password="changeme")
    response = client.post(
        case.get_absolute_url(),
        {
            "action": "status",
            "status": Case.STATUS_AWAITING_CONTRACTOR,
            "comment": "Sent to heating contractor.",
        },
    )
    case.refresh_from_db()
    assert case.status == Case.STATUS_AWAITING_CONTRACTOR
    assert response.status_code == 302
    note = case.notes.filter(kind=CaseNote.STATUS).first()
    assert "Awaiting contractor" in note.body
    assert "Sent to heating contractor" in note.body


@pytest.mark.django_db
def test_filter_by_priority(client, advisor, case):
    client.login(username="advisor", password="changeme")
    Case.objects.create(
        address="Routine House",
        repair_type=Case.REPAIR_ELECTRICAL,
        priority=Case.PRIORITY_ROUTINE,
        trade="electrician",
        summary="Flickering light.",
        created_by=advisor,
    )
    response = client.get(reverse("case_list"), {"priority": "emergency"})
    assert b"12 Oak Court" in response.content
    assert b"Routine House" not in response.content


@pytest.mark.django_db
def test_cannot_close_from_status_form(client, advisor, case):
    client.login(username="advisor", password="changeme")
    response = client.post(
        case.get_absolute_url(),
        {"action": "status", "status": Case.STATUS_CLOSED, "comment": "Done."},
    )
    case.refresh_from_db()
    assert case.status != Case.STATUS_CLOSED
    assert response.status_code == 302
    assert "/close/" in response.url


@pytest.mark.django_db
def test_close_requires_reason_and_confirm(client, advisor, case):
    client.login(username="advisor", password="changeme")
    url = reverse("case_close", kwargs={"reference": case.reference})
    response = client.post(url, {"reason": "too short", "confirm": ""})
    case.refresh_from_db()
    assert case.status == Case.STATUS_OPEN
    assert response.status_code == 200


@pytest.mark.django_db
def test_close_with_reason_writes_audit_and_sets_closed_at(client, advisor, case):
    client.login(username="advisor", password="changeme")
    url = reverse("case_close", kwargs={"reference": case.reference})
    response = client.post(
        url,
        {
            "reason": "Contractor completed the leak repair and electrics are dry.",
            "confirm": "on",
        },
    )
    case.refresh_from_db()
    assert response.status_code == 302
    assert case.status == Case.STATUS_CLOSED
    assert case.closed_at is not None
    note = case.notes.filter(kind=CaseNote.STATUS).first()
    assert "Closed" in note.body
    assert "electrics are dry" in note.body


@pytest.mark.django_db
def test_seed_loads_demo_cases():
    from django.core.management import call_command

    call_command("seed_cases")
    assert Case.objects.filter(reference="CM-DEMO-0001").exists()
    assert Case.objects.filter(status=Case.STATUS_CLOSED).exists()
    assert Case.objects.filter(reference="CM-DEMO-0002", vulnerable=True).exists()
    assert Case.objects.filter(reference="CM-DEMO-0004", access=Case.ACCESS_NO_ACCESS).exists()


@pytest.mark.django_db
def test_filter_vulnerable_and_no_access(client, advisor):
    from django.core.management import call_command

    call_command("seed_cases")
    client.login(username="advisor", password="changeme")
    vulnerable = client.get(reverse("case_list"), {"vulnerable": "1"})
    assert b"4b Highbridge Street" in vulnerable.content
    assert b"8 Abbeyview" not in vulnerable.content
    no_access = client.get(reverse("case_list"), {"access": "no_access"})
    assert b"2 The Green" in no_access.content
    assert b"12 Oak Court" not in no_access.content


@pytest.mark.django_db
def test_update_access_writes_trail(client, advisor, case):
    client.login(username="advisor", password="changeme")
    response = client.post(
        case.get_absolute_url(),
        {
            "action": "access",
            "access": Case.ACCESS_NO_ACCESS,
            "vulnerable": "on",
        },
    )
    case.refresh_from_db()
    assert response.status_code == 302
    assert case.access == Case.ACCESS_NO_ACCESS
    assert case.vulnerable is True
    assert case.notes.filter(body__icontains="No access").exists()


@pytest.mark.django_db
def test_export_requires_login(client):
    response = client.get(reverse("case_export"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_export_csv_respects_filters(client, advisor):
    from django.core.management import call_command

    call_command("seed_cases")
    client.login(username="advisor", password="changeme")
    response = client.get(reverse("case_export"), {"priority": "emergency"})
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    body = response.content.decode("utf-8-sig")
    assert "Reference" in body
    assert "Vulnerable" in body
    assert "CM-DEMO-0001" in body
    assert "CM-DEMO-0002" in body
    assert "CM-DEMO-0006" not in body
