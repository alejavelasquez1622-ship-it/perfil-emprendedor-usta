import io
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from app.config import (
    LOGO_PATH, INSTITUTION_NAME, DEPENDENCY_NAME, SYSTEM_NAME,
    COLOR_NAVY_HEX, COLOR_GOLD_HEX, COLOR_LIGHT_BLUE_HEX
)
from app.stats_service import (
    get_complete_faculty_report_data, compute_period_comparison,
    compute_kpis, compute_stages_distribution, compute_distribution,
    compute_funding_distribution, compute_support_distribution,
    compute_question_profile, generate_accompaniment_guidelines
)

# Numbered canvas to calculate total pages (Page X of Y)
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        
        # Footer text
        footer_text = f"{INSTITUTION_NAME} · {DEPENDENCY_NAME} | Uso institucional"
        self.drawString(36, 25, footer_text)
        
        # Page number right-aligned
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(A4[0] - 36, 25, page_str)
        self.restoreState()

def create_report_styles():
    styles = getSampleStyleSheet()

    title_header = ParagraphStyle(
        "BannerTitle",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.white
    )
    banner_sup = ParagraphStyle(
        "BannerSup",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#D1D5DB")
    )
    banner_sub = ParagraphStyle(
        "BannerSub",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#E5E7EB")
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#6B7280")
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor(COLOR_NAVY_HEX)
    )
    kpi_num = ParagraphStyle(
        "KpiNum",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=24,
        textColor=colors.HexColor(COLOR_NAVY_HEX)
    )
    kpi_label = ParagraphStyle(
        "KpiLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1F2937")
    )
    kpi_sub = ParagraphStyle(
        "KpiSub",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#6B7280")
    )
    sec_title = ParagraphStyle(
        "SectionTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(COLOR_NAVY_HEX),
        spaceBefore=10,
        spaceAfter=5
    )
    sec_sub = ParagraphStyle(
        "SectionSubtitle",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=4
    )
    body_p = ParagraphStyle(
        "BodyFormal",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#374151"),
        spaceAfter=6
    )
    table_cell = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1F2937")
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1F2937")
    )
    table_cell_right = ParagraphStyle(
        "TableCellRight",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        alignment=2,
        textColor=colors.HexColor("#1F2937")
    )
    table_header = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor(COLOR_NAVY_HEX)
    )
    table_header_right = ParagraphStyle(
        "TableHeaderRight",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor(COLOR_NAVY_HEX)
    )
    running_header = ParagraphStyle(
        "RunningHeader",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#6B7280")
    )

    return {
        "BannerTitle": title_header,
        "BannerSup": banner_sup,
        "BannerSub": banner_sub,
        "MetaLabel": meta_label,
        "MetaVal": meta_val,
        "KpiNum": kpi_num,
        "KpiLabel": kpi_label,
        "KpiSub": kpi_sub,
        "SectionTitle": sec_title,
        "SectionSubtitle": sec_sub,
        "BodyFormal": body_p,
        "TableCell": table_cell,
        "TableCellBold": table_cell_bold,
        "TableCellRight": table_cell_right,
        "TableHeader": table_header,
        "TableHeaderRight": table_header_right,
        "RunningHeader": running_header
    }

def build_data_table(
    data_list: List[Dict[str, Any]],
    styles: Dict[str, ParagraphStyle],
    col_widths: List[float] = [340, 80, 100],
    highlight_total: bool = False
) -> Table:
    """Creates a standardized USTA data table with Cantidad and Porcentaje."""
    table_data = [
        [
            Paragraph("Indicador o respuesta", styles["TableHeader"]),
            Paragraph("Cantidad", styles["TableHeaderRight"]),
            Paragraph("Porcentaje", styles["TableHeaderRight"])
        ]
    ]

    for item in data_list:
        lbl = item.get("label", "")
        cnt = str(item.get("count", 0))
        pct = f"{item.get('percentage', 0.0):.1f} %"
        
        is_total = "total" in lbl.lower()
        c_style = styles["TableCellBold"] if is_total else styles["TableCell"]
        r_style = styles["TableCellBold"] if is_total else styles["TableCellRight"]

        table_data.append([
            Paragraph(lbl, c_style),
            Paragraph(cnt, r_style),
            Paragraph(pct, r_style)
        ])

    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_LIGHT_BLUE_HEX)),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t

