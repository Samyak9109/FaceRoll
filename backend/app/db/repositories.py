from datetime import date, datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.services.embedding_crypto import decrypt_embedding, encrypt_embedding


def oid(value: str) -> ObjectId:
    return ObjectId(value)


def serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    output = dict(doc)
    if "_id" in output:
        output["_id"] = str(output["_id"])
    if "student_id" in output and isinstance(output["student_id"], ObjectId):
        output["student_id"] = str(output["student_id"])
    output.pop("face_embedding_encrypted", None)
    output.pop("face_embedding", None)
    return output


class StudentRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    async def create(self, name: str, roll_no: str, class_id: str, consent: bool, embedding: list[float]) -> dict[str, Any]:
        if not consent:
            raise ValueError("Student consent is required before biometric enrollment")
        doc = {
            "name": name,
            "roll_no": roll_no,
            "class_id": class_id,
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
