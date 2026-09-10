````markdown
# FastDoc

FastDoc is a document management web application built with FastAPI, PostgreSQL, SQLAlchemy, and Jinja2.

The application allows users to register, authenticate, upload documents, view document metadata, update their documents, and delete documents they own.

## Features

- User registration
- Secure password hashing using Argon2
- JWT-based authentication
- OAuth2 Password Bearer authentication
- Login and access-token generation
- Current-user (`/me`) endpoint
- Document upload
- Document metadata management
- Document file replacement/update
- Document deletion
- User ownership checks
- Document pagination
- Profile picture upload
- Password reset functionality
- Email testing with Mailtrap
- Automated API tests using pytest
- PostgreSQL test database
- Mocked AWS S3 testing with Moto

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy 2.0
- Pydantic
- Pydantic Settings
- PostgreSQL

### Authentication

- JWT
- PyJWT
- OAuth2 Password Bearer
- pwdlib
- Argon2

### Testing

- pytest
- AnyIO
- HTTPX AsyncClient
- Moto
- AsyncMock

### Frontend

- Jinja2
- HTML
- CSS
- JavaScript
- Bootstrap

### Other

- Mailtrap for testing password-reset emails

---

## Project Structure

get-fast-API/
│
├── main.py
├── models.py
├── schemas.py
├── database.py
├── auth.py
├── config.py
│
├── routers/
│   ├── users.py
│   └── documents.py
│
├── templates/
│   ├── layout.html
│   ├── login.html
│   ├── register.html
│   ├── documents.html
│   └── doc.html
│
├── static/
│   ├── css/
│   └── js/
│
├── uploads/
│
├── tests/
│   ├── conftest.py
│   ├── test_users.py
│   └── test_documents.py
│
├── .env
├── .gitignore
└── README.md
````

---

# Authentication

FastDoc uses **JWT-based authentication with the OAuth2 Password Bearer flow**.

### Authentication Flow

```text
REGISTER
   │
   ▼
username + email + password
   │
   ▼
Hash password with Argon2
   │
   ▼
Store password hash in PostgreSQL
```

After registration:

```text
LOGIN
   │
   ▼
email + password
   │
   ▼
Find user in database
   │
   ▼
Verify password using Argon2
   │
   ▼
Create JWT access token
   │
   ▼
Return access token
```

For authenticated requests:

```text
Client
   │
   │ Authorization: Bearer <JWT>
   ▼
FastAPI
   │
   ▼
Verify JWT
   │
   ▼
Extract user ID from "sub"
   │
   ▼
Find user in database
   │
   ▼
Current User
```

### Password Security

Passwords are never stored as plain text.

They are hashed using Argon2 through `pwdlib`.

```text
Plain password
      │
      ▼
    Argon2
      │
      ▼
Password hash
      │
      ▼
PostgreSQL
```

---

# API Endpoints

## Users

### Register

```http
POST /api/users
```

Example request:

```json
{
    "username": "aryan",
    "email": "aryan@example.com",
    "password": "password123"
}
```

### Login

```http
POST /api/users/token
```

Returns:

```json
{
    "access_token": "<JWT>",
    "token_type": "bearer"
}
```

### Get Current User

```http
GET /api/users/me
```

Requires:

```http
Authorization: Bearer <JWT>
```

### Upload Profile Picture

```http
PATCH /api/users/{user_id}/picture
```

Requires authentication.

### Forgot Password

```http
POST /api/users/forgot-password
```

Used to initiate the password reset process.

---

# Documents

### Get Documents

```http
GET /api/documents
```

Supports pagination:

```http
GET /api/documents?skip=0&limit=10
```

### Upload Document

```http
POST /api/documents
```

Requires authentication.

Uploaded documents are currently stored locally in the `uploads/` directory.

### Get Document

```http
GET /api/documents/{doc_id}
```

### Update Document Metadata

```http
PUT /api/documents/{doc_id}
```

Requires authentication and document ownership.

### Replace Document File

```http
PUT /api/documents/{doc_id}/file
```

Requires authentication and document ownership.

### Delete Document

```http
DELETE /api/documents/{doc_id}
```

Requires authentication and document ownership.

---

# Database

The application uses **PostgreSQL** with **SQLAlchemy's asynchronous API**.

The main database models are:

```text
User
 │
 ├── Documents
 │
 └── PasswordResetTokens
```

A document belongs to a user through:

```text
documents.user_id → users.id
```

The `User` model stores the password as a hash rather than the original password.

The `Document` model stores metadata such as:

* Document name
* File path
* File type
* File size
* Creation date
* Update date
* Folder ID
* Owner
* Public/private status

---

# File Uploads

Documents are currently stored locally.

```text
Uploaded File
     │
     ▼
FastAPI
     │
     ▼
uploads/
     │
     └── document file
```

Profile pictures are stored under the application's media directory.

The project also includes mocked AWS S3 testing using **Moto**, allowing S3-related behavior to be tested without making real AWS requests.

---

# Password Reset

The application includes a password reset workflow using Mailtrap for development/testing.

```text
User requests password reset
        │
        ▼
Generate reset token
        │
        ▼
Store token hash
        │
        ▼
Send reset email
        │
        ▼
Mailtrap
        │
        ▼
User opens reset link
        │
        ▼
Set new password
```

---

# Testing

The project uses **pytest** for automated testing.

Run all tests:

```bash
pytest -v
```

Run document tests:

```bash
pytest tests/test_documents.py -v
```

Run user tests:

```bash
pytest tests/test_users.py -v
```

The tests use asynchronous testing with AnyIO and HTTPX.

Example:

```python
@pytest.mark.anyio
async def test_create_document_success(client):
    response = await client.post(...)
    assert response.status_code == 201
```

---

# Test Coverage

## User Tests

The user test suite covers:

* Invalid registration data
* Duplicate email registration
* Successful registration
* Profile picture upload
* Password reset email generation

## Document Tests

The document test suite covers:

* Empty document list
* Document not found
* Document creation
* Unauthorized document creation
* Document metadata update
* Preventing another user from modifying a document
* Document pagination
* Document file replacement
* Document deletion
* Preventing another user from deleting a document

---

# AWS S3 Testing

The project uses **Moto** to mock AWS S3 during testing.

Instead of communicating with the real AWS service:

```text
Test
 │
 ▼
Boto3
 │
 ▼
Moto
 │
 ▼
Fake S3
```

This allows S3-related functionality to be tested without requiring real AWS infrastructure.

---

# Installation

## Clone the Repository

```bash
git clone <your-repository-url>
cd get-fast-API
```

## Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Database Setup

Make sure PostgreSQL is running and create the database used by the application.

Configure the database connection in the environment configuration.

Example:

```env
DATABASE_URL=postgresql+psycopg://docuser:docpass@localhost/doc
```

Authentication configuration:

```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

# Running the Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Authentication Architecture

The authentication components work together as follows:

```text
pwdlib + Argon2
        │
        ├── Hash passwords
        └── Verify passwords

PyJWT
        │
        ├── Create JWT
        └── Verify JWT

OAuth2PasswordBearer
        │
        └── Extract Bearer token

get_current_user()
        │
        ├── Verify JWT
        ├── Extract user ID
        └── Retrieve user from database

CurrentUser
        │
        └── Inject authenticated user
           into protected endpoints
```
