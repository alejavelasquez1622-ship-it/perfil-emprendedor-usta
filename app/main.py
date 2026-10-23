import io
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import (
    FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Response, Request, Query
)
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import (
    STATIC_DIR, TEMPLATES_DIR, INSTITUTION_NAME, DEPENDENCY_NAME, SYSTEM_NAME,
    SYSTEM_VERSION, LOGO_PATH, PROFILE_QUESTIONS, BACKUPS_DIR, DATA_DIR
)
from app.database import init_db, get_db, SessionLocal
from app.models import User, AcademicPeriod, Faculty, SurveyResponse, LoadHistory, AppSetting, AuditLog
from app.schemas import (
    Token, LoginRequest, UserCreate, UserUpdate, UserResponse,
    PeriodCreate, PeriodResponse, UploadPreviewResponse, UploadConfirmRequest
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin, get_token_from_request
)
from app.excel_processor import ExcelProcessor
from app.stats_service import (
    compute_kpis, compute_distribution, compute_stages_distribution,
    compute_funding_distribution, compute_support_distribution,
    compute_question_profile, get_complete_faculty_report_data,
    compute_period_comparison, get_filtered_query
)
from app.pdf_generator import (
    generate_faculty_pdf, generate_institutional_general_pdf,
    generate_comparative_pdf, generate_all_faculties_zip
)

