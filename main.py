import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from database import Base, engine, get_db
from schemas import DocResponse, DocUpdate, UserCreate, UserResponse, UserUpdate


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan, title="FastDoc")

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
async def home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Document).options(selectinload(models.Document.owner))
    )
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
async def doc_page(
    request: Request, doc_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Document)
        .options(selectinload(models.Document.owner))
        .where(models.Document.id == doc_id)
    )

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
async def user_documents_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(models.Document)
        .options(selectinload(models.Document.owner))
        .where(models.Document.user_id == user_id)
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
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.username == user.username),
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    result = await db.execute(
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
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.get("/api/users/{user_id}/documents", response_model=list[DocResponse])
async def get_user_documents(
    user_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(models.Document)
        .options(selectinload(models.Document.owner))
        .where(models.Document.user_id == user_id)
    )

    documents = result.scalars().all()

    return documents


@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_update.username is not None and user_update.username != user.username:
        result = await db.execute(
            select(models.User).where(models.User.username == user_update.username)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(models.User).where(models.User.email == user_update.email)
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


@app.delete(
    "/api/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await db.delete(user)
    await db.commit()


@app.get("/api/documents", response_model=list[DocResponse])
async def get_documents(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Document).options(selectinload(models.Document.owner)))
    documents = result.scalars().all()
    return documents


@app.post(
    "/api/documents",
    response_model=DocResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    file: UploadFile = File(...),
    user_id: int = 1,  # temporary until authentication
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))

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
    await db.commit()
    await db.refresh(new_document,attribute_names=["owner"],)

    return new_document


@app.get("/api/documents/{doc_id}", response_model=DocResponse)
async def get_document(doc_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Document).options(selectinload(models.Document.owner)).where(models.Document.id == doc_id)
    )

    document = result.scalars().first()

    if document:
        return document

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found",
    )


@app.put(
    "/api/documents/{doc_id}",
    response_model=DocResponse,
)
async def update_document_metadata(
    doc_id: int,
    document_data: DocUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Document).where(models.Document.id == doc_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.name = document_data.name

    await db.commit()
    await db.refresh(document,attribute_names=["owner"],)
    return document


@app.put(
    "/api/documents/{doc_id}/file",
    response_model=DocResponse,
)
async def update_document_file(
    doc_id: int,
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(models.Document).where(models.Document.id == doc_id)
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Create safe filename
    safe_filename = Path(file.filename or "document").name
    # Detect file type
    file_type = detect_file_type(
        safe_filename,
        file.content_type,
    )

    # Temporary file path
    new_file_path = UPLOAD_DIR / safe_filename
    # Save replacement file
    file_size = 0
    with new_file_path.open("wb") as saved_file:
        while chunk := file.file.read(1024 * 1024):
            file_size += len(chunk)
            saved_file.write(chunk)

    # Delete old physical file
    old_file_path = Path(document.file_path)
    if old_file_path.exists():
        old_file_path.unlink()

    # Update database metadata
    document.name = safe_filename
    document.file_path = str(new_file_path)
    document.file_type = file_type
    document.file_size = file_size

    await db.commit()
    await db.refresh(document,attribute_names=["owner"],)
    return document


@app.delete("/api/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(doc_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Document).where(models.Document.id == doc_id)
    )

    document = result.scalars().first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    await db.delete(document,attribute_names=["owner"],)
    await db.commit()


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request, exception: StarletteHTTPException
):

    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
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
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

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
