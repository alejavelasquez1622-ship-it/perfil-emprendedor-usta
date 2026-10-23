from collections import Counter
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import PROFILE_QUESTIONS, INNPULSA_STAGES
from app.models import SurveyResponse, AcademicPeriod

def get_filtered_query(
    db: Session,
    period_code: Optional[str] = None,
    faculty_name: Optional[str] = None,
    semester: Optional[str] = None,
    initiative_status: Optional[str] = None,
    stage: Optional[str] = None,
    only_authorized: bool = True
):
    query = db.query(SurveyResponse)
    if only_authorized:
        query = query.filter(SurveyResponse.authorized == True)
    if period_code and period_code != "Todos":
        query = query.filter(SurveyResponse.period_code == period_code)
    if faculty_name and faculty_name != "Todas":
        query = query.filter(SurveyResponse.faculty_name == faculty_name)
    if semester and semester != "Todos":
        query = query.filter(SurveyResponse.semester_enrolled == semester)
    if initiative_status and initiative_status != "Todos":
        if initiative_status == "con_iniciativa":
            query = query.filter(SurveyResponse.has_initiative == True)
        elif initiative_status == "sin_iniciativa":
            query = query.filter(SurveyResponse.has_initiative == False)
        else:
            query = query.filter(SurveyResponse.initiative_status == initiative_status)
    if stage and stage != "Todas":
        query = query.filter(SurveyResponse.stage == stage)
    return query

def compute_kpis(all_responses: List[SurveyResponse]) -> Dict[str, Any]:
    """Calculates top-level indicators for cards and summaries."""
    total = len(all_responses)
    if total == 0:
        return {
            "total_encuestas": 0,
            "autorizadas": 0,
            "no_autorizadas": 0,
            "con_iniciativa": 0,
            "pct_con_iniciativa": 0.0,
            "sin_iniciativa": 0,
            "pct_sin_iniciativa": 0.0,
            "facultades_count": 0,
            "semestres_count": 0,
            "apoyo_recibido_count": 0,
            "pct_apoyo_recibido": 0.0
        }

    authorized = [r for r in all_responses if r.authorized]
    unauthorized_count = total - len(authorized)
    base_auth = len(authorized)

    con_iniciativa = sum(1 for r in authorized if r.has_initiative)
    sin_iniciativa = base_auth - con_iniciativa
    pct_con = round((con_iniciativa / base_auth * 100), 1) if base_auth > 0 else 0.0
    pct_sin = round((sin_iniciativa / base_auth * 100), 1) if base_auth > 0 else 0.0

    faculties = set(r.faculty_name for r in authorized if r.faculty_name)
    semesters = set(r.semester_enrolled for r in authorized if r.semester_enrolled)

    # Support received among those with initiatives
    iniciativas = [r for r in authorized if r.has_initiative]
    con_apoyo = sum(1 for r in iniciativas if r.received_support and "s" in str(r.received_support).lower())
    pct_apoyo = round((con_apoyo / len(iniciativas) * 100), 1) if len(iniciativas) > 0 else 0.0

    return {
        "total_encuestas": total,
        "autorizadas": base_auth,
        "no_autorizadas": unauthorized_count,
        "con_iniciativa": con_iniciativa,
        "pct_con_iniciativa": pct_con,
        "sin_iniciativa": sin_iniciativa,
        "pct_sin_iniciativa": pct_sin,
        "facultades_count": len(faculties),
        "semestres_count": len(semesters),
        "apoyo_recibido_count": con_apoyo,
        "pct_apoyo_recibido": pct_apoyo
    }

def compute_distribution(items: List[str], base_total: Optional[int] = None) -> List[Dict[str, Any]]:
    """Generates counts and percentages from a list of strings."""
    counter = Counter(items)
    total = base_total if base_total is not None else len(items)
    if total == 0:
        return []

    result = []
    for label, count in counter.most_common():
        pct = round((count / total) * 100, 1)
        result.append({
            "label": label,
            "count": count,
            "percentage": pct
        })
    return result

