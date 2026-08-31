import asyncio
from pathlib import Path

import httpx
from sqlalchemy import delete

import models
from database import AsyncSessionLocal
from main import app

# Number of test users/documents to create
NUM_USERS = 5
NUM_DOCUMENTS = 50

POPULATE_DIR = Path("populate_documents")


async def clear_database():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.Document))
        await db.execute(delete(models.User))
        await db.commit()

    print("Database cleared.")


def create_dummy_files():
    POPULATE_DIR.mkdir(exist_ok=True)

    files = []

    for i in range(1, NUM_DOCUMENTS + 1):
        file_path = POPULATE_DIR / f"document_{i}.txt"

        file_path.write_text(
            f"This is test document number {i}.\n"
            "This file was created automatically for pagination testing.\n"
        )

        files.append(file_path)

    return files


async def populate():
    await clear_database()

    files = create_dummy_files()

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:

        users = []

        # -------------------------
        # Create users
        # -------------------------
        print(f"\nCreating {NUM_USERS} users...")

        for i in range(1, NUM_USERS + 1):

            user_data = {
                "username": f"testuser{i}",
                "email": f"testuser{i}@example.com",
                "password": "TestPassword123!",
            }

            response = await client.post(
                "/api/users",
                json=user_data,
            )

            response.raise_for_status()

            user = response.json()

            print(f"Created user: {user['username']}")

            # -------------------------
            # Login → get JWT
            # -------------------------

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )

            response.raise_for_status()

            token = response.json()["access_token"]

            users.append(
                {
                    "id": user["id"],
                    "token": token,
                }
            )

        # -------------------------
        # Create documents
        # -------------------------

        print(f"\nCreating {NUM_DOCUMENTS} documents...")

        for i, file_path in enumerate(files):

            # Rotate through users
            user = users[i % len(users)]

            with file_path.open("rb") as file:

                response = await client.post(
                    "/api/documents",
                    files={
                        "file": (
                            file_path.name,
                            file,
                            "text/plain",
                        )
                    },
                    headers={
                        "Authorization": f"Bearer {user['token']}"
                    },
                )

            response.raise_for_status()

            document = response.json()

            print(
                f"Created document {i + 1}: "
                f"{document['name']} "
                f"(user {user['id']})"
            )

    print("\nDone!")
    print(f"Created {NUM_USERS} users.")
    print(f"Created {NUM_DOCUMENTS} documents.")


if __name__ == "__main__":
    asyncio.run(populate())