# Document Management System Architecture

This project is a Document Management System being built step by step.

## Current Architecture

The application currently has a small FastAPI web app with:

- A single `FastAPI` application instance in `main.py`.
- Static file serving mounted at `/static`.
- Jinja2 templates loaded from the `templates` directory.
- A Bootstrap-based layout in `templates/layout.html`.
- A home page template in `templates/home.html`.
- Temporary in-memory sample data.
- A template-rendered web route.
- A simple JSON API route.

At this stage, the project is still using the tutorial's blog-shaped sample
data (`posts`). This should be translated to document-shaped sample data before
the app moves further into the Document Management System domain.

## Tech Stack

Implemented now:

- Python
- FastAPI
- Jinja2 templates
- HTML
- CSS
- Bootstrap

Planned, but not implemented yet:

- SQLAlchemy
- Psycopg
- PostgreSQL
- Authentication
- JWT
- File storage
- AI/RAG features

## Project Structure

Current structure:

```text
.
├── main.py
├── templates/
│   ├── layout.html
│   └── home.html
├── static/
│   ├── css/
│   │   └── main.css
│   ├── icons/
│   ├── js/
│   │   └── utils.js
│   └── profile_pics/
│       └── default.jpg
├── home_finished.html
├── layout_finished.html
└── snippets.txt
```

Notes:

- `main.py` currently contains the app setup, temporary data, web routes, and
  API routes in one file.
- `templates/` contains Jinja2 templates.
- `static/` contains CSS, JavaScript, icons, and image assets.
- `home_finished.html`, `layout_finished.html`, and `snippets.txt` appear to be
  tutorial reference or scratch files, not active application files.

## Major Decisions

## Why These Technologies Are Chosen

- **FastAPI**: The main web framework used by the tutorial.
- **Jinja2 templates**: Used for server-rendered HTML pages, matching the
  tutorial's web UI approach.
- **HTML/CSS/Bootstrap**: Provides a simple beginner-friendly frontend without
  introducing a separate JavaScript framework.
- **SQLAlchemy**: Planned for database models and queries when persistence is
  introduced.
- **Psycopg**: Planned PostgreSQL driver for Python.
- **PostgreSQL**: Planned relational database for persistent users, documents,
  and metadata.
- **Authentication/JWT**: Planned for login and protected document workflows.
- **File storage**: Planned for actual uploaded document files.
- **AI/RAG features**: Planned later, after the core DMS foundation exists.

## Implemented

- FastAPI app instance.
- Static file mounting.
- Jinja2 template configuration.
- Bootstrap layout.
- Home page rendered through a template.
- Temporary in-memory sample data.
- Simple JSON API endpoint.

## Planned

Near-term, aligned with the current tutorial stage:

- Rename blog branding in the UI to Document Management System branding.
- Translate `posts` sample data into `documents` sample data.
- Rename `/posts` and `/api/posts` to document-oriented routes when approved.
- Update the home template to display documents instead of blog posts.
- Update sidebar labels to DMS concepts.

- Add database configuration.
- Add SQLAlchemy models.
- Add PostgreSQL support with Psycopg.
- Add user registration and login.
- Add JWT authentication if it matches the tutorial's auth flow or is clearly
  needed for the FastAPI version of the project.
- Add document create/read/update/delete workflows.
- Add file upload and file storage.
- Add protected routes for user-owned documents.
- Add AI/RAG features after the document storage foundation is stable.

