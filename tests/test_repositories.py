from datetime import date

import pytest
from mongomock_motor import AsyncMongoMockClient

from app.db.reports import get_absentees
from app.db.reports import generate_report_rows
from app.db.repositories import AttendanceRepository, ClassRepository, StudentRepository, UserRepository


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

    rows = await generate_report_rows(db, "CS101", "2026-07-01", "2026-07-31")
    assert rows == [
        {
            "student_id": alice["_id"],
            "name": "Alice",
            "roll_no": "45",
            "class_id": "CS101",
            "present_days": 1,
            "total_recorded_days": 1,
            "attendance_percent": 100.0,
        },
        {
            "student_id": bob["_id"],
            "name": "Bob",
            "roll_no": "46",
            "class_id": "CS101",
            "present_days": 0,
            "total_recorded_days": 1,
            "attendance_percent": 0.0,
        },
    ]


@pytest.mark.asyncio
async def test_user_authentication_and_class_assignment():
    client = AsyncMongoMockClient()
    db = client["face_attendance_auth_test"]
    await db.users.create_index("username", unique=True)
    await db.classes.create_index("class_id", unique=True)

    users = UserRepository(db)
    classes = ClassRepository(db)

    teacher = await users.create(
        username="teacher.cs",
        password="secure-password",
        role="teacher",
        name="CS Teacher",
        subject="Computer Science",
    )
    assert "password_hash" not in teacher

    authenticated = await users.authenticate("teacher.cs", "secure-password")
    assert authenticated["_id"] == teacher["_id"]
    assert authenticated["role"] == "teacher"
    assert "password_hash" not in authenticated

    assert await users.authenticate("teacher.cs", "wrong-password") is None

    created_class = await classes.create("CS101", "Intro CS", "Computer Science", teacher["_id"])
    assert created_class["class_id"] == "CS101"

    updated_teacher = await users.get(teacher["_id"])
    assert updated_teacher["assigned_classes"] == ["CS101"]
