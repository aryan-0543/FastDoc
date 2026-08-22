from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="FastDoc")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

documents: list[dict] = [
    {
        "id": 1,
        "title": "Product Requirements",
        "description": "Centralized requirements, notes, and project decisions for the FastDoc product.",
        "category": "Planning",
        "status": "Draft",
        "updated_at": "April 20, 2025",
    },
    {
        "id": 2,
        "title": "API Reference",
        "description": "Endpoint notes and backend reference material for future retrieval workflows.",
        "category": "Engineering",
        "status": "Ready",
        "updated_at": "April 21, 2025",
    },
    {
        "id": 3,
        "title": "Onboarding Guide",
        "description": "A starter document for helping new team members find important resources.",
        "category": "Team",
        "status": "Published",
        "updated_at": "April 22, 2025",
    },
]


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "documents": documents,
            "title": "Home",
            "app_name": "FastDoc",
            "tagline": "A simple document management and retrieval system.",
        },
    )


@app.get("/api/posts")
def get_documents():
    return documents
