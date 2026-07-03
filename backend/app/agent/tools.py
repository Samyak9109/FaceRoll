from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.db.reports import generate_report_rows, get_absentees
from app.db.repositories import AttendanceRepository


class AttendanceInput(BaseModel):
    class_id: str
    date: str


class ReportInput(BaseModel):
    class_id: str
    start_date: str
    end_date: str


def has_agent_class_access(user: dict, class_id: str) -> bool:
    if user["role"] == "admin":
        return True
    return class_id in user.get("assigned_classes", [])


def build_tools(db, user: dict):
    async def get_attendance(class_id: str, date: str):
        if not has_agent_class_access(user, class_id):
            return {"error": f"You are not assigned to class {class_id}"}
        return await AttendanceRepository(db).get_for_class_date(class_id, date)

    async def generate_report(class_id: str, start_date: str, end_date: str):
        if not has_agent_class_access(user, class_id):
            return {"error": f"You are not assigned to class {class_id}"}
        return await generate_report_rows(db, class_id, start_date, end_date)

    async def absentees(class_id: str, date: str):
        if not has_agent_class_access(user, class_id):
            return {"error": f"You are not assigned to class {class_id}"}
        return await get_absentees(db, class_id, date)

    return [
        StructuredTool.from_function(
            coroutine=get_attendance,
            name="get_attendance",
            description="Get present students for a class on a YYYY-MM-DD date.",
            args_schema=AttendanceInput,
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
