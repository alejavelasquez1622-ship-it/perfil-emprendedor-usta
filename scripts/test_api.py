import urllib.request
import json

def run_tests():
    print("Iniciando pruebas de integración HTTP contra http://127.0.0.1:8000...")

    # 1. Test Index HTML
    with urllib.request.urlopen("http://127.0.0.1:8000/") as resp:
        print("[OK] 1. Index status:", resp.status)
        html = resp.read().decode("utf-8")
        assert "Sistema de Análisis y Seguimiento del Perfil Emprendedor" in html
        print("   Titulo institucional verificado en HTML.")

    # 2. Test Periods API
    with urllib.request.urlopen("http://127.0.0.1:8000/api/periods") as resp:
        periods = json.loads(resp.read().decode("utf-8"))
        print("[OK] 2. Periods API status:", resp.status, "Total periodos:", len(periods))
        for p in periods:
            print(f"   - {p['code']}: Total {p['total_responses']} | Autorizados {p['authorized_responses']} | Facultades: {p['faculty_count']}")

    # 3. Test Dashboard API
    with urllib.request.urlopen("http://127.0.0.1:8000/api/stats/dashboard?period_code=2026-1") as resp:
        dash = json.loads(resp.read().decode("utf-8"))
        print("[OK] 3. Dashboard API status:", resp.status)
        print("   KPIs 2026-1:", dash["kpis"])

    # 4. Test Faculty Detail API
    with urllib.request.urlopen("http://127.0.0.1:8000/api/stats/faculty-detail?period_code=2026-1&faculty_name=Ingenier%C3%ADa%20Industrial") as resp:
        fac = json.loads(resp.read().decode("utf-8"))
        print("[OK] 4. Faculty Detail API status:", resp.status)
        print(f"   Ingeniería Industrial 2026-1 -> Participantes: {fac['kpis']['total_encuestas']}, Con iniciativa: {fac['kpis']['con_iniciativa']}")

    # 5. Test Comparison API
    with urllib.request.urlopen("http://127.0.0.1:8000/api/stats/comparison?period_1=2026-1&period_2=2026-2&faculty_name=Todas") as resp:
        comp = json.loads(resp.read().decode("utf-8"))
        print("[OK] 5. Comparison API status:", resp.status)
        print(f"   P1 Total: {comp['kpi_comparison']['participantes']['val1']} vs P2 Total: {comp['kpi_comparison']['participantes']['val2']}")

    # 6. Test PDF Reports
    with urllib.request.urlopen("http://127.0.0.1:8000/api/reports/faculty-pdf?period_code=2026-1&faculty_name=Ingenier%C3%ADa%20Industrial") as resp:
        pdf_bytes = resp.read()
        print("[OK] 6. Faculty PDF status:", resp.status, f"Tamano bytes: {len(pdf_bytes)}")
        assert len(pdf_bytes) > 5000

    with urllib.request.urlopen("http://127.0.0.1:8000/api/reports/general-pdf?period_code=2026-1") as resp:
        gen_bytes = resp.read()
        print("[OK] 7. General Institutional PDF status:", resp.status, f"Tamano bytes: {len(gen_bytes)}")
        assert len(gen_bytes) > 5000

    with urllib.request.urlopen("http://127.0.0.1:8000/api/reports/comparative-pdf?period_1=2026-1&period_2=2026-2&faculty_name=Todas") as resp:
        comp_bytes = resp.read()
        print("[OK] 8. Comparative PDF status:", resp.status, f"Tamano bytes: {len(comp_bytes)}")
        assert len(comp_bytes) > 3000

    with urllib.request.urlopen("http://127.0.0.1:8000/api/reports/faculties-zip?period_code=2026-1") as resp:
        zip_bytes = resp.read()
        print("[OK] 9. Bulk ZIP status:", resp.status, f"Tamano bytes: {len(zip_bytes)}")
        assert len(zip_bytes) > 50000

    # 10. Test Login
    login_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=json.dumps({"username": "admin@usta.edu.co", "password": "AdminUsta2026*"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as resp:
        login_res = json.loads(resp.read().decode("utf-8"))
        print("[OK] 10. Login status:", resp.status, "Token recibido para:", login_res["user"]["full_name"])

    print("\n=======================================================")
    print("TODAS LAS PRUEBAS DE INTEGRACIÓN FUERON EXITOSAS (10/10)")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
