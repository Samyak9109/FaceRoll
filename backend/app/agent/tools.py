from datetime import date as date_type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.db.reports import generate_report_rows, get_absentees
from app.db.repositories import AttendanceRepository


class AttendanceInput(BaseModel):
    class_id: str
    date: str


class ManualMarkInput(BaseModel):
    student_id: str
    class_id: str
    date: str | None = None


class ReportInput(BaseModel):
    class_id: str
    start_date: str
    end_date: str


def build_tools(db):
    async def get_attendance(class_id: str, date: str):
        return await AttendanceRepository(db).get_for_class_date(class_id, date)

    async def mark_manual(student_id: str, class_id: str, date: str | None = None):
        parsed = date_type.fromisoformat(date) if date else None
        doc, inserted = await AttendanceRepository(db).mark_present(student_id, class_id, parsed)
        return {"attendance": doc, "inserted": inserted}

    async def generate_report(class_id: str, start_date: str, end_date: str):
        return await generate_report_rows(db, class_id, start_date, end_date)

    async def absentees(class_id: str, date: str):
        return await get_absentees(db, class_id, date)

    return [
        StructuredTool.from_function(
            coroutine=get_attendance,
            name="get_attendance",
            description="Get present students for a class on a YYYY-MM-DD date.",
            args_schema=AttendanceInput,
        ),
        StructuredTool.from_function(
            coroutine=mark_manual,
            name="mark_manual",
            description="Manually mark a student present for a class and optional YYYY-MM-DD date.",
            args_schema=ManualMarkInput,
        ),
        StructuredTool.from_function(
            coroutine=generate_report,
            name="generate_report",
            description="Generate attendance percentages for a class between YYYY-MM-DD dates.",
            args_schema=ReportInput,
        ),
        StructuredTool.from_function(
            coroutine=absentees,
            name="get_absentees",
            description="Get students without attendance for a class on a YYYY-MM-DD date.",
            args_schema=AttendanceInput,
        ),
    ]
