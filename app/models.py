from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="consulta", nullable=False)  # "admin" | "consulta"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class AcademicPeriod(Base):
    __tablename__ = "academic_periods"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "2026-1", "2026-2"
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)  # 1 or 2
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    responses = relationship("SurveyResponse", back_populates="period", cascade="all, delete-orphan")
    load_history = relationship("LoadHistory", back_populates="period", cascade="all, delete-orphan")

class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    period_code = Column(String(20), index=True, nullable=False)
    original_id = Column(String(50), index=True, nullable=False)  # ID from Microsoft Forms
    
    submission_start = Column(String(50), nullable=True)
    submission_end = Column(String(50), nullable=True)
    authorized = Column(Boolean, default=True, index=True, nullable=False)
    
    faculty_name = Column(String(150), index=True, nullable=False)
    program_name = Column(String(150), nullable=True)
    semester_enrolled = Column(String(50), index=True, nullable=True)
    
    # 13 Profile Questions
    q_motivacion = Column(Text, nullable=True)            # P01
    q_gestion_problemas = Column(Text, nullable=True)     # P02
    q_motivacion_economica = Column(Text, nullable=True)  # P03
    q_dinero_propio = Column(Text, nullable=True)         # P04
    q_iniciativa = Column(Text, nullable=True)            # P05 / P13 en informe
    q_nuevo_proyecto = Column(Text, nullable=True)        # P06
    q_tiempo_dedicacion = Column(Text, nullable=True)     # P07
    q_influencia_social = Column(Text, nullable=True)     # P08 / P16 en informe
    q_funcion_comercial = Column(Text, nullable=True)     # P09 / P17 en informe
    q_liderazgo = Column(Text, nullable=True)             # P10
    q_satisfaccion_logros = Column(Text, nullable=True)   # P11
    q_actitud_riesgo = Column(Text, nullable=True)        # P12 / P20 en informe
    q_validacion_viabilidad = Column(Text, nullable=True) # P13 / P21 en informe

    # Initiative & Characterization
    has_initiative = Column(Boolean, default=False, index=True, nullable=False)
    initiative_status = Column(String(150), nullable=True)
    stage = Column(String(80), index=True, nullable=True)  # "Pre-semilla", "Semilla", "Temprana", "Consolidación", "Escalamiento"
    stage_raw = Column(Text, nullable=True)
    
    idea_name = Column(String(255), nullable=True)
    idea_description = Column(Text, nullable=True)
    problem_addressed = Column(Text, nullable=True)
    time_invested_months = Column(String(100), nullable=True)
    has_invested_money = Column(String(20), nullable=True)
    invested_amount_raw = Column(String(100), nullable=True)
    funding_source_1 = Column(String(100), nullable=True)
    funding_source_2 = Column(String(100), nullable=True)
    monthly_sales_raw = Column(String(150), nullable=True)
    business_model_type = Column(String(100), nullable=True)
    team_size_raw = Column(String(100), nullable=True)
    received_support = Column(String(20), nullable=True)
    support_entities_raw = Column(String(255), nullable=True)
    economic_sector = Column(String(150), index=True, nullable=True)
    target_market = Column(Text, nullable=True)

    raw_data_hash = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    period = relationship("AcademicPeriod", back_populates="responses")

    __table_args__ = (
        Index("idx_period_original_id", "period_id", "original_id", unique=True),
        Index("idx_period_faculty", "period_code", "faculty_name"),
    )

class LoadHistory(Base):
    __tablename__ = "load_history"

    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False)
    period_code = Column(String(20), nullable=False)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, default=0)
    authorized_rows = Column(Integer, default=0)
    unauthorized_rows = Column(Integer, default=0)
    new_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    unchanged_rows = Column(Integer, default=0)
    validation_warnings = Column(Text, nullable=True)  # JSON string
    loaded_by = Column(String(120), nullable=True)
    loaded_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("AcademicPeriod", back_populates="load_history")

class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(80), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(120), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
