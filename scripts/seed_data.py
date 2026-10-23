import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DATA_DIR
from app.database import init_db, SessionLocal
from app.models import User, AcademicPeriod, SurveyResponse
from app.auth import get_password_hash
from app.excel_processor import ExcelProcessor, detect_period_from_date

def seed_database():
    print("Iniciando inicialización de base de datos institucional...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed default users
        admin_email = "admin@usta.edu.co"
        consulta_email = "consulta@usta.edu.co"

        admin = db.query(User).filter(User.username == admin_email).first()
        if not admin:
            admin = User(
                username=admin_email,
                full_name="Administrador Proyección Social",
                hashed_password=get_password_hash("AdminUsta2026*"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            print(f"[OK] Usuario Administrador creado: {admin_email}")

        consulta = db.query(User).filter(User.username == consulta_email).first()
        if not consulta:
            consulta = User(
                username=consulta_email,
                full_name="Funcionario de Consulta (Decanatura)",
                hashed_password=get_password_hash("Consulta2026*"),
                role="consulta",
                is_active=True
            )
            db.add(consulta)
            print(f"[OK] Usuario de Consulta creado: {consulta_email}")

        # 2. Seed Periods
        for code, y, s, desc in [
            ("2026-1", 2026, 1, "Primer Periodo Académico 2026"),
            ("2026-2", 2026, 2, "Segundo Periodo Académico 2026"),
            ("2027-1", 2027, 1, "Primer Periodo Académico 2027")
        ]:
            p = db.query(AcademicPeriod).filter(AcademicPeriod.code == code).first()
            if not p:
                p = AcademicPeriod(code=code, year=y, semester=s, description=desc, is_active=True)
                db.add(p)
                print(f"[OK] Periodo {code} registrado.")
        db.commit()

        # 3. Load Excel Reference Data if available
        excel_file = DATA_DIR / "DIAGNOSTICO_PERFIL_EMPRENDEDOR_2026.xlsx"
        count_2026_1 = db.query(SurveyResponse).filter(SurveyResponse.period_code == "2026-1").count()
        count_2026_2 = db.query(SurveyResponse).filter(SurveyResponse.period_code == "2026-2").count()

        if excel_file.exists() and (count_2026_1 == 0 or count_2026_2 == 0):
            print(f"Sincronizando periodos 2026-1 y 2026-2 desde {excel_file.name}...")
            proc = ExcelProcessor()
            rows = proc.parse_excel_file(excel_file)
            print(f"Filas encontradas en el archivo: {len(rows)}")

            rows_2026_1 = [r for r in rows if detect_period_from_date(r.get("submission_start", "")) == "2026-1"]
            rows_2026_2 = [r for r in rows if detect_period_from_date(r.get("submission_start", "")) == "2026-2"]

            print(f"  - Registros para 2026-1 (meses 04-05): {len(rows_2026_1)}")
            print(f"  - Registros para 2026-2 (meses 09-10): {len(rows_2026_2)}")

            # Preview & Commit 2026-1
            p1_res = proc.analyze_preview(rows_2026_1, db, excel_file.name, "2026-1")
            commit_1 = proc.commit_upload(p1_res["temp_file_id"], "2026-1", db, loaded_by="Instalador Automático")
            print(f"  [OK] Carga 2026-1: {commit_1['total_processed']} registros.")

            # Preview & Commit 2026-2
            p2_res = proc.analyze_preview(rows_2026_2, db, excel_file.name, "2026-2")
            commit_2 = proc.commit_upload(p2_res["temp_file_id"], "2026-2", db, loaded_by="Instalador Automático")
            print(f"  [OK] Carga 2026-2: {commit_2['total_processed']} registros.")

        total_final = db.query(SurveyResponse).count()
        print(f"\n=======================================================")
        print(f"BASE DE DATOS INICIALIZADA EXITOSAMENTE")
        print(f"Total registros almacenados: {total_final}")
        print(f"Credenciales de acceso:")
        print(f"  Admin:    admin@usta.edu.co / AdminUsta2026*")
        print(f"  Consulta: consulta@usta.edu.co / Consulta2026*")
        print(f"=======================================================")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
