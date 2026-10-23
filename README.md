# Sistema de Análisis y Seguimiento del Perfil Emprendedor
## Universidad Santo Tomás – Seccional Villavicencio
### Dirección de Proyección Social

![USTA Logo](app/static/img/logo_usta.png)

Aplicativo web institucional, funcional, seguro y transferible para el procesamiento, análisis estadístico, seguimiento y generación de informes ejecutivos en PDF para las decanaturas a partir del cuestionario institucional **«DIAGNÓSTICO DE PERFIL EMPRENDEDOR»**.

---

## 🚀 Inicio Rápido (1 Clic en Windows)

Simplemente ejecute el archivo:
```cmd
iniciar_sistema.bat
```
*(o con PowerShell: `.\iniciar_sistema.ps1`)*

El sistema instalará automáticamente las dependencias si no están presentes, inicializará la base de datos persistente con el dataset histórico y abrirá el navegador en:
**http://localhost:8000**

### Credenciales de Acceso Iniciales:
- **Administrador:** `admin@usta.edu.co` / `AdminUsta2026*`
- **Usuario de Consulta:** `consulta@usta.edu.co` / `Consulta2026*`

---

## ✨ Características Principales

1. **Carga Directa de Microsoft Forms:** Lee el archivo `.xlsx` original descargado de Microsoft Forms sin necesidad de modificar encabezados ni fórmulas.
2. **Control Inteligente de Duplicados:** Al volver a cargar el mismo archivo o una versión más reciente, el sistema detecta mediante hashes SHA-256 los registros nuevos, los modificados y los idénticos, evitando duplicaciones de datos.
3. **Protección de Datos Personales (Ley 1581 de 2012):** Separa rigurosamente las respuestas autorizadas de las no autorizadas. Los informes para decanaturas no incluyen datos de contacto ni identificadores personales.
4. **Dashboard Administrativo Interactivo:** Filtros reactivos por Periodo Académico (`AAAA-1` / `AAAA-2`), Facultad, Semestre, Estado de Iniciativa y Etapa INNPulsa. Gráficos dinámicos con Chart.js.
5. **Generación de Informes en PDF Oficiales:** Motor ReportLab Platypus que replica exactamente la plantilla institucional de 4 páginas de la Universidad Santo Tomás con estilos corporativos, tablas, métricas y recomendaciones.
6. **Descarga Masiva en ZIP:** Genera con un solo clic todos los informes de las 14 facultades más el informe consolidado general empaquetados en un archivo ZIP.
7. **Comparación Histórica de Periodos:** Compara métricas entre periodos (ej. `2026-1` vs `2026-2`) con cálculo de variaciones absolutas y puntos porcentuales ($\Delta\text{ pp}$).
8. **Administración y Copias de Seguridad:** Gestión de usuarios con roles (Admin y Consulta), creación de periodos futuros y exportación/restauración de respaldos en formato JSON.

---

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.12 + FastAPI + Uvicorn
- **Base de Datos:** SQLite 3 en modo WAL (con soporte nativo para PostgreSQL vía SQLAlchemy)
- **Procesamiento de Datos:** Openpyxl + Pandas
- **Motor de Renderizado PDF:** ReportLab Platypus con `NumberedCanvas`
- **Frontend:** HTML5 semántico, Tailwind CSS, Chart.js, Vanilla JavaScript (sin frameworks pesados ni dependencias externas de compilación)

---

## 📂 Estructura del Proyecto

```
perfil-emprendedor-usta/
├── app/
│   ├── main.py                    # API REST y rutas del aplicativo
│   ├── config.py                  # Parámetros, colores y mapeo de preguntas
│   ├── database.py                # Conexión SQLAlchemy y SQLite WAL
│   ├── models.py                  # Modelos de base de datos relacional
│   ├── schemas.py                 # Esquemas de validación Pydantic
│   ├── auth.py                    # Autenticación segura Bcrypt y JWT
│   ├── excel_processor.py         # Lector de Forms, hashes y control de duplicados
│   ├── stats_service.py           # Cálculos estadísticos y agregaciones
│   ├── pdf_generator.py           # Motor de generación de informes PDF y ZIP
│   ├── static/                    # Recursos CSS, JS e imágenes institucionales
│   └── templates/
│       └── index.html             # Interfaz web responsiva
├── data/                          # Almacenamiento persistente
│   ├── usta_perfil.db             # Base de datos SQLite
│   ├── DIAGNOSTICO_PERFIL_EMPRENDEDOR_2026.xlsx # Dataset de referencia
│   └── Informe_Referencia_Ingenieria_Industrial_2026-1.pdf
├── docs/                          # Documentación institucional
│   ├── MANUAL_USUARIO.md          # Manual para funcionarios
│   ├── MANUAL_TECNICO.md          # Especificaciones de arquitectura
│   ├── GUIA_DESPLIEGUE.md         # Despliegue en Windows/Linux/Docker
│   ├── COPIAS_SEGURIDAD.md        # Respaldo y recuperación
│   └── TRANSFERENCIA_INSTITUCIONAL.md # Protocolo de entrega a USTA
├── scripts/
│   ├── seed_data.py               # Inicializador de datos y usuarios
│   ├── create_backup.py           # Generador de respaldos CLI
│   ├── restore_backup.py          # Restaurador de respaldos CLI
│   └── test_api.py                # Suite de pruebas automatizadas
├── requirements.txt               # Dependencias de Python
├── Dockerfile                     # Imagen de contenedor Docker
├── docker-compose.yml             # Orquestación de contenedores
├── iniciar_sistema.bat            # Lanzador para Windows
└── iniciar_sistema.ps1            # Lanzador para PowerShell
```

---

## 🧪 Pruebas de Integración Automatizadas

Para ejecutar la suite completa de pruebas:
```bash
python scripts/test_api.py
```
Verifica automáticamente:
1. Servidor HTTP y plantilla HTML semántica.
2. API de autenticación y roles.
3. Indicadores del dashboard para periodos y facultades.
4. Generación de PDF individual de facultad.
5. Generación de PDF institucional general.
6. Generación de PDF comparativo.
7. Generación de paquete ZIP masivo.

---

## 🏛️ Propiedad Institucional
Desarrollado para la **Dirección de Proyección Social** de la **Universidad Santo Tomás – Seccional Villavicencio**.
Sostenible, autónomo y sin costos recurrentes.
