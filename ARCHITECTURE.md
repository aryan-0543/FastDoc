# Document Management System Architecture

This project is a Document Management System being built step by step while
following Corey Schafer's FastAPI tutorial as the technical reference.

The goal is to translate each tutorial concept into this project's domain
instead of copying the tutorial's blog application directly.

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

### Follow the tutorial's progression

The project should stay parallel to the tutorial's learning path. When the
tutorial introduces a feature, this project should implement the equivalent
Document Management System feature.

### Translate blog concepts into document concepts

The tutorial uses a blog as its example domain. This project should map those
ideas into the document management domain.

Current expected mappings:

| Tutorial blog concept | DMS equivalent |
| --- | --- |
| Post | Document |
| Posts list | Documents list |
| Post title | Document title |
| Post content | Document description or summary |
| Author | Owner or uploader |
| Date posted | Date uploaded or date created |
| `/posts` | `/documents` |
| `/api/posts` | `/api/documents` |

### Keep temporary data until the tutorial reaches persistence

The current in-memory list is appropriate for the early tutorial stage. It
should be replaced by database-backed models only when the tutorial reaches the
database section.

### Keep the architecture beginner-friendly

The project should not introduce advanced layering, service classes, background
workers, cloud storage, vector databases, or AI/RAG infrastructure before the
tutorial has introduced the necessary foundation.

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

## Differences From The Tutorial

The tutorial's application is a blog. This project is a Document Management
System.

The difference should be domain-specific, not architectural:

- Use the same concepts and project progression as the tutorial.
- Rename and reshape blog features into document management features.
- Avoid adding unrelated DMS features before the tutorial has introduced the
  supporting concepts.

Current difference:

- The project goal is DMS-oriented, but the current code still contains blog
  naming and sample blog posts. This is an early-stage mismatch to fix after
  approval.

## Important Assumptions And Tradeoffs

- The app is intentionally simple right now because the tutorial is still early.
- Temporary in-memory data is acceptable until the database section.
- Routes and templates may still be in one file until the tutorial introduces a
  reason to split them.
- The UI can be document-branded before the database and upload features exist.
- Actual document file uploads should wait until the tutorial reaches forms,
  request handling, or an equivalent concept.
- Authentication should wait until the tutorial introduces users/login concepts.
- AI/RAG features should wait until after the core DMS has users, documents,
  persistence, and file storage.

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

Later, when the tutorial reaches the matching concepts:

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

## Change Workflow

For future tutorial steps:

1. Identify what Corey implemented in the tutorial.
2. Translate that feature into the Document Management System domain.
3. List the files that need to change.
4. Explain why each file needs to change.
5. Flag tutorial decisions that do not fit this project.
6. Wait for approval before changing application code.
7. Keep this architecture document updated as decisions are made.
