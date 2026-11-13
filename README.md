# AI-Powered Civic Complaint Management System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205.3-7952B3.svg)](https://getbootstrap.com/)
[![Testing](https://img.shields.io/badge/Tests-18%2F18%20Passed%20(100%25)-brightgreen.svg)]()

A centralized, full-stack civic grievance redressal and tracking web application developed for municipal governance. The system modernizes public infrastructure defect reporting (potholes, open drains, broken streetlights, sanitation) by automating intake, departmental routing to municipal officers, real-time lifecycle tracking across a 6-stage progress stepper, and transparent chronological audit logging.

---

## System Roles & Personas (RBAC)

The system implements strict **Role-Based Access Control (RBAC)** across three personas:

| Role | Permissions & Workflow | Default Demo Account |
| :--- | :--- | :--- |
| **Citizen** | Registers account, files grievances with location boundaries and photo evidence, tracks own complaints, searches by ID, views 6-stage lifecycle progress stepper & audit trail. | `abc@gmail.com` / `pass123` *(or register live)* |
| **Municipal Officer** | Inspects departmental grievance queue, reviews photo evidence, updates status (*In Progress*, *Needs More Info*, *Complaint Resolved*, *Complaint Rejected*) with field remarks. | `rajesh.sharma@civic.gov.in` / `officer123` |
| **Administrator** | Accesses municipal analytics dashboard, monitors system metrics (total user counts and aggregate civic grievance volume). | `ananya.verma@civic.gov.in` / `admin123` |

---

## Key Features & Technical Highlights

### 1. Complaint Submission Module (SRS Feature 2, FR-4 to FR-6)
- **Input Validation:** Mandatory field validation with boundary constraints on location ($3 \le \text{length} \le 200$ chars) and whitelisted categories.
- **Defense-in-Depth File Security:** Whitelisted MIME-type and extension validation (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) preventing executable payloads (`.exe`, `.sh`, `.py`), enforced with a 5MB size limit.
- **Client-Side Live Preview:** Instant image thumbnail preview before form submission via HTML5 FileReader API.
- **Automated Intake & Routing:** Generates unique Complaint IDs and automatically assigns new grievances to the designated municipal officer with dual initial audit entries.

### 2. Complaint Tracking & Lifecycle Module (SRS Feature 4, FR-10)
- **Strict Ownership Isolation (IDOR Prevention):** Cross-tenant security check ensures citizens can only query and view their own complaints; unauthorized URL tampering returns `HTTP 403 Forbidden`.
- **Dual-Mode Search & Filter:** Exact numeric Complaint ID lookup, case-insensitive keyword search, and lifecycle status dropdown filtering.
- **6-Stage Lifecycle Progress Stepper:** Dynamic visual tracker displaying stages:
  $$\text{Submitted} \longrightarrow \text{Categorized} \longrightarrow \text{Assigned} \longrightarrow \text{Under Review} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved}$$
- **Chronological Audit Trail:** Immutable `StatusHistory` table capturing timestamps, actor identities (Citizen, AI Service, Municipal Officer), and official resolution remarks.

---

## Technology Stack

- **Backend Framework:** Python 3.12, Flask 3.1 (Modular Blueprints architecture)
- **Database & ORM:** SQLite 3, Flask-SQLAlchemy / SQLAlchemy 2.0
- **Security & Authentication:** Werkzeug cryptographic salted SHA-256 password hashing, HTTP session management, server-side RBAC decorators (`@login_required`, `@role_required`)
- **Frontend / Templating:** Jinja2 server-side rendering, Bootstrap 5.3, Bootstrap Icons
- **Testing & Quality Assurance:** Python `unittest` (in-memory SQLite test harness), `pandas`, `openpyxl`
- **Project Management:** Atlassian JIRA (Agile Scrum, Fibonacci story estimation, Sprints 1–3)

---

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
cd <YOUR_REPO_NAME>
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed Pre-configured Demo Accounts
```bash
python seed_demo_data.py
```
*Seeds Officer Rajesh Sharma and Administrator Ananya Verma.*

### 5. Start the Application
```bash
python app.py
```
---

## Automated Testing Suite

The project includes an automated test harness covering **6 Software Engineering Testing Techniques** ($3 \text{ test cases each} = 18 \text{ total}$):

1. **Boundary Value Analysis (BVA):** Min/max location length (2, 3, 200, 201 chars), title boundary.
2. **Equivalence Partitioning (EP):** File extensions (PNG vs EXE), category whitelisting, numeric ID vs text search classes.
3. **Functional Testing:** End-to-end complaint submission, detail page rendering, role-based redirection.
4. **Integration Testing:** Multi-table database transactions (`complaints` $\leftrightarrow$ `status_history`), session binding, IDOR security boundaries.
5. **Unit Testing:** `allowed_file()` validator in isolation, ORM model default initialization, string representation formatting.
6. **Validation Testing:** Blank mandatory field rejection, search whitespace trimming, status filter dataset isolation.

### Run the Tests:
```bash
# Run comprehensive 18-case suite and export styled Excel report
python run_comprehensive_tests.py

# Run prototype core test suite (20 tests / 25 assertions)
python test_prototype.py
```

---

## Database Inspection CLI

To quickly view the state of the SQLite database directly in your terminal:
```bash
python view_database.py
```
Displays formatted ASCII tables for `users`, `complaints`, and `status_history`.

---

## Project Directory Structure

```text
APCCMS/
│── app.py                         # Application factory & Blueprint registration
│── config.py                      # System configuration & upload limits
│── requirements.txt               # Dependencies list
│── seed_demo_data.py              # Database seeding script for demo accounts
│── run_comprehensive_tests.py     # 18-case automated test suite & Excel exporter
│── test_prototype.py              # 20-test prototype integration test suite
│── view_database.py               # Database inspection CLI utility
│── civic_complaint_test_cases.csv # Formatted CSV test matrix
│── instance/
│   └── civic_complaints.db        # SQLite database
│── models/
│   ├── __init__.py                # Database instance
│   ├── user.py                    # User model & password hashing
│   └── complaint.py               # Complaint & StatusHistory models
│── routes/
│   ├── __init__.py                # RBAC decorators (@login_required, @role_required)
│   ├── auth.py                    # Authentication controller (login, register, logout)
│   ├── citizen.py                 # Citizen controller (submit, track, search, detail)
│   ├── officer.py                 # Municipal Officer controller (queue, status updates)
│   └── admin.py                   # Administrator analytics controller
├── static/
│   ├── css/                       # Custom styles
│   └── uploads/                   # Uploaded citizen evidence images
└── templates/
    ├── base.html                  # Master layout with responsive navbar & alerts
    ├── index.html                 # Public landing page
    ├── 403.html / 404.html        # Custom HTTP error pages
    ├── auth/                      # Login & Registration templates
    ├── citizen/                   # Submission & Tracking templates
    ├── officer/                   # Officer queue & action dashboard
    └── admin/                     # Administrator analytics dashboard
```
