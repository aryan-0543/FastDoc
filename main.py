from fastapi import FastAPI, HTTPException, Request, status
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
@app.get("/docs", include_in_schema=False, name="docs")
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

# CREATE PAGES FOR PARTICULAR DOCUMENT( IN TUTORIAL CREATING PAGES FOR PARTICULAR POST)
@app.get("/docs/{doc_id}", include_in_schema=False)
def doc_page(request: Request, doc_id: int):
    for doc in documents:
        if doc.get("id") == doc_id:
            title = doc["title"][:50]
            return templates.TemplateResponse(
                request,
                "doc.html",
                {"doc": doc, "title": title},
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="doc not found")



@app.get("/api/docs")
def get_documents():
    return documents

@app.get("/api/docs/{doc_id}")
def get_doc(doc_id: int):
    for doc in documents:
        if doc.get("id") == doc_id:
            return doc
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="doc not found")

