from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

# Auth & User schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str = "consulta"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Academic Period schemas
class PeriodCreate(BaseModel):
    code: str  # e.g., "2027-1"
    description: Optional[str] = None
    is_active: bool = True

class PeriodResponse(BaseModel):
    id: int
    code: str
    year: int
    semester: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    total_responses: Optional[int] = 0
    authorized_responses: Optional[int] = 0
    faculty_count: Optional[int] = 0
    last_update: Optional[datetime] = None

    class Config:
        from_attributes = True

# Upload Preview and Confirm
class UploadPreviewItem(BaseModel):
    original_id: str
    status: str  # "NUEVO", "MODIFICADO", "SIN_CAMBIOS"
    faculty: str
    authorized: bool
    has_initiative: bool

class UploadPreviewResponse(BaseModel):
    filename: str
    detected_period: str
    total_rows: int
    authorized_rows: int
    unauthorized_rows: int
    new_rows: int
    updated_rows: int
    unchanged_rows: int
    current_db_count: int
    is_fewer_than_current: bool
    faculties_found: List[str]
    warnings: List[str]
    preview_samples: List[Dict[str, Any]]
    temp_file_id: str

class UploadConfirmRequest(BaseModel):
    temp_file_id: str
    period_code: str
    mode: str = "smart_update"  # "smart_update" | "replace_all"

# Dashboard & Statistics schemas
class KPISummary(BaseModel):
    total_encuestas: int
    autorizadas: int
    no_autorizadas: int
    con_iniciativa: int
    pct_con_iniciativa: float
    sin_iniciativa: int
    pct_sin_iniciativa: float
    facultades_count: int
    semestres_count: int
    apoyo_recibido_count: int
    pct_apoyo_recibido: float

class CategoryCount(BaseModel):
    label: str
    count: int
    percentage: float

class QuestionAnalysis(BaseModel):
    question_code: str
    question_title: str
    valid_responses: int
    total_eligible: int
    options: List[CategoryCount]
    other_responses_count: int
    other_responses_pct: float

class FacultyDetailReport(BaseModel):
    period_code: str
    faculty_name: str
    kpis: KPISummary
    etapas: List[CategoryCount]
    sectores: List[CategoryCount]
    fuentes_financiacion: List[CategoryCount]
    apoyo_institucional: List[CategoryCount]
    entidades_apoyo: List[CategoryCount]
    perfil_preguntas: Dict[str, QuestionAnalysis]
    resumen_ejecutivo: str
    orientaciones_acompanamiento: Dict[str, str]
    alcance_metodologico: str
