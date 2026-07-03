from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pymongo.errors import DuplicateKeyError

from app.api.deps import current_user, database, require_roles
from app.core.config import get_settings
from app.core.rate_limit import recognition_limiter
from app.db.reports import generate_report_rows, rows_to_csv
from app.db.repositories import (
    AttendanceRepository,
    AuditRepository,
    ClassRepository,
    StudentRepository,
    UserRepository,
    serialize_doc,
)
from app.models.schemas import (
    AgentAnswer,
    AgentQuery,
    AttendanceOut,
    ClassCreate,
    RecognitionResult,
    StudentOut,
    TeacherCreate,
    UserOut,
)
from app.services.face_embedder import FaceEmbeddingError, face_embedder
from app.services.matcher import find_best_match
from app.agent.executor import run_agent_query

router = APIRouter(dependencies=[Depends(current_user)])


def ensure_class_access(user: dict, class_id: str) -> None:
    if user["role"] == "admin":
        return
    if user["role"] == "teacher" and class_id in user.get("assigned_classes", []):
        return
    raise HTTPException(status_code=403, detail="You are not assigned to this class")


@router.post("/admin/teachers", response_model=UserOut)
async def create_teacher(
    payload: TeacherCreate,
    db=Depends(database),
    _: dict = Depends(require_roles("admin")),
) -> dict:
    try:
        return await UserRepository(db).create(
            username=payload.username,
            password=payload.password,
            role="teacher",
            name=payload.name,
            email=payload.email,
            assigned_classes=payload.assigned_classes,
            subject=payload.subject,
            verified=payload.verified,
        )
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc


@router.post("/admin/classes")
async def create_class(
    payload: ClassCreate,
    db=Depends(database),
    _: dict = Depends(require_roles("admin")),
) -> dict:
    try:
        return await ClassRepository(db).create(
            class_id=payload.class_id,
            name=payload.name,
            subject=payload.subject,
            teacher_id=payload.teacher_id,
            schedule=payload.schedule,
        )
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Class ID already exists") from exc


@router.get("/admin/records")
async def admin_records(db=Depends(database), _: dict = Depends(require_roles("admin"))) -> dict:
    return {
        "teachers": await UserRepository(db).list_by_role("teacher"),
        "students": await StudentRepository(db).list_all(),
        "classes": await ClassRepository(db).list_all(),
    }


@router.post("/admin/students/enroll", response_model=StudentOut)
async def enroll(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    roll_no: str = Form(...),
    class_id: str = Form(...),
    consent: bool = Form(...),
    photo: UploadFile = File(...),
    db=Depends(database),
    _: dict = Depends(require_roles("admin")),
) -> dict:
    image = await photo.read()
    try:
        user = await UserRepository(db).create(
            username=username,
            password=password,
            role="student",
            name=name,
            assigned_classes=[class_id],
        )
        embedding = face_embedder.extract_from_bytes(image)
        student = await StudentRepository(db).create(name, roll_no, class_id, consent, embedding, user["_id"])
        await UserRepository(db).set_student_id(user["_id"], student["_id"])
        return student
    except FaceEmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Student username or roll number already exists") from exc


@router.post("/enroll", response_model=StudentOut)
async def legacy_enroll(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    roll_no: str = Form(...),
    class_id: str = Form(...),
    consent: bool = Form(...),
    photo: UploadFile = File(...),
    db=Depends(database),
    admin: dict = Depends(require_roles("admin")),
) -> dict:
    return await enroll(username, password, name, roll_no, class_id, consent, photo, db, admin)


@router.post("/recognize", response_model=RecognitionResult)
async def recognize(
    request: Request,
    class_id: str = Form(...),
    frame: UploadFile = File(...),
    db=Depends(database),
    user: dict = Depends(require_roles("teacher", "admin")),
) -> RecognitionResult:
    ensure_class_access(user, class_id)
    recognition_limiter.check(request)
    image = await frame.read()
    try:
        embedding = face_embedder.extract_from_bytes(image)
    except FaceEmbeddingError as exc:
        await AuditRepository(db).log_attempt(class_id, False, None, None)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    student_repo = StudentRepository(db)
    candidates = await student_repo.list_by_class_with_embeddings(class_id)
    match, score = find_best_match(embedding, candidates, get_settings().recognition_threshold)
    if match is None:
        await AuditRepository(db).log_attempt(class_id, False, score, None)
        return RecognitionResult(matched=False, score=score, message="Unknown face")

    attendance, inserted = await AttendanceRepository(db).mark_present(match["_id"], class_id)
    await AuditRepository(db).log_attempt(class_id, True, score, match["_id"])
    return RecognitionResult(
        matched=True,
        student=StudentOut.model_validate(serialize_doc(match)),
        score=score,
        attendance_marked=inserted,
        message="Attendance marked" if inserted else "Attendance already marked for today",
    )