def compute_stages_distribution(iniciativas: List[SurveyResponse]) -> List[Dict[str, Any]]:
    """Calculates stage distribution strictly adhering to INNPulsa definitions."""
    base_total = len(iniciativas)
    counter = Counter()

    for r in iniciativas:
        st = r.stage or "Sin etapa identificada"
        counter[st] += 1

    result = []
    # Guarantee standard order
    for stage_name in INNPULSA_STAGES:
        c = counter.get(stage_name, 0)
        pct = round((c / base_total * 100), 1) if base_total > 0 else 0.0
        result.append({
            "label": stage_name,
            "count": c,
            "percentage": pct
        })

    # Include unclassified if any
    c_unclass = counter.get("Sin etapa identificada", 0)
    result.append({
        "label": "Sin etapa identificada",
        "count": c_unclass,
        "percentage": round((c_unclass / base_total * 100), 1) if base_total > 0 else 0.0
    })

    return result

def compute_funding_distribution(iniciativas: List[SurveyResponse]) -> List[Dict[str, Any]]:
    """Extracts funding categories (multiple mentions possible)."""
    base_total = len(iniciativas)
    if base_total == 0:
        return []

    # Map funding mentions
    counts = {
        "Recursos propios": 0,
        "Apoyo familiar": 0,
        "Ahorros": 0,
        "Crédito o préstamo": 0,
        "Otro": 0
    }

    for r in iniciativas:
        f1 = (r.funding_source_1 or "").strip().lower()
        f2 = (r.funding_source_2 or "").strip().lower()
        combined = f"{f1} {f2}"

        if "propio" in combined:
            counts["Recursos propios"] += 1
        if "famil" in combined or "padre" in combined or "mamá" in combined or "papá" in combined:
            counts["Apoyo familiar"] += 1
        if "ahorro" in combined:
            counts["Ahorros"] += 1
        if "préstamo" in combined or "prestamo" in combined or "banco" in combined or "crédito" in combined:
            counts["Crédito o préstamo"] += 1
        if "otro" in combined and "propio" not in combined and "ahorro" not in combined:
            counts["Otro"] += 1

    result = []
    for cat in ["Recursos propios", "Apoyo familiar", "Ahorros", "Crédito o préstamo"]:
        c = counts[cat]
        pct = round((c / base_total * 100), 1)
        result.append({"label": cat, "count": c, "percentage": pct})

    if counts["Otro"] > 0:
        result.append({"label": "Otro", "count": counts["Otro"], "percentage": round((counts["Otro"] / base_total * 100), 1)})

    return result

