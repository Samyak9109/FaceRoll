from datetime import date

import pytest
from mongomock_motor import AsyncMongoMockClient

from app.db.reports import get_absentees
from app.db.repositories import AttendanceRepository, StudentRepository


@pytest.mark.asyncio
async def test_student_attendance_and_absentee_query(monkeypatch):
    client = AsyncMongoMockClient()
    db = client["face_attendance_test"]
    await db.students.create_index([("class_id", 1), ("roll_no", 1)], unique=True)
    await db.attendance.create_index([("student_id", 1), ("class_id", 1), ("date", 1)], unique=True)

    student_repo = StudentRepository(db)
    attendance_repo = AttendanceRepository(db)

    alice = await student_repo.create("Alice", "45", "CS101", True, [1.0, 0.0])
    bob = await student_repo.create("Bob", "46", "CS101", True, [0.0, 1.0])

    attendance, inserted = await attendance_repo.mark_present(alice["_id"], "CS101", date(2026, 7, 2))
    assert inserted is True
    assert attendance["date"] == "2026-07-02"

    duplicate, inserted = await attendance_repo.mark_present(alice["_id"], "CS101", date(2026, 7, 2))
    assert inserted is False
    assert duplicate["student_id"] == alice["_id"]

    present = await attendance_repo.get_for_class_date("CS101", "2026-07-02")
    assert [row["roll_no"] for row in present] == ["45"]

    absentees = await get_absentees(db, "CS101", "2026-07-02")
    assert [student["_id"] for student in absentees] == [bob["_id"]]
