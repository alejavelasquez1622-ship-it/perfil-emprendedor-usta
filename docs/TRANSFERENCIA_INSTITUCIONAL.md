# ACTA Y PROTOCOLO DE TRANSFERENCIA INSTITUCIONAL
## Sistema de Análisis y Seguimiento del Perfil Emprendedor
### Universidad Santo Tomás – Seccional Villavicencio
**Destinatario:** Dirección de Proyección Social y Departamento de Tecnologías de la Información (DTI)

---

## 1. Declaración de Propiedad y Autonomía Institucional

El presente aplicativo ha sido concebido y desarrollado bajo estrictos principios de **independencia tecnológica, sostenibilidad, transferibilidad y soberanía del dato institucional**:

1. **Sin dependencias de cuentas personales:** El funcionamiento del sistema no depende de la cuenta, correo ni computador del desarrollador.
2. **Cero costos recurrentes:** El stack seleccionado (Python, FastAPI, SQLite/PostgreSQL, ReportLab, Tailwind CSS) es de código abierto con licencias permisivas (MIT, BSD, Apache 2.0). La universidad no incurre en cobros mensuales por licencias de software, bases de datos propietarias ni cuotas de usuario.
3. **Plena potestad de modificación:** La Universidad Santo Tomás recibe el código fuente completo, comentado, desacoplado y documentado para su custodia, mantenimiento y evolución futura.

---

## 2. Lista de Entregables Formales (Checklist de Cumplimiento)

| Entregable | Ubicación / Archivo | Estado |
| :--- | :--- | :--- |
| **1. Código fuente completo** | `/app/`, `/scripts/`, `/docs/` | Entregado y probado |
| **2. Base de datos persistente** | `/data/usta_perfil.db` | Inicializada con 848 registros |
| **3. Módulo de carga Excel** | `/app/excel_processor.py` | Funcional con Forms original |
| **4. Control de duplicados** | Algoritmo SHA-256 en `/app/excel_processor.py` | Probado (0 duplicados) |
| **5. Dashboard interactivo** | `/app/static/js/app.js` + Chart.js | 6 gráficos + filtros |
| **6. Análisis por facultad** | `/api/stats/faculty-detail` | 14 facultades caracterizadas |
| **7. Comparación de periodos** | `/app/stats_service.py` | Cálculo $\Delta$ y $\Delta\text{ pp}$ |
| **8. Generador de PDF individual** | `/app/pdf_generator.py` | 4 páginas, idéntico a referencia |
| **9. Descarga masiva en ZIP** | `/api/reports/faculties-zip` | 15 PDFs en un solo paquete |
| **10. Informe general y comparativo** | `/app/pdf_generator.py` | Disponibles en PDF |
| **11. Plantilla maestra institucional** | `/app/pdf_generator.py` | Diseño unificado y normativo |
| **12. Histórico de periodos** | Vista y API `/api/periods` | Cohortes 2026-1, 2026-2, 2027-1 |
| **13. Administración de usuarios** | Módulo `/api/admin/users` | Roles Admin y Consulta |
| **14. Lanzadores en 1 clic** | `iniciar_sistema.bat`, `iniciar_sistema.ps1` | Probados en Windows |
| **15. Manual de Usuario** | `/docs/MANUAL_USUARIO.md` | Guía para no programadores |
| **16. Manual Técnico** | `/docs/MANUAL_TECNICO.md` | Arquitectura y modelo de datos |
| **17. Guía de Despliegue** | `/docs/GUIA_DESPLIEGUE.md` | Windows, Linux, Docker, IIS |
| **18. Protocolo de Respaldo** | `/docs/COPIAS_SEGURIDAD.md` | Respaldo web y scripts CLI |

---

## 3. Hoja de Ruta para Integración con Microsoft 365 (Fase 2)

El sistema ha sido estructurado con una arquitectura modular que permite, en una segunda etapa, conectar directamente el archivo de Microsoft Forms alojado en el OneDrive o SharePoint institucional mediante **Microsoft Graph API**.

### Requisitos institucionales previos en Azure Active Directory:
1. Registro de una aplicación en el portal de Azure AD institucional de la Universidad Santo Tomás (`portal.azure.com`).
2. Configuración de permisos de aplicación tipo `Files.Read.All` o delegados con OAuth 2.0.
3. Obtención de:
   - `TENANT_ID`
   - `CLIENT_ID`
   - `CLIENT_SECRET`
4. Parámetros a configurar en el archivo `.env`:
   ```env
   M365_INTEGRATION_ENABLED=True
   M365_TENANT_ID=xxxx-xxxx-xxxx
   M365_CLIENT_ID=yyyy-yyyy-yyyy
   M365_CLIENT_SECRET=zzzz-zzzz-zzzz
   M365_FORMS_EXCEL_SHAREPOINT_URL=https://ustavillavicencio.sharepoint.com/...
   ```
5. Mientras estos permisos corporativos son formalizados por el área de infraestructura de TI de la sede, **el sistema opera de forma plena, autónoma y continua a través de la carga manual del archivo Excel descargado**.

---

## 4. Credenciales Iniciales de Entrega

Para la recepción inicial del sistema se entregan las siguientes cuentas:

- **Administrador:**
  - Correo: `admin@usta.edu.co`
  - Contraseña inicial: `AdminUsta2026*`
  *(Se recomienda al funcionario cambiar la contraseña desde el panel de administración tras la primera sesión).*

- **Usuario de Consulta:**
  - Correo: `consulta@usta.edu.co`
  - Contraseña inicial: `Consulta2026*`

---

## 5. Procedimiento de Traspaso del Repositorio

1. Copiar la carpeta íntegra `perfil-emprendedor-usta` al servidor o almacenamiento institucional.
2. Definir los administradores titulares en la Dirección de Proyección Social.
3. Ejecutar `python scripts/create_backup.py` para generar el primer respaldo en frío.
4. Conectar al DNS institucional (ej. `perfil.villavicencio.usta.edu.co`) siguiendo la `GUIA_DESPLIEGUE.md`.