def build_question_table(
    q_data: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
    col_widths: List[float] = [340, 80, 100]
) -> Table:
    """Formats question table with Top 3 + Otras respuestas matching reference PDF."""
    items = []
    for opt in q_data.get("top_options", []):
        items.append({
            "label": opt["label"],
            "count": opt["count"],
            "percentage": opt["percentage"]
        })

    if q_data.get("other_count", 0) > 0:
        items.append({
            "label": "Otras respuestas",
            "count": q_data["other_count"],
            "percentage": q_data["other_pct"]
        })

    return build_data_table(items, styles, col_widths)

def generate_faculty_pdf(data: Dict[str, Any], output_path: Optional[Path] = None) -> bytes:
    """
    Generates a 4-page formal institutional PDF matching the official USTA reference document.
    """
    buffer = io.BytesIO()
    target_file = str(output_path) if output_path else buffer
    doc = SimpleDocTemplate(
        target_file,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = create_report_styles()
    story = []
    page_width = A4[0] - 72  # 523.27 pt printable width

    fac_name = data["faculty_name"]
    per_code = data["period_code"]
    emission_date = datetime.now().strftime("%d de %B de %Y").replace(
        "January", "enero").replace("February", "febrero").replace("March", "marzo").replace(
        "April", "abril").replace("May", "mayo").replace("June", "junio").replace(
        "July", "julio").replace("August", "agosto").replace("September", "septiembre").replace(
        "October", "octubre").replace("November", "noviembre").replace("December", "diciembre")

    # ================= PAGE 1 =================
    # Institutional Header Banner
    banner_content = [
        [
            Paragraph("UNIVERSIDAD SANTO TOMÁS · SECCIONAL VILLAVICENCIO", styles["BannerSup"]),
        ],
        [
            Paragraph("Informe de perfil emprendedor estudiantil", styles["BannerTitle"]),
        ],
        [
            Paragraph("Dirección de Proyección Social · Caracterización por facultad y periodo", styles["BannerSub"]),
        ]
    ]
    banner_table = Table(banner_content, colWidths=[page_width])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_NAVY_HEX)),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(COLOR_NAVY_HEX)),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Metadata Box
    meta_table_data = [
        [
            Paragraph("FACULTAD", styles["MetaLabel"]),
            Paragraph("PERIODO ACADÉMICO", styles["MetaLabel"]),
            Paragraph("EMISIÓN", styles["MetaLabel"])
        ],
        [
            Paragraph(fac_name, styles["MetaVal"]),
            Paragraph(per_code, styles["MetaVal"]),
            Paragraph(emission_date, styles["MetaVal"])
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[page_width * 0.45, page_width * 0.28, page_width * 0.27])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3 Stat Cards
    kpis = data["kpis"]
    card1 = [
        Paragraph(str(kpis["total_encuestas"]), styles["KpiNum"]),
        Paragraph("Participantes", styles["KpiLabel"]),
        Paragraph("Encuestas del periodo", styles["KpiSub"])
    ]
    card2 = [
        Paragraph(str(kpis["con_iniciativa"]), styles["KpiNum"]),
        Paragraph("Con iniciativa", styles["KpiLabel"]),
        Paragraph(f"{kpis['pct_con_iniciativa']:.1f} % del total", styles["KpiSub"])
    ]
    card3 = [
        Paragraph(str(kpis["sin_iniciativa"]), styles["KpiNum"]),
        Paragraph("Sin emprendimiento", styles["KpiLabel"]),
        Paragraph(f"{kpis['pct_sin_iniciativa']:.1f} % del total", styles["KpiSub"])
    ]
    stat_cards_data = [[card1, card2, card3]]
    card_w = page_width / 3.0
    stat_cards_table = Table(stat_cards_data, colWidths=[card_w, card_w, card_w])
    stat_cards_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBEFORE', (0, 0), (-1, -1), 3, colors.HexColor(COLOR_NAVY_HEX)),
    ]))
    story.append(stat_cards_table)
    story.append(Spacer(1, 12))

    # Section 1: Resumen ejecutivo
    story.append(Paragraph("1. Resumen ejecutivo", styles["SectionTitle"]))
    story.append(Paragraph(data["resumen_ejecutivo"], styles["BodyFormal"]))
    story.append(Spacer(1, 8))

    # Section 2: Participación y situación emprendedora
    story.append(Paragraph("2. Participación y situación emprendedora", styles["SectionTitle"]))
    part_table = build_data_table(data["participacion_table"], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
    story.append(part_table)
    story.append(Spacer(1, 4))

    # Visual proportion bar
    pct_con_bar = kpis["pct_con_iniciativa"]
    bar_w_con = (pct_con_bar / 100.0) * page_width if pct_con_bar > 0 else 0
    bar_w_sin = page_width - bar_w_con
    bar_cells = [["", ""]]
    bar_table = Table(bar_cells, colWidths=[bar_w_con, bar_w_sin], rowHeights=[7])
    bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#2563EB")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(bar_table)
    story.append(Spacer(1, 2))
    story.append(Paragraph("Azul: estudiantes con idea o emprendimiento · Fondo: resto de participantes", styles["SectionSubtitle"]))
    story.append(Spacer(1, 8))

    # Section 3: Etapas de las iniciativas
    story.append(Paragraph("3. Etapas de las iniciativas", styles["SectionTitle"]))
    story.append(Paragraph(f"Base del análisis: {kpis['con_iniciativa']} estudiantes con idea o emprendimiento.", styles["SectionSubtitle"]))
    etapas_table = build_data_table(data["etapas"], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
    story.append(etapas_table)
    story.append(Spacer(1, 10))

    # ================= PAGE 2 =================
    story.append(PageBreak())
    story.append(Paragraph(f"{fac_name} · {per_code} | Caracterización de iniciativas", styles["RunningHeader"]))
    story.append(Spacer(1, 6))

    # Section 4: Sectores económicos
    story.append(Paragraph("4. Sectores económicos", styles["SectionTitle"]))
    sectores_table = build_data_table(data["sectores"][:8], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
    story.append(sectores_table)
    story.append(Spacer(1, 2))
    story.append(Paragraph("Se muestran los sectores declarados; las categorías “Otro” y las denominaciones no estandarizadas requieren revisión.", styles["SectionSubtitle"]))
    story.append(Spacer(1, 10))

    # Section 5: Fuentes de financiación
    story.append(Paragraph("5. Fuentes de financiación", styles["SectionTitle"]))
    story.append(Paragraph(f"Una persona puede mencionar más de una fuente. Base: {kpis['con_iniciativa']} participantes con iniciativa.", styles["SectionSubtitle"]))
    fuentes_table = build_data_table(data["fuentes"], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
    story.append(fuentes_table)
    story.append(Spacer(1, 10))

    # Section 6: Apoyo institucional declarado
    story.append(Paragraph("6. Apoyo institucional declarado", styles["SectionTitle"]))
    apoyo_table = build_data_table(data["apoyo_status"], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
    story.append(apoyo_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Entidades de apoyo mencionadas", styles["SectionTitle"]))
    if data["entidades"]:
        ent_table = build_data_table(data["entidades"][:6], styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18])
        story.append(ent_table)
    else:
        no_ent_p = Paragraph("No se registran entidades específicas reportadas en este periodo.", styles["BodyFormal"])
        story.append(no_ent_p)
    story.append(Spacer(1, 2))
    story.append(Paragraph("Entidades declaradas por quienes indicaron haber recibido apoyo. 'Sin entidad identificada' recoge respuestas vacías o no clasificables. Las siglas deben validarse antes de atribuirlas a una institución.", styles["SectionSubtitle"]))

    # ================= PAGE 3 =================
    story.append(PageBreak())
    story.append(Paragraph(f"{fac_name} · {per_code} | Perfil emprendedor declarado", styles["RunningHeader"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("7. Orientaciones del perfil emprendedor", styles["SectionTitle"]))
    story.append(Paragraph("Distribución descriptiva de respuestas. No representa una medición psicométrica ni una evaluación de competencias.", styles["SectionSubtitle"]))
    story.append(Spacer(1, 6))

    perfil = data["perfil"]

    # P13 - Iniciativa emprendedora
    p13_data = perfil.get("P13", {})
    story.append(Paragraph("Iniciativa emprendedora (P13)", styles["TableCellBold"]))
    story.append(Paragraph(f"{p13_data.get('valid_responses', 0)} respuestas válidas de {p13_data.get('total_eligible', 0)}. Opciones de respuesta más frecuentes.", styles["SectionSubtitle"]))
    story.append(build_question_table(p13_data, styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18]))
    story.append(Spacer(1, 8))

    # P16 - Comunicación e influencia social
    p16_data = perfil.get("P16", {})
    story.append(Paragraph("Comunicación e influencia social (P16)", styles["TableCellBold"]))
    story.append(Paragraph(f"{p16_data.get('valid_responses', 0)} respuestas válidas de {p16_data.get('total_eligible', 0)}. Opciones de respuesta más frecuentes.", styles["SectionSubtitle"]))
    story.append(build_question_table(p16_data, styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18]))
    story.append(Spacer(1, 8))

    # P17 - Orientación comercial
    p17_data = perfil.get("P17", {})
    story.append(Paragraph("Orientación comercial (P17)", styles["TableCellBold"]))
    story.append(Paragraph(f"{p17_data.get('valid_responses', 0)} respuestas válidas de {p17_data.get('total_eligible', 0)}. Opciones de respuesta más frecuentes.", styles["SectionSubtitle"]))
    story.append(build_question_table(p17_data, styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18]))

    # ================= PAGE 4 =================
    story.append(PageBreak())
    story.append(Paragraph(f"{fac_name} · {per_code} | Perfil y recomendaciones", styles["RunningHeader"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("7. Orientaciones del perfil emprendedor (continuación)", styles["SectionTitle"]))
    story.append(Spacer(1, 4))

    # P20 - Actitud frente al riesgo
    p20_data = perfil.get("P20", {})
    story.append(Paragraph("Actitud frente al riesgo (P20)", styles["TableCellBold"]))
    story.append(Paragraph(f"{p20_data.get('valid_responses', 0)} respuestas válidas de {p20_data.get('total_eligible', 0)}. Opciones de respuesta más frecuentes.", styles["SectionSubtitle"]))
    story.append(build_question_table(p20_data, styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18]))
    story.append(Spacer(1, 8))

    # P21 - Validación y viabilidad
    p21_data = perfil.get("P21", {})
    story.append(Paragraph("Validación y viabilidad (P21)", styles["TableCellBold"]))
    story.append(Paragraph(f"{p21_data.get('valid_responses', 0)} respuestas válidas de {p21_data.get('total_eligible', 0)}. Opciones de respuesta más frecuentes.", styles["SectionSubtitle"]))
    story.append(build_question_table(p21_data, styles, [page_width * 0.65, page_width * 0.17, page_width * 0.18]))
    story.append(Spacer(1, 10))

    # Section 8: Orientaciones de acompañamiento
    story.append(Paragraph("8. Orientaciones de acompañamiento", styles["SectionTitle"]))
    orient = data["orientaciones"]
    acomp_p = (
        f"<b>Exploración e innovación:</b> {orient.get('exploracion', '')}<br/>"
        f"<b>Validación:</b> {orient.get('validacion', '')}<br/>"
        f"<b>Fortalecimiento empresarial:</b> {orient.get('fortalecimiento', '')}"
    )
    story.append(Paragraph(acomp_p, styles["BodyFormal"]))
    story.append(Paragraph("Estas líneas son orientaciones generales; su priorización debe considerar los resultados de cada pregunta y las necesidades manifestadas por los estudiantes.", styles["SectionSubtitle"]))
    story.append(Spacer(1, 10))

    # Section 9: Alcance metodológico
    story.append(Paragraph("9. Alcance metodológico", styles["SectionTitle"]))
    story.append(Paragraph(data["alcance_metodologico"], styles["BodyFormal"]))

    # Build document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    
    if output_path:
        return output_path.read_bytes()
    return buffer.getvalue()

def generate_institutional_general_pdf(
    db,
    period_code: str,
    output_path: Optional[Path] = None
) -> bytes:
    """Generates a comprehensive institutional report for the entire Universidad Santo Tomás."""
    # Aggregated data across all faculties
    from app.models import SurveyResponse
    all_responses = db.query(SurveyResponse).filter(
        SurveyResponse.period_code == period_code,
        SurveyResponse.authorized == True
    ).all()

    kpis = data_kpis = compute_kpis(all_responses)
    iniciativas = [r for r in all_responses if r.has_initiative]

    etapas_gen = compute_stages_distribution(iniciativas)
    active_gen = [s for s in etapas_gen if s["count"] > 0 and s["label"] != "Sin etapa identificada"]
    top_hl = ""
    top_stage_name_gen = "N/A"
    if active_gen:
        max_gen = max(s["count"] for s in active_gen)
        best_gen = [s for s in active_gen if s["count"] == max_gen]
        if len(best_gen) == 1:
            top_hl = f"A nivel institucional, la etapa más reportada entre las iniciativas es {best_gen[0]['label']} ({best_gen[0]['percentage']:.1f} %)."
            top_stage_name_gen = best_gen[0]['label']
        elif len(best_gen) == 2:
            top_hl = f"A nivel institucional, las etapas con mayor concentración son {best_gen[0]['label']} ({best_gen[0]['percentage']:.1f} %) y {best_gen[1]['label']} ({best_gen[1]['percentage']:.1f} %)."
            top_stage_name_gen = f"{best_gen[0]['label']} y {best_gen[1]['label']}"
        else:
            items_str = ", ".join([f"{s['label']} ({s['percentage']:.1f} %)" for s in best_gen[:-1]]) + f" y {best_gen[-1]['label']} ({best_gen[-1]['percentage']:.1f} %)"
            top_hl = f"A nivel institucional, las etapas con mayor concentración son {items_str}."
            top_stage_name_gen = ", ".join([s['label'] for s in best_gen[:-1]]) + f" y {best_gen[-1]['label']}"

    # Structure data as general university
    data = {
        "faculty_name": "Informe General Consolidado (Toda la Seccional)",
        "period_code": period_code,
        "kpis": kpis,
        "participacion_table": [
            {"label": "Con idea o emprendimiento", "count": kpis["con_iniciativa"], "percentage": kpis["pct_con_iniciativa"]},
            {"label": "Sin emprendimiento", "count": kpis["sin_iniciativa"], "percentage": kpis["pct_sin_iniciativa"]},
            {"label": "Sin clasificación", "count": 0, "percentage": 0.0}
        ],
        "etapas": etapas_gen,
        "top_stage_highlight": top_hl,
        "sectores": compute_distribution([r.economic_sector for r in iniciativas if r.economic_sector], len(iniciativas)),
        "fuentes": compute_funding_distribution(iniciativas),
        "apoyo_status": compute_support_distribution(iniciativas)[0],
        "entidades": compute_support_distribution(iniciativas)[1],
        "perfil": {
            "P13": compute_question_profile(all_responses, "q_iniciativa", top_n=3),
            "P16": compute_question_profile(all_responses, "q_influencia_social", top_n=3),
            "P17": compute_question_profile(all_responses, "q_funcion_comercial", top_n=3),
            "P20": compute_question_profile(all_responses, "q_actitud_riesgo", top_n=3),
            "P21": compute_question_profile(all_responses, "q_validacion_viabilidad", top_n=3),
        },
        "resumen_ejecutivo": (
            f"El presente informe institucional consolida los resultados del diagnóstico de perfil emprendedor "
            f"en la Universidad Santo Tomás, Seccional Villavicencio, para el periodo {period_code}. "
            f"Se analizaron {kpis['total_encuestas']} encuestas autorizadas en {kpis['facultades_count']} unidades académicas. "
            f"El {kpis['pct_con_iniciativa']}% de los participantes ({kpis['con_iniciativa']} estudiantes) reportó contar con "
            f"iniciativas o ideas de negocio, mientras que el {kpis['pct_sin_iniciativa']}% ({kpis['sin_iniciativa']} estudiantes) "
            "no manifiesta iniciativas activas en este momento."
        ),
        "orientaciones": generate_accompaniment_guidelines("Pre-semilla", len(iniciativas) > 0),
        "alcance_metodologico": (
            f"Consolidado general de {kpis['total_encuestas']} respuestas voluntarias autorizadas en {period_code}. "
            "Información destinada a la toma de decisiones estratégicas de la Dirección de Proyección Social y directivas seccionales."
        )
    }
    return generate_faculty_pdf(data, output_path)

def generate_comparative_pdf(
    comp_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> bytes:
    """Generates an institutional comparative report between two periods."""
    buffer = io.BytesIO()
    target_file = str(output_path) if output_path else buffer
    doc = SimpleDocTemplate(
        target_file,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = create_report_styles()
    story = []
    page_width = A4[0] - 72

    p1 = comp_data["period_1"]
    p2 = comp_data["period_2"]
    fac = comp_data["faculty_name"]

    # Header Banner
    banner_content = [
        [Paragraph("UNIVERSIDAD SANTO TOMÁS · SECCIONAL VILLAVICENCIO", styles["BannerSup"])],
        [Paragraph(f"Informe Comparativo de Periodos ({p1} vs {p2})", styles["BannerTitle"])],
        [Paragraph(f"Dirección de Proyección Social · Análisis Comparativo: {fac}", styles["BannerSub"])]
    ]
    banner_table = Table(banner_content, colWidths=[page_width])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_NAVY_HEX)),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Analytical Commentary
    story.append(Paragraph("1. Resumen y Consideraciones de Comparabilidad", styles["SectionTitle"]))
    story.append(Paragraph(comp_data["analytical_commentary"], styles["BodyFormal"]))
    story.append(Spacer(1, 10))

    # KPI Comparison Table
    story.append(Paragraph("2. Comparación de Indicadores Clave", styles["SectionTitle"]))
    k_comp = comp_data["kpi_comparison"]
    
    comp_table_data = [
        [
            Paragraph("Indicador", styles["TableHeader"]),
            Paragraph(f"Periodo {p1}", styles["TableHeaderRight"]),
            Paragraph(f"Periodo {p2}", styles["TableHeaderRight"]),
            Paragraph("Diferencia (Δ)", styles["TableHeaderRight"]),
            Paragraph("Variación", styles["TableHeaderRight"])
        ],
        [
            Paragraph("Participantes totales", styles["TableCellBold"]),
            Paragraph(str(int(k_comp["participantes"]["val1"])), styles["TableCellRight"]),
            Paragraph(str(int(k_comp["participantes"]["val2"])), styles["TableCellRight"]),
            Paragraph(f"{k_comp['participantes']['diff']:+g}", styles["TableCellRight"]),
            Paragraph(f"{k_comp['participantes']['rel_pct']:+.1f}%", styles["TableCellRight"])
        ],
        [
            Paragraph("Estudiantes con iniciativa", styles["TableCellBold"]),
            Paragraph(str(int(k_comp["con_iniciativa"]["val1"])), styles["TableCellRight"]),
            Paragraph(str(int(k_comp["con_iniciativa"]["val2"])), styles["TableCellRight"]),
            Paragraph(f"{k_comp['con_iniciativa']['diff']:+g}", styles["TableCellRight"]),
            Paragraph(f"{k_comp['con_iniciativa']['rel_pct']:+.1f}%", styles["TableCellRight"])
        ],
        [
            Paragraph("Tasa con iniciativa (%)", styles["TableCellBold"]),
            Paragraph(f"{k_comp['pct_con_iniciativa']['val1']:.1f}%", styles["TableCellRight"]),
            Paragraph(f"{k_comp['pct_con_iniciativa']['val2']:.1f}%", styles["TableCellRight"]),
            Paragraph(f"{k_comp['pct_con_iniciativa']['diff']:+.1f} pp", styles["TableCellRight"]),
            Paragraph("Puntos %", styles["TableCellRight"])
        ],
        [
            Paragraph("Sin emprendimiento", styles["TableCellBold"]),
            Paragraph(str(int(k_comp["sin_iniciativa"]["val1"])), styles["TableCellRight"]),
            Paragraph(str(int(k_comp["sin_iniciativa"]["val2"])), styles["TableCellRight"]),
            Paragraph(f"{k_comp['sin_iniciativa']['diff']:+g}", styles["TableCellRight"]),
            Paragraph(f"{k_comp['sin_iniciativa']['rel_pct']:+.1f}%", styles["TableCellRight"])
        ],
        [
            Paragraph("Iniciativas con apoyo institucional", styles["TableCellBold"]),
            Paragraph(str(int(k_comp["apoyo_count"]["val1"])), styles["TableCellRight"]),
            Paragraph(str(int(k_comp["apoyo_count"]["val2"])), styles["TableCellRight"]),
            Paragraph(f"{k_comp['apoyo_count']['diff']:+g}", styles["TableCellRight"]),
            Paragraph(f"{k_comp['pct_apoyo']['diff']:+.1f} pp", styles["TableCellRight"])
        ],
    ]
    t_comp = Table(comp_table_data, colWidths=[page_width * 0.40, page_width * 0.15, page_width * 0.15, page_width * 0.15, page_width * 0.15])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_LIGHT_BLUE_HEX)),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 12))

    # Stage comparison table
    story.append(Paragraph("3. Evolución por Etapas de Madurez (INNPulsa)", styles["SectionTitle"]))
    stage_data = [
        [
            Paragraph("Etapa INNPulsa", styles["TableHeader"]),
            Paragraph(f"{p1} (Cant.)", styles["TableHeaderRight"]),
            Paragraph(f"{p1} (%)", styles["TableHeaderRight"]),
            Paragraph(f"{p2} (Cant.)", styles["TableHeaderRight"]),
            Paragraph(f"{p2} (%)", styles["TableHeaderRight"]),
            Paragraph("Dif. (pp)", styles["TableHeaderRight"])
        ]
    ]
    for st in comp_data.get("stage_comparison", []):
        stage_data.append([
            Paragraph(st["stage"], styles["TableCell"]),
            Paragraph(str(st["count_p1"]), styles["TableCellRight"]),
            Paragraph(f"{st['pct_p1']:.1f}%", styles["TableCellRight"]),
            Paragraph(str(st["count_p2"]), styles["TableCellRight"]),
            Paragraph(f"{st['pct_p2']:.1f}%", styles["TableCellRight"]),
            Paragraph(f"{st['diff_pp']:+.1f} pp", styles["TableCellRight"])
        ])
    t_st = Table(stage_data, colWidths=[page_width * 0.35, page_width * 0.13, page_width * 0.13, page_width * 0.13, page_width * 0.13, page_width * 0.13])
    t_st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_LIGHT_BLUE_HEX)),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_st)
    story.append(Spacer(1, 12))

    # Faculty breakdown if full university
    fac_bd = comp_data.get("fac_breakdown", [])
    if len(fac_bd) > 1:
        story.append(Paragraph("4. Desglose Comparativo por Facultad", styles["SectionTitle"]))
        fb_data = [
            [
                Paragraph("Facultad", styles["TableHeader"]),
                Paragraph(f"{p1} Part.", styles["TableHeaderRight"]),
                Paragraph(f"{p1} % Con", styles["TableHeaderRight"]),
                Paragraph(f"{p2} Part.", styles["TableHeaderRight"]),
                Paragraph(f"{p2} % Con", styles["TableHeaderRight"]),
                Paragraph("Variación pp", styles["TableHeaderRight"])
            ]
        ]
        for f in fac_bd[:14]:
            fb_data.append([
                Paragraph(f["faculty"][:28], styles["TableCell"]),
                Paragraph(str(f["total_p1"]), styles["TableCellRight"]),
                Paragraph(f"{f['pct_p1']:.1f}%", styles["TableCellRight"]),
                Paragraph(str(f["total_p2"]), styles["TableCellRight"]),
                Paragraph(f"{f['pct_p2']:.1f}%", styles["TableCellRight"]),
                Paragraph(f"{f['diff_pp']:+.1f} pp", styles["TableCellRight"])
            ])
        t_fb = Table(fb_data, colWidths=[page_width * 0.40, page_width * 0.12, page_width * 0.12, page_width * 0.12, page_width * 0.12, page_width * 0.12])
        t_fb.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_LIGHT_BLUE_HEX)),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_fb)

    doc.build(story, canvasmaker=NumberedCanvas)
    if output_path:
        return output_path.read_bytes()
    return buffer.getvalue()

def generate_all_faculties_zip(db, period_code: str) -> io.BytesIO:
    """
    Generates all faculty PDF reports for the given period and zips them.
    Returns in-memory zip bytes buffer.
    """
    from app.models import SurveyResponse
    # Get all distinct faculties with responses in this period
    faculties = [
        f[0] for f in db.query(SurveyResponse.faculty_name).filter(
            SurveyResponse.period_code == period_code,
            SurveyResponse.authorized == True
        ).distinct().all()
    ]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Also include general institutional PDF
        gen_pdf_bytes = generate_institutional_general_pdf(db, period_code)
        zip_file.writestr(f"Informe_General_Consolidado_{period_code}.pdf", gen_pdf_bytes)

        for fac in sorted(faculties):
            fac_data = get_complete_faculty_report_data(db, period_code, fac)
            pdf_bytes = generate_faculty_pdf(fac_data)
            clean_name = re.sub(r'[^\w\-_\. ]', '_', fac).replace(" ", "_")
            filename = f"Informe_{clean_name}_{period_code}.pdf"
            zip_file.writestr(filename, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer
