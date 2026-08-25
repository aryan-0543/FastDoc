import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import DocResponse, DocUpdate

router = APIRouter()


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

@router.get("", response_model=list[DocResponse])
async def get_documents(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Document).options(selectinload(models.Document.owner)))
    documents = result.scalars().all()
    return documents


@router.post(
    "",
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


@router.get("/{doc_id}", response_model=DocResponse)
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


@router.put(
    "/{doc_id}",
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


@router.put(
    "/{doc_id}/file",
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


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
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
