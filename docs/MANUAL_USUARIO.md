# MANUAL DE USUARIO
## Sistema de Análisis y Seguimiento del Perfil Emprendedor
### Universidad Santo Tomás – Seccional Villavicencio
**Dependencia:** Dirección de Proyección Social

---

## 1. Introducción y Objetivo del Sistema

El **Sistema de Análisis y Seguimiento del Perfil Emprendedor** es una plataforma web desarrollada a la medida para la **Dirección de Proyección Social** de la Universidad Santo Tomás, Seccional Villavicencio. 

Su propósito central es automatizar el procesamiento, consolidación, análisis estadístico y emisión de informes ejecutivos en formato PDF para las decanaturas a partir de las respuestas del cuestionario institucional aplicado a los estudiantes.

El aplicativo ha sido diseñado pensando en funcionarios que **no poseen conocimientos de programación**, permitiendo operar todo el ciclo de información mediante una interfaz gráfica intuitiva, moderna y en español.

---

## 2. Acceso y Roles de Usuario

### 2.1. Ingreso a la plataforma
1. Abra un navegador web moderno (Google Chrome o Microsoft Edge).
2. Diríjase a la dirección institucional suministrada (por ejemplo: `http://localhost:8000` o la URL del servidor universitario).
3. En la barra superior, haga clic en el botón dorado **«Acceder»**.
4. Ingrese sus credenciales institucionales:
   - **Correo institucional**
   - **Contraseña**

### 2.2. Roles disponibles
- **Administrador:** Diseñado para los coordinadores de Proyección Social. Permite cargar y actualizar archivos Excel, gestionar periodos académicos, crear usuarios, generar copias de seguridad y emitir todos los informes.
- **Usuario de Consulta:** Diseñado para decanos y personal administrativo. Permite navegar los dashboards interactivos, aplicar filtros por facultad y semestre, previsualizar y descargar los informes PDF, sin riesgo de alterar la base de datos original.

---

## 3. Navegación Principal

El sistema organiza sus funciones en un menú lateral accesible:

- 🏠 **Inicio / Resumen:** Panorama global de participantes, respuestas autorizadas, tasa de emprendimiento y estado de las cohortes registradas.
- 📊 **Panel de Análisis (Dashboard):** Visualizaciones interactivas con filtros multidimensionales (periodo, facultad, semestre, estado de iniciativa y etapa INNPulsa).
- 🏛️ **Análisis por Facultad:** Vista detallada de una unidad académica específica con resumen ejecutivo y líneas de acompañamiento.
- ⚖️ **Comparación de Periodos:** Módulo comparativo entre dos semestres académicos con cálculo automático de variaciones absolutas y puntos porcentuales ($\Delta\text{ pp}$).
- 📤 **Cargar Información:** Módulo para importar el archivo Excel descargado directamente de Microsoft Forms.
- 📄 **Generar Informes (PDF):** Centro de emisión para descargar reportes individuales, consolidados generales, comparativos o el paquete masivo en ZIP.
- 🕒 **Histórico de Periodos:** Bitácora permanente de cohortes académicas y auditoría de cargas previas.
- ⚙️ **Administración:** Gestión de usuarios, nuevos periodos y respaldos de seguridad.

---

## 4. Módulo de Carga de Información (Excel de Forms)

### 4.1. Preparación del archivo
**No es necesario modificar el archivo descargado de Microsoft Forms.**
- El sistema acepta directamente el archivo con extensión `.xlsx`.
- No cambie los nombres de las columnas.
- No elimine filas vacías ni modifique fórmulas.

### 4.2. Paso a paso de la carga
1. Ingrese a la vista **«Cargar Información»** en el menú lateral.
2. Haga clic en la zona punteada o arrastre el archivo `DIAGNÓSTICO DE PERFIL EMPRENDEDOR [AÑO].xlsx`.
3. El sistema procesará el archivo en memoria y abrirá la **Ventana de Previsualización y Control de Duplicados**.

