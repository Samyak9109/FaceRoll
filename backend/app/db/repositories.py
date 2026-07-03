from datetime import date, datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password
from app.services.embedding_crypto import decrypt_embedding, encrypt_embedding


def oid(value: str) -> ObjectId:
    return ObjectId(value)


def serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    output = dict(doc)
    if "_id" in output:
        output["_id"] = str(output["_id"])
    if "student_id" in output and isinstance(output["student_id"], ObjectId):
        output["student_id"] = str(output["student_id"])
    if "user_id" in output and isinstance(output["user_id"], ObjectId):
        output["user_id"] = str(output["user_id"])
    if "teacher_id" in output and isinstance(output["teacher_id"], ObjectId):
        output["teacher_id"] = str(output["teacher_id"])
    output.pop("face_embedding_encrypted", None)
    output.pop("face_embedding", None)
    output.pop("password_hash", None)
    return output


class UserRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def create(
        self,
        username: str,
        password: str,
        role: str,
        name: str,
        email: str | None = None,
        assigned_classes: list[str] | None = None,
        subject: str | None = None,
        student_id: str | None = None,
        verified: bool = True,
    ) -> dict[str, Any]:
        doc = {
            "username": username.lower().strip(),
            "password_hash": hash_password(password),
            "role": role,
            "name": name,
            "email": email,
            "assigned_classes": assigned_classes or [],
            "subject": subject,
            "student_id": oid(student_id) if student_id else None,
            "active": True,
            "verified": verified,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_doc(doc)

    async def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        doc = await self.db.users.find_one({"username": username.lower().strip(), "active": True})
        if not doc or not verify_password(password, doc["password_hash"]):
            return None
        return serialize_doc(doc)

    async def get(self, user_id: str) -> dict[str, Any] | None:
        doc = await self.db.users.find_one({"_id": oid(user_id), "active": True})
        return serialize_doc(doc) if doc else None

    async def list_by_role(self, role: str | None = None) -> list[dict[str, Any]]:
        query = {"role": role} if role else {}
        cursor = self.db.users.find(query).sort("created_at", -1)
        return [serialize_doc(doc) async for doc in cursor]

    async def set_student_id(self, user_id: str, student_id: str) -> None:
        await self.db.users.update_one({"_id": oid(user_id)}, {"$set": {"student_id": oid(student_id)}})


class ClassRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def create(
        self,
        class_id: str,
        name: str,
        subject: str,
        teacher_id: str | None = None,
        schedule: str | None = None,
    ) -> dict[str, Any]:
        doc = {
            "class_id": class_id,
            "name": name,
            "subject": subject,
            "teacher_id": oid(teacher_id) if teacher_id else None,
            "schedule": schedule,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.db.classes.insert_one(doc)
        doc["_id"] = result.inserted_id
        if teacher_id:
            await self.db.users.update_one(
                {"_id": oid(teacher_id)},
                {"$addToSet": {"assigned_classes": class_id}, "$set": {"subject": subject}},
            )
        return serialize_doc(doc)

    async def list_all(self) -> list[dict[str, Any]]:
        cursor = self.db.classes.find({}).sort("class_id", 1)
        return [serialize_doc(doc) async for doc in cursor]

    async def list_for_teacher(self, teacher: dict[str, Any]) -> list[dict[str, Any]]:
        cursor = self.db.classes.find({"class_id": {"$in": teacher.get("assigned_classes", [])}}).sort("class_id", 1)
        return [serialize_doc(doc) async for doc in cursor]


class StudentRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def create(
        self,
        name: str,
        roll_no: str,
        class_id: str,
        consent: bool,
        embedding: list[float],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        if not consent:
            raise ValueError("Student consent is required before biometric enrollment")
        doc = {
            "name": name,
            "roll_no": roll_no,
            "class_id": class_id,
            "user_id": oid(user_id) if user_id else None,
            "consent": consent,
            "face_embedding_encrypted": encrypt_embedding(embedding),
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.db.students.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_doc(doc)

    async def list_by_class_with_embeddings(self, class_id: str) -> list[dict[str, Any]]:
        cursor = self.db.students.find({"class_id": class_id})
        students: list[dict[str, Any]] = []
        async for doc in cursor:
            doc["face_embedding"] = decrypt_embedding(doc["face_embedding_encrypted"])
            doc["_id"] = str(doc["_id"])
            students.append(doc)
        return students

    async def list_by_class(self, class_id: str) -> list[dict[str, Any]]:
        cursor = self.db.students.find({"class_id": class_id}).sort("roll_no", 1)
        return [serialize_doc(doc) async for doc in cursor]

    async def list_all(self) -> list[dict[str, Any]]:
        cursor = self.db.students.find({}).sort([("class_id", 1), ("roll_no", 1)])
        return [serialize_doc(doc) async for doc in cursor]

    async def get_by_user(self, user_id: str) -> dict[str, Any] | None:
        doc = await self.db.students.find_one({"user_id": oid(user_id)})
        return serialize_doc(doc) if doc else None


class AttendanceRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def mark_present(self, student_id: str, class_id: str, when: date | None = None) -> tuple[dict[str, Any], bool]:
        now = datetime.now(timezone.utc)
        attendance_date = (when or now.date()).isoformat()
        doc = {
            "student_id": oid(student_id),
            "class_id": class_id,
            "date": attendance_date,
            "time": now.strftime("%H:%M:%S"),
            "status": "present",
        }
        try:
            result = await self.db.attendance.insert_one(doc)
            doc["_id"] = result.inserted_id
            return serialize_doc(doc), True
        except DuplicateKeyError:
            existing = await self.db.attendance.find_one(
                {"student_id": oid(student_id), "class_id": class_id, "date": attendance_date}
            )
            return serialize_doc(existing), False

    async def get_for_class_date(self, class_id: str, attendance_date: str) -> list[dict[str, Any]]:
        pipeline = [
            {"$match": {"class_id": class_id, "date": attendance_date}},
            {"$lookup": {"from": "students", "localField": "student_id", "foreignField": "_id", "as": "student"}},
            {"$unwind": {"path": "$student", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 1,
                "student_id": 1,
                "class_id": 1,
                "date": 1,
                "time": 1,
                "status": 1,
                "name": "$student.name",
                "roll_no": "$student.roll_no",
            }},
            {"$sort": {"roll_no": 1}},
        ]
        cursor = self.db.attendance.aggregate(pipeline)
        return [serialize_doc(doc) async for doc in cursor]

    async def present_counts_by_student(self, class_id: str, start: str, end: str) -> tuple[dict[str, int], list[str]]:
        cursor = self.db.attendance.find(
            {"class_id": class_id, "date": {"$gte": start, "$lte": end}, "status": "present"},
            {"student_id": 1, "date": 1},
        )
        counts: dict[str, int] = {}
        dates: set[str] = set()
        async for row in cursor:
            student_id = str(row["student_id"])
            counts[student_id] = counts.get(student_id, 0) + 1
            dates.add(row["date"])
        return counts, sorted(dates)

    async def get_for_student(self, student_id: str) -> list[dict[str, Any]]:
        cursor = self.db.attendance.find({"student_id": oid(student_id)}).sort([("date", -1), ("time", -1)])
        return [serialize_doc(doc) async for doc in cursor]

    async def present_dates_for_student_class(self, student_id: str, class_id: str) -> set[str]:
        dates = await self.db.attendance.distinct("date", {"student_id": oid(student_id), "class_id": class_id})
        return set(dates)

    async def recorded_dates_for_class(self, class_id: str) -> set[str]:
        dates = await self.db.attendance.distinct("date", {"class_id": class_id})
        return set(dates)

    async def daily_counts_for_classes(self, class_ids: list[str], start: str, end: str) -> list[dict[str, Any]]:
        pipeline = [
            {"$match": {"class_id": {"$in": class_ids}, "date": {"$gte": start, "$lte": end}, "status": "present"}},
            {"$group": {"_id": {"class_id": "$class_id", "date": "$date"}, "present": {"$sum": 1}}},
            {"$sort": {"_id.date": 1, "_id.class_id": 1}},
        ]
        cursor = self.db.attendance.aggregate(pipeline)
        return [
            {"class_id": row["_id"]["class_id"], "date": row["_id"]["date"], "present": row["present"]}
            async for row in cursor
        ]


class AuditRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def log_attempt(self, class_id: str, matched: bool, score: float | None, student_id: str | None) -> None:
        await self.db.recognition_audit.insert_one(
            {
                "class_id": class_id,
                "matched": matched,
                "score": score,
                "student_id": oid(student_id) if student_id else None,
                "created_at": datetime.now(timezone.utc),
            }
        )