@router.get("/attendance/{class_id}/{attendance_date}", response_model=list[AttendanceOut])
async def attendance(
    class_id: str,
    attendance_date: str,
    db=Depends(database),
    user: dict = Depends(require_roles("teacher", "admin")),
) -> list[dict]:
    ensure_class_access(user, class_id)
    return await AttendanceRepository(db).get_for_class_date(class_id, attendance_date)


@router.post("/agent/query", response_model=AgentAnswer)
async def agent_query(
    payload: AgentQuery,
    db=Depends(database),
    _: dict = Depends(require_roles("teacher", "admin")),
) -> AgentAnswer:
    answer = await run_agent_query(db, payload.query)
    return AgentAnswer(answer=answer)


@router.get("/report/{class_id}")
async def report(
    class_id: str,
    start_date: date,
    end_date: date,
    format: str = "csv",
    db=Depends(database),
    user: dict = Depends(require_roles("teacher", "admin")),
):
    ensure_class_access(user, class_id)
    rows = await generate_report_rows(db, class_id, start_date.isoformat(), end_date.isoformat())
    if format.lower() == "json":
        return rows
    csv_body = rows_to_csv(rows)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{class_id}-attendance.csv"'},
    )


@router.get("/teacher/classes")
async def teacher_classes(db=Depends(database), user: dict = Depends(require_roles("teacher", "admin"))) -> list[dict]:
    if user["role"] == "admin":
        return await ClassRepository(db).list_all()
    return await ClassRepository(db).list_for_teacher(user)


@router.get("/teacher/dashboard")
async def teacher_dashboard(
    class_id: str | None = None,
    db=Depends(database),
    user: dict = Depends(require_roles("teacher", "admin")),
) -> dict:
    class_ids = [class_id] if class_id else user.get("assigned_classes", [])
    if user["role"] == "admin" and not class_ids:
        class_ids = [row["class_id"] for row in await ClassRepository(db).list_all()]
    for cid in class_ids:
        ensure_class_access(user, cid)
    today = date.today()
    start = (today - timedelta(days=13)).isoformat()
    end = today.isoformat()
    daily = await AttendanceRepository(db).daily_counts_for_classes(class_ids, start, end) if class_ids else []
    classes = await ClassRepository(db).list_all() if user["role"] == "admin" else await ClassRepository(db).list_for_teacher(user)
    class_summaries = []
    for row in classes:
        if class_ids and row["class_id"] not in class_ids:
            continue
        students = await StudentRepository(db).list_by_class(row["class_id"])
        present_today = await AttendanceRepository(db).get_for_class_date(row["class_id"], end)
        class_summaries.append(
            {
                "class_id": row["class_id"],
                "name": row["name"],
                "subject": row["subject"],
                "students": len(students),
                "present_today": len(present_today),
            }
        )
    return {"classes": class_summaries, "daily": daily}


@router.get("/student/dashboard")
async def student_dashboard(db=Depends(database), user: dict = Depends(require_roles("student"))) -> dict:
    student = await StudentRepository(db).get_by_user(user["_id"])
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    attendance_rows = await AttendanceRepository(db).get_for_student(student["_id"])
    attendance_repo = AttendanceRepository(db)
    class_dates = await attendance_repo.present_dates_for_student_class(student["_id"], student["class_id"])
    recorded_dates = await attendance_repo.recorded_dates_for_class(student["class_id"])
    all_class_attendance = await AttendanceRepository(db).get_for_class_date(student["class_id"], date.today().isoformat())
    today_present = any(row["student_id"] == student["_id"] for row in all_class_attendance)
    missed_dates = sorted(recorded_dates - class_dates, reverse=True)
    return {
        "student": student,
        "attended_count": len(attendance_rows),
        "missed_count": len(missed_dates),
        "missed_dates": missed_dates,
        "records": attendance_rows,
        "classes": [
            {
                "class_id": student["class_id"],
                "attended": len(class_dates),
                "present_today": today_present,
            }
        ],
    }
