from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: dict


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str = Field(alias="_id")
    username: str
    role: str
    name: str
    email: str | None = None
    assigned_classes: list[str] = []
    subject: str | None = None
    student_id: str | None = None
    active: bool = True
    verified: bool = True
    created_at: datetime

    class Config:
        populate_by_name = True


class TeacherCreate(BaseModel):
    username: str
    password: str
    name: str
    email: str | None = None
    subject: str
    assigned_classes: list[str] = []
    verified: bool = True


class ClassCreate(BaseModel):
    class_id: str
    name: str
    subject: str
    teacher_id: str | None = None
    schedule: str | None = None


class StudentOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    roll_no: str
    class_id: str
    user_id: str | None = None
    consent: bool
    created_at: datetime

    class Config:
        populate_by_name = True


class AttendanceOut(BaseModel):
    id: str = Field(alias="_id")
    student_id: str
    class_id: str
    date: str
    time: str
    status: str
    name: str | None = None
    roll_no: str | None = None

    class Config:
        populate_by_name = True


class RecognitionResult(BaseModel):
    matched: bool
    student: StudentOut | None = None
    score: float | None = None
    attendance_marked: bool = False
    message: str


class AgentQuery(BaseModel):
    query: str


class AgentAnswer(BaseModel):
    answer: str
