from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.db.repositories import UserRepository

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    return get_client()[settings.mongo_db]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ensure_indexes() -> None:
    db = get_db()
    await db.users.create_index("username", unique=True)
    await db.users.create_index([("role", 1), ("active", 1)])
    await db.students.create_index([("class_id", 1), ("roll_no", 1)], unique=True)
    await db.students.create_index("user_id")
    await db.attendance.create_index([("student_id", 1), ("class_id", 1), ("date", 1)], unique=True)
    await db.attendance.create_index([("class_id", 1), ("date", 1)])
    await db.classes.create_index("class_id", unique=True)
    await db.classes.create_index("teacher_id")
    await db.recognition_audit.create_index([("created_at", -1)])
    await ensure_admin_user()


async def ensure_admin_user() -> None:
    settings = get_settings()
    db = get_db()
    existing = await db.users.find_one({"role": "admin"})
    if existing:
        return
    await UserRepository(db).create(
        username=settings.admin_username,
        password=settings.admin_password,
        role="admin",
        name=settings.admin_name,
        verified=True,
    )
