from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import DocCreate, DocResponse

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
@app.get("/documents", include_in_schema=False, name="documents")
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


@app.get("/documents/{doc_id}", include_in_schema=False)
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


@app.get("/api/documents", response_model=list[DocResponse])
def get_documents():
    return documents


@app.post("/api/documents", response_model=DocResponse, status_code=status.HTTP_201_CREATED,)
def create_post(doc: DocCreate):
    new_id = max(p["id"] for p in documents) + 1 if documents else 1
    new_doc = {
        "id": new_id,
        "title": doc.title,        
        "description": doc.description,
        "category": doc.category,
        "status": doc.status,
        "updated_at": "April 23, 2025",  # hard-coded for now
    }
    documents.append(new_doc)
    return new_doc


@app.get("/api/documents/{doc_id}", response_model=DocResponse)
def get_doc(doc_id: int):
    for doc in documents:
        if doc.get("id") == doc_id:
            return doc
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="doc not found")


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
