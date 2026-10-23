# MANUAL TÉCNICO Y DE ARQUITECTURA
## Sistema de Análisis y Seguimiento del Perfil Emprendedor
### Universidad Santo Tomás – Seccional Villavicencio
**Dependencia:** Dirección de Proyección Social

---

## 1. Arquitectura General del Sistema

El sistema implementa una arquitectura desacoplada basada en microservicios ligeros con Python 3.12 y FastAPI, orientada a alta disponibilidad, portabilidad institucional y cero costos recurrentes de licencias.

```
┌────────────────────────────────────────────────────────┐
│           Capa de Presentación Web (SPA)               │
│ HTML5 Semántico + Tailwind CSS + Chart.js + JavaScript │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / REST / JSON
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI Application                     │
│  - Control de Autenticación JWT (Bcrypt + HttpOnly)     │
│  - Middleware de Seguridad y CORS                      │
│  - Motor de Normalización y Carga Excel (openpyxl)     │
│  - Motor Estadístico y de Comparación (stats_service)  │
│  - Motor de Renderizado PDF Vectorial (ReportLab)      │
└──────────────────────────┬─────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼─────────────────────────────┐
│                 Base de Datos Persistente              │
│       SQLite 3 con WAL Mode (o PostgreSQL en Prod)     │
└────────────────────────────────────────────────────────┘
```

### Componentes principales
1. **Backend:** FastAPI 0.110+ sobre ASGI Uvicorn.
2. **Procesamiento de Archivos:** `openpyxl` para lectura estricta y sanitización de tablas de Microsoft Forms (`OfficeForms.Table` o `Sheet1`).
3. **Motor Estadístico:** Algoritmo propio de agregación con exclusión rigurosa de registros no autorizados para variables cualitativas, cálculo de porcentajes sobre denominadores válidos y cálculo de variaciones en puntos porcentuales ($\Delta\text{ pp}$).
4. **Motor de Generación PDF:** `ReportLab Platypus` con `NumberedCanvas` (cálculo de 2 pasadas para numeración formal "Página X de Y", encabezados institucionales fijos y estilos tipográficos corporativos).
5. **Base de Datos:** SQLite 3 en modo `PRAGMA journal_mode=WAL` (Write-Ahead Logging) y `PRAGMA foreign_keys=ON`. Totalmente migrable a PostgreSQL con solo cambiar la variable `DATABASE_URL`.

---

## 2. Modelo de Datos y Esquema Relacional

### Tabla: `academic_periods`
Almacena la definición de los semestres académicos con restricción de unicidad en `code` (`AAAA-1` o `AAAA-2`).
- `id` (INTEGER, PK)
- `code` (VARCHAR(20), UNIQUE, INDEX)
- `year` (INTEGER)
- `semester` (INTEGER)
- `description` (VARCHAR(255))
- `is_active` (BOOLEAN)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

### Tabla: `survey_responses`
Almacena las respuestas del diagnóstico asociadas a cada periodo.
- `id` (INTEGER, PK)
- `period_id` (INTEGER, FK -> academic_periods.id, ON DELETE CASCADE)
- `period_code` (VARCHAR(20), INDEX)
- `original_id` (VARCHAR(50), INDEX)
- `submission_start` (VARCHAR(50))
- `submission_end` (VARCHAR(50))
- `authorized` (BOOLEAN, INDEX)
- `faculty_name` (VARCHAR(150), INDEX)
- `program_name` (VARCHAR(150))
- `semester_enrolled` (VARCHAR(50), INDEX)
- **Preguntas de perfil:** `q_motivacion`, `q_gestion_problemas`, `q_motivacion_economica`, `q_dinero_propio`, `q_iniciativa`, `q_nuevo_proyecto`, `q_tiempo_dedicacion`, `q_influencia_social`, `q_funcion_comercial`, `q_liderazgo`, `q_satisfaccion_logros`, `q_actitud_riesgo`, `q_validacion_viabilidad`.
- **Caracterización:** `has_initiative`, `initiative_status`, `stage`, `stage_raw`, `idea_name`, `idea_description`, `problem_addressed`, `time_invested_months`, `has_invested_money`, `invested_amount_raw`, `funding_source_1`, `funding_source_2`, `monthly_sales_raw`, `business_model_type`, `team_size_raw`, `received_support`, `support_entities_raw`, `economic_sector`, `target_market`.
- `raw_data_hash` (VARCHAR(64), INDEX): Hash SHA-256 de los campos de la fila.
- **Índices de unicidad y rendimiento:**
  - `UNIQUE (period_id, original_id)`: Garantiza que no existan duplicados dentro de un mismo periodo.
  - `INDEX (period_code, faculty_name)`: Optimiza los filtros de consulta del dashboard y generación de reportes.

### Tabla: `users`
- `id` (INTEGER, PK)
- `username` (VARCHAR(120), UNIQUE, INDEX)
- `full_name` (VARCHAR(150))
- `hashed_password` (VARCHAR(255)): Hash generado con `bcrypt` (gensalt de 12 rondas).
- `role` (VARCHAR(30)): `"admin"` o `"consulta"`.
- `is_active` (BOOLEAN)
- `last_login` (DATETIME)