### 4.3. Interpretación de la pantalla de verificación
La ventana muestra un balance exacto de los datos antes de guardarlos:
- **Total Filas:** Cantidad total de registros en el Excel.
- **Autorizados:** Estudiantes que seleccionaron *"Autorizo"* para el tratamiento de datos personales. Estos registros alimentan las caracterizaciones y porcentajes de perfil.
- **No Autorizados:** Registros donde el estudiante no autorizó. El sistema los conserva únicamente como conteo administrativo de participación, protegiendo su privacidad.
- **Nuevos:** Encuestas que no existían previamente en ese periodo.
- **Modificados:** Respuestas que ya existían pero cuyo contenido cambió en el formulario de origen.
- **Sin Cambios:** Registros idénticos a los ya almacenados (no se duplican).
- **Alerta de Registros Menores:** Si el archivo tiene menos respuestas que la base actual, el sistema emitirá una advertencia preventiva para evitar pérdidas accidentales.
4. Seleccione el modo de actualización:
   - **Actualización Inteligente (Recomendado):** Agrega los nuevos, actualiza los modificados y conserva los existentes.
   - **Sustitución Completa:** Reemplaza todos los registros del periodo.
5. Haga clic en **«Confirmar y Actualizar Base de Datos»**.

---

## 5. Consulta y Uso del Dashboard Interactivo

En el **Panel de Análisis**, utilice los selectores de la barra superior para explorar la información:
- **Periodo:** Permite ver una cohorte específica (ej. `2026-1`, `2026-2`) o el acumulado general.
- **Facultad:** Filtre por cualquiera de las 14 facultades institucionales.
- **Semestre:** Examine las tendencias desde 1° hasta 10° semestre.
- **Iniciativa Emprendedora:** Concentre el análisis en estudiantes con ideas/empresas activas o sin iniciativa.
- **Etapa INNPulsa:** Filtre por madurez (Pre-semilla, Semilla, Temprana, Consolidación, Escalamiento).

Los gráficos circulares, barras de distribución y tarjetas se actualizan al instante de forma reactiva.

---

## 6. Generación de Informes Institucionales (PDF y ZIP)

El módulo **«Generar Informes»** ofrece 4 opciones estándar con la plantilla institucional oficial:

### Opción 1: Informe Individual por Facultad
1. Seleccione el Periodo Académico y la Facultad.
2. Haga clic en **«Previsualizar»** para revisar el documento en pantalla sin descargarlo, o en **«Descargar PDF»** para guardarlo localmente.
3. El archivo tendrá el nombre formal: `Informe_[Nombre_Facultad]_[Periodo].pdf`.

### Opción 2: Todos los Informes por Facultad en ZIP (Descarga Masiva)
1. Seleccione el Periodo Académico (ej. `2026-1`).
2. Haga clic en **«Descargar Paquete ZIP con Todos los Informes»**.
3. El sistema generará en segundos los 14 informes independientes de cada facultad más el informe general consolidado, comprimidos en un archivo `Informes_Facultades_[Periodo].zip`.

### Opción 3: Informe General Consolidado
Genera el informe institucional de toda la Seccional Villavicencio para presentar ante la Vicerrectoría o el Consejo Académico.

### Opción 4: Informe Comparativo
Seleccione dos periodos (ej. `2026-1` vs `2026-2`) y la unidad académica para obtener el informe PDF con tablas comparativas y análisis de puntos porcentuales.

---

## 7. Copias de Seguridad y Respaldo

En la sección **«Administración»**:
- **Exportar Copia de Seguridad:** Con un solo clic descarga un archivo `.json` que contiene todos los periodos, respuestas, usuarios y configuraciones.
- **Restaurar Respaldo:** Permite cargar un archivo de respaldo previo para restablecer el sistema en caso de mantenimiento de servidores.
