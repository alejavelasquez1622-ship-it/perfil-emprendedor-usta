import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATA_DIR, BACKUPS_DIR, INSTITUTION_NAME
from app.database import SessionLocal
from app.models import AcademicPeriod, SurveyResponse, User

def make_backup(output_path: Path = None):
    db = SessionLocal()
    try:
        periods = db.query(AcademicPeriod).all()
        responses = db.query(SurveyResponse).all()
        users = db.query(User).all()

        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
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

        if not output_path:
            fname = f"Respaldo_USTA_Perfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = BACKUPS_DIR / fname

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"✔ Copia de seguridad guardada exitosamente en:")
        print(f"  {output_path.resolve()}")
        print(f"  Total periodos: {len(periods)} | Total respuestas: {len(responses)}")
    finally:
        db.close()

if __name__ == "__main__":
    make_backup()
