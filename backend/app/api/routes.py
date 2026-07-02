from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.api.deps import current_teacher, database
from app.core.config import get_settings
from app.core.rate_limit import recognition_limiter
from app.db.reports import generate_report_rows, rows_to_csv
from app.db.repositories import AttendanceRepository, AuditRepository, StudentRepository, serialize_doc
from app.models.schemas import AgentAnswer, AgentQuery, AttendanceOut, RecognitionResult, StudentOut
from app.services.face_embedder import FaceEmbeddingError, face_embedder
from app.services.matcher import find_best_match
from app.agent.executor import run_agent_query

router = APIRouter(dependencies=[Depends(current_teacher)])


@router.post("/enroll", response_model=StudentOut)
async def enroll(
    name: str = Form(...),
    roll_no: str = Form(...),
    class_id: str = Form(...),
    consent: bool = Form(...),
    photo: UploadFile = File(...),
    db=Depends(database),
) -> dict:
    image = await photo.read()
    try:
        embedding = face_embedder.extract_from_bytes(image)
        return await StudentRepository(db).create(name, roll_no, class_id, consent, embedding)
    except FaceEmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recognize", response_model=RecognitionResult)
async def recognize(
    request: Request,
    class_id: str = Form(...),
    frame: UploadFile = File(...),
    db=Depends(database),
) -> RecognitionResult:
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
async def attendance(class_id: str, attendance_date: str, db=Depends(database)) -> list[dict]:
    return await AttendanceRepository(db).get_for_class_date(class_id, attendance_date)


@router.post("/agent/query", response_model=AgentAnswer)
async def agent_query(payload: AgentQuery, db=Depends(database)) -> AgentAnswer:
    answer = await run_agent_query(db, payload.query)
    return AgentAnswer(answer=answer)


@router.get("/report/{class_id}")
async def report(
    class_id: str,
    start_date: date,
    end_date: date,
    format: str = "csv",
    db=Depends(database),
):
    rows = await generate_report_rows(db, class_id, start_date.isoformat(), end_date.isoformat())
    if format.lower() == "json":
        return rows
    csv_body = rows_to_csv(rows)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{class_id}-attendance.csv"'},
    )
