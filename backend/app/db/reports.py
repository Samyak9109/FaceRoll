import csv
from io import StringIO

from app.db.repositories import AttendanceRepository, StudentRepository


async def get_absentees(db, class_id: str, attendance_date: str) -> list[dict]:
    students = await StudentRepository(db).list_by_class(class_id)
    present = await AttendanceRepository(db).get_for_class_date(class_id, attendance_date)
    present_ids = {row["student_id"] for row in present}
    return [student for student in students if student["_id"] not in present_ids]


async def generate_report_rows(db, class_id: str, start_date: str, end_date: str) -> list[dict]:
    student_repo = StudentRepository(db)
    attendance_repo = AttendanceRepository(db)
    students = await student_repo.list_by_class(class_id)
    class_dates = await attendance_repo.class_dates(class_id, start_date, end_date)
    total_days = max(len(class_dates), 1)
    rows = []
    for student in students:
        present_days = await attendance_repo.attendance_count(student["_id"], class_id, start_date, end_date)
        rows.append(
            {
                "student_id": student["_id"],
                "name": student["name"],
                "roll_no": student["roll_no"],
                "class_id": class_id,
                "present_days": present_days,
                "total_recorded_days": total_days,
                "attendance_percent": round((present_days / total_days) * 100, 2),
            }
        )
    return rows


def rows_to_csv(rows: list[dict]) -> str:
    buffer = StringIO()
    fieldnames = [
        "student_id",
        "name",
        "roll_no",
        "class_id",
        "present_days",
        "total_recorded_days",
        "attendance_percent",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
