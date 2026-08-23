import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from database import Base, engine, get_db
from schemas import DocResponse, UserCreate, UserResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastDoc")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def detect_file_type(filename: str, content_type: str | None) -> str:
    extension = Path(filename).suffix.lower().removeprefix(".")
    if extension:
        return extension

    guessed_type = mimetypes.guess_type(filename)[0] or content_type
    if guessed_type and "/" in guessed_type:
        subtype = guessed_type.rsplit("/", maxsplit=1)[-1]
        return "txt" if subtype == "plain" else subtype
    return "txt"


@app.get("/", include_in_schema=False, name="home")
@app.get("/documents", include_in_schema=False, name="documents")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document))
    documents = result.scalars().all()

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
def doc_page(request: Request, doc_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document).where(models.Document.id == doc_id))

    document = result.scalars().first()

    if document:
        title = document.name[:50]

        return templates.TemplateResponse(
            request,
            "doc.html",
            {
                "document": document,
                "title": title,
            },
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found",
    )


@app.get(
    "/users/{user_id}/documents",
    include_in_schema=False,
    name="user_documents",
)
def user_documents_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(
        select(models.Document).where(models.Document.user_id == user_id)
    )

    documents = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_documents.html",
        {
            "documents": documents,
            "user": user,
            "title": f"{user.username}'s Documents",
        },
    )


@app.post(
    "/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.username == user.username),
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    result = db.execute(
        select(models.User).where(models.User.email == user.email),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.get("/api/users/{user_id}/documents", response_model=list[DocResponse])
def get_user_documents(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(
        select(models.Document).where(models.Document.user_id == user_id)
    )

    documents = result.scalars().all()

    return documents


@app.get("/api/documents", response_model=list[DocResponse])
def get_documents(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document))
    documents = result.scalars().all()
    return documents


@app.post(
    "/api/documents",
    response_model=DocResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    file: UploadFile = File(...),
    user_id: int = 1,  # temporary until authentication
    db: Annotated[Session, Depends(get_db)] = None,
):
    result = db.execute(select(models.User).where(models.User.id == user_id))

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    safe_filename = Path(file.filename or "document").name

    file_path = UPLOAD_DIR / safe_filename

    file_size = 0

    with file_path.open("wb") as saved_file:
        while chunk := file.file.read(1024 * 1024):
            file_size += len(chunk)
            saved_file.write(chunk)

    file_type = detect_file_type(
        safe_filename,
        file.content_type,
    )

    new_document = models.Document(
        name=safe_filename,
        user_id=user_id,
        file_path=str(file_path),
        file_type=file_type,
        file_size=file_size,
        folder_id=None,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@app.get("/api/documents/{doc_id}", response_model=DocResponse)
def get_document(doc_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document).where(models.Document.id == doc_id))

    document = result.scalars().first()

    if document:
        return document

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found",
    )


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
