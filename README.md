# Housing Case Management

Django web application for housing repairs advisors and coordinators: raise a case, keep the works-order trail, change status, and record notes.

This is the third of three related tools:

| Application | Job |
| --- | --- |
| [Housing Repairs Diagnostic Tool](https://github.com/jomoz-dev/housing-repairs-diagnostic-tool) | Decide Emergency / Urgent / Routine, trade and attendance |
| [Repairs Knowledge Base](https://github.com/jomoz-dev/repairs-knowledge-base) | Look up the procedure and what to tell the resident |
| **Housing Case Management** (this app) | Keep the case record after the job is logged |

It is a portfolio piece for Systems Officer, Application Support and Business Analyst roles, and a product that can be offered to private clients who need a lightweight case list without a full housing-management system.

SQLite is used locally. PostgreSQL can replace it later without changing the case model.

---

## What this version does

- Sign-in (Django auth)
- Raise a case: address, resident, repair type, priority, trade, summary
- Unique reference (`CM-YYYYMMDD-HHMMSS-xxxx`)
- Status: Open, Awaiting contractor, Awaiting resident, In progress, Closed
- Case notes and an audit line when status changes
- Close only after a confirmation page with a written reason (the case is not deleted)
- Access and vulnerability flags on the case (no access, appointment needed, vulnerable household)
- CSV export of the current caseload (respects search and filters)
- Search by reference, address or resident
- Filters by status, priority and repair type
- Counts on the case list
- Django admin
- Seeded demo cases and pytest coverage

Repair types match the diagnostic tool and knowledge base: water leak, electrical, heating, damp and mould, roofing, doors and windows.

---

## Run locally

Python 3.9+. Django 4.2 LTS.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_cases
python manage.py runserver
```

Open http://127.0.0.1:8000/

| User | Password | Role |
| --- | --- | --- |
| `advisor` | `changeme` | Raise and progress cases |
| `admin` | `changeme` | Django admin (`/admin/`) |

```bash
python -m pytest
```

---

## How it maps to advisor work

```text
Repair reported
      |
      v
Diagnose (diagnostic tool) / look up procedure (knowledge base)
      |
      v
Raise a case here (priority, trade, summary)
      |
      v
Status: awaiting contractor / resident / in progress
      |
      v
Notes on the record → Closed
```

Demo content is operational sample data, not live resident records.

---

## Project layout

| Path | Role |
| --- | --- |
| `config/` | Django project settings and URLs |
| `cases/` | Case and note models, views, seed command |
| `templates/` | Advisor screens |
| `static/style.css` | Case-desk theme (forest rail, parchment, terracotta) — not the navy diagnostic look |
