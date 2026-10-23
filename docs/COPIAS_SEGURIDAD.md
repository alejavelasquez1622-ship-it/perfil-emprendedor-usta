# PROTOCOLO DE COPIAS DE SEGURIDAD Y RESTAURACIÓN
## Sistema de Análisis y Seguimiento del Perfil Emprendedor
### Universidad Santo Tomás – Seccional Villavicencio
**Dependencia:** Dirección de Proyección Social

---

## 1. Estrategia de Respaldo

Para garantizar la integridad y preservación histórica de la información académica (2026, 2027, 2028 y periodos posteriores), el sistema implementa dos modalidades complementarias de copia de seguridad:

1. **Copia de Seguridad Lógica (JSON Estructurado):**
   - Exporta todos los periodos, respuestas normalizadas, usuarios y configuraciones en un formato estándar, legible, auditable y portable entre diferentes motores de base de datos.
2. **Copia de Seguridad Física (Snapshot SQLite):**
   - Copia bit a bit del archivo `data/usta_perfil.db`.

---

## 2. Procedimiento de Respaldo desde la Interfaz Web

Cualquier funcionario con rol de **Administrador** puede generar una copia de seguridad en segundos:
1. Ingrese con sus credenciales al aplicativo web.
2. Diríjase a la vista **«Administración»** en el menú lateral.
3. En la tarjeta **Copias de Seguridad**, haga clic en:
   **«⬇️ Exportar Copia de Seguridad»**.
4. Su navegador descargará de inmediato un archivo con la nomenclatura:
   `Respaldo_USTA_Perfil_Emprendedor_AAAAMMDD_HHMMSS.json`.
5. Almacene este archivo en el repositorio institucional o SharePoint de la Dirección de Proyección Social.

---

## 3. Procedimiento de Respaldo Automatizado por Consola (CLI)

En servidores institucionales, es recomendable programar una copia automática periódica (semanal o al cierre de cada cohorte).

### Ejecución manual por terminal:
```bash
python scripts/create_backup.py
```
El archivo generado se almacenará en la carpeta `data/backups/`.

### Automatización en Linux (Crontab):
Para ejecutar una copia todos los domingos a las 23:00 hrs:
```bash
0 23 * * 0 /opt/perfil-emprendedor-usta/venv/bin/python /opt/perfil-emprendedor-usta/scripts/create_backup.py >> /var/log/usta_backup.log 2>&1
```

### Automatización en Windows (Programador de Tareas):
1. Abra el *Programador de Tareas de Windows*.
2. Cree una tarea básica semanal.
3. En Acción, seleccione *Iniciar un programa*:
   - Programa: `python.exe` (ruta a python)
   - Argumentos: `scripts\create_backup.py`
   - Iniciar en: `C:\ruta\al\proyecto\perfil-emprendedor-usta`

---

## 4. Procedimiento de Restauración

### Opción A: Desde la Interfaz Web (Administración)
1. Ingrese al módulo **«Administración»**.
2. En la tarjeta **Copias de Seguridad**, haga clic en **«Restaurar Respaldo»**.
3. Seleccione el archivo `.json` previamente generado.
4. Confirme el mensaje del sistema.
5. El sistema integrará los periodos y respuestas faltantes sin duplicar registros existentes y confirmará el total de datos restaurados.

### Opción B: Por Línea de Comandos (CLI)
En caso de migración en frío de servidor:
```bash
python scripts/restore_backup.py data/backups/Respaldo_USTA_Perfil_Emprendedor_20261022_120000.json
```
El script reportará el número exacto de registros y periodos reconstruidos.
