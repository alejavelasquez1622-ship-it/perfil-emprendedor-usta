import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import init_db, SessionLocal
from app.models import AcademicPeriod, SurveyResponse

def restore_backup(backup_file: Path):
    if not backup_file.exists():
        print(f"Error: el archivo {backup_file} no existe.")
        return

    init_db()
    db = SessionLocal()
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        periods_in = data.get("periods", [])
        responses_in = data.get("responses", [])

        print(f"Restaurando {len(periods_in)} periodos y {len(responses_in)} respuestas...")

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

        new_count = 0
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
                new_count += 1

        db.commit()
        print(f"✔ Restauración finalizada. Nuevos registros integrados: {new_count}")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        restore_backup(Path(sys.argv[1]))
    else:
        print("Uso: python restore_backup.py <ruta_archivo_respaldo.json>")
