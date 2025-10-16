# Django Project Setup Guide

This guide explains how to set up and run the **Django project locally**, both on **Windows** and **Linux/macOS** systems.

-----

## 🧰 Prerequisites

Before starting, make sure you have the following installed:

  * [**Python 3.8+**](https://www.python.org/downloads/)
  * [**pip**](https://pip.pypa.io/en/stable/installation/)
  * (Optional but recommended) [**Virtualenv**](https://virtualenv.pypa.io/en/latest/) or `venv`

-----

## ⚙️ Setup Instructions

### 🔹 1. Activate the Virtual Environment

#### **Windows**

```powershell
.\env\Scripts\activate
```

#### **Linux / macOS**

```bash
source env/bin/activate
```

### 🔹 2. Install Required Packages

Install all dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 🔹 3. Apply Migrations

Prepare the database schema.

1.  **Make migrations** for your app (e.g., `survey_app`):
    ```bash
    python manage.py makemigrations survey_app
    ```
2.  **Apply all migrations**:
    ```bash
    python manage.py migrate
    ```

### 🔹 4. Create a Superuser

Set up an admin account for Django’s admin panel:

```bash
python manage.py createsuperuser
```

> **Note:** Follow the prompts to create your username, email, and password.

### 🔹 5. Run the Development Server

Start the Django server on port 8000 or any port:

```bash
python manage.py runserver 8000
```

Then open your browser and visit:

[**http://127.0.0.1:8000/**](http://127.0.0.1:8000/)

-----

## 🧪 Optional: Verifying Setup

After running the server, log in to the Django admin panel:

[**http://127.0.0.1:8000/admin/**](http://127.0.0.1:8000/admin/)

Use the credentials from your superuser account.