### Tabla: `load_history`
Auditoría y trazabilidad de importaciones.
- `id` (INTEGER, PK)
- `period_id` (INTEGER, FK)
- `period_code` (VARCHAR(20))
- `filename` (VARCHAR(255))
- `total_rows`, `authorized_rows`, `unauthorized_rows`
- `new_rows`, `updated_rows`, `unchanged_rows`
- `loaded_by`, `loaded_at`

---

## 3. Algoritmo de Detección de Duplicados y Actualización Inteligente

Para cumplir con el Requisito 8 del pliego (evitar duplicaciones al recargar cortes más recientes del mismo periodo):

```python
# Pseudo-código del algoritmo implementado en ExcelProcessor:
for fila in filas_excel:
    id_original = fila["Id"]
    hash_fila = sha256(fila.valores_ordenados)
    
    registro_existente = db.buscar(periodo_id, id_original)
    if not registro_existente:
        estado = "NUEVO"
        accion = "INSERTAR"
    else:
        if registro_existente.hash == hash_fila:
            estado = "SIN_CAMBIOS"
            accion = "OMITIR"
        else:
            estado = "MODIFICADO"
            accion = "ACTUALIZAR"
```

### Resultados garantizados:
1. Si se cargan 800 encuestas y al mes siguiente se carga el archivo con 950, el sistema agrega exactamente las 150 nuevas y actualiza las que hayan sido corregidas.
2. Si se carga dos veces el mismo archivo de 848 registros, el balance resultante es: `Nuevos: 0 | Modificados: 0 | Sin Cambios: 848`, manteniendo intacta la base de datos en 848 registros.

---

## 4. Reglas de Cálculo Estadístico y Calidad del Dato

Siguiendo las directrices institucionales de Proyección Social:
1. **Denominador de Caracterización:** Se calcula exclusivamente sobre la población que respondió `Autorizo` en el tratamiento de datos personales.
2. **Denominador de Etapas, Sectores y Financiación:** Se calcula únicamente sobre la subpoblación con iniciativa declarada (`has_initiative == True`).
3. **Agrupación de Preguntas de Perfil:** En el informe PDF formal para decanaturas, se reportan las 3 opciones con mayor frecuencia individualmente, y las opciones restantes se consolidan bajo la categoría `Otras respuestas` con el número exacto de respuestas válidas reportado en el subtítulo (`X respuestas válidas de Y`).
4. **Variación entre Periodos:** Se calculan tanto las diferencias absolutas ($\Delta$) como la variación relativa en porcentaje y la diferencia en **puntos porcentuales** ($\Delta\text{ pp}$), incorporando la aclaración metodológica de no inferencia longitudinal individual sobre cohortes independientes.

---

## 5. Especificaciones de la Plantilla Maestra PDF (ReportLab)

Los informes PDF utilizan una plantilla maestra única (`generate_faculty_pdf`) que asegura coherencia total entre todas las facultades:
- **Dimensiones:** Estándar A4 (`595.27 x 841.89` pt).
- **Márgenes:** 36 pt (1.27 cm) en los cuatro bordes.
- **Paleta Oficial:**
  - Azul Institucional Primario: `#0B2545` (RGB: 11, 37, 69)
  - Azul Medio: `#133E87` (RGB: 19, 62, 135)
  - Dorado USTA: `#FDB813` (RGB: 253, 184, 19)
  - Fondo Encabezados de Tabla: `#EBF3FA` (RGB: 235, 243, 250)
  - Bordes de Rejilla: `#CBD5E1` (RGB: 203, 213, 225)
- **Estructura editorial fija de 4 páginas:**
  - Página 1: Banner institucional, Metadatos (Facultad, Periodo, Emisión), 3 Tarjetas KPI principales, 1. Resumen ejecutivo, 2. Participación y situación emprendedora (tabla y barra visual proporcional), 3. Etapas de las iniciativas (INNPulsa) con recuadro destacado.
  - Página 2: Encabezado continuo, 4. Sectores económicos, 5. Fuentes de financiación, 6. Apoyo institucional declarado y entidades mencionadas.
  - Página 3: Encabezado continuo, 7. Orientaciones del perfil emprendedor (Tablas descriptivas para P13 Iniciativa, P16 Comunicación, P17 Comercial).
  - Página 4: Encabezado continuo, 7. Orientaciones del perfil (P20 Riesgo, P21 Validación), 8. Orientaciones de acompañamiento institucional (3 líneas estratégicas adaptadas), 9. Alcance metodológico y pie de página institucional.

---

## 6. Seguridad y Protección de Datos Personales (Ley 1581 de 2012)

1. **Principio de Privacidad desde el Diseño:**
   - La base de datos y los informes PDF para decanaturas **no incluyen nombres, números de cédula, correos personales ni teléfonos de los estudiantes**.
   - Los resultados se presentan únicamente de manera agrupada y anonimizada.
2. **Autenticación y Sesiones:**
   - Hashing de contraseñas mediante algoritmo `bcrypt` estándar de la industria.
   - Tokens de sesión JWT transmitidos tanto en header `Authorization: Bearer` como en cookie `HttpOnly`, con flag `SameSite=Lax`.
3. **Control de Acceso Basado en Roles (RBAC):**
   - Endpoints de carga, administración de usuarios, creación de periodos y respaldos protegidos por la dependencia `require_admin`.
