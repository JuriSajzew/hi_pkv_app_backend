# hi pkv app

This repository contains the backend for the **hi pkv app**.  
It is a Django REST Framework–based API that handles user management,
insurance selection, email workflows, document handling, and supporting
services.

The backend is designed to be production-ready, secure, and easily extensible.

---

## 🚀 Features

- User registration with email verification
- Token-based authentication
- Password reset via email
- User profile management
- Insurance company and tariff selection
- Support for additional (add-on) tariffs
- Contact message handling
- Upload and management of user contract documents (PDF)
- Static file handling
- PostgreSQL support
- PDF parsing and processing
- NLP / AI-ready infrastructure

---

## 🛠 Tech Stack

- **Framework:** Django, Django REST Framework
- **Authentication:** Token Authentication
- **Database:** PostgreSQL
- **Static Files:** WhiteNoise
- **Email:** SMTP (HTML + Plain Text)
- **PDF Processing:** pdfplumber, PyPDF2
- **AI / NLP:** Sentence Transformers, Transformers, Torch
- **Application Server:** Gunicorn

---

## 📦 Installation

Install dependencies using `pip`:

```bash
pip install -r requirements.txt
