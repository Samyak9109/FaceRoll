from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class StudentOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    roll_no: str
    class_id: str
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
