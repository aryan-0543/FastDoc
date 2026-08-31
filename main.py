from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from config import settings
from database import Base, engine, get_db
from routers import documents, users


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

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/", include_in_schema=False, name="home")
@app.get("/documents", include_in_schema=False, name="documents")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    count_result = await db.execute(
        select(func.count()).select_from(models.Document)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Document)
        .options(selectinload(models.Document.owner))
        .order_by(models.Document.date_updated.desc())
        .limit(settings.documents_per_page),
    )
    documents = result.scalars().all()

    has_more = len(documents) < total

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "documents": documents,
            "title": "Home",
            "app_name": "FastDoc",
            "tagline": "A simple document management and retrieval system.",
            "limit": settings.documents_per_page,
            "has_more": has_more,
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
        .order_by(models.Document.date_updated.desc())
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


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )


@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )


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
