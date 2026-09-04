import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user


@pytest.mark.anyio
async def test_get_documents_empty(client: AsyncClient):
    response = await client.get("/api/documents")

    assert response.status_code == 200

    data = response.json()

    assert data["documents"] == []
    assert data["total"] == 0
    assert data["has_more"] is False


@pytest.mark.anyio
async def test_get_document_not_found(client: AsyncClient):
    response = await client.get("/api/documents/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.anyio
async def test_create_document_success(client: AsyncClient):
    user = await create_test_user(client)

    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "test.txt",
                b"Hello, this is a test document.",
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "test.txt"
    assert data["user_id"] == user["id"]
    assert data["file_type"] == "txt"
    assert data["file_size"] == len(b"Hello, this is a test document.")
    assert "id" in data
    assert "date_created" in data
    assert "date_updated" in data
    assert "file_path" in data


@pytest.mark.anyio
async def test_create_document_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "test.txt",
                b"Test content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.anyio
async def test_update_document_success(client: AsyncClient):
    await create_test_user(client)

    token = await login_user(client)
    headers = auth_header(token)

    # Create document
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "original.txt",
                b"Original content",
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 201

    document_id = response.json()["id"]

    # Update document name
    response = await client.put(
        f"/api/documents/{document_id}",
        json={
            "name": "renamed.txt",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "renamed.txt"


@pytest.mark.anyio
async def test_update_document_wrong_user(client: AsyncClient):
    # Create user 1
    await create_test_user(
        client,
        username="user1",
        email="user1@example.com",
    )
    token1 = await login_user(
        client,
        email="user1@example.com",
    )

    # User 1 creates document
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "user1.txt",
                b"Only user 1 should edit this.",
                "text/plain",
            )
        },
        headers=auth_header(token1),
    )

    assert response.status_code == 201
    document_id = response.json()["id"]

    # Create user 2
    await create_test_user(
        client,
        username="user2",
        email="user2@example.com",
    )
    token2 = await login_user(
        client,
        email="user2@example.com",
    )

    # User 2 tries to update user 1's document
    response = await client.put(
        f"/api/documents/{document_id}",
        json={
            "name": "hacked.txt",
        },
        headers=auth_header(token2),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == ("Not authorized to update this document")


@pytest.mark.anyio
async def test_get_documents_with_pagination(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    # Create 5 documents
    for i in range(5):
        response = await client.post(
            "/api/documents",
            files={
                "file": (
                    f"document{i}.txt",
                    f"Content for document {i}".encode(),
                    "text/plain",
                )
            },
            headers=headers,
        )
        assert response.status_code == 201

    # Get all documents
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["documents"]) == 5
    assert data["has_more"] is False

    # Limit to 2
    response = await client.get("/api/documents?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["documents"]) == 2
    assert data["has_more"] is True

    # Skip first 2 and get next 2
    response = await client.get("/api/documents?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["documents"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


@pytest.mark.anyio
async def test_update_document_file(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    # Create original document
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "original.txt",
                b"Original content",
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 201
    document_id = response.json()["id"]
    # Replace the file
    response = await client.put(
        f"/api/documents/{document_id}/file",
        files={
            "file": (
                "updated.txt",
                b"Updated content",
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "updated.txt"
    assert data["file_type"] == "txt"
    assert data["file_size"] == len(b"Updated content")


@pytest.mark.anyio
async def test_delete_document_success(client: AsyncClient):
    await create_test_user(client)

    token = await login_user(client)
    headers = auth_header(token)

    # Create document
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "delete_me.txt",
                b"This document will be deleted.",
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 201

    document_id = response.json()["id"]

    # Delete document
    response = await client.delete(
        f"/api/documents/{document_id}",
        headers=headers,
    )

    assert response.status_code == 204

    # Verify it no longer exists
    response = await client.get(f"/api/documents/{document_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.anyio
async def test_delete_document_wrong_user(client: AsyncClient):
    # User 1
    await create_test_user(
        client,
        username="user1",
        email="user1@example.com",
    )

    token1 = await login_user(
        client,
        email="user1@example.com",
    )

    # User 1 creates document
    response = await client.post(
        "/api/documents",
        files={
            "file": (
                "protected.txt",
                b"Protected document",
                "text/plain",
            )
        },
        headers=auth_header(token1),
    )

    assert response.status_code == 201

    document_id = response.json()["id"]

    # User 2
    await create_test_user(
        client,
        username="user2",
        email="user2@example.com",
    )

    token2 = await login_user(
        client,
        email="user2@example.com",
    )

    # User 2 tries to delete User 1's document
    response = await client.delete(
        f"/api/documents/{document_id}",
        headers=auth_header(token2),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == ("Not authorized to delete this document")