def compute_support_distribution(iniciativas: List[SurveyResponse]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Computes support status and declared entities."""
    base_total = len(iniciativas)
    if base_total == 0:
        return [], []

    yes_count = 0
    no_count = 0
    entities = Counter()

    for r in iniciativas:
        sup = str(r.received_support or "").strip().lower()
        if "s" in sup:
            yes_count += 1
            ent = str(r.support_entities_raw or "").strip()
            if not ent or "ninguna" in ent.lower():
                ent = "Sin entidad identificada"
            entities[ent] += 1
        else:
            no_count += 1

    status_dist = [
        {"label": "Sí recibió apoyo", "count": yes_count, "percentage": round((yes_count / base_total * 100), 1)},
        {"label": "No recibió apoyo", "count": no_count, "percentage": round((no_count / base_total * 100), 1)},
        {"label": "Sin respuesta clasificable", "count": 0, "percentage": 0.0}
    ]

    ent_dist = []
    if yes_count > 0:
        for name, cnt in entities.most_common():
            ent_dist.append({
                "label": name,
                "count": cnt,
                "percentage": round((cnt / yes_count * 100), 1)
            })

    return status_dist, ent_dist

def compute_question_profile(
    responses: List[SurveyResponse],
    attr_name: str,
    top_n: int = 3
) -> Dict[str, Any]:
    """
    Computes profile question distributions.
    Formats top_n individual options + 'Otras respuestas' matching reference PDF.
    """
    valid_answers = [getattr(r, attr_name) for r in responses if getattr(r, attr_name)]
    total_valid = len(valid_answers)
    total_eligible = len(responses)

    if total_valid == 0:
        return {
            "valid_responses": 0,
            "total_eligible": total_eligible,
            "top_options": [],
            "other_count": 0,
            "other_pct": 0.0,
            "all_options": []
        }

    counter = Counter(valid_answers)
    all_options = []
    for opt, cnt in counter.most_common():
        all_options.append({
            "label": opt,
            "count": cnt,
            "percentage": round((cnt / total_valid * 100), 1)
        })

    top_options = all_options[:top_n]
    top_count = sum(item["count"] for item in top_options)
    other_count = total_valid - top_count
    other_pct = round((other_count / total_valid * 100), 1) if total_valid > 0 else 0.0

    return {
        "valid_responses": total_valid,
        "total_eligible": total_eligible,
        "top_options": top_options,
        "other_count": other_count,
        "other_pct": other_pct,
        "all_options": all_options
    }

def generate_executive_summary(
    faculty_name: str,
    period_code: str,
    kpis: Dict[str, Any],
    top_stage: str,
    top_sector: str
) -> str:
    """Generates formal, non-colloquial institutional summary for Deans."""
    total = kpis["total_encuestas"]
    con_iniciativa = kpis["con_iniciativa"]
    pct_con = kpis["pct_con_iniciativa"]
    sin_iniciativa = kpis["sin_iniciativa"]
    pct_sin = kpis["pct_sin_iniciativa"]

    if total == 0:
        return "Para el periodo académico evaluado no se registran respuestas autorizadas en esta unidad académica."

    text = (
        f"Durante el periodo académico {period_code}, se consolidó un total de {total} respuestas en la facultad de {faculty_name}, "
        f"de las cuales {con_iniciativa} estudiantes ({pct_con} %) declararon contar con una iniciativa emprendedora o idea de negocio estructurada, "
        f"mientras que {sin_iniciativa} participantes ({pct_sin} %) manifestaron no poseer emprendimiento en la actualidad. "
    )
    if con_iniciativa > 0:
        if top_stage and top_stage != "N/A" and top_stage != "en proceso de caracterización":
            if " y " in top_stage:
                stage_clause = f"Las iniciativas se concentran principalmente en las etapas {top_stage}"
            else:
                stage_clause = f"La mayor concentración de iniciativas se ubica en la etapa {top_stage}"
        else:
            stage_clause = "Las iniciativas reportadas se encuentran en fase de caracterización inicial"

        if top_sector and top_sector not in ["Diversos sectores", "diversos sectores", "Sin sector", "N/A"]:
            sector_clause = f", con presencia destacada en el sector de {top_sector}."
        else:
            sector_clause = "."

        text += (
            f"{stage_clause}{sector_clause} "
            "Esta caracterización proporciona insumos objetivos a la Dirección de Proyección Social y al equipo directivo de la facultad "
            "para diseñar programas de acompañamiento, incubación y fortalecimiento acordes con el nivel de madurez y los recursos reportados."
        )
    else:
        text += (
            "Este comportamiento constituye un elemento de análisis para la definición de estrategias formativas de sensibilización "
            "y fomento de la cultura emprendedora articuladas con el plan de estudios de la facultad."
        )
    return text

def generate_accompaniment_guidelines(top_stage: str, has_initiatives: bool) -> Dict[str, str]:
    """Generates 3 formal accompaniment lines based on actual maturity."""
    return {
        "exploracion": (
            "Exploración e innovación: Talleres y metodologías ágiles de ideación orientados a estudiantes sin iniciativa, "
            "fomentando la detección de oportunidades y retos productivos en el contexto regional del Meta y la Orinoquía."
        ),
        "validacion": (
            "Validación y viabilidad: Asesoría técnica en investigación de mercado, entrevistas con clientes potenciales, "
            "prototipado rápido y formulación de propuestas de valor para proyectos en fases tempranas y pre-semilla."
        ),
        "fortalecimiento": (
            "Fortalecimiento empresarial: Consultoría especializada en planeación comercial, estructura de costos, formalización, "
            "gestión tributaria y articulación con redes de apoyo externas (SENA, Cámaras de Comercio y convocatorias públicas) "
            "para iniciativas consolidadas o en etapa de escalamiento."
        )
    }

def get_complete_faculty_report_data(
    db: Session,
    period_code: str,
    faculty_name: str
) -> Dict[str, Any]:
    """Gathers all processed data needed for web view or PDF report."""
    query = db.query(SurveyResponse).filter(
        SurveyResponse.period_code == period_code,
        SurveyResponse.faculty_name == faculty_name,
        SurveyResponse.authorized == True
    )
    responses = query.all()

    kpis = compute_kpis(responses)
    iniciativas = [r for r in responses if r.has_initiative]

    # Section 2: Participation table
    participacion_table = [
        {"label": "Con idea o emprendimiento", "count": kpis["con_iniciativa"], "percentage": kpis["pct_con_iniciativa"]},
        {"label": "Sin emprendimiento", "count": kpis["sin_iniciativa"], "percentage": kpis["pct_sin_iniciativa"]},
        {"label": "Sin clasificación", "count": 0, "percentage": 0.0}
    ]

    # Section 3: Stages (faithful evaluation of top stages with real counts)
    etapas = compute_stages_distribution(iniciativas)
    active_stages = [s for s in etapas if s["count"] > 0 and s["label"] != "Sin etapa identificada"]

    top_stage_highlight = ""
    top_stage_name = "N/A"

    if active_stages:
        max_c = max(s["count"] for s in active_stages)
        best_stages = [s for s in active_stages if s["count"] == max_c]

        # Only display highlight callout when there is an unequivocal predominant stage
        # (must have at least 2 initiatives and be the single clear leader, matching the reference report style)
        if len(best_stages) == 1 and best_stages[0]["count"] >= 2:
            st = best_stages[0]
            top_stage_name = st["label"]
            top_stage_highlight = f"La etapa con mayor reporte entre las iniciativas es {st['label']} ({st['percentage']:.1f} %)."
        else:
            # If tied, low-sample, or fragmented, do not add filler callout box (clean table only)
            top_stage_highlight = ""
            if len(best_stages) == 1:
                top_stage_name = best_stages[0]["label"]
            elif len(best_stages) == 2:
                top_stage_name = f"{best_stages[0]['label']} y {best_stages[1]['label']}"
            else:
                top_stage_name = "distribución diversa entre etapas"
    elif iniciativas:
        top_stage_highlight = ""
        top_stage_name = "en proceso de caracterización"
    else:
        top_stage_highlight = ""
        top_stage_name = "N/A"

    # Section 4: Sectors
    raw_sectors = [r.economic_sector.strip() for r in iniciativas if r.economic_sector and r.economic_sector.strip()]
    sectores = compute_distribution(raw_sectors, base_total=len(iniciativas))
    valid_sectors = [s for s in sectores if s["count"] > 0 and s["label"].lower() not in ["otro", "otra", "sin sector"]]
    top_sector_name = valid_sectors[0]["label"] if valid_sectors else (sectores[0]["label"] if (sectores and sectores[0]["count"] > 0) else "diversos sectores")

    # Section 5: Funding
    fuentes = compute_funding_distribution(iniciativas)

    # Section 6: Support
    apoyo_status, entidades = compute_support_distribution(iniciativas)

    # Section 7: Profile Questions
    perfil = {
        "P13": compute_question_profile(responses, "q_iniciativa", top_n=3),
        "P16": compute_question_profile(responses, "q_influencia_social", top_n=3),
        "P17": compute_question_profile(responses, "q_funcion_comercial", top_n=3),
        "P20": compute_question_profile(responses, "q_actitud_riesgo", top_n=3),
        "P21": compute_question_profile(responses, "q_validacion_viabilidad", top_n=3),
        # Additional profile questions for dashboard
        "P01": compute_question_profile(responses, "q_motivacion", top_n=3),
        "P02": compute_question_profile(responses, "q_gestion_problemas", top_n=3),
        "P03": compute_question_profile(responses, "q_motivacion_economica", top_n=3),
        "P04": compute_question_profile(responses, "q_dinero_propio", top_n=3),
        "P06": compute_question_profile(responses, "q_nuevo_proyecto", top_n=3),
        "P07": compute_question_profile(responses, "q_tiempo_dedicacion", top_n=3),
        "P10": compute_question_profile(responses, "q_liderazgo", top_n=3),
        "P11": compute_question_profile(responses, "q_satisfaccion_logros", top_n=3),
    }

    # Summary and recommendations
    resumen = generate_executive_summary(faculty_name, period_code, kpis, top_stage_name, top_sector_name)
    orientaciones = generate_accompaniment_guidelines(top_stage_name, len(iniciativas) > 0)
    metodologia = (
        f"Resultados correspondientes a {kpis['total_encuestas']} encuestas procesadas en {faculty_name} durante {period_code}. "
        "Las cifras describen a quienes diligenciaron voluntariamente el instrumento institucional y autorizaron el tratamiento "
        "de datos personales. Las variables de perfil corresponden a respuestas autodeclaradas y no constituyen un índice psicométrico validado."
    )

    return {
        "faculty_name": faculty_name,
        "period_code": period_code,
        "kpis": kpis,
        "participacion_table": participacion_table,
        "etapas": etapas,
        "top_stage_highlight": top_stage_highlight,
        "sectores": sectores,
        "fuentes": fuentes,
        "apoyo_status": apoyo_status,
        "entidades": entidades,
        "perfil": perfil,
        "resumen_ejecutivo": resumen,
        "orientaciones": orientaciones,
        "alcance_metodologico": metodologia
    }

def compute_period_comparison(
    db: Session,
    period_code_1: str,
    period_code_2: str,
    faculty_name: Optional[str] = None
) -> Dict[str, Any]:
    """Computes comparison between two academic periods with delta and percentage points."""
    q1 = db.query(SurveyResponse).filter(
        SurveyResponse.period_code == period_code_1,
        SurveyResponse.authorized == True
    )
    q2 = db.query(SurveyResponse).filter(
        SurveyResponse.period_code == period_code_2,
        SurveyResponse.authorized == True
    )

    if faculty_name and faculty_name != "Todas":
        q1 = q1.filter(SurveyResponse.faculty_name == faculty_name)
        q2 = q2.filter(SurveyResponse.faculty_name == faculty_name)

    resp_1 = q1.all()
    resp_2 = q2.all()

    kpis_1 = compute_kpis(resp_1)
    kpis_2 = compute_kpis(resp_2)

    def calc_delta(val1: float, val2: float, is_pct: bool = False):
        diff = round(val2 - val1, 1)
        rel_pct = round(((val2 - val1) / val1 * 100), 1) if val1 > 0 else 0.0
        return {
            "val1": val1,
            "val2": val2,
            "diff": diff,
            "rel_pct": rel_pct,
            "is_positive": diff >= 0
        }

    kpi_comparison = {
        "participantes": calc_delta(kpis_1["total_encuestas"], kpis_2["total_encuestas"]),
        "con_iniciativa": calc_delta(kpis_1["con_iniciativa"], kpis_2["con_iniciativa"]),
        "pct_con_iniciativa": calc_delta(kpis_1["pct_con_iniciativa"], kpis_2["pct_con_iniciativa"], is_pct=True),
        "sin_iniciativa": calc_delta(kpis_1["sin_iniciativa"], kpis_2["sin_iniciativa"]),
        "pct_sin_iniciativa": calc_delta(kpis_1["pct_sin_iniciativa"], kpis_2["pct_sin_iniciativa"], is_pct=True),
        "apoyo_count": calc_delta(kpis_1["apoyo_recibido_count"], kpis_2["apoyo_recibido_count"]),
        "pct_apoyo": calc_delta(kpis_1["pct_apoyo_recibido"], kpis_2["pct_apoyo_recibido"], is_pct=True)
    }

    # Faculty comparison breakdown
    faculties_all = sorted(list(set(
        [r.faculty_name for r in resp_1 if r.faculty_name] + [r.faculty_name for r in resp_2 if r.faculty_name]
    )))
    fac_breakdown = []
    for f in faculties_all:
        f_resp_1 = [r for r in resp_1 if r.faculty_name == f]
        f_resp_2 = [r for r in resp_2 if r.faculty_name == f]
        t1 = len(f_resp_1)
        t2 = len(f_resp_2)
        init1 = sum(1 for r in f_resp_1 if r.has_initiative)
        init2 = sum(1 for r in f_resp_2 if r.has_initiative)
        p1 = round((init1 / t1 * 100), 1) if t1 > 0 else 0.0
        p2 = round((init2 / t2 * 100), 1) if t2 > 0 else 0.0
        diff_pp = round(p2 - p1, 1)

        fac_breakdown.append({
            "faculty": f,
            "total_p1": t1,
            "total_p2": t2,
            "init_p1": init1,
            "init_p2": init2,
            "pct_p1": p1,
            "pct_p2": p2,
            "diff_pp": diff_pp
        })

    # Stage comparison
    init_1 = [r for r in resp_1 if r.has_initiative]
    init_2 = [r for r in resp_2 if r.has_initiative]
    st_1 = compute_stages_distribution(init_1)
    st_2 = compute_stages_distribution(init_2)
    stage_comp = []
    for s_name in INNPULSA_STAGES:
        c1 = next((item["count"] for item in st_1 if item["label"] == s_name), 0)
        p1 = next((item["percentage"] for item in st_1 if item["label"] == s_name), 0.0)
        c2 = next((item["count"] for item in st_2 if item["label"] == s_name), 0)
        p2 = next((item["percentage"] for item in st_2 if item["label"] == s_name), 0.0)
        stage_comp.append({
            "stage": s_name,
            "count_p1": c1,
            "pct_p1": p1,
            "count_p2": c2,
            "pct_p2": p2,
            "diff_pp": round(p2 - p1, 1)
        })

    analytical_commentary = (
        f"Al contrastar los periodos {period_code_1} y {period_code_2}, la participación total pasó de "
        f"{kpis_1['total_encuestas']} a {kpis_2['total_encuestas']} participantes. "
        f"La tasa de estudiantes con iniciativas o ideas emprendedoras presentó una variación de "
        f"{kpi_comparison['pct_con_iniciativa']['diff']:+} puntos porcentuales ({kpis_1['pct_con_iniciativa']}% vs {kpis_2['pct_con_iniciativa']}%). "
        "Nota metodológica: Las variaciones observadas reflejan diferencias transversales entre cohortes de estudiantes y no deben interpretarse "
        "como trayectorias longitudinales individuales de los mismos sujetos."
    )

    return {
        "period_1": period_code_1,
        "period_2": period_code_2,
        "faculty_name": faculty_name or "Universidad Completa",
        "kpi_comparison": kpi_comparison,
        "fac_breakdown": fac_breakdown,
        "stage_comparison": stage_comp,
        "analytical_commentary": analytical_commentary
    }
