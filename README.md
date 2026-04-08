# 📦 IMS Pro - Backend API

![CI Status](https://github.com/JackScoble/ims-backend/actions/workflows/backend-ci.yml/badge.svg)

Welcome to the backend repository for **IMS Pro**, a robust Inventory Management System. This Django REST Framework (DRF) API serves as the central data engine, handling complex business logic, real-time audit logging, and automated notification triggers.

✅ **Live Backend:** [Render Deployed Backend](https://ims-backend-9nhi.onrender.com/api/)

🖥️ **Frontend Repository:** [JackScoble/ims-frontend](https://github.com/JackScoble/ims-frontend)

---

## 🛠️ Tech Stack

* **Framework:** Django & Django REST Framework (DRF)
* **Language:** Python 3.x
* **Authentication:** JSON Web Tokens (JWT)
* **Database:** PostgreSQL (Production-ready)

---

## ✨ Key Features

* **Comprehensive Inventory Management:** Full CRUD operations for items and categories with built-in low-stock threshold monitoring.
* **Transaction Processing:** Dedicated order execution endpoints that automatically deduct stock safely.
* **Advanced Audit Engine:** An automated tracking system that logs exactly *who* changed *what*, calculating diffs and capturing object states for strict accountability.
* **Automated Email Alerts:** Intercepts database saves to dispatch HTML-formatted low-stock alerts and secure password reset tokens.
* **Time-Series Analytics:** Captures daily total-value snapshots for financial charting on the frontend.
* **Extended User Profiles:** Custom user schemas mapping organizational departments, job titles, and UI theme preferences.

---

## 🚀 Local Setup Instructions

Follow these steps to get the API running on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/JackScoble/ims-backend.git](https://github.com/JackScoble/ims-backend.git)
cd ims-backend
```

### 2. Set Up a Virtual Environment
It is best practice to run this project inside an isolated virtual environment.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (alongside `manage.py`) and add the following variables:

```ini
# Frontend Settings
FRONTEND_URL=https://glowing-space-engine-r4v46p4pxwxf57xx-5173.app.github.dev

# Cloudinary Settings
CLOUDINARY_CLOUD_NAME=name
CLOUDINARY_API_KEY=key
CLOUDINARY_API_SECRET=secret

# Email Settings
SENDGRID_API_KEY=SG.xyz
DEFAULT_FROM_EMAIL=email

# Database Settings
DB_NAME=inventory_db
DB_USER=myuser
DB_PASSWORD=mypassword
```

### 5. Run Migrations
Apply the database schema:

```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional but recommended)
To access the Django Admin panel:

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server
```bash
python manage.py runserver
```
The API will now be available at http://localhost:8000/.

---

## 🧪 Running Tests
This project includes a comprehensive suite of automated tests verifying business logic, API workflows, and authentication security.

To run the test suite:

```bash
python manage.py test
```

