import urllib.request
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from app.config import DATA_DIR

def test_upload():
    print("Iniciando prueba de carga de Excel contra /api/upload/preview...")

    # 1. Login as admin
    login_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=json.dumps({"username": "admin@usta.edu.co", "password": "AdminUsta2026*"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as resp:
        token = json.loads(resp.read().decode("utf-8"))["access_token"]
    print("Token obtenido para admin.")

    # 2. Build multipart payload
    boundary = "----TestBoundary123456789"
    excel_path = DATA_DIR / "DIAGNOSTICO_PERFIL_EMPRENDEDOR_2026.xlsx"
    with open(excel_path, "rb") as f:
        file_bytes = f.read()

    lines = [
        f"--{boundary}".encode("utf-8"),
        b'Content-Disposition: form-data; name="file"; filename="DIAGNOSTICO_PERFIL_EMPRENDEDOR_2026.xlsx"',
        b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        b"",
        file_bytes,
        f"--{boundary}--".encode("utf-8"),
        b""
    ]
    payload = b"\r\n".join(lines)

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/upload/preview",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}"
        }
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("[OK] Preview exitoso. Código:", resp.status)
        print("  - Archivo:", data["filename"])
        print("  - Total filas:", data["total_rows"])
        print("  - Autorizados:", data["authorized_rows"])
        print("  - No autorizados:", data["unauthorized_rows"])
        print("  - Periodo dominante detectado:", data["detected_period"])
        print("  - Desglose por periodos:", data.get("periods_detected"))
        print("  - Nuevos:", data["new_rows"], "| Modificados:", data["updated_rows"], "| Sin cambios:", data["unchanged_rows"])
        temp_id = data["temp_file_id"]
        assert data["total_rows"] == 848

    # 3. Test Confirm with auto_split
    confirm_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/upload/confirm",
        data=json.dumps({
            "temp_file_id": temp_id,
            "period_code": "auto_split",
            "mode": "smart_update"
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    with urllib.request.urlopen(confirm_req) as resp:
        cdata = json.loads(resp.read().decode("utf-8"))
        print("[OK] Confirmación exitosa:")
        print("  - Periodos afectados:", cdata.get("period_code"))
        print("  - Mensaje:", cdata.get("message"))
        print("  - Procesados:", cdata.get("total_processed"))
        print("  - Nuevos:", cdata.get("new_records"), "| Modificados:", cdata.get("updated_records"), "| Sin cambios:", cdata.get("unchanged_records"))

    print("PRUEBA DE PREVIEW Y CONFIRMACIÓN COMPLETADA CON ÉXITO.")

if __name__ == "__main__":
    test_upload()