# Initialize application
app = FastAPI(
    title=SYSTEM_NAME,
    description="Aplicativo web para procesamiento, análisis, seguimiento y generación de informes del diagnóstico de perfil emprendedor.",
    version=SYSTEM_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files & templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

excel_proc = ExcelProcessor()

# Startup event: ensure DB and default seed records exist
@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        # Check if admin user exists, create if not
        admin_user = db.query(User).filter(User.username == "admin@usta.edu.co").first()
        if not admin_user:
            admin_user = User(
                username="admin@usta.edu.co",
                full_name="Administrador Proyección Social",
                hashed_password=get_password_hash("AdminUsta2026*"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()

        # Check if consultation user exists, create if not
        consulta_user = db.query(User).filter(User.username == "consulta@usta.edu.co").first()
        if not consulta_user:
            consulta_user = User(
                username="consulta@usta.edu.co",
                full_name="Funcionario de Decanatura",
                hashed_password=get_password_hash("Consulta2026*"),
                role="consulta",
                is_active=True
            )
            db.add(consulta_user)
            db.commit()

        # Seed default period 2026-1 if none
        p2026 = db.query(AcademicPeriod).filter(AcademicPeriod.code == "2026-1").first()
        if not p2026:
            p2026 = AcademicPeriod(
                code="2026-1",
                year=2026,
                semester=1,
                description="Primer Periodo Académico 2026",
                is_active=True
            )
            db.add(p2026)
            db.commit()

    finally:
        db.close()

# Helper for audit logging
def log_audit(db: Session, user: Optional[User], action: str, details: str = "", ip: str = ""):
    try:
        log_entry = AuditLog(
            user_email=user.username if user else "Sistema",
            action=action,
            details=details,
            ip_address=ip
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        pass

# =========================================================================
# 1. AUTHENTICATION ENDPOINTS
# =========================================================================

@app.post("/api/auth/login", response_model=Token)
def login(login_data: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username.strip().lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo institucional o contraseña incorrectos."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta institucional se encuentra inactiva."
        )

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(data={"sub": user.username, "role": user.role, "name": user.full_name})
    
    # Set HTTP-only cookie for secure browser navigation
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    log_audit(db, user, "Inicio de sesión exitoso", ip=request.client.host if request.client else "")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@app.post("/api/auth/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    response.delete_cookie(key="access_token")
    return {"message": "Sesión cerrada exitosamente."}

@app.get("/api/auth/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

# =========================================================================
# 2. PERIODS ENDPOINTS
# =========================================================================

@app.get("/api/periods")
def list_periods(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    periods = db.query(AcademicPeriod).order_by(AcademicPeriod.year.desc(), AcademicPeriod.semester.desc()).all()
    results = []
    for p in periods:
        total = db.query(SurveyResponse).filter(SurveyResponse.period_id == p.id).count()
        auth_count = db.query(SurveyResponse).filter(
            SurveyResponse.period_id == p.id,
            SurveyResponse.authorized == True
        ).count()
        fac_count = db.query(SurveyResponse.faculty_name).filter(
            SurveyResponse.period_id == p.id,
            SurveyResponse.authorized == True
        ).distinct().count()

        results.append({
            "id": p.id,
            "code": p.code,
            "year": p.year,
            "semester": p.semester,
            "description": p.description,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "total_responses": total,
            "authorized_responses": auth_count,
            "faculty_count": fac_count,
            "last_update": p.updated_at
        })
    return results

@app.post("/api/periods")
def create_period(
    period_in: PeriodCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    code = period_in.code.strip()
    match = re.match(r"^(\d{4})-([12])$", code)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Formato de periodo inválido. Debe ser AAAA-1 o AAAA-2 (ejemplo: 2027-1)."
        )
    existing = db.query(AcademicPeriod).filter(AcademicPeriod.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El periodo {code} ya se encuentra registrado.")

    year = int(match.group(1))
    semester = int(match.group(2))
    new_p = AcademicPeriod(
        code=code,
        year=year,
        semester=semester,
        description=period_in.description or f"Periodo Académico {code}",
        is_active=period_in.is_active
    )
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    log_audit(db, current_user, "Creación de periodo académico", f"Periodo {code} creado.")
    return new_p

# =========================================================================
# 3. FACULTIES & SEMESTERS ENDPOINTS
# =========================================================================

@app.get("/api/faculties")
def list_faculties(period_code: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(SurveyResponse.faculty_name).filter(SurveyResponse.authorized == True)
    if period_code and period_code != "Todos":
        query = query.filter(SurveyResponse.period_code == period_code)
    faculties = sorted([f[0] for f in query.distinct().all() if f[0]])
    return faculties

@app.get("/api/semesters")
def list_semesters(period_code: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(SurveyResponse.semester_enrolled).filter(SurveyResponse.authorized == True)
    if period_code and period_code != "Todos":
        query = query.filter(SurveyResponse.period_code == period_code)
    semesters = sorted([s[0] for s in query.distinct().all() if s[0]])
    return semesters

# =========================================================================
# 4. EXCEL UPLOAD & PREVIEW ENDPOINTS
# =========================================================================

@app.post("/api/upload/preview")
async def upload_preview(
    file: UploadFile = File(...),
    period_code: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Formato no admitido. Por favor cargue un archivo .xlsx de Microsoft Forms.")

    # Save to temp location
    temp_file_path = DATA_DIR / "temp_uploads" / f"upload_{datetime.utcnow().timestamp()}_{file.filename}"
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_file_path, "wb") as f_out:
        content = await file.read()
        f_out.write(content)

    try:
        rows = excel_proc.parse_excel_file(temp_file_path)
        if not rows:
            raise HTTPException(status_code=400, detail="No se encontraron filas con datos válidos en el archivo.")

        preview_result = excel_proc.analyze_preview(
            rows=rows,
            db=db,
            filename=file.filename,
            target_period_code=period_code
        )
        return preview_result
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()

@app.post("/api/upload/confirm")
def upload_confirm(
    confirm_data: UploadConfirmRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        res = excel_proc.commit_upload(
            temp_file_id=confirm_data.temp_file_id,
            period_code=confirm_data.period_code,
            db=db,
            loaded_by=current_user.full_name,
            mode=confirm_data.mode
        )
        log_audit(
            db, current_user, "Carga de información",
            f"Periodo {confirm_data.period_code}: {res['new_records']} nuevos, {res['updated_records']} actualizados, {res['unchanged_records']} sin cambios."
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/upload/history")
def upload_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hist = db.query(LoadHistory).order_by(LoadHistory.loaded_at.desc()).limit(50).all()
    return hist

# =========================================================================
# 5. DASHBOARD & STATISTICAL INDICATORS API
# =========================================================================

@app.get("/api/stats/dashboard")
def get_dashboard_data(
    period_code: Optional[str] = "Todos",
    faculty_name: Optional[str] = "Todas",
    semester: Optional[str] = "Todos",
    initiative_status: Optional[str] = "Todos",
    stage: Optional[str] = "Todas",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Query authorized responses
    q = get_filtered_query(
        db, period_code, faculty_name, semester, initiative_status, stage, only_authorized=True
    )
    authorized_responses = q.all()

    # Unauthorized responses count for participation metrics
    unauth_query = db.query(SurveyResponse).filter(SurveyResponse.authorized == False)
    if period_code and period_code != "Todos":
        unauth_query = unauth_query.filter(SurveyResponse.period_code == period_code)
    unauthorized_count = unauth_query.count()

    total_with_unauth = len(authorized_responses) + unauthorized_count
    kpis = compute_kpis(authorized_responses)
    kpis["total_encuestas"] = total_with_unauth
    kpis["no_autorizadas"] = unauthorized_count

    iniciativas = [r for r in authorized_responses if r.has_initiative]

    # Chart 1: Distribution by Faculty
    fac_counts = Counter(r.faculty_name for r in authorized_responses if r.faculty_name)
    dist_facultades = [{"label": f, "count": c, "percentage": round(c/len(authorized_responses)*100, 1)} for f, c in fac_counts.most_common(12)] if authorized_responses else []

    # Chart 2: Distribution by Semester
    sem_counts = Counter(r.semester_enrolled for r in authorized_responses if r.semester_enrolled)
    # Order semesters 1 to 10
    ordered_semesters = []
    for s_num in range(1, 11):
        for s_key in sem_counts:
            if f"{s_num}°" in s_key or f"{s_num} " in s_key or f"{s_num}º" in s_key:
                ordered_semesters.append({
                    "label": f"Semestre {s_num}",
                    "count": sem_counts[s_key],
                    "percentage": round(sem_counts[s_key] / len(authorized_responses) * 100, 1) if authorized_responses else 0
                })
                break
    dist_semestres = ordered_semesters if ordered_semesters else compute_distribution([r.semester_enrolled for r in authorized_responses if r.semester_enrolled])

    # Chart 3: Stages (INNPulsa)
    dist_etapas = compute_stages_distribution(iniciativas)

    # Chart 4: Sectors
    dist_sectores = compute_distribution([r.economic_sector for r in iniciativas if r.economic_sector], len(iniciativas))[:10]

    # Chart 5: Funding
    dist_fuentes = compute_funding_distribution(iniciativas)

    # Chart 6: Institutional Support
    apoyo_status, entidades = compute_support_distribution(iniciativas)

    # Chart 7: Profile Dimensions (P13, P16, P17, P20, P21)
    dist_perfil = {
        "P13": compute_question_profile(authorized_responses, "q_iniciativa", top_n=4),
        "P16": compute_question_profile(authorized_responses, "q_influencia_social", top_n=4),
        "P17": compute_question_profile(authorized_responses, "q_funcion_comercial", top_n=4),
        "P20": compute_question_profile(authorized_responses, "q_actitud_riesgo", top_n=4),
        "P21": compute_question_profile(authorized_responses, "q_validacion_viabilidad", top_n=4),
    }

    return {
        "kpis": kpis,
        "dist_facultades": dist_facultades,
        "dist_semestres": dist_semestres,
        "dist_etapas": dist_etapas,
        "dist_sectores": dist_sectores,
        "dist_fuentes": dist_fuentes,
        "dist_apoyo": apoyo_status,
        "entidades_apoyo": entidades[:8],
        "dist_perfil": dist_perfil
    }

@app.get("/api/stats/faculty-detail")
def get_faculty_detail(
    period_code: str,
    faculty_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = get_complete_faculty_report_data(db, period_code, faculty_name)
    return data

@app.get("/api/stats/comparison")
def get_comparison(
    period_1: str,
    period_2: str,
    faculty_name: Optional[str] = "Todas",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = compute_period_comparison(db, period_1, period_2, faculty_name)
    return comp

# =========================================================================
# 6. PDF & ZIP GENERATION API
# =========================================================================

@app.get("/api/reports/faculty-pdf")
def get_faculty_pdf_endpoint(
    period_code: str,
    faculty_name: str,
    download: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = get_complete_faculty_report_data(db, period_code, faculty_name)
    pdf_bytes = generate_faculty_pdf(data)

    clean_fac = re.sub(r'[^\w\-_\. ]', '_', faculty_name).replace(" ", "_")
    filename = f"Informe_{clean_fac}_{period_code}.pdf"

    disposition = f'attachment; filename="{filename}"' if download else f'inline; filename="{filename}"'
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition}
    )

@app.get("/api/reports/general-pdf")
def get_general_pdf_endpoint(
    period_code: str,
    download: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pdf_bytes = generate_institutional_general_pdf(db, period_code)
    filename = f"Informe_General_Consolidado_{period_code}.pdf"
    disposition = f'attachment; filename="{filename}"' if download else f'inline; filename="{filename}"'
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition}
    )

@app.get("/api/reports/comparative-pdf")
def get_comparative_pdf_endpoint(
    period_1: str,
    period_2: str,
    faculty_name: Optional[str] = "Todas",
    download: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = compute_period_comparison(db, period_1, period_2, faculty_name)
    pdf_bytes = generate_comparative_pdf(comp)

    clean_fac = re.sub(r'[^\w\-_\. ]', '_', faculty_name).replace(" ", "_") if faculty_name else "Universidad"
    filename = f"Informe_Comparativo_{clean_fac}_{period_1}_vs_{period_2}.pdf"

    disposition = f'attachment; filename="{filename}"' if download else f'inline; filename="{filename}"'
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition}
    )

@app.get("/api/reports/faculties-zip")
def get_faculties_zip_endpoint(
    period_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    zip_buffer = generate_all_faculties_zip(db, period_code)
    filename = f"Informes_Facultades_{period_code}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# =========================================================================
# 7. ADMIN, USERS & BACKUP ENDPOINTS
# =========================================================================

@app.get("/api/admin/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()

@app.post("/api/admin/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    username = user_in.username.strip().lower()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya se encuentra registrado.")

    new_user = User(
        username=username,
        full_name=user_in.full_name.strip(),
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log_audit(db, current_user, "Creación de usuario", f"Usuario {username} creado con rol {user_in.role}.")
    return new_user

@app.put("/api/admin/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name.strip()
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)

    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "Modificación de usuario", f"Usuario {user.username} modificado.")
    return user

@app.get("/api/admin/backup/download")
def download_backup(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Exports full database as a clean JSON backup file."""
    periods = db.query(AcademicPeriod).all()
    responses = db.query(SurveyResponse).all()
    users = db.query(User).all()

    backup_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "exported_by": current_user.username,
        "institution": INSTITUTION_NAME,
        "periods": [
            {"code": p.code, "year": p.year, "semester": p.semester, "description": p.description, "is_active": p.is_active}
            for p in periods
        ],
        "responses": [
            {
                "period_code": r.period_code,
                "original_id": r.original_id,
                "submission_start": r.submission_start,
                "submission_end": r.submission_end,
                "authorized": r.authorized,
                "faculty_name": r.faculty_name,
                "program_name": r.program_name,
                "semester_enrolled": r.semester_enrolled,
                "has_initiative": r.has_initiative,
                "initiative_status": r.initiative_status,
                "stage": r.stage,
                "stage_raw": r.stage_raw,
                "economic_sector": r.economic_sector,
                "q_motivacion": r.q_motivacion,
                "q_gestion_problemas": r.q_gestion_problemas,
                "q_motivacion_economica": r.q_motivacion_economica,
                "q_dinero_propio": r.q_dinero_propio,
                "q_iniciativa": r.q_iniciativa,
                "q_nuevo_proyecto": r.q_nuevo_proyecto,
                "q_tiempo_dedicacion": r.q_tiempo_dedicacion,
                "q_influencia_social": r.q_influencia_social,
                "q_funcion_comercial": r.q_funcion_comercial,
                "q_liderazgo": r.q_liderazgo,
                "q_satisfaccion_logros": r.q_satisfaccion_logros,
                "q_actitud_riesgo": r.q_actitud_riesgo,
                "q_validacion_viabilidad": r.q_validacion_viabilidad,
                "time_invested_months": r.time_invested_months,
                "has_invested_money": r.has_invested_money,
                "invested_amount_raw": r.invested_amount_raw,
                "funding_source_1": r.funding_source_1,
                "funding_source_2": r.funding_source_2,
                "monthly_sales_raw": r.monthly_sales_raw,
                "business_model_type": r.business_model_type,
                "team_size_raw": r.team_size_raw,
                "received_support": r.received_support,
                "support_entities_raw": r.support_entities_raw,
                "raw_data_hash": r.raw_data_hash
            }
            for r in responses
        ],
        "users": [
            {"username": u.username, "full_name": u.full_name, "role": u.role, "is_active": u.is_active}
            for u in users
        ]
    }

    json_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
    fname = f"Respaldo_USTA_Perfil_Emprendedor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'}
    )

@app.post("/api/admin/backup/restore")
async def restore_backup(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        backup = json.loads(content.decode("utf-8"))

        periods_in = backup.get("periods", [])
        responses_in = backup.get("responses", [])

        # Create or update periods
        for p in periods_in:
            p_obj = db.query(AcademicPeriod).filter(AcademicPeriod.code == p["code"]).first()
            if not p_obj:
                p_obj = AcademicPeriod(
                    code=p["code"],
                    year=p["year"],
                    semester=p["semester"],
                    description=p.get("description"),
                    is_active=p.get("is_active", True)
                )
                db.add(p_obj)
        db.commit()

        # Insert responses
        restored_count = 0
        for r in responses_in:
            p_code = r.get("period_code", "2026-1")
            p_obj = db.query(AcademicPeriod).filter(AcademicPeriod.code == p_code).first()
            if not p_obj:
                continue

            orig_id = str(r["original_id"])
            existing = db.query(SurveyResponse).filter(
                SurveyResponse.period_id == p_obj.id,
                SurveyResponse.original_id == orig_id
            ).first()

            if not existing:
                new_r = SurveyResponse(
                    period_id=p_obj.id,
                    period_code=p_code,
                    original_id=orig_id,
                    submission_start=r.get("submission_start"),
                    submission_end=r.get("submission_end"),
                    authorized=r.get("authorized", True),
                    faculty_name=r.get("faculty_name", "Sin Facultad"),
                    program_name=r.get("program_name"),
                    semester_enrolled=r.get("semester_enrolled"),
                    has_initiative=r.get("has_initiative", False),
                    initiative_status=r.get("initiative_status"),
                    stage=r.get("stage"),
                    stage_raw=r.get("stage_raw"),
                    economic_sector=r.get("economic_sector"),
                    q_motivacion=r.get("q_motivacion"),
                    q_gestion_problemas=r.get("q_gestion_problemas"),
                    q_motivacion_economica=r.get("q_motivacion_economica"),
                    q_dinero_propio=r.get("q_dinero_propio"),
                    q_iniciativa=r.get("q_iniciativa"),
                    q_nuevo_proyecto=r.get("q_nuevo_proyecto"),
                    q_tiempo_dedicacion=r.get("q_tiempo_dedicacion"),
                    q_influencia_social=r.get("q_influencia_social"),
                    q_funcion_comercial=r.get("q_funcion_comercial"),
                    q_liderazgo=r.get("q_liderazgo"),
                    q_satisfaccion_logros=r.get("q_satisfaccion_logros"),
                    q_actitud_riesgo=r.get("q_actitud_riesgo"),
                    q_validacion_viabilidad=r.get("q_validacion_viabilidad"),
                    time_invested_months=r.get("time_invested_months"),
                    has_invested_money=r.get("has_invested_money"),
                    invested_amount_raw=r.get("invested_amount_raw"),
                    funding_source_1=r.get("funding_source_1"),
                    funding_source_2=r.get("funding_source_2"),
                    monthly_sales_raw=r.get("monthly_sales_raw"),
                    business_model_type=r.get("business_model_type"),
                    team_size_raw=r.get("team_size_raw"),
                    received_support=r.get("received_support"),
                    support_entities_raw=r.get("support_entities_raw"),
                    raw_data_hash=r.get("raw_data_hash", "")
                )
                db.add(new_r)
                restored_count += 1
        db.commit()

        log_audit(db, current_user, "Restauración de respaldo", f"Se restauraron {restored_count} registros.")
        return {"status": "success", "message": f"Respaldo restaurado con éxito. Se procesaron {restored_count} nuevos registros."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al restaurar respaldo: {str(e)}")

@app.get("/api/admin/audit-logs")
def get_audit_logs(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()

# =========================================================================
# 8. MAIN UI TEMPLATE ROUTE
# =========================================================================

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "institution_name": INSTITUTION_NAME,
            "dependency_name": DEPENDENCY_NAME,
            "system_name": SYSTEM_NAME,
            "system_version": SYSTEM_VERSION
        }
    )
