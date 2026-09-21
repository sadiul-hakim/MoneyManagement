# 💸 MoneyFlow — Personal Money Management System

Welcome to **MoneyFlow** (MoneyManagement), a modern, intuitive, and mobile-first personal finance tracking web application built with **Django 6.1** and **Progressive Web App (PWA)** capabilities. Take full control of your daily financial life — from multiple wallet balances and cash flow categorization to peer-to-peer lending, borrowing, and inter-wallet transfers.

---

## ✨ Key Highlights & Features

### 📱 1. Mobile-First Design & PWA Ready
* **Installable App Experience**: Powered by `django-pwa`, install MoneyFlow directly onto your iOS, Android, or desktop device with standalone launch and dedicated app icons.
* **Responsive Bottom Navigation**: Native app-like ergonomics with instant bottom bar navigation for fast thumb navigation on smartphones.
* **Dynamic Dark / Light Theme**: Instant one-tap theme toggle with persistence in `localStorage` and system theme detection.
* **Fast Touch UX**: Touch-optimized form fields, card layouts, status badges, and quick-action modals.

---

### 💼 2. Core Financial Tracking
* **Multi-Wallet Architecture**: Manage separate physical and digital balances (e.g., *Cash in Hand*, *Bank Account*, *bKash*, *Nagad*, *Credit Card*).
* **Income & Expense Tracking**:
  * Organize cash inflows by custom source (Salary, Freelance, Investments, etc.).
  * Track outflows across categories (Groceries, Utilities, Dining, Rent, Entertainment, etc.).
  * Real-time wallet balance calculations upon creation, editing, or deletion of entries.
* **Peer-to-Peer Lending & Borrowing**:
  * Track money lent to or borrowed from colleagues, friends, or family.
  * Expected return dates, notes, and quick status toggles (`✅ Returned` vs. `⏳ Pending`).
* **Inter-Wallet Transfers**:
  * Move money effortlessly between wallets with built-in validation preventing transfers exceeding available balances.
  * Atomic transaction handling and automatic balance reconciliation on edit or delete.

---

### 📊 3. Analytics & Interactive Visual Reports
* **Dashboard Summary**: Real-time overview of total balance, monthly cash flows, ratio progress bars, and recent transaction feeds.
* **In-Depth Reports (`/reports/`)**:
  * Month-by-month cash flow summaries and category-wise spending distributions.
  * Visual metrics for both income channels and expense allocations.

---

### ⚙️ 4. Supercharged Admin Suite with Charts & Advanced Tooling
MoneyFlow features an enterprise-grade Django Admin panel enhanced with powerful community packages:

* 📈 **Admin Charts & Statistics**: Visual graphs and aggregated statistics integrated directly inside admin views using `admin_tools_stats`, `django-admin-charts`, and `django-nvd3` (NVD3 / D3.js).
* 🎨 **Modern Admin Interface**: Customized brand styling, color schemes, and header branding with `django-admin-interface` and `django-colorfield`.
* 🔍 **Select2 Searchable Dropdowns**: Auto-complete and searchable foreign key pickers powered by `django-select2` for smooth entry selection even with high data volume.
* 📅 **Advanced Range Filters**: Drill down through date ranges and monetary amount filters using `django-admin-rangefilter`.
* ⚡ **Quick Action Buttons**: Top-bar action buttons via `django-admin-action-buttons` for quick batch operations (e.g., batch-mark loans as returned).
* 📥📤 **Import / Export Data**: Full spreadsheet (Excel, CSV, JSON) export and import capabilities for all financial records via `django-import-export` and `tablib`.

---

## 🛠️ Technology Stack

Derived directly from [`requirements.txt`](./requirements.txt):

| Category | Technology / Package |
| :--- | :--- |
| **Backend & Framework** | `Django 6.1.1`, `asgiref`, `sqlparse`, `tzdata` |
| **PWA & Mobile** | `django-pwa 2.0.1` |
| **Admin & UI Enhancement** | `django-admin-interface`, `django-colorfield`, `django-select2`, `django-admin-action-buttons`, `django-admin-rangefilter` |
| **Data Import/Export** | `django-import-export 4.4.1`, `tablib`, `diff-match-patch` |
| **Charts & Metrics** | `django-admin-charts`, `admin_tools_stats`, `django-nvd3`, `python-nvd3` |
| **Templating & Utilities** | `Jinja2`, `MarkupSafe`, `Pillow`, `python-dateutil`, `datetime-truncate`, `python-slugify` |

---

## 🚀 Quick Start & Installation

### 1. Clone the repository
```bash
git clone https://github.com/sadiul-hakim/MoneyManagement.git
cd MoneyManagement
```

### 2. Create and activate a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Create a Superuser (for Admin access)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
* **Web App & Dashboard**: `http://127.0.0.1:8000/`
* **Admin Panel**: `http://127.0.0.1:8000/admin/`
* **Reports**: `http://127.0.0.1:8000/reports/`

---

## 🧪 Running Automated Tests

MoneyFlow includes tests covering wallet reconciliations, transfers, income/expense entries, and validation rules:

```bash
python manage.py test
```

---

## 📁 Project Structure

```text
MoneyManagement/
├── MoneyManagement/         # Project configuration & settings
│   ├── settings.py          # App configs, PWA settings, Admin tools
│   ├── urls.py              # Root URL routing & PWA endpoints
│   ├── asgi.py & wsgi.py    # Server gateway entry points
├── main/                    # Main application
│   ├── models.py            # Wallets, Income, Expense, Lending, Borrowing, Transfer
│   ├── views.py             # Dashboard, CRUD views, and Analytics reports
│   ├── forms.py             # Validation forms & widgets
│   ├── admin.py             # Select2 forms, import/export, range filters, actions
│   ├── urls.py              # App routes
│   └── tests.py             # Unit and integration test suite
├── templates/               # Responsive HTML templates
│   ├── base.html            # Theme switch, PWA meta, top bar & bottom nav
│   ├── dashboard.html       # Visual dashboard cards and summary
│   ├── reports.html         # Analytics and cashflow breakdowns
│   └── ...                  # Forms and list templates for all entities
├── static/                  # CSS styles, JavaScript, and PWA icons
├── requirements.txt         # Project dependencies
└── manage.py                # Django CLI management script
```

---

## 💡 Tips & Best Practices
* **PWA on iOS / Android**: On iOS Safari, tap *Share* -> *Add to Home Screen*. On Android Chrome, tap the menu or banner *Install App* to run MoneyFlow in standalone full-screen mode.
* **Backups**: Use the Admin **Export** button on any model table to backup your financial history to `.xlsx` or `.csv`.

---

Happy tracking! 🚀 If you find this project helpful, feel free to give it a ⭐!
